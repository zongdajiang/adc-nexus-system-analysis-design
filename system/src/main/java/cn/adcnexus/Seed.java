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
            "patient.manage",
            "appointment.read",
            "appointment.manage",
            "clinical.read",
            "finance.read",
            "finance.manage",
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

  static void practicePermissions(Connection c) throws Exception {
    var definitions=Map.of("catalog.manage",List.of("HQ_OPERATIONS","REVIEWER"),
        "followup.read",List.of("FRONT_DESK","DENTIST","CLINIC_MANAGER","HQ_OPERATIONS","REVIEWER"),
        "followup.manage",List.of("FRONT_DESK","CLINIC_MANAGER","REVIEWER"),
        "followup.recommend",List.of("DENTIST","REVIEWER"));
    for(var entry:definitions.entrySet()){
      String id="jdbc-perm-"+entry.getKey();
      insert(c,"permissions",map("id",id,"code",entry.getKey(),"domain",entry.getKey().split("\\.")[0],
          "description_zh",entry.getKey(),"description_en",entry.getKey()));
      for(String role:entry.getValue()) insert(c,"role_permissions",map("role_id","jdbc-role-"+role,"permission_id",id));
    }
  }

  static void clinicOperationsPermissions(Connection c) throws Exception {
    // An assigned clinic owner can cover reception and cash-desk work. This does
    // not confer clinician signatures, network finance or access administration.
    for (String permission : List.of("patient.manage", "appointment.manage", "finance.manage", "followup.manage")) {
      var definition = one(c, "SELECT id FROM permissions WHERE code=?", permission);
      check(definition != null, 500, "PERMISSION_DEFINITION", "缺少门诊业务权限定义");
      if (count(c,"SELECT COUNT(*) FROM role_permissions WHERE role_id=? AND permission_id=?","jdbc-role-CLINIC_MANAGER",definition.get("id"))==0)
        insert(c, "role_permissions", map("role_id", "jdbc-role-CLINIC_MANAGER", "permission_id", definition.get("id")));
    }
  }

  static void waitlistPermissions(Connection c) throws Exception {
    String id="jdbc-perm-waitlist.manage";
    if (one(c,"SELECT id FROM permissions WHERE code='waitlist.manage'")==null)
      insert(c,"permissions",map("id",id,"code","waitlist.manage","domain","appointment",
          "description_zh","安排候补与登记患者答复","description_en","Manage waiting list"));
    else id=s(one(c,"SELECT id FROM permissions WHERE code='waitlist.manage'"),"id");
    for(String role:List.of("CLINIC_MANAGER","FRONT_DESK","DENTIST","REVIEWER"))
      if(count(c,"SELECT COUNT(*) FROM role_permissions WHERE role_id=? AND permission_id=?","jdbc-role-"+role,id)==0)
        insert(c,"role_permissions",map("role_id","jdbc-role-"+role,"permission_id",id));
  }

  static void responsibilityPermissions(Connection c) throws Exception {
    var grants=Map.of("period.read",List.of("CLINIC_MANAGER","HQ_FINANCE","REVIEWER"),
        "expansion.read",List.of("HQ_OPERATIONS","HQ_FINANCE","REVIEWER"));
    for(var entry:grants.entrySet()){
      String id="jdbc-perm-"+entry.getKey();
      if(one(c,"SELECT id FROM permissions WHERE code=?",entry.getKey())==null)
        insert(c,"permissions",map("id",id,"code",entry.getKey(),"domain",entry.getKey().split("\\.")[0],
            "description_zh",entry.getKey().equals("period.read")?"查看授权范围内的期间核算":"查看总部扩张测算","description_en",entry.getKey()));
      else id=s(one(c,"SELECT id FROM permissions WHERE code=?",entry.getKey()),"id");
      for(String role:entry.getValue())if(count(c,"SELECT COUNT(*) FROM role_permissions WHERE role_id=? AND permission_id=?","jdbc-role-"+role,id)==0)
        insert(c,"role_permissions",map("role_id","jdbc-role-"+role,"permission_id",id));
    }
  }

  static void complete(Connection c, Db db) throws Exception {
    boolean production = production();
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
      if (production) continue;
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
    if (production)
      check(adminPassword != null && adminPassword.length() >= 20 && adminPassword.length() < 256
              && !adminPassword.equalsIgnoreCase(DemoAccounts.PASSWORD),
          500, "ADMIN_BOOTSTRAP", "首次初始化需提供 20 至 255 位随机管理员密码");
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
    if (production) return;
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
    if (DemoData.enabled()) return;
    // Compact fixtures used by isolated business regression tests.
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
      if (h == 9 && Boolean.parseBoolean(System.getenv().getOrDefault("DEMO_MODE", "false"))) {
        var frontDesk = new Auth.Principal("jdbc-demo-front_desk", "前台接待",
            Set.copyOf(GRANTS.get("FRONT_DESK")), Set.of("cln-tianhe"), false, null, null,
            List.of(), false);
        Scheduling.command(c, frontDesk, id, map("action", "check_in", "version", 1,
            "identity_confirmed", true, "declaration", "合成演示患者已到店，待医师核对病史"));
      }
    }
  }

  static void bootstrapProduction(Connection c, Db db) throws Exception {
    String name = System.getenv().getOrDefault("ORGANIZATION_NAME", "").trim();
    check(!name.isBlank() && name.length() <= 120, 500, "ORGANIZATION_REQUIRED",
        "首次初始化需配置机构名称 ORGANIZATION_NAME");
    insert(c, "organizations", map("id", "org-adc", "code", "ADC", "name_en", name, "name_zh", name));
    complete(c, db);
  }

  static void checkProfile(Connection c) throws SQLException {
    boolean synthetic = count(c, "SELECT COUNT(*) FROM system_settings WHERE organization_id='org-adc'"
        + " AND setting_key='release:jdbc' AND value_json LIKE ?", "%\"synthetic\":true%") == 1;
    boolean demoPrincipals = count(c, "SELECT COUNT(*) FROM app_users WHERE id LIKE 'jdbc-demo-%'") > 0;
    if (production())
      check(!synthetic && !demoPrincipals, 500, "PRODUCTION_ISOLATION",
          "检测到样例数据库。请为生产环境使用独立数据库");
    if (DemoAccounts.enabled())
      check(synthetic && demoPrincipals, 500, "DEMO_DATABASE",
          "演示环境须使用专用样例数据库");
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
