package cn.adcnexus;

import static cn.adcnexus.Db.*;
import static cn.adcnexus.Support.*;

import java.sql.*;
import java.util.*;

final class Workforce {
  static Object data(Connection c, Auth.Principal p) throws Exception {
    p.need("clinic.read");
    var availability =
        rows(
            c,
            "SELECT * FROM dentist_availability_rules WHERE " + p.scope("clinic_id"),
            p.scopeArgs());
    for (var row : availability) row.put("fingerprint", hash(json(row)));
    return map(
        "clinics",
        rows(c, "SELECT * FROM clinics WHERE " + p.scope("id") + " ORDER BY code", p.scopeArgs()),
        "dentists",
        rows(c, "SELECT * FROM dentists ORDER BY employee_code"),
        "assignments",
        rows(
            c,
            "SELECT a.*,d.name_zh dentist_name,c.name_zh clinic_name FROM"
                + " dentist_clinic_assignments a JOIN dentists d ON d.id=a.dentist_id JOIN clinics"
                + " c ON c.id=a.clinic_id WHERE "
                + p.scope("a.clinic_id"),
            p.scopeArgs()),
        "credentials",
        rows(
            c,
            "SELECT q.*,d.name_zh dentist_name,t.name_zh qualification_name FROM"
                + " dentist_qualifications q JOIN dentists d ON d.id=q.dentist_id JOIN"
                + " qualification_types t ON t.id=q.qualification_type_id ORDER BY q.expires_on"),
        "hours",
        rows(
            c, "SELECT * FROM clinic_operating_hours WHERE " + p.scope("clinic_id"), p.scopeArgs()),
        "availability",
        availability,
        "exceptions",
        rows(
            c,
            "SELECT * FROM dentist_schedule_exceptions WHERE " + p.scope("clinic_id"),
            p.scopeArgs()),
        "closures",
        rows(c, "SELECT * FROM clinic_closures WHERE " + p.scope("clinic_id"), p.scopeArgs()),
        "chairs",
        rows(c, "SELECT * FROM clinic_chairs WHERE " + p.scope("clinic_id"), p.scopeArgs()),
        "treatments",
        rows(c, "SELECT * FROM treatment_catalog ORDER BY code,version"),
        "requirements",
        rows(c, "SELECT * FROM treatment_qualification_requirements"));
  }

