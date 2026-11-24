package cn.adcnexus;

import static cn.adcnexus.Db.*;
import static cn.adcnexus.Support.*;

import java.sql.*;
import java.time.*;
import java.util.*;

final class Scheduling {
  static String offerNow() { return DailyDemo.enabled()?wallNow():now(); }
  private static void waitlistAudit(Connection c,Auth.Principal p,String action,String id,String clinic,String reason) throws SQLException {
    insert(c,"audit_events",map("request_id",uuid(),"actor_user_id",p.userId(),"actor_subject",p.userId(),
        "action",action,"entity_type","waitlist_entries","entity_id",id,"clinic_id",clinic,"reason",reason,
        "outcome","SUCCESS","source","JDBC_API","metadata_json","{}","occurred_at",now()));
  }
  static void ownSlot(Auth.Principal p, Map<String,Object> slot) {
    if(p.dentistId()!=null&&!p.dentistId().isBlank()&&!p.permissions().contains("appointment.manage"))
      check(p.dentistId().equals(slot.get("dentist_id")),403,"DENTIST_SCOPE","医师只能安排本人负责的候补时段，请交由前台协调其他医师");
  }
  static final String SELECT =
      "SELECT a.*,p.name_zh patient_name,p.patient_code,p.date_of_birth patient_date_of_birth,p.gender patient_gender,d.name_zh dentist_name,c.name_zh"
          + " clinic_name,t.name_zh treatment_name,ch.name_zh chair_name,v.status linked_visit_status,"
          + " CASE WHEN v.id IS NOT NULL AND (v.patient_id<>a.patient_id OR v.clinic_id<>a.clinic_id"
          + " OR (v.status<>'CANCELLED' AND (v.dentist_id<>a.dentist_id OR"
          + " v.chair_id IS DISTINCT FROM a.chair_id))) THEN 1 ELSE 0 END linked_visit_mismatch"
          + " FROM appointments a JOIN"
          + " patients p ON p.id=a.patient_id JOIN dentists d ON d.id=a.dentist_id JOIN clinics c"
          + " ON c.id=a.clinic_id JOIN treatment_catalog t ON t.id=a.treatment_id LEFT JOIN"
          + " clinic_chairs ch ON ch.id=a.chair_id LEFT JOIN clinical_visits v ON v.appointment_id=a.id ";

  private static Map<String,Object> reviewState(Map<String,Object> row) {
    String status=s(row,"status"), visit=s(row,"linked_visit_status");
    boolean coherent = switch (status) {
      case "CHECKED_IN" -> Set.of("SAFETY_REVIEW","WAITING").contains(visit);
      case "IN_PROGRESS", "COMPLETED" -> status.equals(visit);
      case "CONFIRMED", "CANCELLED", "NO_SHOW" -> visit.isBlank() || "CANCELLED".equals(visit);
      default -> false;
    };
    boolean overdue = s(row,"scheduled_start_at").compareTo(today()) < 0
        && Set.of("CONFIRMED","CHECKED_IN","IN_PROGRESS").contains(status);
    boolean mismatch = !coherent || val(row,"linked_visit_mismatch") != 0;
    row.put("review_state", mismatch ? "VISIT_MISMATCH" : overdue ? "HISTORICAL_OPEN" : null);
    row.remove("linked_visit_status");
    row.remove("linked_visit_mismatch");
    return row;
  }

  static List<Map<String, Object>> list(Connection c, Auth.Principal p, Map<String, String> q)
      throws Exception {
    p.need("appointment.read");
    List<Object> a = new ArrayList<>(List.of(p.scopeArgs()));
    String where = p.scope("a.clinic_id");
    for (String key : List.of("clinic_id", "dentist_id", "patient_id", "status")) {
      String v = q.get(key);
      if (v != null && !v.isBlank()) {
        if (key.equals("clinic_id")) p.clinic(v);
        where += " AND a." + key + "=?";
        a.add(v);
      }
    }
    for (String key : List.of("from", "to")) {
      String v = q.get(key);
      if (v != null && !v.isBlank()) {
        where +=
            " AND substr(a.scheduled_start_at,1,10) " + (key.equals("from") ? ">=" : "<=") + "?";
        a.add(v);
      }
    }
    return rows(
        c,
        SELECT + " WHERE " + where + " ORDER BY a.scheduled_start_at DESC LIMIT 600",
        a.toArray()).stream().map(Scheduling::reviewState).toList();
  }

