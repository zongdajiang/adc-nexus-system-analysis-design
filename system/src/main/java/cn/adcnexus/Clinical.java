package cn.adcnexus;

import static cn.adcnexus.Db.*;
import static cn.adcnexus.Support.*;

import java.sql.*;
import java.util.*;

final class Clinical {
  static void requireAppointment(Connection c, Map<String,Object> visit, String expected) throws SQLException {
    var booking = one(c, "SELECT patient_id,clinic_id,dentist_id,chair_id,status FROM appointments WHERE id=?",
        visit.get("appointment_id"));
    check(booking != null && expected.equals(s(booking,"status"))
            && List.of("patient_id","clinic_id","dentist_id","chair_id").stream()
                .allMatch(key -> Objects.equals(booking.get(key),visit.get(key))),
        409, "APPOINTMENT_VISIT_MISMATCH", "预约与就诊记录不一致，请核实后继续");
  }
  static final String SELECT =
      "SELECT v.*,p.name_zh patient_name,p.patient_code,p.date_of_birth patient_date_of_birth,p.gender patient_gender,d.name_zh dentist_name,c.name_zh"
          + " clinic_name,a.scheduled_start_at FROM clinical_visits v JOIN patients p ON"
          + " p.id=v.patient_id JOIN dentists d ON d.id=v.dentist_id JOIN clinics c ON"
          + " c.id=v.clinic_id JOIN appointments a ON a.id=v.appointment_id ";

  static Object list(Connection c, Auth.Principal p) throws Exception {
    p.need("clinical.read");
    boundClinician(p);
    return rows(
        c,
        SELECT
            + " WHERE "
            + p.scope("v.clinic_id")
            + (p.dentistId() == null ? "" : " AND v.dentist_id=?")
            + " ORDER BY v.started_at DESC LIMIT 300",
        p.dentistId() == null
            ? p.scopeArgs()
            : Service.join(p.scopeArgs(), new Object[] {p.dentistId()}));
  }

  static Map<String, Object> get(Connection c, Auth.Principal p, String id) throws Exception {
    p.need("clinical.read");
    boundClinician(p);
    var v = one(c, SELECT + " WHERE v.id=?", id);
    check(v != null, 404, "NOT_FOUND", "就诊不存在");
    p.clinic(s(v, "clinic_id"));
    check(
        p.dentistId() == null || p.dentistId().equals(v.get("dentist_id")),
        403,
        "RESPONSIBLE_DENTIST",
        "无权查阅其他负责牙医的就诊明细");
    return v;
  }

  private static void boundClinician(Auth.Principal p) {
    check(p.roles().stream().noneMatch(r->s(r,"code").equals("JDBC_DENTIST"))||p.dentistId()!=null,
        403,"CLINICIAN_NOT_LINKED","医师账号尚未关联医师档案，请联系管理员核对");
  }

  static Object detail(Connection c, Auth.Principal p, String id) throws Exception {
    var v = get(c, p, id);
    return map(
        "visit",
        v,
        "history",
        rows(c, "SELECT history_status,history_text,created_at,reason FROM patient_history_versions WHERE patient_id=? ORDER BY version_number DESC LIMIT 3", v.get("patient_id")),
        "eligible_treatments",
        eligibleTreatments(c, s(v, "dentist_id")),
        "allergies",
        rows(
            c,
            "SELECT * FROM patient_allergies WHERE patient_id=? AND status='ACTIVE'",
            v.get("patient_id")),
        "acknowledgements",
        rows(c, "SELECT * FROM visit_allergy_acknowledgements WHERE visit_id=?", id),
        "observations",
        rows(c, "SELECT * FROM odontogram_observations WHERE visit_id=? ORDER BY observed_at", id),
        "plans",
        rows(c, "SELECT * FROM treatment_plans WHERE visit_id=? ORDER BY created_at DESC", id),
        "requested",
        rows(
            c,
            "SELECT r.*,t.name_zh treatment_name FROM requested_treatment_items r JOIN"
                + " treatment_catalog t ON t.id=r.treatment_id WHERE r.visit_id=? ORDER BY"
                + " r.created_at,r.sequence",
            id),
        "consents",
        rows(
            c,
            "SELECT ic.* FROM treatment_item_consents ic JOIN requested_treatment_items r ON"
                + " r.id=ic.requested_treatment_item_id WHERE r.visit_id=? ORDER BY ic.captured_at",
            id),
        "actual",
        rows(
            c,
            "SELECT a.*,t.name_zh treatment_name FROM actual_treatment_items a JOIN"
                + " treatment_catalog t ON t.id=a.treatment_id WHERE a.visit_id=? ORDER BY"
                + " a.performed_at",
            id),
        "notes",
        rows(
            c,
            "SELECT n.id,n.current_version,n.status,v.id"
                + " version_id,v.created_at,v.content_zh,v.version_number,v.amendment_reason,v.author_user_id,v.content_checksum,s.signed_at,s.signer_user_id,d.name_zh"
                + " signer_dentist FROM clinical_notes n JOIN clinical_note_versions v ON"
                + " v.clinical_note_id=n.id LEFT JOIN clinical_note_signatures s ON"
                + " s.note_version_id=v.id LEFT JOIN dentists d ON d.id=s.dentist_id WHERE"
                + " n.visit_id=? ORDER BY n.created_at,v.version_number",
            id),
        "corrections",
        rows(c,"SELECT e.entity_id actual_id,e.reason,e.occurred_at,u.display_name actor_name FROM audit_events e JOIN actual_treatment_items a ON a.id=e.entity_id LEFT JOIN app_users u ON u.id=e.actor_user_id WHERE a.visit_id=? AND e.action='CLINICAL_TREATMENT_VOIDED' ORDER BY e.occurred_at",id),
        "blockers",
        blockers(c, v));
  }