  static Object command(Connection c, Auth.Principal p, Map<String, Object> b) throws Exception {
    String action = req(b, "action"), clinic = s(b, "clinic_id");
    if (!clinic.isBlank()) p.clinic(clinic);
    if (action.equals("chair")) {
      p.need("resource.manage");
      var chair = one(c, "SELECT * FROM clinic_chairs WHERE id=?", req(b, "chair_id"));
      check(chair != null, 404, "NOT_FOUND", "牙椅不存在");
      p.clinic(s(chair, "clinic_id"));
      check(
          req(b, "updated_at").equals(s(chair, "updated_at")), 409, "VERSION_CONFLICT", "牙椅资料已变化");
      String status = req(b, "status");
      check(
          Set.of("AVAILABLE", "MAINTENANCE", "INACTIVE").contains(status), 422, "STATUS", "牙椅状态无效");
      if (!status.equals("AVAILABLE"))
        check(
            count(
                    c,
                    "SELECT COUNT(*) FROM appointments WHERE chair_id=? AND status IN"
                        + " ('CONFIRMED','CHECKED_IN','IN_PROGRESS') AND scheduled_end_at>?",
                    chair.get("id"),
                    now())
                == 0,
            409,
            "AFFECTED_APPOINTMENTS",
            "牙椅存在有效预约，请先协调改期或资源");
      update(c, "clinic_chairs", s(chair, "id"), map("status", status, "updated_at", now()));
    } else if (action.equals("closure") || action.equals("exception")) {
      p.need("resource.manage");
      p.clinic(req(b, "clinic_id"));
      String start = dateTime(req(b, "starts_at")).format(DT),
          end = dateTime(req(b, "ends_at")).format(DT);
      check(start.compareTo(end) < 0, 422, "RANGE", "结束时间须晚于开始时间");
      String dentist = s(b, "dentist_id");
      List<Object> args = new ArrayList<>(List.of(clinic, end, start));
      String extra = "";
      if (action.equals("exception")) {
        check(!dentist.isBlank(), 422, "DENTIST", "请选择牙医");
        extra = " AND dentist_id=?";
        args.add(dentist);
      }
      var affected =
          rows(
              c,
              "SELECT appointment_code,scheduled_start_at FROM appointments WHERE clinic_id=? AND"
                  + " scheduled_start_at<? AND scheduled_end_at>? AND status IN"
                  + " ('CONFIRMED','CHECKED_IN','IN_PROGRESS')"
                  + extra,
              args.toArray());
      if (!affected.isEmpty())
        throw new Problem(
            409,
            "AFFECTED_APPOINTMENTS",
            "变更将影响现有预约，请先协调",
            affected.stream()
                .map(r -> s(r, "appointment_code") + " " + s(r, "scheduled_start_at"))
                .toList());
      if (action.equals("closure"))
        insert(
            c,
            "clinic_closures",
            map(
                "id",
                uuid(),
                "clinic_id",
                clinic,
                "starts_at",
                start,
                "ends_at",
                end,
                "reason_code",
                "MANUAL",
                "reason_zh",
                req(b, "reason"),
                "reason_en",
                "",
                "status",
                "ACTIVE"));
      else {
        check(
            count(
                    c,
                    "SELECT COUNT(*) FROM dentist_clinic_assignments WHERE dentist_id=? AND"
                        + " clinic_id=? AND status='ACTIVE'",
                    dentist,
                    clinic)
                > 0,
            422,
            "ASSIGNMENT",
            "牙医没有本店任职");
        insert(
            c,
            "dentist_schedule_exceptions",
            map(
                "id",
                uuid(),
                "dentist_id",
                dentist,
                "clinic_id",
                clinic,
                "starts_at",
                start,
                "ends_at",
                end,
                "exception_type",
                "UNAVAILABLE",
                "reason_zh",
                req(b, "reason"),
                "reason_en",
                "",
                "status",
                "ACTIVE"));
      }
    } else if (action.equals("availability")) {
      p.need("resource.manage");
      p.clinic(req(b, "clinic_id"));
      String dentist = req(b, "dentist_id"),
          start = req(b, "starts_at"),
          end = req(b, "ends_at"),
          from = req(b, "effective_from");
      long day = n(b, "day_of_week");
      check(
          start.matches("\\d{2}:\\d{2}")
              && end.matches("\\d{2}:\\d{2}")
              && start.compareTo(end) < 0
              && day >= 0
              && day <= 6,
          422,
          "HOURS",
          "排班时段无效");
      java.time.LocalTime.parse(start);
      java.time.LocalTime.parse(end);
      java.time.LocalDate.parse(from);
      String to = s(b, "effective_to");
      if (!to.isBlank()) java.time.LocalDate.parse(to);
      check(to.isBlank() || to.compareTo(from) >= 0, 422, "VALIDITY", "排班有效期无效");
      check(
          count(
                  c,
                  "SELECT COUNT(*) FROM dentist_clinic_assignments WHERE dentist_id=? AND"
                      + " clinic_id=? AND status='ACTIVE' AND effective_from<=? AND (effective_to"
                      + " IS NULL OR effective_to>=?)",
                  dentist,
                  clinic,
                  from,
                  from)
              > 0,
          409,
          "ASSIGNMENT",
          "班次生效日任职无效");
      String id = s(b, "rule_id");
      if (!id.isBlank()) {
        var existing = one(c, "SELECT * FROM dentist_availability_rules WHERE id=?", id);
        check(
            existing != null
                && s(existing, "dentist_id").equals(dentist)
                && s(existing, "clinic_id").equals(clinic),
            422,
            "RULE",
            "排班规则归属不一致");
        check(
            req(b, "fingerprint").equals(hash(json(existing))),
            409,
            "VERSION_CONFLICT",
            "排班已变化，请刷新");
        update(
            c,
            "dentist_availability_rules",
            id,
            map(
                "day_of_week",
                day,
                "starts_at",
                start,
                "ends_at",
                end,
                "effective_from",
                from,
                "effective_to",
                to.isBlank() ? null : to));
        // Check the resulting rule set, not just the proposed weekday. Other
        // valid overlapping rules may still cover a booking; an uncovered one
        // rejects this transaction and restores the original rule atomically.
        checkAvailabilityImpact(c, dentist, clinic);
      } else
        insert(
            c,
            "dentist_availability_rules",
            map(
                "id",
                uuid(),
                "dentist_id",
                dentist,
                "clinic_id",
                clinic,
                "day_of_week",
                day,
                "starts_at",
                start,
                "ends_at",
                end,
                "effective_from",
                from,
                "effective_to",
                to.isBlank() ? null : to,
                "recurrence_rule",
                "WEEKLY",
                "status",
                "ACTIVE"));
    } else if (action.equals("credential")) {
      p.need("workforce.manage");
      String issued = req(b, "issued_on"), expires = s(b, "expires_on");
      java.time.LocalDate.parse(issued);
      if (!expires.isBlank()) java.time.LocalDate.parse(expires);
      check(expires.isBlank() || expires.compareTo(issued) >= 0, 422, "VALIDITY", "资质到期日不能早于颁发日");
      insert(
          c,
          "dentist_qualifications",
          map(
              "id",
              uuid(),
              "dentist_id",
              req(b, "dentist_id"),
              "qualification_type_id",
              req(b, "qualification_type_id"),
              "issuing_body",
              req(b, "issuing_body"),
              "reference_number",
              req(b, "reference_number"),
              "issued_on",
              issued,
              "expires_on",
              expires.isBlank() ? null : expires,
              "verification_status",
              Boolean.TRUE.equals(b.get("verified")) ? "VERIFIED" : "PENDING",
              "verified_at",
              Boolean.TRUE.equals(b.get("verified")) ? now() : null));
    } else if (action.equals("assignment")) {
      p.need("workforce.manage");
      p.clinic(req(b, "clinic_id"));
      String from = req(b, "effective_from"), to = s(b, "effective_to");
      java.time.LocalDate.parse(from);
      if (!to.isBlank()) java.time.LocalDate.parse(to);
      check(to.isBlank() || to.compareTo(from) >= 0, 422, "VALIDITY", "任职有效期无效");
      check(n(b, "weekly_hours") > 0 && n(b, "weekly_hours") <= 168,
          422, "WEEKLY_HOURS", "周工时需为 1 至 168 的整数");
      insert(
          c,
          "dentist_clinic_assignments",
          map(
              "id",
              uuid(),
              "dentist_id",
              req(b, "dentist_id"),
              "clinic_id",
              clinic,
              "effective_from",
              from,
              "effective_to",
              to.isBlank() ? null : to,
              "weekly_hours",
              n(b, "weekly_hours"),
              "status",
              "ACTIVE",
              "is_primary",
              0));
    } else throw error(422, "ACTION", "未知资源操作");
    Service.audit(
        c,
        p,
        "RESOURCE_" + action.toUpperCase(Locale.ROOT),
        "resources",
        s(b, "chair_id").isBlank() ? clinic : s(b, "chair_id"),
        clinic.isBlank() ? null : clinic);
    return map("ok", true);
  }