  static Map<String, Object> get(Connection c, Auth.Principal p, String id) throws Exception {
    var row = one(c, SELECT + " WHERE a.id=?", id);
    check(row != null, 404, "NOT_FOUND", "预约不存在");
    p.clinic(text(row.get("clinic_id")));
    return reviewState(row);
  }

  static List<String> validate(
      Connection c, Auth.Principal p, Map<String, Object> b, String exclude, boolean checkFuture)
      throws Exception {
    String clinic = req(b, "clinic_id"),
        dentist = req(b, "dentist_id"),
        patient = req(b, "patient_id"),
        treatment = req(b, "treatment_id");
    p.clinic(clinic);
    LocalDateTime start = dateTime(req(b, "scheduled_start_at"));
    var item = one(c, "SELECT * FROM treatment_catalog WHERE id=? AND status='ACTIVE'", treatment);
    check(item != null, 422, "TREATMENT", "治疗项目已失效");
    long duration = n(b, "duration_minutes");
    if (duration == 0) duration = val(item, "duration_minutes");
    check(duration >= 10 && duration <= 480, 422, "DURATION", "预约时长需为 10 至 480 分钟");
    LocalDateTime end = start.plusMinutes(duration);
    check(start.toLocalDate().equals(end.toLocalDate()), 422, "CROSS_DAY", "预约不能跨越营业日");
    if (checkFuture)
      check(
          !start.isBefore(dateTime(now()).minusMinutes(1)),
          422,
          "PAST_APPOINTMENT",
          "请选择尚未开始的服务时段");
    b.put("scheduled_start_at", start.format(DT));
    b.put("scheduled_end_at", end.format(DT));
    b.put("duration_minutes", duration);
    String date = start.toLocalDate().toString(),
        st = start.toLocalTime().toString().substring(0, 5),
        et = end.toLocalTime().toString().substring(0, 5);
    int day = start.getDayOfWeek().getValue() % 7;
    List<String> issues = new ArrayList<>();
    if (count(c, "SELECT COUNT(*) FROM clinics WHERE id=? AND status='ACTIVE'", clinic) == 0)
      issues.add("诊所不在营业状态");
    if (count(c, "SELECT COUNT(*) FROM patients WHERE id=? AND status='ACTIVE'", patient) == 0)
      issues.add("患者档案无效");
    if (count(c, "SELECT COUNT(*) FROM dentists WHERE id=? AND employment_status='ACTIVE'", dentist)
        == 0) issues.add("牙医不在有效任职状态");
    if (count(
            c,
            "SELECT COUNT(*) FROM dentist_clinic_assignments WHERE dentist_id=? AND clinic_id=? AND"
                + " status='ACTIVE' AND effective_from<=? AND (effective_to IS NULL OR"
                + " effective_to>=?)",
            dentist,
            clinic,
            date,
            date)
        == 0) issues.add("牙医在服务日没有本店有效任职");
    if (count(
            c,
            "SELECT COUNT(*) FROM clinic_operating_hours WHERE clinic_id=? AND day_of_week=? AND"
                + " is_closed=0 AND opens_at<=? AND closes_at>=?",
            clinic,
            day,
            st,
            et)
        == 0) issues.add("时段不在诊所营业时间内");
    if (count(
            c,
            "SELECT COUNT(*) FROM clinic_closures WHERE clinic_id=? AND status='ACTIVE' AND"
                + " starts_at<? AND ends_at>?",
            clinic,
            end.format(DT),
            start.format(DT))
        > 0) issues.add("诊所在该时段停诊");
    if (count(
            c,
            "SELECT COUNT(*) FROM dentist_availability_rules WHERE dentist_id=? AND clinic_id=? AND"
                + " day_of_week=? AND status='ACTIVE' AND effective_from<=? AND (effective_to IS"
                + " NULL OR effective_to>=?) AND starts_at<=? AND ends_at>=?",
            dentist,
            clinic,
            day,
            date,
            date,
            st,
            et)
        == 0) issues.add("牙医排班未覆盖该时段");
    if (count(
            c,
            "SELECT COUNT(*) FROM dentist_schedule_exceptions WHERE dentist_id=? AND"
                + " status='ACTIVE' AND (clinic_id IS NULL OR clinic_id=?) AND starts_at<? AND"
                + " ends_at>?",
            dentist,
            clinic,
            end.format(DT),
            start.format(DT))
        > 0) issues.add("牙医有请假或停诊例外");
    for (var r :
        rows(
            c,
            "SELECT r.qualification_type_id,q.name_zh FROM treatment_qualification_requirements r"
                + " JOIN qualification_types q ON q.id=r.qualification_type_id WHERE"
                + " r.treatment_id=? AND r.requirement_level='REQUIRED'",
            treatment)) {
      if (count(
              c,
              "SELECT COUNT(*) FROM dentist_qualifications WHERE dentist_id=? AND"
                  + " qualification_type_id=? AND verification_status='VERIFIED' AND issued_on<=?"
                  + " AND (expires_on IS NULL OR expires_on>=?)",
              dentist,
              r.get("qualification_type_id"),
              date,
              date)
          == 0) issues.add("服务日资质无效：" + r.get("name_zh"));
    }
    if (text(item.get("effective_from")).compareTo(date) > 0
        || (!text(item.get("effective_to")).isBlank()
            && text(item.get("effective_to")).compareTo(date) < 0)) issues.add("治疗目录在服务日尚未生效或已到期");
    for (String key : List.of("dentist_id", "patient_id", "chair_id")) {
      String resource = s(b, key);
      if (resource.isBlank()) continue;
      if (key.equals("chair_id")
          && count(
                  c,
                  "SELECT COUNT(*) FROM clinic_chairs WHERE id=? AND clinic_id=? AND"
                      + " status='AVAILABLE'",
                  resource,
                  clinic)
              == 0) issues.add("牙椅不属于本店或不可用");
      if (count(
              c,
              "SELECT COUNT(*) FROM appointments WHERE "
                  + key
                  + "=? AND status NOT IN ('CANCELLED','NO_SHOW','COMPLETED') AND id<>? AND"
                  + " scheduled_start_at<? AND scheduled_end_at>?",
              resource,
              exclude == null ? "" : exclude,
              end.format(DT),
              start.format(DT))
          > 0)
        issues.add(
            switch (key) {
              case "dentist_id" -> "牙医时段冲突（含跨店）";
              case "patient_id" -> "患者已有重叠预约";
              default -> "牙椅被其他预约占用";
            });
    }
    if (count(
            c,
            "SELECT COUNT(*) FROM waitlist_offers WHERE status='OFFERED' AND expires_at>? AND id<>?"
                + " AND (dentist_id=? OR (chair_id IS NOT NULL AND chair_id=?)) AND"
                + " offered_start_at<? AND offered_end_at>?",
            offerNow(),
            s(b, "offer_id"),
            dentist,
            s(b, "chair_id"),
            end.format(DT),
            start.format(DT))
        > 0) issues.add("该资源正在候补确认窗口内");
    return issues;
  }