  static List<Map<String, Object>> eligibleTreatments(Connection c, String dentist) throws Exception {
    List<Map<String, Object>> eligible = new ArrayList<>();
    for (var treatment : rows(c, "SELECT id,code,name_zh,standard_price_fen,duration_minutes FROM treatment_catalog WHERE status='ACTIVE' AND effective_from<=? AND (effective_to IS NULL OR effective_to>=?) ORDER BY name_zh", today(), today())) {
      try { qualification(c, dentist, s(treatment,"id"), today()); eligible.add(treatment); }
      catch (Problem problem) { if (!Set.of("QUALIFICATION","CATALOG_VALIDITY").contains(problem.code)) throw problem; }
    }
    return eligible;
  }

  static void editable(Connection c, Auth.Principal p, Map<String, Object> v, boolean amendment)
      throws Exception {
    p.need("clinical.write");
    boolean clinician = p.roles().stream().anyMatch(r -> s(r, "code").equals("JDBC_DENTIST"));
    if (clinician)
      check(
          p.dentistId() != null && p.dentistId().equals(v.get("dentist_id")),
          403,
          "RESPONSIBLE_DENTIST",
          "只有负责牙医可以修改本次诊疗记录");
    check(!s(v, "status").equals("CANCELLED"), 409, "STATE", "就诊已撤销");
    if (!amendment) check(!s(v, "status").equals("COMPLETED"), 409, "COMPLETED", "已完成就诊仅允许附理由补记");
  }

  static void qualification(Connection c, String dentist, String treatment, String date)
      throws Exception {
    check(
        count(
                c,
                "SELECT COUNT(*) FROM treatment_catalog WHERE id=? AND status='ACTIVE' AND"
                    + " effective_from<=? AND (effective_to IS NULL OR effective_to>=?)",
                treatment,
                date,
                date)
            > 0,
        409,
        "CATALOG_VALIDITY",
        "项目在实施日无效");
    for (var r :
        rows(
            c,
            "SELECT qualification_type_id FROM treatment_qualification_requirements WHERE"
                + " treatment_id=? AND requirement_level='REQUIRED'",
            treatment))
      check(
          count(
                  c,
                  "SELECT COUNT(*) FROM dentist_qualifications WHERE dentist_id=? AND"
                      + " qualification_type_id=? AND verification_status='VERIFIED' AND"
                      + " issued_on<=? AND (expires_on IS NULL OR expires_on>=?)",
                  dentist,
                  r.get("qualification_type_id"),
                  date,
                  date)
              > 0,
          409,
          "QUALIFICATION",
          "负责牙医在实施日缺少有效必需资质");
  }