  private static void checkAvailabilityImpact(Connection c, String dentist, String clinic)
      throws Exception {
    List<String> affected = new ArrayList<>();
    for (var a : rows(c,
        "SELECT appointment_code,scheduled_start_at,scheduled_end_at FROM appointments"
            + " WHERE dentist_id=? AND clinic_id=? AND status IN"
            + " ('CONFIRMED','CHECKED_IN','IN_PROGRESS') AND"
            + " (scheduled_end_at>? OR status IN ('CHECKED_IN','IN_PROGRESS'))",
        dentist, clinic, now())) {
      var start = dateTime(s(a, "scheduled_start_at"));
      String date = start.toLocalDate().toString();
      if (count(c,
          "SELECT COUNT(*) FROM dentist_availability_rules WHERE dentist_id=? AND clinic_id=?"
              + " AND status='ACTIVE' AND day_of_week=? AND effective_from<=?"
              + " AND (effective_to IS NULL OR effective_to>=?) AND starts_at<=? AND ends_at>=?",
          dentist, clinic, start.getDayOfWeek().getValue() % 7, date, date,
          s(a, "scheduled_start_at").substring(11, 16),
          s(a, "scheduled_end_at").substring(11, 16)) == 0)
        affected.add(s(a, "appointment_code") + " " + s(a, "scheduled_start_at"));
    }
    if (!affected.isEmpty())
      throw new Problem(409, "AFFECTED_APPOINTMENTS", "新班次将使既有预约失去覆盖，请先协调", affected);
  }