  static void requireValid(List<String> issues) {
    if (!issues.isEmpty()) throw new Problem(409, "SCHEDULING_CONFLICT", "当前方案不可执行，请调整后重试", issues);
  }

  static Map<String, Object> create(Connection c, Auth.Principal p, Map<String, Object> b)
      throws Exception {
    return create(c,p,b,false);
  }
  private static Map<String, Object> create(Connection c, Auth.Principal p, Map<String, Object> b, boolean waitlist)
      throws Exception {
    p.need(waitlist?"waitlist.manage":"appointment.manage");
    if(waitlist) ownSlot(p,b);
    Service.patientAccess(c, p, req(b, "patient_id"));
    requireValid(validate(c, p, b, null, true));
    String id = uuid();
    insert(
        c,
        "appointments",
        map(
            "id",
            id,
            "appointment_code",
            "APT-" + today().replace("-", "") + "-" + id.substring(0, 6).toUpperCase(Locale.ROOT),
            "patient_id",
            b.get("patient_id"),
            "clinic_id",
            b.get("clinic_id"),
            "dentist_id",
            b.get("dentist_id"),
            "chair_id",
            s(b, "chair_id").isBlank() ? null : b.get("chair_id"),
            "treatment_id",
            b.get("treatment_id"),
            "scheduled_start_at",
            b.get("scheduled_start_at"),
            "scheduled_end_at",
            b.get("scheduled_end_at"),
            "duration_minutes",
            b.get("duration_minutes"),
            "notes",
            s(b, "notes"),
            "created_by_user_id",
            p.userId(),
            "booking_channel",
            "FRONT_DESK",
            "status",
            "CONFIRMED"));
    history(c, p, id, null, "CONFIRMED", s(b, "notes"));
    Service.audit(c, p, "APPOINTMENT_CREATE", "appointments", id, s(b, "clinic_id"));
    return get(c, p, id);
  }

