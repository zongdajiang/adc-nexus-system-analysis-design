package cn.adcnexus;

import static cn.adcnexus.Db.*;
import static cn.adcnexus.Support.*;

import java.nio.file.*;
import java.sql.*;
import java.util.*;

final class Seed {
  static final Map<String, List<String>> GRANTS = new LinkedHashMap<>();

  static {
    GRANTS.put(
        "FRONT_DESK",
        List.of(
            "dashboard.read",
            "patient.read",
            "patient.manage",
            "appointment.read",
            "appointment.manage",
            "clinic.read",
            "workforce.read"));
    GRANTS.put(
        "DENTIST",
        List.of(
            "dashboard.read",
            "patient.read",
            "appointment.read",
            "clinical.read",
            "clinical.write",
            "clinic.read",
            "workforce.read"));
    GRANTS.put(
        "CASHIER",
        List.of(
            "dashboard.read",
            "patient.read",
            "appointment.read",
            "finance.read",
            "finance.manage",
            "clinic.read"));
    GRANTS.put(
        "CLINIC_MANAGER",
        List.of(
            "dashboard.read",
            "patient.read",
            "appointment.read",
            "clinical.read",
            "finance.read",
            "analytics.read",
            "clinic.read",
            "clinic.manage",
            "workforce.read",
            "resource.manage"));
    GRANTS.put(
        "HQ_OPERATIONS",
        List.of(
            "dashboard.read",
            "patient.read",
            "appointment.read",
            "clinic.read",
            "clinic.manage",
            "workforce.read",
            "workforce.manage",
            "resource.manage",
            "analytics.read",
            "expansion.manage"));
    GRANTS.put(
        "HQ_FINANCE",
        List.of(
            "dashboard.read",
            "clinic.read",
            "finance.read",
            "analytics.read",
            "period.manage",
            "expense.manage"));
    GRANTS.put("ADMIN", List.of("dashboard.read", "clinic.read", "access.manage", "audit.read"));
    GRANTS.put("PATIENT", List.of("portal.read"));
    GRANTS.put(
        "REVIEWER",
        List.of(
            "dashboard.read",
            "patient.read",
            "patient.manage",
            "appointment.read",
            "appointment.manage",
            "clinical.read",
            "clinical.write",
            "finance.read",
            "finance.manage",
            "period.manage",
            "expense.manage",
            "clinic.read",
            "clinic.manage",
            "resource.manage",
            "workforce.read",
            "workforce.manage",
            "analytics.read",
            "expansion.manage",
            "audit.read"));
  }

