package cn.adcnexus;

import static cn.adcnexus.Db.*;
import static cn.adcnexus.Support.*;

import com.sun.net.httpserver.HttpExchange;
import java.security.MessageDigest;
import java.sql.*;
import java.util.*;

final class Auth {
  record Principal(
      String userId,
      String name,
      Set<String> permissions,
      Set<String> clinics,
      boolean network,
      String patientId,
      String dentistId,
      List<Map<String, Object>> roles) {
    void need(String permission) {
      check(permissions.contains(permission), 403, "FORBIDDEN", "当前岗位没有此操作权限");
    }

    void clinic(String id) {
      check(network || clinics.contains(id), 403, "CLINIC_SCOPE", "无权访问该诊所资料");
    }

    String scope(String column) {
      return network
          ? "1=1"
          : clinics.isEmpty()
              ? "1=0"
              : column + " IN (" + String.join(",", Collections.nCopies(clinics.size(), "?")) + ")";
    }

    Object[] scopeArgs() {
      return network ? new Object[0] : clinics.toArray();
    }
  }

  final Db db;
  final boolean demo = Boolean.parseBoolean(System.getenv().getOrDefault("DEMO_MODE", "false"));

  Auth(Db db) {
    this.db = db;
  }

  static Principal forPermission(Connection c, Principal p, String permission) throws SQLException {
    if (permission.isBlank()) return p;
    p.need(permission);
    var grants =
        rows(
            c,
            "SELECT a.clinic_id FROM user_role_assignments a JOIN roles r ON r.id=a.role_id JOIN"
                + " role_permissions rp ON rp.role_id=r.id JOIN permissions pm ON"
                + " pm.id=rp.permission_id WHERE a.user_id=? AND a.status='ACTIVE' AND"
                + " r.status='ACTIVE' AND a.effective_from<=? AND (a.effective_to IS NULL OR"
                + " a.effective_to>=?) AND pm.code=?",
            p.userId(),
            today(),
            today(),
            permission);
    check(!grants.isEmpty(), 403, "FORBIDDEN", "当前操作授权已失效，请重新登录");
    boolean network = grants.stream().anyMatch(g -> g.get("clinic_id") == null);
    Set<String> clinics = new LinkedHashSet<>();
    for (var g : grants) if (g.get("clinic_id") != null) clinics.add(s(g, "clinic_id"));
    if (!p.network()) {
      if (network) clinics = new LinkedHashSet<>(p.clinics());
      else clinics.retainAll(p.clinics());
      network = false;
    }
    return new Principal(
        p.userId(),
        p.name(),
        p.permissions(),
        clinics,
        network,
        p.patientId(),
        p.dentistId(),
        p.roles());
  }

  Principal principal(Connection c, HttpExchange x) throws Exception {
    String cookie = x.getRequestHeaders().getFirst("Cookie");
    String token = null;
    if (cookie != null)
      for (String item : cookie.split(";")) {
        String[] p = item.trim().split("=", 2);
        if (p.length == 2 && p[0].equals("adc_session")) token = p[1];
      }
    check(token != null, 401, "AUTH_REQUIRED", "请先登录");
    var user =
        one(
            c,
            "SELECT u.* FROM auth_sessions s JOIN app_users u ON u.id=s.user_id WHERE"
                + " s.token_hash=? AND s.revoked_at IS NULL AND s.expires_at>? AND"
                + " u.status='ACTIVE'",
            hash(token),
            now());
    check(user != null, 401, "SESSION_EXPIRED", "会话已失效，请重新登录");
    String uid = text(user.get("id"));
    var roles =
        rows(
            c,
            "SELECT r.id,r.code,r.name_zh,r.name_en,a.clinic_id FROM user_role_assignments a JOIN"
                + " roles r ON r.id=a.role_id WHERE a.user_id=? AND a.status='ACTIVE' AND"
                + " r.status='ACTIVE' AND a.effective_from<=? AND (a.effective_to IS NULL OR"
                + " a.effective_to>=?)",
            uid,
            today(),
            today());
    Set<String> perms = new LinkedHashSet<>(), clinics = new LinkedHashSet<>();
    boolean network = false;
    for (var role : roles) {
      if (role.get("clinic_id") == null) {
        if (!s(role, "code").equals("JDBC_PATIENT")) network = true;
      } else clinics.add(text(role.get("clinic_id")));
      for (var p :
          rows(
              c,
              "SELECT p.code FROM role_permissions rp JOIN permissions p ON p.id=rp.permission_id"
                  + " WHERE rp.role_id=?",
              role.get("id"))) perms.add(text(p.get("code")));
    }
    var link = one(c, "SELECT patient_id FROM patient_account_links WHERE user_id=?", uid);
    var dentist =
        one(
            c,
            "SELECT value_json FROM system_settings WHERE organization_id='org-adc' AND"
                + " setting_key=?",
            "dentist_user:" + uid);
    String did =
        dentist == null ? null : JSON.readValue(text(dentist.get("value_json")), String.class);
    if (roles.stream().noneMatch(r -> s(r, "code").equals("JDBC_DENTIST"))) did = null;
    return new Principal(
        uid,
        text(user.get("display_name")),
        perms,
        clinics,
        network,
        link == null ? null : text(link.get("patient_id")),
        did,
        roles);
  }