  static void history(
      Connection c, Auth.Principal p, String id, String old, String next, String reason)
      throws Exception {
    history(c,p,id,old,next,reason,map());
  }

  static void history(Connection c, Auth.Principal p, String id, String old, String next,
      String reason, Map<String,Object> metadata) throws Exception {
    insert(
        c,
        "appointment_status_history",
        map(
            "id",
            uuid(),
            "appointment_id",
            id,
            "from_status",
            old,
            "to_status",
            next,
            "reason_text",
            reason,
            "metadata_json",
            json(metadata),
            "actor_user_id",
            p.userId(),
            "occurred_at",
            now()));
  }

  static Object command(Connection c, Auth.Principal p, String id, Map<String, Object> b)
      throws Exception {
    p.need("appointment.manage");
    var a = get(c, p, id);
    Service.version(a, "appointment_version", b);
    String action = req(b, "action"),
        old = text(a.get("status")),
        next = old,
        reason = s(b, "reason");
    Map<String, Object> v = map();
    switch (action) {
      case "confirmation" -> {
        check(old.equals("CONFIRMED"),409,"STATE","只有尚未到诊的有效预约可以登记联系确认");
        String confirmation=PracticeSetup.selected(b,"confirmation_state",Set.of("PENDING","CONFIRMED","UNREACHABLE"));
        String channel=PracticeSetup.selected(b,"channel",Set.of("PHONE","EMAIL","SMS","IN_PERSON"));
        check(!reason.isBlank(),422,"REASON","请登记实际联系结果与依据；此操作不会发送消息");
        v.put("confirmation_state",confirmation);
      }
      case "reschedule" -> {
        check(old.equals("CONFIRMED"), 409, "STATE", "只有已确认且未到诊预约可以改期");
        Map<String, Object> newSlot = new LinkedHashMap<>(a);
        newSlot.putAll(b);
        requireValid(validate(c, p, newSlot, id, true));
        for (String k :
            List.of(
                "clinic_id",
                "dentist_id",
                "chair_id",
                "treatment_id",
                "scheduled_start_at",
                "scheduled_end_at",
                "duration_minutes")) v.put(k, newSlot.get(k));
        check(!reason.isBlank(), 422, "REASON", "请记录改期原因");
        v.put("confirmation_state","PENDING");
      }
      case "cancel" -> {
        check(old.equals("CONFIRMED") || old.equals("HOLD"), 409, "STATE", "已到诊或存在临床事实的预约不能取消");
        next = "CANCELLED";
        check(!reason.isBlank(), 422, "REASON", "请记录取消发起方和原因");
        v.put(
            "cancellation_reason_code", s(b, "initiator").equals("CLINIC") ? "CLINIC" : "PATIENT");
      }
      case "no_show" -> {
        check(
            old.equals("CONFIRMED")
                && dateTime(text(a.get("scheduled_end_at")))
                    .plusMinutes(15)
                    .isBefore(dateTime(now())),
            409,
            "TOO_EARLY",
            "须超过预约结束及 15 分钟保留时限才能标记未到诊");
        next = "NO_SHOW";
        check(!reason.isBlank(),422,"REASON","请记录患者未到店的核实情况");
      }
      case "check_in" -> {
        if (old.equals("CHECKED_IN")) {
          var visit = one(c, "SELECT id FROM clinical_visits WHERE appointment_id=?", id);
          return map("appointment", a, "visit_id", visit == null ? null : visit.get("id"));
        }
        check(old.equals("CONFIRMED"), 409, "STATE", "当前预约不能办理到诊");
        check(
            s(a, "scheduled_start_at").startsWith(today()),
            409,
            "SERVICE_DATE",
            "仅办理当日预约到诊；日期变化请先改期");
        check(Boolean.TRUE.equals(b.get("identity_confirmed")), 422, "IDENTITY", "请先核对患者身份");
        next = "CHECKED_IN";
        var previous=one(c,"SELECT * FROM clinical_visits WHERE appointment_id=?",id);
        String visitId = previous==null?uuid():s(previous,"id");
        if(previous!=null) {
          check(s(previous,"status").equals("CANCELLED"),409,"VISIT_STATE","本次接诊已有业务记录，请先核对接诊状态");
          update(c,"clinical_visits",visitId,map("status","SAFETY_REVIEW","safety_gate_status","PENDING",
              "started_at",now(),"completed_at",null,"chief_complaint_zh",s(b,"declaration"),
              "visit_version",val(previous,"visit_version")+1));
        } else insert(
            c,
            "clinical_visits",
            map(
                "id",
                visitId,
                "visit_code",
                "VIS-" + visitId.substring(0, 8).toUpperCase(Locale.ROOT),
                "appointment_id",
                id,
                "patient_id",
                a.get("patient_id"),
                "clinic_id",
                a.get("clinic_id"),
                "dentist_id",
                a.get("dentist_id"),
                "chair_id",
                a.get("chair_id"),
                "status",
                "SAFETY_REVIEW",
                "safety_gate_status",
                "PENDING",
                "started_at",
                now(),
                "chief_complaint_zh",
                s(b, "declaration"),
                "created_by_user_id",
                p.userId()));
      }
      case "revoke_arrival" -> {
        check(old.equals("CHECKED_IN"), 409, "STATE", "仅能撤销尚未诊疗的到诊");
        check(!reason.isBlank(), 422, "REASON", "请输入更正原因");
        var visit = one(c, "SELECT * FROM clinical_visits WHERE appointment_id=?", id);
        check(
            visit != null
                && Set.of("SAFETY_REVIEW","WAITING").contains(s(visit,"status"))
                && count(
                        c,
                        "SELECT COUNT(*) FROM actual_treatment_items WHERE visit_id=?",
                        visit.get("id"))
                    == 0
                && count(
                        c,
                        "SELECT COUNT(*) FROM clinical_notes WHERE visit_id=?",
                        visit.get("id"))
                    == 0
                && count(c,"SELECT COUNT(*) FROM odontogram_observations WHERE visit_id=?",visit.get("id")) == 0
                && count(c,"SELECT COUNT(*) FROM treatment_plans WHERE visit_id=?",visit.get("id")) == 0,
            409,
            "CLINICAL_FACT",
            "本次就诊已有检查、计划、病历或实施记录，不能撤销签到");
        update(c, "clinical_visits", text(visit.get("id")), map("status", "CANCELLED"));
        next = "CONFIRMED";
      }
      default -> throw error(422, "ACTION", "未知预约操作");
    }
    v.put("status", next);
    v.put("appointment_version", val(a, "appointment_version") + 1);
    v.put("updated_at", now());
    update(c, "appointments", id, v);
    history(c, p, id, old, next, reason,action.equals("confirmation")
        ? map("event_type","PATIENT_CONFIRMATION","channel",s(b,"channel"),"confirmation_state",s(b,"confirmation_state"))
        : map("event_type",action.toUpperCase(Locale.ROOT)));
    Service.audit(
        c,
        p,
        "APPOINTMENT_" + action.toUpperCase(Locale.ROOT),
        "appointments",
        id,
        text(a.get("clinic_id")));
    return get(c, p, id);
  }