  static Object access(Connection c, Auth.Principal p) throws Exception {
    p.need("access.manage");
    check(p.network(), 403, "NETWORK_REQUIRED", "账户与授权治理需要总部级管理员权限");
    return map(
        "users",
        rows(
            c,
            "SELECT id,username,display_name,email,status,last_sign_in_at,created_at FROM app_users"
                + " ORDER BY created_at DESC"),
        "roles",
        rows(
            c,
            "SELECT id,code,name_zh FROM roles WHERE code LIKE 'JDBC_%' AND code<>'JDBC_REVIEWER'"
                + " ORDER BY code"),
        "assignments",
        rows(
            c,
            "SELECT a.*,u.display_name,r.name_zh role_name FROM user_role_assignments a JOIN"
                + " app_users u ON u.id=a.user_id JOIN roles r ON r.id=a.role_id ORDER BY"
                + " a.created_at DESC"),
        "links",
        rows(
            c,
            "SELECT l.*,u.display_name,p.name_zh patient_name FROM patient_account_links l JOIN"
                + " app_users u ON u.id=l.user_id JOIN patients p ON p.id=l.patient_id"));
  }

  static Object accessCommand(Connection c, Auth.Principal p, Map<String, Object> b)
      throws Exception {
    p.need("access.manage");
    check(p.network(), 403, "NETWORK_REQUIRED", "账户与授权治理需要总部级管理员权限");
    String action = req(b, "action"), uid = s(b, "user_id");
    if (action.equals("create_user")) {
      String password = req(b, "password"), username = req(b, "username");
      check(
          password.length() >= 12 && password.length() <= 128,
          422,
          "PASSWORD_POLICY",
          "密码长度为 12 至 128 个字符");
      check(username.matches("[a-zA-Z0-9_.-]{3,60}"), 422, "USERNAME", "账号为 3 至 60 位英文、数字或下划线");
      uid = uuid();
      String salt = salt();
      insert(
          c,
          "app_users",
          map(
              "id",
              uid,
              "auth_subject",
              "jdbc:" + uid,
              "username",
              username,
              "email",
              req(b, "email"),
              "display_name",
              req(b, "display_name"),
              "password_hash",
              password(password, salt, 600000),
              "password_salt",
              salt,
              "password_iterations",
              600000,
              "password_set_at",
              now()));
    } else if (action.equals("grant")) {
      uid = req(b, "user_id");
      String role = req(b, "role_id"), clinic = s(b, "clinic_id"), from = req(b, "effective_from");
      check(
          count(
                  c,
                  "SELECT COUNT(*) FROM roles WHERE id=? AND code LIKE 'JDBC_%' AND"
                      + " code<>'JDBC_REVIEWER'",
                  role)
              == 1,
          422,
          "ROLE",
          "角色不存在或不可授予");
      java.time.LocalDate.parse(from);
      String to = s(b, "effective_to");
      if (!to.isBlank()) java.time.LocalDate.parse(to);
      check(to.isBlank() || to.compareTo(from) >= 0, 422, "DATE_RANGE", "授权有效期无效");
      check(
          !role.equals("jdbc-role-ADMIN") || clinic.isBlank(),
          422,
          "ADMIN_SCOPE",
          "权限管理员负责总部级账户治理，请勿指定单店范围；单店管理请使用诊所经理岗位");
      if (!clinic.isBlank()) p.clinic(clinic);
      if (Set.of(
              "jdbc-role-FRONT_DESK",
              "jdbc-role-DENTIST",
              "jdbc-role-CASHIER",
              "jdbc-role-CLINIC_MANAGER")
          .contains(role)) check(!clinic.isBlank(), 422, "SCOPE_REQUIRED", "门店岗位必须指定诊所范围");
      insert(
          c,
          "user_role_assignments",
          map(
              "id",
              uuid(),
              "user_id",
              uid,
              "role_id",
              role,
              "clinic_id",
              clinic.isBlank() ? null : clinic,
              "effective_from",
              from,
              "effective_to",
              to.isBlank() ? null : to,
              "granted_by_user_id",
              p.userId()));
      if (role.equals("jdbc-role-DENTIST")) {
        String did = req(b, "dentist_id");
        check(
            count(c, "SELECT COUNT(*) FROM dentists WHERE id=?", did) > 0,
            422,
            "DENTIST",
            "牙医档案不存在");
        execute(
            c,
            "DELETE FROM system_settings WHERE organization_id='org-adc' AND setting_key=?",
            "dentist_user:" + uid);
        insert(
            c,
            "system_settings",
            map(
                "organization_id",
                "org-adc",
                "setting_key",
                "dentist_user:" + uid,
                "value_json",
                json(did),
                "updated_by_user_id",
                p.userId()));
      }
    } else if (action.equals("revoke")) {
      var assignment =
          one(c, "SELECT * FROM user_role_assignments WHERE id=?", req(b, "assignment_id"));
      check(assignment != null, 404, "NOT_FOUND", "授权不存在");
      uid = s(assignment, "user_id");
      check(!uid.equals(p.userId()), 409, "SELF_LOCKOUT", "不能通过此入口撤销本人管理员授权");
      update(c, "user_role_assignments", s(assignment, "id"), map("status", "REVOKED"));
    } else if (action.equals("status")) {
      uid = req(b, "user_id");
      check(!uid.equals(p.userId()), 409, "SELF_LOCKOUT", "不能停用本人账号");
      String status = req(b, "status");
      check(Set.of("ACTIVE", "DISABLED").contains(status), 422, "STATUS", "账号状态无效");
      update(c, "app_users", uid, map("status", status, "updated_at", now()));
    } else if (action.equals("patient_link")) {
      uid = req(b, "user_id");
      String patient = req(b, "patient_id");
      check(Boolean.TRUE.equals(b.get("identity_verified")), 422, "IDENTITY", "必须先完成机构身份核实");
      Service.patientAccess(c, p, patient);
      insert(
          c,
          "patient_account_links",
          map(
              "id",
              uuid(),
              "user_id",
              uid,
              "patient_id",
              patient,
              "verification_method",
              req(b, "evidence"),
              "verified_at",
              now()));
    } else throw error(422, "ACTION", "未知授权操作");
    execute(
        c,
        "UPDATE auth_sessions SET revoked_at=? WHERE user_id=? AND revoked_at IS NULL",
        now(),
        uid);
    Service.audit(c, p, "ACCESS_" + action.toUpperCase(Locale.ROOT), "app_users", uid, null);
    return map("ok", true, "user_id", uid);
  }