  static void complete(Connection c, Db db) throws Exception {
    execute(c, "UPDATE appointments SET status='CHECKED_IN' WHERE status='ARRIVED'");
    execute(c, "UPDATE appointments SET status='IN_PROGRESS' WHERE status='IN_TREATMENT'");
    execute(c, "UPDATE clinical_visits SET status='IN_PROGRESS' WHERE status='IN_TREATMENT'");
    execute(c, "UPDATE invoices SET status='ISSUED' WHERE status='OVERDUE'");
    execute(
        c,
        "UPDATE dentist_availability_rules SET effective_from='2026-01-01' WHERE"
            + " effective_from>'2026-01-01'");
    for (var e : GRANTS.entrySet()) {
      String role = "jdbc-role-" + e.getKey();
      insert(
          c,
          "roles",
          map(
              "id",
              role,
              "code",
              "JDBC_" + e.getKey(),
              "name_en",
              e.getKey(),
              "name_zh",
              roleName(e.getKey())));
      for (String permission : e.getValue()) {
        String id = "jdbc-perm-" + permission;
        if (count(c, "SELECT COUNT(*) FROM permissions WHERE code=?", permission) == 0)
          insert(
              c,
              "permissions",
              map(
                  "id",
                  id,
                  "code",
                  permission,
                  "domain",
                  permission.split("\\.")[0],
                  "description_en",
                  permission,
                  "description_zh",
                  permission));
        var p = one(c, "SELECT id FROM permissions WHERE code=?", permission);
        insert(c, "role_permissions", map("role_id", role, "permission_id", p.get("id")));
      }
      String user = "jdbc-demo-" + e.getKey().toLowerCase(Locale.ROOT);
      insert(
          c,
          "app_users",
          map(
              "id",
              user,
              "auth_subject",
              user,
              "email",
              user + "@example.invalid",
              "display_name",
              roleName(e.getKey()),
              "username",
              user));
      insert(
          c,
          "user_role_assignments",
          map(
              "id",
              uuid(),
              "user_id",
              user,
              "role_id",
              role,
              "clinic_id",
              Set.of("FRONT_DESK", "DENTIST", "CASHIER", "CLINIC_MANAGER").contains(e.getKey())
                  ? "cln-tianhe"
                  : null,
              "effective_from",
              "2026-01-01"));
      if (e.getKey().equals("PATIENT")) {
        var p =
            one(
                c,
                "SELECT id FROM patients WHERE primary_clinic_id='cln-tianhe' ORDER BY patient_code"
                    + " LIMIT 1");
        insert(
            c,
            "patient_account_links",
            map(
                "id",
                uuid(),
                "user_id",
                user,
                "patient_id",
                p.get("id"),
                "verification_method",
                "COURSE_SYNTHETIC_SEED",
                "verified_at",
                now()));
      }
    }
    String adminPassword = System.getenv("ADMIN_PASSWORD");
    if (adminPassword == null || adminPassword.length() < 12) {
      adminPassword = "ADC-" + random().substring(0, 20);
      Path dir = Path.of(System.getenv().getOrDefault("DATA_DIR", "data"));
      Files.createDirectories(dir);
      Files.writeString(
          dir.resolve("setup-credentials.txt"),
          "仅用于本机首次初始化，请自行保管。\n用户名: owner\n密码: " + adminPassword + "\n管理员不默认拥有临床或财务操作权限。\n");
    }
    String salt = salt();
    insert(
        c,
        "app_users",
        map(
            "id",
            "jdbc-owner",
            "auth_subject",
            "jdbc-owner",
            "username",
            "owner",
            "email",
            "owner@example.invalid",
            "display_name",
            "系统管理员",
            "password_salt",
            salt,
            "password_hash",
            password(adminPassword, salt, 600000),
            "password_iterations",
            600000,
            "password_set_at",
            now()));
    insert(
        c,
        "user_role_assignments",
        map(
            "id",
            uuid(),
            "user_id",
            "jdbc-owner",
            "role_id",
            "jdbc-role-ADMIN",
            "effective_from",
            "2026-01-01"));
    var period =
        one(
            c,
            "SELECT id FROM financial_reporting_periods WHERE starts_on<=? AND ends_on>=?",
            today(),
            today());
    if (period == null) {
      String year = today().substring(0, 4);
      int q = (java.time.LocalDate.parse(today()).getMonthValue() - 1) / 3 + 1;
      java.time.LocalDate start =
          java.time.LocalDate.of(Integer.parseInt(year), (q - 1) * 3 + 1, 1);
      insert(
          c,
          "financial_reporting_periods",
          map(
              "id",
              "period-" + year + "-Q" + q,
              "period_code",
              year + "-Q" + q,
              "name_en",
              year + " Q" + q,
              "name_zh",
              year + " 年第 " + q + " 季度",
              "starts_on",
              start.toString(),
              "ends_on",
              start.plusMonths(3).minusDays(1).toString()));
    }
    // Seed clinician binding is an explicit controlled setting, not a name comparison.
    insert(
        c,
        "system_settings",
        map(
            "organization_id",
            "org-adc",
            "setting_key",
            "dentist_user:jdbc-demo-dentist",
            "value_json",
            json("dnt-lin-wei")));
    insert(
        c,
        "system_settings",
        map(
            "organization_id",
            "org-adc",
            "setting_key",
            "release:jdbc",
            "value_json",
            json(map("version", VERSION, "synthetic", true))));
    // Additional same-day appointments are real records in the demonstration database.
    String patient =
        text(
            one(
                    c,
                    "SELECT id FROM patients WHERE primary_clinic_id='cln-tianhe' ORDER BY"
                        + " patient_code LIMIT 1")
                .get("id"));
    String treatment =
        text(
            one(
                    c,
                    "SELECT id FROM treatment_catalog WHERE status='ACTIVE' AND id NOT IN (SELECT"
                        + " treatment_id FROM treatment_qualification_requirements WHERE"
                        + " requirement_level='REQUIRED') ORDER BY standard_price_fen LIMIT 1")
                .get("id"));
    for (int h : new int[] {9, 11, 14, 16}) {
      String id = uuid();
      String start = today() + String.format(" %02d:00:00", h);
      insert(
          c,
          "appointments",
          map(
              "id",
              id,
              "appointment_code",
              "ADC-TODAY-" + h,
              "status",
              "CONFIRMED",
              "patient_id",
              patient,
              "clinic_id",
              "cln-tianhe",
              "dentist_id",
              "dnt-lin-wei",
              "treatment_id",
              treatment,
              "scheduled_start_at",
              start,
              "scheduled_end_at",
              today() + String.format(" %02d:30:00", h),
              "duration_minutes",
              30,
              "created_by_user_id",
              "jdbc-demo-front_desk"));
      insert(
          c,
          "appointment_status_history",
          map(
              "id",
              uuid(),
              "appointment_id",
              id,
              "to_status",
              "CONFIRMED",
              "reason_text",
              "课程合成初始数据",
              "occurred_at",
              now(),
              "actor_user_id",
              "jdbc-demo-front_desk"));
    }
  }

  static String roleName(String role) {
    return switch (role) {
      case "FRONT_DESK" -> "前台接待";
      case "DENTIST" -> "牙医";
      case "CASHIER" -> "收费员";
      case "CLINIC_MANAGER" -> "诊所经理";
      case "HQ_OPERATIONS" -> "总部运营";
      case "HQ_FINANCE" -> "总部财务";
      case "ADMIN" -> "权限管理员";
      case "PATIENT" -> "患者本人";
      default -> "综合业务试用";
    };
  }

  static void normalizeLegacyStates(Connection c) throws SQLException {
    execute(c, "UPDATE clinic_chairs SET status='AVAILABLE' WHERE status='ACTIVE'");
    execute(c, "UPDATE waitlist_entries SET status='WAITING' WHERE status='ACTIVE'");
    execute(c, "UPDATE payments SET status='COMPLETED' WHERE status='CAPTURED'");
    execute(c, "UPDATE payment_refunds SET status='COMPLETED' WHERE status='SUCCEEDED'");
    execute(c, "UPDATE financial_reporting_periods SET status='CLOSED' WHERE status='LOCKED'");
    execute(c, "UPDATE appointments SET status='CHECKED_IN' WHERE status='ARRIVED'");
    execute(c, "UPDATE appointments SET status='IN_PROGRESS' WHERE status='IN_TREATMENT'");
    execute(c, "UPDATE clinical_visits SET status='IN_PROGRESS' WHERE status='IN_TREATMENT'");
  }
}