  static Object waitlist(Connection c, Auth.Principal p) {
    try {
      p.need("appointment.read");
      var result=map(
          "entries",
          rows(
              c,
              "SELECT w.*,p.name_zh patient_name,t.name_zh treatment_name FROM waitlist_entries w"
                  + " JOIN patients p ON p.id=w.patient_id JOIN treatment_catalog t ON"
                  + " t.id=w.treatment_id WHERE "
                  + p.scope("COALESCE(w.preferred_clinic_id,p.primary_clinic_id)")
                  + " ORDER BY w.priority_score DESC,w.created_at DESC",
              p.scopeArgs()),
          "offers",
          rows(
              c,
              "SELECT o.*,p.name_zh patient_name FROM waitlist_offers o JOIN waitlist_entries w ON"
                  + " w.id=o.waitlist_entry_id JOIN patients p ON p.id=w.patient_id WHERE "
                  + p.scope("o.clinic_id")
                  + " ORDER BY o.created_at DESC LIMIT 100",
              p.scopeArgs()));
      for(var entry:(List<Map<String,Object>>)result.get("entries"))entry.put("fingerprint",hash(json(one(c,"SELECT * FROM waitlist_entries WHERE id=?",entry.get("id")))));
      // Expired leases are projected accurately without requiring a write on GET.
      for(var offer:(List<Map<String,Object>>)result.get("offers")) {
        if(s(offer,"status").equals("OFFERED")&&s(offer,"expires_at").compareTo(offerNow())<=0)offer.put("status","EXPIRED");
        offer.put("remaining_minutes",Math.max(0,java.time.Duration.between(dateTime(offerNow()),dateTime(s(offer,"expires_at"))).toMinutes()));
        offer.put("can_manage",p.dentistId()==null||p.permissions().contains("appointment.manage")||p.dentistId().equals(offer.get("dentist_id")));
      }
      return result;
    } catch (SQLException e) {
      throw new IllegalStateException(e);
    }
  }

