package cn.adcnexus;

import static cn.adcnexus.Db.*;
import static cn.adcnexus.Support.*;

import java.sql.*;
import java.util.*;

final class Service {
  static Auth.Principal filterClinic(Auth.Principal p, String clinic) {
    if (clinic == null || clinic.isBlank()) return p;
    p.clinic(clinic);
    return new Auth.Principal(
        p.userId(),
        p.name(),
        p.permissions(),
        Set.of(clinic),
        false,
        p.patientId(),
        p.dentistId(),
        p.roles());
  }

  static void version(Map<String, Object> row, String col, Map<String, Object> b) {
    check(
        b.containsKey("version") && n(b, "version") == val(row, col),
        409,
        "VERSION_CONFLICT",
        "记录已变化，请刷新后核对新版本");
  }

  static void audit(
      Connection c, Auth.Principal p, String action, String type, String id, String clinic)
      throws SQLException {
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
            action,
            "entity_type",
            type,
            "entity_id",
            id,
            "clinic_id",
            clinic,
            "outcome",
            "SUCCESS",
            "source",
            "JDBC_API",
            "metadata_json",
            "{}",
            "occurred_at",
            now()));
  }

  static Map<String, Object> patientAccess(Connection c, Auth.Principal p, String id)
      throws Exception {
    var row = one(c, "SELECT * FROM patients WHERE id=?", id);
    check(row != null, 404, "NOT_FOUND", "患者不存在");
    if (!p.network() && !p.clinics().contains(s(row, "primary_clinic_id"))) {
      var args = new ArrayList<Object>();
      args.add(id);
      args.addAll(List.of(p.scopeArgs()));
      check(
          count(
                  c,
                  "SELECT COUNT(*) FROM appointments a WHERE a.patient_id=? AND "
                      + p.scope("a.clinic_id"),
                  args.toArray())
              > 0,
          403,
          "PATIENT_SCOPE",
          "无权访问该患者档案");
    }
    return row;
  }

  static Map<String, Object> safePatient(Auth.Principal p, Map<String, Object> patient) {
    var out = new LinkedHashMap<>(patient);
    if (!p.permissions().contains("patient.manage") && !p.permissions().contains("clinical.read"))
      out.remove("allergy_count");
    if (!p.permissions().contains("patient.manage")
        && !p.permissions().contains("clinical.write")) {
      String phone = s(out, "phone");
      if (phone.length() > 6)
        out.put("phone", phone.substring(0, 3) + "****" + phone.substring(phone.length() - 4));
      out.remove("government_id_last4");
      out.remove("email");
    }
    return out;
  }

  static Object bootstrap(Connection c, Auth.Principal p) throws Exception {
    Map<String, Object> out =
        map(
            "today",
            today(),
            "principal",
            map(
                "id",
                p.userId(),
                "name",
                p.name(),
                "permissions",
                p.permissions(),
                "roles",
                p.roles(),
                "clinic_ids",
                p.clinics(),
                "network",
                p.network(),
                "patient_id",
                p.patientId(),
                "dentist_id",
                p.dentistId()),
            "clinics",
            rows(
                c,
                "SELECT"
                    + " id,code,name_zh,name_en,city_zh,city_en,chair_capacity,status,address_zh,phone"
                    + " FROM clinics WHERE "
                    + p.scope("id")
                    + " ORDER BY code",
                p.scopeArgs()));
    if (!p.permissions().contains("portal.read")) {
      out.put(
          "dentists",
          rows(
              c,
              "SELECT id,employee_code,name_zh,name_en,title_zh,employment_status FROM dentists"
                  + " ORDER BY name_zh"));
      out.put("treatments", rows(c, "SELECT * FROM treatment_catalog ORDER BY category,code"));
      out.put(
          "chairs",
          rows(
              c,
              "SELECT * FROM clinic_chairs WHERE " + p.scope("clinic_id") + " ORDER BY code",
              p.scopeArgs()));
      out.put("qualifications", rows(c, "SELECT * FROM qualification_types ORDER BY code"));
    }
    return out;
  }

  static Object patients(Connection c, Auth.Principal p, Map<String, String> q) throws Exception {
    p.need("patient.read");
    String scope = p.scope("p.primary_clinic_id");
    List<Object> args = new ArrayList<>(List.of(p.scopeArgs()));
    String search = q.getOrDefault("q", "").trim();
    if (!search.isBlank()) {
      scope +=
          " AND (lower(p.name_zh) LIKE ? OR lower(p.name_en) LIKE ? OR p.patient_code LIKE ? OR"
              + " p.phone LIKE ?)";
      String term = "%" + search.toLowerCase(Locale.ROOT) + "%";
      args.addAll(List.of(term, term, term, term));
    }
    String clinic = q.getOrDefault("clinic_id", "");
    if (!clinic.isBlank()) {
      p.clinic(clinic);
      scope += " AND p.primary_clinic_id=?";
      args.add(clinic);
    }
    long total = count(c, "SELECT COUNT(*) FROM patients p WHERE " + scope, args.toArray());
    int offset = 0;
    try {
      offset = Math.max(0, Integer.parseInt(q.getOrDefault("offset", "0")));
    } catch (Exception ignored) {
    }
    args.add(60);
    args.add(offset);
    var list =
        rows(
            c,
            "SELECT p.*,c.name_zh clinic_name,(SELECT COUNT(*) FROM patient_allergies a WHERE"
                + " a.patient_id=p.id AND a.status='ACTIVE') allergy_count FROM patients p LEFT"
                + " JOIN clinics c ON c.id=p.primary_clinic_id WHERE "
                + scope
                + " ORDER BY p.updated_at DESC,p.patient_code LIMIT ? OFFSET ?",
            args.toArray());
    return map(
        "items",
        list.stream().map(r -> safePatient(p, r)).toList(),
        "total",
        total,
        "offset",
        offset,
        "limit",
        60);
  }

  static Object patientDetail(Connection c, Auth.Principal p, String id) throws Exception {
    p.need("patient.read");
    var patient = patientAccess(c, p, id);
    boolean care = false;
    for (String permission : List.of("patient.manage", "clinical.read"))
      if (p.permissions().contains(permission)) {
        try {
          patientAccess(c, Auth.forPermission(c, p, permission), id);
          care = true;
          break;
        } catch (Problem denied) {
          if (denied.status != 403) throw denied;
        }
      }
    return map(
        "clinical_details_available",
        care,
        "patient",
        safePatient(p, patient),
        "contacts",
        care
            ? rows(c, "SELECT * FROM emergency_contacts WHERE patient_id=? ORDER BY priority", id)
            : List.of(),
        "allergies",
        care ? rows(c, "SELECT * FROM patient_allergies WHERE patient_id=?", id) : List.of(),
        "history",
        care
            ? rows(
                c,
                "SELECT * FROM patient_history_versions WHERE patient_id=? ORDER BY version_number"
                    + " DESC",
                id)
            : List.of(),
        "consents",
        care
            ? rows(
                c,
                "SELECT * FROM patient_consents WHERE patient_id=? ORDER BY captured_at DESC",
                id)
            : List.of(),
        "timeline",
        care
            ? rows(
                c,
                "SELECT event_type,occurred_at,title_zh,description_zh,reference_type,reference_id"
                    + " FROM patient_timeline_events WHERE patient_id=? AND "
                    + p.scope("clinic_id")
                    + " ORDER BY occurred_at DESC LIMIT 60",
                join(new Object[] {id}, p.scopeArgs()))
            : List.of(),
        "appointments",
        p.permissions().contains("appointment.read")
            ? Scheduling.list(c, p, Map.of("patient_id", id))
            : List.of(),
        "duplicates",
        care && p.permissions().contains("patient.manage")
            ? rows(
                c,
                "SELECT d.id,d.status,d.match_score,d.resolution_notes FROM"
                    + " patient_duplicate_reviews d WHERE d.source_patient_id=? OR"
                    + " d.candidate_patient_id=?",
                id,
                id)
            : List.of());
  }

  static Object[] join(Object[] first, Object[] second) {
    Object[] out = Arrays.copyOf(first, first.length + second.length);
    System.arraycopy(second, 0, out, first.length, second.length);
    return out;
  }

  static Object createPatient(Connection c, Auth.Principal p, Map<String, Object> b)
      throws Exception {
    p.need("patient.manage");
    String clinic = req(b, "primary_clinic_id");
    p.clinic(clinic);
    String name = req(b, "name_zh"), phone = req(b, "phone"), dob = req(b, "date_of_birth");
    validateIdentity(b);
    var matches =
        rows(
            c,
            "SELECT * FROM patients WHERE status='ACTIVE' AND (phone=? OR (name_zh=? AND"
                + " date_of_birth=?))",
            phone,
            name,
            dob);
    if (!matches.isEmpty() && !Boolean.TRUE.equals(b.get("duplicate_reviewed")))
      throw new Problem(
          409,
          "POSSIBLE_DUPLICATE",
          "发现相似档案，请先核对身份；如确认为不同患者，填写依据后再建档",
          List.of("相似线索数：" + matches.size()));
    if (!matches.isEmpty()) req(b, "duplicate_reason");
    String id = uuid();
    insert(
        c,
        "patients",
        map(
            "id",
            id,
            "patient_code",
            "PAT-" + today().replace("-", "") + "-" + id.substring(0, 6).toUpperCase(Locale.ROOT),
            "name_zh",
            name,
            "name_en",
            s(b, "name_en"),
            "date_of_birth",
            dob,
            "gender",
            s(b, "gender").isBlank() ? "UNKNOWN" : s(b, "gender"),
            "phone",
            phone,
            "primary_clinic_id",
            clinic));
    for (var match : matches)
      insert(
          c,
          "patient_duplicate_reviews",
          map(
              "id",
              uuid(),
              "source_patient_id",
              id,
              "candidate_patient_id",
              match.get("id"),
              "match_score",
              90,
              "match_reasons_json",
              json(List.of("身份线索相似；仅授权人员核对")),
              "status",
              "DISTINCT",
              "reviewed_by_user_id",
              p.userId(),
              "reviewed_at",
              now(),
              "resolution_notes",
              s(b, "duplicate_reason")));
    insert(
        c,
        "patient_history_versions",
        map(
            "id",
            uuid(),
            "patient_id",
            id,
            "version_number",
            1,
            "history_text",
            s(b, "history_text"),
            "history_status",
            s(b, "history_text").isBlank() ? "UNKNOWN" : "DECLARED",
            "author_user_id",
            p.userId(),
            "reason",
            "初次建档",
            "created_at",
            now()));
    audit(c, p, "PATIENT_CREATE", "patients", id, clinic);
    return safePatient(p, patientAccess(c, p, id));
  }

  static void validateIdentity(Map<String, Object> b) {
    try {
      java.time.LocalDate dob = java.time.LocalDate.parse(req(b, "date_of_birth"));
      check(
          !dob.isAfter(java.time.LocalDate.parse(today())) && dob.getYear() > 1900,
          422,
          "DOB",
          "出生日期无效");
    } catch (java.time.format.DateTimeParseException e) {
      throw error(422, "DOB", "出生日期无效");
    }
    check(req(b, "phone").matches("[+0-9 ()-]{7,24}"), 422, "PHONE", "联系电话格式无效");
  }

  static Object patientCommand(Connection c, Auth.Principal p, String id, Map<String, Object> b)
      throws Exception {
    p.need("patient.manage");
    var patient = patientAccess(c, p, id);
    String action = req(b, "action");
    switch (action) {
      case "update" -> {
        validateIdentity(b);
        if (b.containsKey("updated_at"))
          check(
              s(b, "updated_at").equals(s(patient, "updated_at")),
              409,
              "VERSION_CONFLICT",
              "档案已变化，请刷新");
        update(
            c,
            "patients",
            id,
            map(
                "name_zh",
                req(b, "name_zh"),
                "name_en",
                s(b, "name_en"),
                "date_of_birth",
                b.get("date_of_birth"),
                "phone",
                b.get("phone"),
                "email",
                s(b, "email"),
                "updated_at",
                now()));
      }
      case "history" -> {
        String status = req(b, "history_status");
        check(
            Set.of("UNKNOWN", "DECLARED_NONE", "DECLARED").contains(status),
            422,
            "STATUS",
            "病史状态无效");
        insert(
            c,
            "patient_history_versions",
            map(
                "id",
                uuid(),
                "patient_id",
                id,
                "version_number",
                count(
                    c,
                    "SELECT COALESCE(MAX(version_number),0)+1 FROM patient_history_versions WHERE"
                        + " patient_id=?",
                    id),
                "history_text",
                s(b, "history_text"),
                "history_status",
                status,
                "author_user_id",
                p.userId(),
                "reason",
                req(b, "reason"),
                "created_at",
                now()));
      }
      case "allergy" -> {
        String severity = req(b, "severity");
        check(
            Set.of("LOW", "MODERATE", "HIGH", "SEVERE").contains(severity),
            422,
            "SEVERITY",
            "风险级别无效");
        insert(
            c,
            "patient_allergies",
            map(
                "id",
                uuid(),
                "patient_id",
                id,
                "substance_zh",
                req(b, "substance"),
                "substance_en",
                "",
                "reaction_zh",
                req(b, "reaction"),
                "reaction_en",
                "",
                "severity",
                severity,
                "status",
                "ACTIVE"));
      }
      case "contact" ->
          insert(
              c,
              "emergency_contacts",
              map(
                  "id",
                  uuid(),
                  "patient_id",
                  id,
                  "contact_name",
                  req(b, "name"),
                  "relationship_zh",
                  req(b, "relationship"),
                  "relationship_en",
                  "",
                  "phone",
                  req(b, "phone"),
                  "priority",
                  1));
      case "privacy_consent" -> {
        String status = req(b, "status");
        check(Set.of("GRANTED", "DECLINED", "WITHDRAWN").contains(status), 422, "STATUS", "同意状态无效");
        insert(
            c,
            "patient_consents",
            map(
                "id",
                uuid(),
                "patient_id",
                id,
                "consent_type",
                "DATA_SHARING",
                "status",
                status,
                "policy_version",
                "COURSE-2026.1",
                "captured_at",
                now(),
                "source",
                "PATIENT_CONFIRMED"));
      }
      case "duplicate_decision" -> {
        var review =
            one(c, "SELECT * FROM patient_duplicate_reviews WHERE id=?", req(b, "review_id"));
        check(review != null, 404, "NOT_FOUND", "复核条目不存在");
        patientAccess(c, p, s(review, "source_patient_id"));
        patientAccess(c, p, s(review, "candidate_patient_id"));
        check(s(review, "status").equals("PENDING"), 409, "ALREADY_DECIDED", "复核已处理");
        String decision = req(b, "decision");
        check(
            Set.of("DISTINCT", "SAME_PERSON_REQUIRES_MERGE").contains(decision),
            422,
            "DECISION",
            "请记录不同患者或待授权合并");
        update(
            c,
            "patient_duplicate_reviews",
            s(review, "id"),
            map(
                "status",
                decision,
                "reviewed_by_user_id",
                p.userId(),
                "reviewed_at",
                now(),
                "resolution_notes",
                req(b, "reason")));
      }
      default -> throw error(422, "ACTION", "未知患者操作");
    }
    audit(
        c,
        p,
        "PATIENT_" + action.toUpperCase(Locale.ROOT),
        "patients",
        id,
        s(patient, "primary_clinic_id"));
    return patientDetail(c, p, id);
  }

  static Object dashboard(Connection c, Auth.Principal p, Map<String, String> q) throws Exception {
    p.need("dashboard.read");
    String
        from = q.getOrDefault("from", java.time.LocalDate.parse(today()).minusDays(90).toString()),
        to = q.getOrDefault("to", today());
    check(from.compareTo(to) <= 0, 422, "RANGE", "日期范围无效");
    String scope = p.scope("a.clinic_id");
    List<Object> args = new ArrayList<>(List.of(p.scopeArgs()));
    args.add(from);
    args.add(to);
    var appointments =
        rows(
            c,
            "SELECT a.status,COUNT(*) value FROM appointments a WHERE "
                + scope
                + " AND substr(a.scheduled_start_at,1,10)>=? AND"
                + " substr(a.scheduled_start_at,1,10)<=? GROUP BY a.status",
            args.toArray());
    var clinics =
        rows(
            c,
            "SELECT c.id,c.name_zh,c.code,c.city_zh,c.chair_capacity,(SELECT COUNT(*) FROM"
                + " appointments a WHERE a.clinic_id=c.id AND substr(a.scheduled_start_at,1,10)>=?"
                + " AND substr(a.scheduled_start_at,1,10)<=?) appointments,(SELECT COUNT(*) FROM"
                + " clinical_visits v WHERE v.clinic_id=c.id AND v.status='COMPLETED' AND"
                + " substr(v.started_at,1,10)>=? AND substr(v.started_at,1,10)<=?) completed FROM"
                + " clinics c WHERE "
                + p.scope("c.id")
                + " ORDER BY appointments DESC",
            join(new Object[] {from, to, from, to}, p.scopeArgs()));
    Map<String, Object> out =
        map(
            "range",
            map("from", from, "to", to, "date_basis", "计划服务日；临床按就诊建立日"),
            "generated_at",
            now(),
            "appointment_states",
            appointments,
            "clinics",
            clinics,
            "patient_count",
            count(
                c,
                "SELECT COUNT(*) FROM patients WHERE " + p.scope("primary_clinic_id"),
                p.scopeArgs()),
            "today_agenda",
            p.permissions().contains("appointment.read")
                ? Scheduling.list(c, p, Map.of("from", today(), "to", today()))
                : List.of(),
            "daily",
            rows(
                c,
                "SELECT substr(a.scheduled_start_at,1,10) AS day,COUNT(*) total,SUM(CASE WHEN"
                    + " status='COMPLETED' THEN 1 ELSE 0 END) completed FROM appointments a WHERE "
                    + scope
                    + " AND substr(a.scheduled_start_at,1,10)>=? AND"
                    + " substr(a.scheduled_start_at,1,10)<=? GROUP BY"
                    + " substr(a.scheduled_start_at,1,10) ORDER BY day",
                args.toArray()));
    if (p.permissions().contains("finance.read"))
      out.put("finance", Finance.summary(c, Auth.forPermission(c, p, "finance.read"), from, to));
    return out;
  }

  static Object portal(Connection c, Auth.Principal p) throws Exception {
    p.need("portal.read");
    check(p.patientId() != null, 403, "PATIENT_NOT_BOUND", "尚未完成机构核实绑定，请联系前台");
    String id = p.patientId();
    return map(
        "patient",
        one(
            c,
            "SELECT patient_code,name_zh,name_en,date_of_birth,preferred_language FROM patients"
                + " WHERE id=?",
            id),
        "appointments",
        rows(
            c,
            "SELECT a.appointment_code,a.scheduled_start_at,a.scheduled_end_at,a.status,c.name_zh"
                + " clinic_name,d.name_zh dentist_name,t.name_zh treatment_name FROM appointments a"
                + " JOIN clinics c ON c.id=a.clinic_id JOIN dentists d ON d.id=a.dentist_id JOIN"
                + " treatment_catalog t ON t.id=a.treatment_id WHERE a.patient_id=? ORDER BY"
                + " a.scheduled_start_at DESC",
            id),
        "visits",
        rows(
            c,
            "SELECT visit_code,status,started_at,completed_at FROM clinical_visits WHERE"
                + " patient_id=? ORDER BY started_at DESC",
            id),
        "invoices",
        rows(
            c,
            "SELECT invoice_code,total_fen,paid_fen,refunded_fen,balance_fen,status,issued_at FROM"
                + " invoices WHERE patient_id=? ORDER BY issued_at DESC",
            id));
  }
}