  static Object auditData(Connection c, Auth.Principal p) throws Exception {
    p.need("audit.read");
    return rows(
        c,
        "SELECT e.id,e.request_id,e.actor_user_id,u.display_name"
            + " actor_name,e.action,e.entity_type,e.entity_id,e.clinic_id,e.outcome,e.reason,e.occurred_at"
            + " FROM audit_events e LEFT JOIN app_users u ON u.id=e.actor_user_id WHERE "
            + p.scope("e.clinic_id")
            + " ORDER BY e.id DESC LIMIT 400",
        p.scopeArgs());
  }

  static Object expansion(Connection c, Auth.Principal p) throws Exception {
    p.need("analytics.read");
    return map(
        "scenarios",
        rows(c, "SELECT * FROM expansion_scenarios ORDER BY scenario_code,version DESC"),
        "candidates",
        rows(c, "SELECT * FROM expansion_candidate_clinics ORDER BY candidate_code"),
        "assumptions",
        rows(c, "SELECT * FROM expansion_assumptions ORDER BY scenario_id"),
        "results",
        rows(c, "SELECT * FROM expansion_scenario_results ORDER BY calculated_at DESC"));
  }

  static Object expansionCommand(Connection c, Auth.Principal p, Map<String, Object> b)
      throws Exception {
    p.need("expansion.manage");
    check(p.network(), 403, "NETWORK_REQUIRED", "情景设计需要总部权限");
    long chairs = n(b, "chairs"),
        appointments = n(b, "appointments"),
        avg = n(b, "average_price_fen"),
        fixed = n(b, "fixed_cost_fen"),
        capital = n(b, "capital_fen"),
        costRatio = n(b, "cost_basis_points");
    check(
        chairs > 0
            && chairs <= 50
            && appointments > 0
            && appointments <= 100000
            && avg > 0
            && avg <= 10000000
            && fixed >= 0
            && capital > 0
            && costRatio >= 0
            && costRatio < 10000,
        422,
        "MODEL_INPUT",
        "情景参数超出合理范围");
    long revenue = Math.multiplyExact(appointments, avg),
        cost = Math.multiplyExact(revenue, costRatio) / 10000,
        profit = revenue - cost - fixed;
    String id = uuid(), code = "SCN-" + id.substring(0, 8);
    insert(
        c,
        "expansion_scenarios",
        map(
            "id",
            id,
            "scenario_code",
            code,
            "version",
            1,
            "name_zh",
            req(b, "name"),
            "name_en",
            req(b, "name"),
            "description_zh",
            req(b, "basis"),
            "description_en",
            "",
            "forecast_horizon_months",
            12,
            "status",
            "DRAFT",
            "advisory_disclaimer_en",
            "Scenario only, not a revenue promise",
            "advisory_disclaimer_zh",
            "仅为参数化情景，不改变实际诊所、排班或预约，不代表经营承诺。",
            "created_by_user_id",
            p.userId()));
    insert(
        c,
        "expansion_candidate_clinics",
        map(
            "id",
            uuid(),
            "scenario_id",
            id,
            "candidate_code",
            code + "-01",
            "name_zh",
            req(b, "name"),
            "name_en",
            req(b, "name"),
            "city_zh",
            req(b, "city"),
            "city_en",
            req(b, "city"),
            "district_zh",
            "待选址",
            "district_en",
            "TBD",
            "planned_chair_count",
            chairs,
            "planned_dentist_count",
            Math.max(1, chairs / 2),
            "planned_support_staff_count",
            chairs,
            "forecast_quarterly_appointments",
            appointments,
            "initial_capital_fen",
            capital,
            "quarterly_fixed_cost_fen",
            fixed,
            "required_qualifications_json",
            "[]",
            "qualification_coverage_basis_points",
            0,
            "travel_constraint_minutes",
            60,
            "readiness_status",
            "NEEDS_QUALIFICATION_REVIEW"));
    insert(
        c,
        "expansion_assumptions",
        map(
            "id",
            uuid(),
            "scenario_id",
            id,
            "assumption_key",
            "USER_INPUT",
            "label_en",
            "Input evidence",
            "label_zh",
            "用户情景输入",
            "value_text",
            json(b),
            "unit",
            "MIXED",
            "source_en",
            "User scenario, not observed performance",
            "source_zh",
            req(b, "basis")));
    insert(
        c,
        "expansion_scenario_results",
        map(
            "id",
            uuid(),
            "scenario_id",
            id,
            "projected_quarter_revenue_fen",
            revenue,
            "projected_treatment_cost_fen",
            cost,
            "projected_operating_expense_fen",
            fixed,
            "projected_net_profit_fen",
            profit,
            "projected_margin_basis_points",
            revenue == 0 ? 0 : profit * 10000 / revenue,
            "payback_months",
            profit <= 0 ? 0 : (capital * 3 + profit - 1) / profit,
            "demand_coverage_basis_points",
            0,
            "qualification_coverage_basis_points",
            0,
            "composite_score",
            0,
            "risk_level",
            profit <= 0 ? "HIGH" : "UNREVIEWED",
            "formula_evidence_json",
            json(
                map(
                    "formula",
                    "appointments * average_price_fen - variable_cost - quarterly_fixed_cost_fen",
                    "inputs",
                    b,
                    "qualification_reviewed",
                    false)),
            "calculated_at",
            now()));
    Service.audit(c, p, "SCENARIO_CREATE", "expansion_scenarios", id, null);
    return map("id", id);
  }
}