  static Object candidates(Connection c,Auth.Principal p,String entryId) throws Exception {
    p.need("waitlist.manage");
    var entry=one(c,"SELECT * FROM waitlist_entries WHERE id=?",entryId);
    check(entry!=null,404,"NOT_FOUND","候补记录不存在");
    p.clinic(s(entry,"preferred_clinic_id"));
    Service.patientAccess(c,p,s(entry,"patient_id"));
    check(s(entry,"status").equals("WAITING"),409,"WAITLIST_STATE","该患者不在候补名单中");
    List<Map<String,Object>> candidates=new ArrayList<>();
    for(var released:list(c,p,mapString("status","CANCELLED","from",s(entry,"earliest_date"),"to",s(entry,"latest_date")))) {
      if(!s(entry,"preferred_clinic_id").equals(s(released,"clinic_id")))continue;
      if(p.dentistId()!=null&&!p.permissions().contains("appointment.manage")&&!p.dentistId().equals(released.get("dentist_id")))continue;
      if(dateTime(s(released,"scheduled_start_at")).isBefore(dateTime(now()).plusHours(val(entry,"notice_hours"))))continue;
      var proposed=new LinkedHashMap<>(released);proposed.put("patient_id",entry.get("patient_id"));proposed.put("treatment_id",entry.get("treatment_id"));
      if(validate(c,p,proposed,null,true).isEmpty())candidates.add(released);
    }
    return map("slots",candidates);
  }
  private static Map<String,String> mapString(String... values) {
    Map<String,String> out=new LinkedHashMap<>();for(int i=0;i<values.length;i+=2)out.put(values[i],values[i+1]);return out;
  }