  static List<String> blockers(Connection c, Map<String, Object> v) throws Exception {
    String id = s(v, "id");
    List<String> b = new ArrayList<>();
    if (!s(v, "safety_gate_status").equals("PASSED")) b.add("请核对本次病史和过敏");
    var history =
        one(
            c,
            "SELECT id FROM patient_history_versions WHERE patient_id=? ORDER BY version_number"
                + " DESC LIMIT 1",
            v.get("patient_id"));
    if (history != null) {
      var review =
          one(
              c,
              "SELECT metadata_json FROM audit_events WHERE action='CLINICAL_HISTORY_REVIEW' AND"
                  + " entity_id=? ORDER BY id DESC LIMIT 1",
              id);
      if (review == null
          || !history.get("id").equals(parse(s(review, "metadata_json")).get("history_version_id")))
        b.add("病史声明有待复核的新版本");
    }
    if (count(
            c,
            "SELECT COUNT(*) FROM patient_allergies a WHERE a.patient_id=? AND a.status='ACTIVE'"
                + " AND NOT EXISTS(SELECT 1 FROM visit_allergy_acknowledgements k WHERE"
                + " k.allergy_id=a.id AND k.visit_id=?)",
            v.get("patient_id"),
            id)
        > 0) b.add("存在新增或尚未逐项确认的过敏资料");
    if (count(c, "SELECT COUNT(*) FROM odontogram_observations WHERE visit_id=?", id) == 0)
      b.add("尚未登记检查或牙位观察");
    if (count(
            c,
            "SELECT COUNT(*) FROM actual_treatment_items WHERE visit_id=? AND status='RECORDED'",
            id)
        == 0) b.add("尚未登记实际治疗");
    if (count(
                c,
                "SELECT COUNT(*) FROM clinical_notes n WHERE n.visit_id=? AND n.status='SIGNED' AND"
                    + " EXISTS (SELECT 1 FROM clinical_note_versions nv JOIN"
                    + " clinical_note_signatures ns ON ns.note_version_id=nv.id WHERE"
                    + " nv.clinical_note_id=n.id AND nv.version_number=n.current_version AND"
                    + " ns.content_checksum=nv.content_checksum)",
                id)
            == 0
        || count(c, "SELECT COUNT(*) FROM clinical_notes WHERE visit_id=? AND status<>'SIGNED'", id)
            > 0) b.add("本次病历尚未签署");
    for (var a :
        rows(
            c,
            "SELECT a.*,t.name_zh FROM actual_treatment_items a JOIN treatment_catalog t ON"
                + " t.id=a.treatment_id WHERE a.visit_id=? AND a.status='RECORDED'",
            id)) {
      if (a.get("requested_treatment_item_id") == null
          || count(
                  c,
                  "SELECT COUNT(*) FROM treatment_item_consents WHERE requested_treatment_item_id=?"
                      + " AND decision='ACCEPTED'",
                  a.get("requested_treatment_item_id"))
              == 0) b.add("缺少项目同意依据：" + a.get("name_zh"));
      if (a.get("requested_treatment_item_id") != null) {
        var plan =
            one(
                c,
                "SELECT * FROM requested_treatment_items WHERE id=?",
                a.get("requested_treatment_item_id"));
        if (plan == null
            || !s(plan, "tooth_code").equals(s(a, "tooth_code"))
            || count(
                    c,
                    "SELECT COALESCE(SUM(units),0) FROM actual_treatment_items WHERE"
                        + " requested_treatment_item_id=? AND status='RECORDED'",
                    a.get("requested_treatment_item_id"))
                > val(plan, "units")) b.add("实施牙位或累计数量与确认计划不一致，请补全同意与关联：" + a.get("name_zh"));
      }
      try {
        qualification(
            c, s(v, "dentist_id"), s(a, "treatment_id"), s(a, "performed_at").substring(0, 10));
      } catch (Problem e) {
        b.add(e.getMessage() + "：" + a.get("name_zh"));
      }
    }
    return b;
  }