  Object login(HttpExchange x, Map<String, Object> b) throws Exception {
    String username = req(b, "username"), pass = req(b, "password");
    check(username.length() < 150 && pass.length() < 256, 422, "INVALID_CREDENTIALS", "账号或密码格式错误");
    // Failure counters commit even when credentials are rejected.
    return db.tx(
        c -> {
          var user = one(c, "SELECT * FROM app_users WHERE username=?", username);
          if (user == null) return map("denied", true);
          if (!text(user.get("locked_until")).isBlank()
              && text(user.get("locked_until")).compareTo(now()) > 0) return map("locked", true);
          boolean valid =
              user.get("password_hash") != null
                  && MessageDigest.isEqual(
                      text(user.get("password_hash"))
                          .getBytes(java.nio.charset.StandardCharsets.UTF_8),
                      password(
                              pass,
                              text(user.get("password_salt")),
                              ((Number) user.get("password_iterations")).intValue())
                          .getBytes(java.nio.charset.StandardCharsets.UTF_8));
          if (!valid || !text(user.get("status")).equals("ACTIVE")) {
            long failures = val(user, "failed_login_count") + 1;
            update(
                c,
                "app_users",
                text(user.get("id")),
                map(
                    "failed_login_count",
                    failures,
                    "locked_until",
                    failures >= 5 ? dateTime(now()).plusMinutes(15).format(DT) : null));
            return map("denied", true);
          }
          String requestedRole = s(b, "role");
          if (!requestedRole.isBlank() && !requestedRole.equals("STAFF")) {
            boolean granted =
                count(
                        c,
                        "SELECT COUNT(*) FROM user_role_assignments a JOIN roles r ON"
                            + " r.id=a.role_id WHERE a.user_id=? AND r.code=? AND a.status='ACTIVE'"
                            + " AND r.status='ACTIVE' AND a.effective_from<=? AND (a.effective_to"
                            + " IS NULL OR a.effective_to>=?)",
                        user.get("id"),
                        "JDBC_" + requestedRole,
                        today(),
                        today())
                    > 0;
            if (!granted) return map("wrong_role", true);
          }
          update(
              c,
              "app_users",
              text(user.get("id")),
              map("failed_login_count", 0, "locked_until", null, "last_sign_in_at", now()));
          return issue(c, x, text(user.get("id")), "PASSWORD");
        });
  }

  Object demo(HttpExchange x, Map<String, Object> b) throws Exception {
    check(demo, 404, "NOT_AVAILABLE", "此环境未开放演示入口");
    String role = req(b, "role");
    check(Seed.GRANTS.containsKey(role) && !role.equals("ADMIN"), 422, "INVALID_ROLE", "请选择可试用的岗位");
    return db.tx(
        c -> issue(c, x, "jdbc-demo-" + role.toLowerCase(Locale.ROOT), "SYNTHETIC_EVALUATION"));
  }

  Object issue(Connection c, HttpExchange x, String uid, String method) throws Exception {
    check(
        count(c, "SELECT COUNT(*) FROM app_users WHERE id=? AND status='ACTIVE'", uid) == 1,
        403,
        "INACTIVE",
        "账户未启用");
    String token = random();
    insert(
        c,
        "auth_sessions",
        map(
            "id",
            uuid(),
            "user_id",
            uid,
            "token_hash",
            hash(token),
            "auth_method",
            method,
            "expires_at",
            dateTime(now()).plusHours(8).format(DT)));
    boolean secure = "https".equalsIgnoreCase(x.getRequestHeaders().getFirst("X-Forwarded-Proto"));
    x.getResponseHeaders()
        .add(
            "Set-Cookie",
            "adc_session="
                + token
                + "; Path=/; HttpOnly; SameSite=Lax; Max-Age=28800"
                + (secure ? "; Secure" : ""));
    return map("ok", true, "csrf", hash(token + ":csrf"));
  }

  void csrf(HttpExchange x) {
    String cookie = x.getRequestHeaders().getFirst("Cookie"), token = null;
    if (cookie != null)
      for (String p : cookie.split(";")) {
        String[] v = p.trim().split("=", 2);
        if (v.length == 2 && v[0].equals("adc_session")) token = v[1];
      }
    check(
        token != null
            && hash(token + ":csrf").equals(x.getRequestHeaders().getFirst("X-CSRF-Token")),
        403,
        "CSRF",
        "页面已过期，请刷新后重试");
  }

  static String csrfToken(HttpExchange x) {
    String cookie = x.getRequestHeaders().getFirst("Cookie");
    if (cookie != null)
      for (String p : cookie.split(";")) {
        String[] v = p.trim().split("=", 2);
        if (v.length == 2 && v[0].equals("adc_session")) return hash(v[1] + ":csrf");
      }
    return "";
  }

  Object changePassword(Connection c, Principal p, Map<String, Object> b) throws Exception {
    var user = one(c, "SELECT * FROM app_users WHERE id=?", p.userId());
    String old = req(b, "oldPassword"), fresh = req(b, "newPassword");
    check(
        user.get("password_hash") != null
            && password(
                    old,
                    text(user.get("password_salt")),
                    ((Number) user.get("password_iterations")).intValue())
                .equals(user.get("password_hash")),
        422,
        "OLD_PASSWORD",
        "原密码不正确");
    check(
        fresh.length() >= 12 && fresh.length() <= 128,
        422,
        "PASSWORD_POLICY",
        "密码长度需为 12 至 128 个字符");
    String salt = salt();
    update(
        c,
        "app_users",
        p.userId(),
        map(
            "password_salt",
            salt,
            "password_hash",
            password(fresh, salt, 600000),
            "password_iterations",
            600000,
            "password_set_at",
            now()));
    execute(
        c,
        "UPDATE auth_sessions SET revoked_at=? WHERE user_id=? AND revoked_at IS NULL",
        now(),
        p.userId());
    return map("ok", true, "reauthenticate", true);
  }
}