  static Object waitlistCommand(Connection c, Auth.Principal p, Map<String, Object> b)
      throws Exception {
    p.need("waitlist.manage");
    String action = req(b, "action");
    execute(
        c,
        "UPDATE waitlist_offers SET status='EXPIRED' WHERE status='OFFERED' AND expires_at<=?",
        offerNow());
    if (action.equals("add")) {
      Service.patientAccess(c, p, req(b, "patient_id"));
      String clinic = req(b, "clinic_id");
      p.clinic(clinic);
      LocalDate first = LocalDate.parse(req(b, "earliest_date")),
          last = LocalDate.parse(req(b, "latest_date"));
      check(
          !first.isAfter(last) && !last.isBefore(LocalDate.parse(today())),
          422,
          "DATE_RANGE",
          "候补日期范围无效");
      check(
          n(b, "notice_hours") >= 0 && n(b, "notice_hours") <= 720,
          422,
          "NOTICE",
          "提前通知时限须为 0 至 720 小时");
      check(one(c,"SELECT id FROM treatment_catalog WHERE id=? AND status='ACTIVE'",req(b,"treatment_id"))!=null,422,"TREATMENT","请选择当前有效的治疗项目");
      check(count(c,"SELECT COUNT(*) FROM waitlist_entries WHERE patient_id=? AND treatment_id=? AND preferred_clinic_id=? AND status='WAITING' AND latest_date>=?",b.get("patient_id"),b.get("treatment_id"),clinic,today())==0,409,"DUPLICATE_WAITLIST","该患者已有同项目的候补记录，请修改原候补意愿");
      String id = uuid();
      insert(
          c,
          "waitlist_entries",
          map(
              "id",
              id,
              "patient_id",
              b.get("patient_id"),
              "treatment_id",
              req(b, "treatment_id"),
              "preferred_clinic_id",
              clinic,
              "earliest_date",
              first.toString(),
              "latest_date",
              last.toString(),
              "notice_hours",
              n(b, "notice_hours"),
              "priority_score",
              Math.min(100, Math.max(0, n(b, "priority_score"))),
              "status",
              "WAITING"));
      return map("id", id);
    }
    if(Set.of("edit","withdraw").contains(action)) {
      var entry=one(c,"SELECT * FROM waitlist_entries WHERE id=?",req(b,"entry_id"));
      check(entry!=null,404,"NOT_FOUND","候补记录不存在");
      Service.patientAccess(c,p,s(entry,"patient_id"));
      p.clinic(s(entry,"preferred_clinic_id"));
      check(s(entry,"status").equals("WAITING"),409,"WAITLIST_STATE","候补已结束，不能再次修改");
      check(hash(json(entry)).equals(req(b,"fingerprint")),409,"STALE_WRITE","候补信息已更新，请刷新后重试");
      check(count(c,"SELECT COUNT(*) FROM waitlist_offers WHERE waitlist_entry_id=? AND status='OFFERED' AND expires_at>?",entry.get("id"),offerNow())==0,409,"ACTIVE_OFFER","请先处理已发出的邀请，再修改候补意愿");
      check(!req(b,"reason").isBlank(),422,"REASON","请填写修改原因");
      Map<String,Object> changes=map("updated_at",now());
      if(action.equals("withdraw"))changes.put("status","WITHDRAWN");
      else {
        LocalDate first=LocalDate.parse(req(b,"earliest_date")),last=LocalDate.parse(req(b,"latest_date"));
        check(!first.isAfter(last)&&!last.isBefore(LocalDate.parse(today())),422,"DATE_RANGE","请填写有效的候补日期范围");
        check(n(b,"notice_hours")>=0&&n(b,"notice_hours")<=720,422,"NOTICE","提前通知须为0至720小时");
        changes.putAll(map("earliest_date",first.toString(),"latest_date",last.toString(),"notice_hours",n(b,"notice_hours")));
      }
      update(c,"waitlist_entries",s(entry,"id"),changes);
      waitlistAudit(c,p,"WAITLIST_"+action.toUpperCase(Locale.ROOT),s(entry,"id"),s(entry,"preferred_clinic_id"),s(b,"reason"));
      return map("ok",true);
    }
    if (action.equals("offer")) {
      var entry = one(c, "SELECT * FROM waitlist_entries WHERE id=?", req(b, "entry_id"));
      check(
          entry != null && s(entry, "status").equals("WAITING"), 409, "WAITLIST_STATE", "候补条目不可邀约");
      Service.patientAccess(c, p, s(entry, "patient_id"));
      check(count(c,"SELECT COUNT(*) FROM waitlist_offers WHERE waitlist_entry_id=? AND status='OFFERED' AND expires_at>?",entry.get("id"),offerNow())==0,409,"ACTIVE_OFFER","已有待答复邀请，请先处理患者答复");
      var released = get(c, p, req(b, "released_appointment_id"));
      ownSlot(p,released);
      check(s(released, "status").equals("CANCELLED"), 409, "RELEASE_REQUIRED", "请选择已取消并释放的预约时段");
      String date = s(released, "scheduled_start_at").substring(0, 10);
      check(
          date.compareTo(s(entry, "earliest_date")) >= 0
              && date.compareTo(s(entry, "latest_date")) <= 0,
          409,
          "PREFERENCE",
          "释放时段不在候补日期范围内");
      check(
          entry.get("preferred_clinic_id") == null
              || entry.get("preferred_clinic_id").equals(released.get("clinic_id")),
          409,
          "PREFERENCE",
          "患者未接受该诊所");
      check(
          !dateTime(s(released, "scheduled_start_at"))
              .isBefore(dateTime(now()).plusHours(val(entry, "notice_hours"))),
          409,
          "NOTICE",
          "未满足患者提前通知时限");
      var proposed = new LinkedHashMap<>(released);
      proposed.put("patient_id", entry.get("patient_id"));
      proposed.put("treatment_id", entry.get("treatment_id"));
      requireValid(validate(c, p, proposed, null, true));
      String id = uuid();
      insert(
          c,
          "waitlist_offers",
          map(
              "id",
              id,
              "waitlist_entry_id",
              entry.get("id"),
              "released_appointment_id",
              released.get("id"),
              "clinic_id",
              released.get("clinic_id"),
              "dentist_id",
              released.get("dentist_id"),
              "chair_id",
              released.get("chair_id"),
              "offered_start_at",
              proposed.get("scheduled_start_at"),
              "offered_end_at",
              proposed.get("scheduled_end_at"),
              "compatibility_score",
              100,
              "reasons_json",
              json(List.of("日期与诊所符合；提交时重新核验资源")),
              "status",
              "OFFERED",
              "expires_at",
              dateTime(offerNow()).plusMinutes(15).format(DT)));
      return map("id", id);
    }
    var offer = one(c, "SELECT * FROM waitlist_offers WHERE id=?", req(b, "offer_id"));
    check(offer != null, 404, "NOT_FOUND", "邀请不存在");
    p.clinic(s(offer, "clinic_id"));
    ownSlot(p,offer);
    check(
        s(offer, "status").equals("OFFERED") && s(offer, "expires_at").compareTo(offerNow()) > 0,
        409,
        "OFFER_EXPIRED",
        "邀请已处理或过期");
    if (action.equals("decline")) {
      check(!req(b,"reason").isBlank(),422,"REASON","请记录患者拒绝原因");
      update(
          c, "waitlist_offers", s(offer, "id"), map("status", "DECLINED", "responded_at", now()));
      waitlistAudit(c,p,"WAITLIST_DECLINED",s(offer,"waitlist_entry_id"),s(offer,"clinic_id"),s(b,"reason"));
      return map("ok", true);
    }
    check(action.equals("accept"), 422, "ACTION", "未知候补操作");
    check(
        Boolean.TRUE.equals(b.get("patient_confirmed")),
        422,
        "PATIENT_CONFIRMATION",
        "必须记录患者已明确接受该诊所、牙医与时间");
    var e = one(c, "SELECT * FROM waitlist_entries WHERE id=?", offer.get("waitlist_entry_id"));
    check(s(e,"status").equals("WAITING"),409,"WAITLIST_STATE","该患者的候补已处理，请刷新列表");
    var proposed =
        map(
            "patient_id",
            e.get("patient_id"),
            "treatment_id",
            e.get("treatment_id"),
            "clinic_id",
            offer.get("clinic_id"),
            "dentist_id",
            offer.get("dentist_id"),
            "chair_id",
            offer.get("chair_id"),
            "scheduled_start_at",
            offer.get("offered_start_at"),
            "duration_minutes",
            java.time.Duration.between(
                    dateTime(s(offer, "offered_start_at")), dateTime(s(offer, "offered_end_at")))
                .toMinutes(),
            "offer_id",
            offer.get("id"),
            "notes",
            "候补确认 " + offer.get("id"));
    var appointment = create(c, p, proposed,true);
    update(c, "waitlist_offers", s(offer, "id"), map("status", "ACCEPTED", "responded_at", now()));
    update(c, "waitlist_entries", s(e, "id"), map("status", "FULFILLED", "updated_at", now()));
    return appointment;
  }
}