  static Object command(Connection c, Auth.Principal p, String id, Map<String, Object> b)
      throws Exception {
    p.need("clinical.write");
    var v = get(c, p, id);
    String action = req(b, "action");
    editable(c, p, v, action.equals("note"));
    Service.version(v, "visit_version", b);
    if (Set.of("review_start", "record_treatment", "sign_complete").contains(action))
      return workflow(c, p, id, b, v);
    String patient = s(v, "patient_id"), dentist = s(v, "dentist_id");
    switch (action) {
      case "safety" -> {
        String evidence = req(b, "evidence");
        check(
            Boolean.TRUE.equals(b.get("history_confirmed")),
            422,
            "HISTORY_REVIEW",
            "请确认已询问并复核病史变化");
        for (var allergy :
            rows(
                c,
                "SELECT * FROM patient_allergies WHERE patient_id=? AND status='ACTIVE'",
                patient))
          if (count(
                  c,
                  "SELECT COUNT(*) FROM visit_allergy_acknowledgements WHERE visit_id=? AND"
                      + " allergy_id=?",
                  id,
                  allergy.get("id"))
              == 0)
            insert(
                c,
                "visit_allergy_acknowledgements",
                map(
                    "id",
                    uuid(),
                    "visit_id",
                    id,
                    "allergy_id",
                    allergy.get("id"),
                    "acknowledged_by_user_id",
                    p.userId(),
                    "acknowledged_at",
                    now(),
                    "precaution_en",
                    "",
                    "precaution_zh",
                    evidence,
                    "outcome",
                    "REVIEWED"));
        update(
            c,
            "clinical_visits",
            id,
            map(
                "safety_gate_status",
                "PASSED",
                "status",
                s(v, "status").equals("IN_PROGRESS") ? "IN_PROGRESS" : "WAITING"));
        var reviewedHistory =
            one(
                c,
                "SELECT id FROM patient_history_versions WHERE patient_id=? ORDER BY version_number"
                    + " DESC LIMIT 1",
                patient);
        insert(
            c,
            "audit_events",
            map(
                "request_id",
                uuid(),
                "actor_user_id",
                p.userId(),
                "actor_subject",
                p.userId(),
                "action",
                "CLINICAL_HISTORY_REVIEW",
                "entity_type",
                "clinical_visits",
                "entity_id",
                id,
                "clinic_id",
                v.get("clinic_id"),
                "outcome",
                "SUCCESS",
                "source",
                "JDBC_API",
                "metadata_json",
                json(
                    map(
                        "history_version_id",
                        reviewedHistory == null ? null : reviewedHistory.get("id"))),
                "occurred_at",
                now()));
        if (s(v, "status").equals("IN_PROGRESS")) invalidateSignatures(c, id);
      }
      case "start" -> {
        check(count(c,"SELECT COUNT(*) FROM dentists WHERE id=? AND employment_status='ACTIVE'",dentist)==1
            && count(c,"SELECT COUNT(*) FROM clinics WHERE id=? AND status='ACTIVE'",v.get("clinic_id"))==1,
            409,"SERVICE_INACTIVE","医师或诊所已停用，请先由机构协调本次接诊");
        check(
            s(v, "safety_gate_status").equals("PASSED") && s(v, "status").equals("WAITING"),
            409,
            "SAFETY_GATE",
            "须先完成安全复核");
        check(
            count(
                    c,
                    "SELECT COUNT(*) FROM dentist_clinic_assignments WHERE dentist_id=? AND"
                        + " clinic_id=? AND status='ACTIVE' AND effective_from<=? AND (effective_to"
                        + " IS NULL OR effective_to>=?)",
                    dentist,
                    v.get("clinic_id"),
                    today(),
                    today())
                > 0,
            409,
            "ASSIGNMENT",
            "实施日任职无效");
        requireAppointment(c, v, "CHECKED_IN");
        update(c, "clinical_visits", id, map("status", "IN_PROGRESS"));
        execute(
            c,
            "UPDATE appointments SET"
                + " status='IN_PROGRESS',appointment_version=appointment_version+1,updated_at=?"
                + " WHERE id=?",
            now(),
            v.get("appointment_id"));
        Scheduling.history(c, p, s(v, "appointment_id"), "CHECKED_IN", "IN_PROGRESS", "牙医开始接诊");
      }
      case "observation" -> {
        check(Set.of("WAITING", "IN_PROGRESS").contains(s(v, "status")), 409, "STATE", "请先完成安全复核");
        String tooth = req(b, "tooth_code");
        check(tooth.matches("[1-4][1-8]|[5-8][1-5]|GENERAL"), 422, "TOOTH", "牙位使用 FDI 编码或 GENERAL");
        insert(
            c,
            "odontogram_observations",
            map(
                "id",
                uuid(),
                "visit_id",
                id,
                "patient_id",
                patient,
                "tooth_code",
                tooth,
                "dentition",
                tooth.startsWith("5")
                        || tooth.startsWith("6")
                        || tooth.startsWith("7")
                        || tooth.startsWith("8")
                    ? "PRIMARY"
                    : "PERMANENT",
                "observation_type",
                req(b, "observation_type"),
                "severity",
                s(b, "severity").isBlank() ? "NORMAL" : s(b, "severity"),
                "finding_en",
                "",
                "finding_zh",
                req(b, "finding"),
                "observed_by_dentist_id",
                dentist,
                "observed_at",
                now()));
        invalidateSignatures(c, id);
      }
      case "plan" -> {
        check(s(v, "safety_gate_status").equals("PASSED"), 409, "SAFETY_GATE", "请先完成风险复核");
        String treatment = req(b, "treatment_id");
        qualification(c, dentist, treatment, today());
        var t = one(c, "SELECT * FROM treatment_catalog WHERE id=?", treatment);
        long units = n(b, "units");
        check(units > 0 && units <= 32, 422, "UNITS", "数量须为 1 至 32");
        String pid = uuid(), rid = uuid();
        insert(
            c,
            "treatment_plans",
            map(
                "id",
                pid,
                "visit_id",
                id,
                "plan_code",
                "PLAN-" + pid.substring(0, 8),
                "status",
                "PROPOSED",
                "estimated_total_fen",
                Math.multiplyExact(units, val(t, "standard_price_fen")),
                "notes_zh",
                req(b, "rationale")));
        String tooth = s(b, "tooth_code");
        if (!tooth.isBlank()) check(tooth.matches("[1-4][1-8]|[5-8][1-5]"), 422, "TOOTH", "牙位编码无效");
        insert(
            c,
            "requested_treatment_items",
            map(
                "id",
                rid,
                "plan_id",
                pid,
                "visit_id",
                id,
                "treatment_id",
                treatment,
                "sequence",
                1,
                "units",
                units,
                "tooth_code",
                tooth.isBlank() ? null : tooth,
                "rationale_zh",
                req(b, "rationale"),
                "status",
                "PROPOSED"));
      }
      case "consent" -> {
        var r =
            one(
                c,
                "SELECT * FROM requested_treatment_items WHERE id=? AND visit_id=?",
                req(b, "item_id"),
                id);
        check(r != null, 404, "NOT_FOUND", "计划项目不存在");
        String decision = req(b, "decision");
        check(
            Set.of("ACCEPTED", "DECLINED", "DEFERRED").contains(decision),
            422,
            "DECISION",
            "患者决定无效");
        check(
            count(
                    c,
                    "SELECT COUNT(*) FROM treatment_item_consents WHERE"
                        + " requested_treatment_item_id=?",
                    r.get("id"))
                == 0,
            409,
            "CONSENT_IMMUTABLE",
            "决定已留痕；变更方案请新增计划版本");
        insert(
            c,
            "treatment_item_consents",
            map(
                "id",
                uuid(),
                "requested_treatment_item_id",
                r.get("id"),
                "decision",
                decision,
                "policy_version",
                "COURSE-2026.1",
                "evidence",
                req(b, "evidence"),
                "witnessed_by_user_id",
                p.userId(),
                "captured_at",
                now()));
        update(c, "requested_treatment_items", s(r, "id"), map("status", decision));
        update(
            c,
            "treatment_plans",
            s(r, "plan_id"),
            map("acceptance_status", decision, "accepted_at", now(), "accepted_by", "患者本人经医患沟通确认"));
      }
      case "actual" -> {
        check(s(v, "status").equals("IN_PROGRESS"), 409, "STATE", "请先开始诊疗");
        String treatment = req(b, "treatment_id");
        qualification(c, dentist, treatment, today());
        var t = one(c, "SELECT * FROM treatment_catalog WHERE id=?", treatment);
        long units = n(b, "units");
        check(units > 0 && units <= 32, 422, "UNITS", "数量须为 1 至 32");
        String requested = s(b, "requested_treatment_item_id");
        if (!requested.isBlank())
          check(
              count(
                      c,
                      "SELECT COUNT(*) FROM requested_treatment_items WHERE id=? AND visit_id=? AND"
                          + " treatment_id=?",
                      requested,
                      id,
                      treatment)
                  == 1,
              422,
              "PLAN_LINK",
              "计划来源不匹配");
        String tooth = s(b, "tooth_code");
        if (!tooth.isBlank()) check(tooth.matches("[1-4][1-8]|[5-8][1-5]"), 422, "TOOTH", "牙位编码无效");
        if (requested.isBlank())
          check(!s(b, "notes").isBlank(), 422, "DEVIATION_REASON", "无计划来源的实施须记录原因及补全同意依据");
        insert(
            c,
            "actual_treatment_items",
            map(
                "id",
                uuid(),
                "visit_id",
                id,
                "requested_treatment_item_id",
                requested.isBlank() ? null : requested,
                "treatment_id",
                treatment,
                "provider_dentist_id",
                dentist,
                "tooth_code",
                tooth.isBlank() ? null : tooth,
                "units",
                units,
                "effective_unit_price_fen",
                t.get("standard_price_fen"),
                "line_amount_fen",
                Math.multiplyExact(units, val(t, "standard_price_fen")),
                "performed_at",
                now(),
                "notes_zh",
                s(b, "notes")));
        invalidateSignatures(c, id);
      }
      case "void_actual" -> {
        check(s(v,"status").equals("IN_PROGRESS"),409,"STATE","仅诊疗中的误录项目可以撤销；已完成记录请走更正流程");
        check(count(c,"SELECT COUNT(*) FROM invoices WHERE visit_id=?",id)==0,409,"BILLED","这次就诊已经开单，不能直接撤销治疗项目");
        String reason=req(b,"reason"),actualId=req(b,"actual_id");
        var actual=one(c,"SELECT * FROM actual_treatment_items WHERE id=? AND visit_id=? AND status='RECORDED'",actualId,id);
        check(actual!=null,409,"ACTUAL_STATE","该治疗记录已变化，请刷新后核对");
        update(c,"actual_treatment_items",actualId,map("status","VOIDED"));
        insert(c,"audit_events",map("request_id",uuid(),"actor_user_id",p.userId(),"actor_subject",p.userId(),"action","CLINICAL_TREATMENT_VOIDED","entity_type","actual_treatment_items","entity_id",actualId,"clinic_id",v.get("clinic_id"),"outcome","SUCCESS","source","JDBC_API","reason",reason,"metadata_json",json(map("visit_id",id,"previous_status","RECORDED","units",actual.get("units"),"line_amount_fen",actual.get("line_amount_fen"))),"occurred_at",now()));
        invalidateSignatures(c,id);
      }
      case "note" -> {
        String content = req(b, "content"), reason = s(b, "reason");
        var note =
            one(
                c,
                "SELECT * FROM clinical_notes WHERE visit_id=? ORDER BY created_at DESC LIMIT 1",
                id);
        int version = 1;
        String nid;
        if (note == null) {
          nid = uuid();
          insert(
              c,
              "clinical_notes",
              map(
                  "id",
                  nid,
                  "visit_id",
                  id,
                  "note_type",
                  "PROGRESS",
                  "current_version",
                  1,
                  "status",
                  "DRAFT"));
        } else {
          nid = s(note, "id");
          version = (int) val(note, "current_version") + 1;
          if (s(note, "status").equals("SIGNED")
              || s(v, "status").equals("COMPLETED")
              || count(
                      c,
                      "SELECT COUNT(*) FROM clinical_note_signatures s JOIN clinical_note_versions"
                          + " nv ON nv.id=s.note_version_id WHERE nv.clinical_note_id=?",
                      nid)
                  > 0) check(!reason.isBlank(), 422, "AMENDMENT_REASON", "签署后补记必须填写更正原因");
        }
        String versionId = uuid();
        insert(
            c,
            "clinical_note_versions",
            map(
                "id",
                versionId,
                "clinical_note_id",
                nid,
                "version_number",
                version,
                "content_zh",
                content,
                "content_en",
                "",
                "amendment_reason",
                reason.isBlank() ? null : reason,
                "author_user_id",
                p.userId(),
                "content_checksum",
                hash(content)));
        boolean sign = Boolean.TRUE.equals(b.get("sign"));
        update(
            c,
            "clinical_notes",
            nid,
            map(
                "current_version",
                version,
                "status",
                sign ? "SIGNED" : "DRAFT",
                "signed_by_dentist_id",
                sign ? dentist : null,
                "signed_at",
                sign ? now() : null,
                "updated_at",
                now()));
        if (sign)
          insert(
              c,
              "clinical_note_signatures",
              map(
                  "id",
                  uuid(),
                  "note_version_id",
                  versionId,
                  "dentist_id",
                  dentist,
                  "signer_user_id",
                  p.userId(),
                  "content_checksum",
                  hash(content),
                  "signed_at",
                  now()));
      }
      case "reconcile_actual" -> {
        check(s(v, "status").equals("IN_PROGRESS"), 409, "STATE", "仅诊疗中可以补全实施项目的计划关联");
        var actual =
            one(
                c,
                "SELECT * FROM actual_treatment_items WHERE id=? AND visit_id=? AND"
                    + " status='RECORDED'",
                req(b, "actual_id"),
                id);
        var requested =
            one(
                c,
                "SELECT * FROM requested_treatment_items WHERE id=? AND visit_id=?",
                req(b, "item_id"),
                id);
        check(
            actual != null
                && requested != null
                && actual.get("treatment_id").equals(requested.get("treatment_id")),
            422,
            "PLAN_LINK",
            "须关联本次就诊同一治疗的计划项目");
        check(
            count(
                    c,
                    "SELECT COUNT(*) FROM treatment_item_consents WHERE"
                        + " requested_treatment_item_id=? AND decision='ACCEPTED'",
                    requested.get("id"))
                > 0,
            409,
            "CONSENT_REQUIRED",
            "须先记录患者接受该项目的依据");
        check(
            s(actual, "tooth_code").equals(s(requested, "tooth_code"))
                && val(actual, "units") <= val(requested, "units"),
            422,
            "PLAN_DETAILS",
            "计划牙位与数量须涵盖本次实施");
        String reason = req(b, "reason");
        update(
            c,
            "actual_treatment_items",
            s(actual, "id"),
            map("requested_treatment_item_id", requested.get("id")));
        insert(
            c,
            "audit_events",
            map(
                "request_id",
                uuid(),
                "actor_user_id",
                p.userId(),
                "actor_subject",
                p.userId(),
                "action",
                "ACTUAL_PLAN_RECONCILE",
                "entity_type",
                "actual_treatment_items",
                "entity_id",
                actual.get("id"),
                "clinic_id",
                v.get("clinic_id"),
                "outcome",
                "SUCCESS",
                "source",
                "JDBC_API",
                "reason",
                reason,
                "metadata_json",
                json(
                    map(
                        "previous_plan_item_id",
                        actual.get("requested_treatment_item_id"),
                        "new_plan_item_id",
                        requested.get("id"))),
                "occurred_at",
                now()));
        invalidateSignatures(c, id);
      }
      case "complete" -> {
        check(s(v, "status").equals("IN_PROGRESS"), 409, "STATE", "只有诊疗中就诊可完成");
        requireAppointment(c, v, "IN_PROGRESS");
        var blockers = blockers(c, v);
        if (!blockers.isEmpty()) throw new Problem(409, "CLINICAL_BLOCKERS", "完成条件尚未满足", blockers);
        update(c, "clinical_visits", id, map("status", "COMPLETED", "completed_at", now()));
        execute(
            c,
            "UPDATE appointments SET"
                + " status='COMPLETED',appointment_version=appointment_version+1,updated_at=? WHERE"
                + " id=?",
            now(),
            v.get("appointment_id"));
        Scheduling.history(c, p, s(v, "appointment_id"), "IN_PROGRESS", "COMPLETED", "临床完成条件已核对");
      }
      default -> throw error(422, "ACTION", "未知临床操作");
    }
    execute(
        c,
        "UPDATE clinical_visits SET visit_version=visit_version+1,updated_at=? WHERE id=?",
        now(),
        id);
    Service.audit(
        c,
        p,
        "CLINICAL_" + action.toUpperCase(Locale.ROOT),
        "clinical_visits",
        id,
        s(v, "clinic_id"));
    return detail(c, p, id);
  }

  static Object step(Connection c, Auth.Principal p, String id, Map<String,Object> input) throws Exception {
    var live = get(c,p,id);
    input.put("version", live.get("visit_version"));
    return command(c,p,id,input);
  }

  static Object workflow(Connection c, Auth.Principal p, String id, Map<String,Object> b, Map<String,Object> visit) throws Exception {
    String action = s(b,"action");
    if (action.equals("review_start")) {
      check(Set.of("SAFETY_REVIEW","WAITING").contains(s(visit,"status")),409,"STATE","这次就诊已开始或已结束，请刷新后继续");
      check(Boolean.TRUE.equals(b.get("confirm")),422,"CONFIRM","请确认本人与本次患者、接诊身份一致");
      if (!s(b,"chief_complaint").isBlank()) update(c,"clinical_visits",id,map("chief_complaint_zh",s(b,"chief_complaint")));
      step(c,p,id,map("action","safety","history_confirmed",b.get("history_confirmed"),"evidence",req(b,"evidence")));
      step(c,p,id,map("action","start","confirm",true));
    } else if (action.equals("record_treatment")) {
      check(s(visit,"status").equals("IN_PROGRESS"),409,"STATE","请先核对病史并开始接诊");
      String requested = s(b,"item_id");
      String treatment, tooth;
      if (requested.isBlank()) {
        check(Boolean.TRUE.equals(b.get("patient_consented")),422,"CONSENT_REQUIRED","请先核实患者已同意本项治疗，再登记已做治疗");
        treatment = req(b,"treatment_id"); tooth = s(b,"tooth_code");
        Set<String> previousItems = new HashSet<>();
        for (var existing : rows(c,"SELECT id FROM requested_treatment_items WHERE visit_id=?",id)) previousItems.add(s(existing,"id"));
        step(c,p,id,map("action","plan","treatment_id",treatment,"tooth_code",tooth,"units",b.get("units"),"rationale",req(b,"rationale")));
        var newItems = rows(c,"SELECT id FROM requested_treatment_items WHERE visit_id=?",id).stream().filter(item -> !previousItems.contains(s(item,"id"))).toList();
        check(newItems.size()==1,500,"PLAN_IDENTITY","治疗方案保存失败，请重试");
        requested = s(newItems.getFirst(),"id");
        step(c,p,id,map("action","consent","item_id",requested,"decision","ACCEPTED","evidence",req(b,"consent_evidence")));
      } else {
        var item = one(c,"SELECT * FROM requested_treatment_items WHERE id=? AND visit_id=?",requested,id);
        check(item != null,404,"NOT_FOUND","本次治疗方案不存在");
        check(count(c,"SELECT COUNT(*) FROM treatment_item_consents WHERE requested_treatment_item_id=? AND decision='ACCEPTED'",requested)>0,409,"CONSENT_REQUIRED","此方案尚未取得患者同意，请先记录患者决定");
        treatment=s(item,"treatment_id");tooth=s(item,"tooth_code");
      }
      long units=n(b,"units");
      var confirmed = one(c,"SELECT units FROM requested_treatment_items WHERE id=?",requested);
      long done=count(c,"SELECT COALESCE(SUM(units),0) FROM actual_treatment_items WHERE requested_treatment_item_id=? AND status='RECORDED'",requested);
      check(units>0 && done+units<=val(confirmed,"units"),422,"PLAN_UNITS","本次数量超过方案剩余数量，请核对后重试");
      if (!s(b,"finding").isBlank()) {
        String severity=req(b,"finding_severity");
        check(Set.of("NORMAL","LOW","MODERATE","HIGH").contains(severity),422,"SEVERITY","请选择检查记录的程度");
        step(c,p,id,map("action","observation","tooth_code",tooth.isBlank()?"GENERAL":tooth,"observation_type","EXAMINATION","severity",severity,"finding",s(b,"finding")));
      }
      step(c,p,id,map("action","actual","treatment_id",treatment,"requested_treatment_item_id",requested,"tooth_code",tooth,"units",units,"notes",s(b,"notes")));
    } else {
      check(s(visit,"status").equals("IN_PROGRESS"),409,"STATE","仅诊疗中的就诊可以签署完成");
      check(Boolean.TRUE.equals(b.get("signature_confirmed")),422,"SIGNATURE_REQUIRED","请本人核对病历、已做治疗和同意依据后签署");
      String content=req(b,"content");
      var signed=one(c,"SELECT n.id FROM clinical_notes n JOIN clinical_note_versions nv ON nv.clinical_note_id=n.id AND nv.version_number=n.current_version JOIN clinical_note_signatures ns ON ns.note_version_id=nv.id AND ns.content_checksum=nv.content_checksum WHERE n.visit_id=? AND n.status='SIGNED' AND nv.content_zh=?",id,content);
      if(signed==null) step(c,p,id,map("action","note","content",content,"reason",s(b,"reason"),"sign",true));
      step(c,p,id,map("action","complete","confirmed",true));
    }
    Service.audit(c,p,"CLINICAL_WORKFLOW_"+action.toUpperCase(Locale.ROOT),"clinical_visits",id,s(visit,"clinic_id"));
    return detail(c,p,id);
  }

  static void invalidateSignatures(Connection c, String id) throws SQLException {
    execute(
        c,
        "UPDATE clinical_notes SET status='DRAFT',signed_at=NULL,signed_by_dentist_id=NULL WHERE"
            + " visit_id=?",
        id);
  }
}
