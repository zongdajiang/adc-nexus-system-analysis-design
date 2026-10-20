package cn.adcnexus;

import static cn.adcnexus.Db.*;
import static cn.adcnexus.Support.*;

import com.sun.net.httpserver.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.sql.*;
import java.util.*;
import java.util.concurrent.*;

public final class Main {
  private final Db db;
  private final Auth auth;

  private Main(Db db) {
    this.db = db;
    auth = new Auth(db);
  }

  public static void main(String[] args) throws Exception {
    TimeZone.setDefault(TimeZone.getTimeZone(Support.ZONE));
    check(
        !"PRODUCTION".equals(System.getenv("APP_ENV"))
            || System.getenv("DATABASE_URL") != null && !System.getenv("DATABASE_URL").isBlank(),
        500,
        "DATABASE_REQUIRED",
        "托管部署必须配置 PostgreSQL DATABASE_URL，不能依赖临时 SQLite 文件");
    Db db = new Db();
    db.migrate();
    int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));
    HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", port), 128);
    Main app = new Main(db);
    server.createContext("/", app::handle);
    server.setExecutor(Executors.newVirtualThreadPerTaskExecutor());
    server.start();
    Runtime.getRuntime()
        .addShutdownHook(
            new Thread(
                () -> {
                  server.stop(3);
                  db.close();
                }));
    System.out.println(
        "ADC Nexus JDBC listening at http://localhost:"
            + port
            + "; database="
            + (db.postgres ? "PostgreSQL" : "SQLite")
            + "; demo="
            + app.auth.demo);
  }

  private void handle(HttpExchange x) throws IOException {
    String requestId = uuid(), path = x.getRequestURI().getPath(), method = x.getRequestMethod();
    Auth.Principal[] who = new Auth.Principal[1];
    x.getResponseHeaders().set("X-Request-ID", requestId);
    x.getResponseHeaders().set("X-Content-Type-Options", "nosniff");
    x.getResponseHeaders().set("Referrer-Policy", "same-origin");
    x.getResponseHeaders().set("X-Frame-Options", "DENY");
    x.getResponseHeaders()
        .set(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src"
                + " 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';"
                + " base-uri 'none'; form-action 'self'");
    try {
      if (!path.startsWith("/api/")) {
        staticFile(x, path);
        return;
      }
      x.getResponseHeaders().set("Cache-Control", "no-store");
      if (path.equals("/api/health")) {
        Object result =
            db.read(
                c ->
                    map(
                        "ok",
                        count(c, "SELECT COUNT(*) FROM organizations") > 0,
                        "version",
                        VERSION,
                        "data_access",
                        "JAVA_JDBC",
                        "database",
                        db.postgres ? "PostgreSQL" : "SQLite",
                        "time",
                        now(),
                        "synthetic",
                        true,
                        "demo_mode",
                        auth.demo));
        respond(x, 200, result);
        return;
      }
      if (path.equals("/api/auth/config")) {
        respond(
            x,
            200,
            map(
                "demo",
                auth.demo,
                "sms",
                false,
                "wechat",
                false,
                "roles",
                Seed.GRANTS.keySet().stream()
                    .filter(r -> !r.equals("ADMIN"))
                    .map(r -> map("code", r, "name", Seed.roleName(r)))
                    .toList(),
                "service_notice",
                "课程合成数据环境。短信与微信需机构凭据启用；密码登录可用。"));
        return;
      }
      check(method.equals("GET") || method.equals("POST"), 405, "METHOD", "此接口不支持该方法");
      boolean mutation = method.equals("POST");
      if (mutation) sameOrigin(x);
      Map<String, Object> b = mutation ? body(x) : map();
      if (path.equals("/api/auth/login") && method.equals("POST")) {
        var result = (Map<String, Object>) auth.login(x, b);
        if (result.containsKey("denied")) throw error(401, "LOGIN_FAILED", "账号或密码不正确");
        if (result.containsKey("locked")) throw error(429, "LOGIN_LOCKED", "尝试次数过多，请 15 分钟后重试");
        if (result.containsKey("wrong_role"))
          throw error(403, "ROLE_MISMATCH", "此账号未获所选岗位授权，请选择对应入口");
        respond(x, 200, result);
        return;
      }
      if (path.equals("/api/auth/demo") && method.equals("POST")) {
        respond(x, 200, auth.demo(x, b));
        return;
      }
      if (path.startsWith("/api/auth/sms")
          || path.startsWith("/api/auth/wechat")
          || path.equals("/api/auth/recover"))
        throw error(503, "PROVIDER_NOT_CONFIGURED", "机构尚未配置此身份通道，请使用账号密码或联系管理员");
      Auth.Principal p = db.read(c -> auth.principal(c, x));
      who[0] = p;
      if (path.equals("/api/auth/session")) {
        respond(
            x,
            200,
            map(
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
                "csrf",
                Auth.csrfToken(x)));
        return;
      }
      if (mutation) auth.csrf(x);
      if (path.equals("/api/auth/logout") && method.equals("POST")) {
        db.tx(
            c -> {
              execute(
                  c,
                  "UPDATE auth_sessions SET revoked_at=? WHERE user_id=? AND token_hash=?",
                  now(),
                  p.userId(),
                  cookieHash(x));
              return null;
            });
        x.getResponseHeaders()
            .add("Set-Cookie", "adc_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0");
        respond(x, 200, map("ok", true));
        return;
      }
      Map<String, String> q = query(x.getRequestURI().getRawQuery());
      if (mutation) {
        String idem = x.getRequestHeaders().getFirst("Idempotency-Key");
        if (idem != null)
          check(idem.matches("[a-zA-Z0-9-]{12,100}"), 422, "IDEMPOTENCY_KEY", "请求标识无效");
        Object result =
            db.tx(
                c -> {
                  authorizeRoute(p, path);
                  String
                      operation =
                          method
                              + " "
                              + path
                              + " "
                              + hash(
                                  json(
                                      map(
                                          "permissions",
                                          p.permissions(),
                                          "clinics",
                                          p.clinics(),
                                          "network",
                                          p.network()))),
                      signature = hash(json(b));
                  if (idem != null) {
                    var receipt =
                        one(
                            c,
                            "SELECT * FROM request_receipts WHERE id=? AND actor_user_id=? AND"
                                + " operation=?",
                            idem,
                            p.userId(),
                            operation);
                    if (receipt != null) {
                      check(
                          signature.equals(receipt.get("request_hash")),
                          409,
                          "IDEMPOTENCY_CONFLICT",
                          "同一请求标识不能提交不同内容");
                      return JSON.readValue(s(receipt, "response_json"), Object.class);
                    }
                  }
                  Object r = route(c, p, x, path, method, q, b);
                  if (idem != null)
                    insert(
                        c,
                        "request_receipts",
                        map(
                            "id",
                            idem,
                            "actor_user_id",
                            p.userId(),
                            "operation",
                            operation,
                            "request_hash",
                            signature,
                            "response_json",
                            json(r),
                            "created_at",
                            now()));
                  return r;
                });
        respond(x, 200, result);
      } else {
        respond(
            x,
            200,
            db.read(
                c -> {
                  Auth.Principal scoped = Service.filterClinic(p, q.get("clinic_id"));
                  authorizeRoute(scoped, path);
                  return route(c, scoped, x, path, method, q, b);
                }));
      }
    } catch (Problem e) {
      if (who[0] != null && e.status >= 400 && path.startsWith("/api/"))
        denied(who[0], requestId, path, e);
      respond(
          x,
          e.status,
          map(
              "error",
              map(
                  "code",
                  e.code,
                  "message",
                  e.getMessage(),
                  "details",
                  e.details,
                  "request_id",
                  requestId)));
    } catch (java.time.format.DateTimeParseException e) {
      respond(
          x,
          422,
          map(
              "error",
              map(
                  "code",
                  "INVALID_DATE",
                  "message",
                  "请填写有效日期（YYYY-MM-DD）",
                  "request_id",
                  requestId)));
    } catch (Exception e) {
      System.err.println("request=" + requestId + " type=" + e.getClass().getSimpleName());
      // Log class and SQL state only: no raw SQL, request body, password or medical text.
      if (e instanceof SQLException sql) {
        System.err.println("sqlstate=" + sql.getSQLState() + " code=" + sql.getErrorCode());
        boolean constraint =
            sql.getErrorCode() == 19
                || "23505".equals(sql.getSQLState())
                || "23503".equals(sql.getSQLState());
        respond(
            x,
            constraint ? 409 : 500,
            map(
                "error",
                map(
                    "code",
                    constraint ? "DATA_CONFLICT" : "INTERNAL_ERROR",
                    "message",
                    constraint ? "该记录已存在、被引用或不满足数据约束，请刷新后核对" : "服务暂时无法完成请求，请保留请求编号重试",
                    "request_id",
                    requestId)));
      } else
        respond(
            x,
            500,
            map(
                "error",
                map(
                    "code",
                    "INTERNAL_ERROR",
                    "message",
                    "服务暂时无法完成请求，请保留请求编号重试",
                    "request_id",
                    requestId)));
    } finally {
      x.close();
    }
  }

  private void authorizeRoute(Auth.Principal p, String path) {
    if (path.startsWith("/api/patients")) p.need("patient.read");
    else if (path.startsWith("/api/appointments")
        || path.startsWith("/api/waitlist")
        || path.startsWith("/api/scheduling")) p.need("appointment.read");
    else if (path.startsWith("/api/visits")) p.need("clinical.read");
    else if (path.startsWith("/api/finance")) p.need("finance.read");
    else if (path.startsWith("/api/admin")) p.need("access.manage");
    else if (path.startsWith("/api/audit")) p.need("audit.read");
    else if (path.startsWith("/api/portal")) p.need("portal.read");
    else if (path.startsWith("/api/analytics") || path.startsWith("/api/expansion"))
      p.need("analytics.read");
  }

  private Object route(
      Connection c,
      Auth.Principal p,
      HttpExchange x,
      String path,
      String method,
      Map<String, String> q,
      Map<String, Object> b)
      throws Exception {
    String[] parts = path.split("/");
    boolean post = method.equals("POST");
    p = auth.forPermission(c, p, scopePermission(path, post, b));
    if (path.equals("/api/bootstrap")) return Service.bootstrap(c, p);
    if (path.equals("/api/dashboard")) return Service.dashboard(c, p, q);
    if (path.equals("/api/auth/password") && post) return auth.changePassword(c, p, b);
    if (path.equals("/api/patients"))
      return post ? Service.createPatient(c, p, b) : Service.patients(c, p, q);
    if (path.startsWith("/api/patients/") && parts.length == 4)
      return post
          ? Service.patientCommand(c, p, parts[3], b)
          : Service.patientDetail(c, p, parts[3]);
    if (path.equals("/api/appointments"))
      return post ? Scheduling.create(c, p, b) : Scheduling.list(c, p, q);
    if (path.startsWith("/api/appointments/") && parts.length == 4)
      return post
          ? Scheduling.command(c, p, parts[3], b)
          : map(
              "appointment",
              Scheduling.get(c, p, parts[3]),
              "history",
              rows(
                  c,
                  "SELECT h.*,u.display_name actor_name FROM appointment_status_history h LEFT JOIN"
                      + " app_users u ON u.id=h.actor_user_id WHERE h.appointment_id=? ORDER BY"
                      + " h.occurred_at",
                  parts[3]));
    if (path.equals("/api/scheduling/validate") && post) {
      p.need("appointment.manage");
      var issues = Scheduling.validate(c, p, b, null, true);
      return map("valid", issues.isEmpty(), "issues", issues, "proposal", b);
    }
    if (path.equals("/api/waitlist"))
      return post ? Scheduling.waitlistCommand(c, p, b) : Scheduling.waitlist(c, p);
    if (path.equals("/api/visits")) return Clinical.list(c, p);
    if (path.startsWith("/api/visits/") && parts.length == 4)
      return post ? Clinical.command(c, p, parts[3], b) : Clinical.detail(c, p, parts[3]);
    if (path.equals("/api/finance/invoices"))
      return post ? Finance.issue(c, p, b) : Finance.list(c, p);
    if (path.equals("/api/finance/unbilled")) {
      p.need("finance.read");
      return rows(
          c,
          "SELECT v.id,v.visit_code,v.patient_id,p.name_zh patient_name,d.name_zh"
              + " dentist_name,v.completed_at FROM clinical_visits v JOIN patients p ON"
              + " p.id=v.patient_id JOIN dentists d ON d.id=v.dentist_id WHERE v.status='COMPLETED'"
              + " AND NOT EXISTS (SELECT 1 FROM invoices i WHERE i.visit_id=v.id) AND "
              + p.scope("v.clinic_id")
              + " ORDER BY v.completed_at DESC LIMIT 300",
          p.scopeArgs());
    }
    if (path.startsWith("/api/finance/invoices/") && parts.length == 5)
      return post ? Finance.command(c, p, parts[4], b) : Finance.detail(c, p, parts[4]);
    if (path.equals("/api/finance/periods"))
      return post ? Finance.periodCommand(c, p, b) : Finance.periods(c, p);
    if (path.equals("/api/finance/preflight"))
      return Finance.calculate(c, p, q.getOrDefault("period_id", ""));
    if (path.equals("/api/resources"))
      return post ? Workforce.command(c, p, b) : Workforce.data(c, p);
    if (path.equals("/api/admin/access"))
      return post ? Workforce.accessCommand(c, p, b) : Workforce.access(c, p);
    if (path.equals("/api/audit")) return Workforce.auditData(c, p);
    if (path.equals("/api/portal")) return Service.portal(c, p);
    if (path.equals("/api/analytics")) {
      p.need("analytics.read");
      return Analytics.metrics(c, p, q);
    }
    if (path.equals("/api/expansion"))
      return post ? Workforce.expansionCommand(c, p, b) : Workforce.expansion(c, p);
    throw error(404, "NOT_FOUND", "此接口不存在");
  }

  private String scopePermission(String path, boolean post, Map<String, Object> b) {
    if (path.startsWith("/api/patients")) return post ? "patient.manage" : "patient.read";
    if (path.startsWith("/api/appointments")
        || path.startsWith("/api/scheduling")
        || path.startsWith("/api/waitlist"))
      return post ? "appointment.manage" : "appointment.read";
    if (path.startsWith("/api/visits")) return post ? "clinical.write" : "clinical.read";
    if (path.startsWith("/api/finance/preflight")) return "period.manage";
    if (path.startsWith("/api/finance/periods") && post)
      return Set.of("expense", "allocate", "cost").contains(s(b, "action"))
          ? "expense.manage"
          : "period.manage";
    if (path.startsWith("/api/finance")) return post ? "finance.manage" : "finance.read";
    if (path.startsWith("/api/resources"))
      return post
          ? (Set.of("credential", "assignment").contains(s(b, "action"))
              ? "workforce.manage"
              : "resource.manage")
          : "clinic.read";
    if (path.startsWith("/api/admin")) return "access.manage";
    if (path.startsWith("/api/audit")) return "audit.read";
    if (path.startsWith("/api/portal")) return "portal.read";
    if (path.startsWith("/api/expansion") && post) return "expansion.manage";
    if (path.startsWith("/api/analytics") || path.startsWith("/api/expansion"))
      return "analytics.read";
    if (path.startsWith("/api/dashboard")) return "dashboard.read";
    return "";
  }

  private void denied(Auth.Principal p, String requestId, String path, Problem e) {
    try {
      db.tx(
          c -> {
            insert(
                c,
                "audit_events",
                map(
                    "request_id",
                    requestId,
                    "actor_user_id",
                    p.userId(),
                    "actor_subject",
                    p.userId(),
                    "action",
                    "REQUEST_DENIED",
                    "entity_type",
                    "API",
                    "entity_id",
                    path,
                    "outcome",
                    "DENIED",
                    "source",
                    "JDBC_API",
                    "reason",
                    e.code,
                    "occurred_at",
                    now()));
            return null;
          });
    } catch (Exception ignored) {
      System.err.println("denial_audit_failed request=" + requestId);
    }
  }

  private void sameOrigin(HttpExchange x) {
    String origin = x.getRequestHeaders().getFirst("Origin");
    if (origin == null) return;
    try {
      URI uri = URI.create(origin);
      String host = x.getRequestHeaders().getFirst("Host");
      check(
          uri.getAuthority() != null && uri.getAuthority().equalsIgnoreCase(host),
          403,
          "ORIGIN",
          "拒绝跨站提交");
    } catch (IllegalArgumentException e) {
      throw error(403, "ORIGIN", "来源无效");
    }
  }

  private Map<String, Object> body(HttpExchange x) throws IOException {
    byte[] bytes = x.getRequestBody().readNBytes(262145);
    check(bytes.length <= 262144, 413, "BODY_LIMIT", "提交内容过大");
    return bytes.length == 0 ? map() : parse(new String(bytes, StandardCharsets.UTF_8));
  }

  private Map<String, String> query(String raw) {
    Map<String, String> m = new LinkedHashMap<>();
    if (raw != null)
      for (String item : raw.split("&")) {
        String[] p = item.split("=", 2);
        m.put(
            URLDecoder.decode(p[0], StandardCharsets.UTF_8),
            p.length == 1 ? "" : URLDecoder.decode(p[1], StandardCharsets.UTF_8));
      }
    return m;
  }

  private String cookieHash(HttpExchange x) {
    String cookie = x.getRequestHeaders().getFirst("Cookie");
    if (cookie != null)
      for (String pair : cookie.split(";")) {
        String[] p = pair.trim().split("=", 2);
        if (p.length == 2 && p[0].equals("adc_session")) return hash(p[1]);
      }
    return "";
  }

  private void respond(HttpExchange x, int status, Object data) throws IOException {
    byte[] out = JSON.writeValueAsBytes(data);
    x.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
    x.sendResponseHeaders(status, out.length);
    x.getResponseBody().write(out);
  }

  private void staticFile(HttpExchange x, String path) throws Exception {
    check(
        x.getRequestMethod().equals("GET") || x.getRequestMethod().equals("HEAD"),
        405,
        "METHOD",
        "此资源不支持该方法");
    String file =
        path.equals("/") || !path.substring(path.lastIndexOf('/') + 1).contains(".")
            ? "index.html"
            : path.substring(1);
    check(
        Set.of("index.html", "app.js", "app.css", "mark.svg").contains(file),
        404,
        "NOT_FOUND",
        "文件不存在");
    byte[] bytes;
    try (var in = Main.class.getResourceAsStream("/web/" + file)) {
      check(in != null, 404, "NOT_FOUND", "界面资源尚未构建");
      bytes = in.readAllBytes();
    }
    String type =
        file.endsWith(".js")
            ? "text/javascript"
            : file.endsWith(".css")
                ? "text/css"
                : file.endsWith(".svg") ? "image/svg+xml" : "text/html";
    x.getResponseHeaders().set("Content-Type", type + "; charset=utf-8");
    x.getResponseHeaders()
        .set("Cache-Control", file.equals("mark.svg") ? "public, max-age=600" : "no-cache");
    if (x.getRequestMethod().equals("HEAD")) {
      x.sendResponseHeaders(200, -1);
      return;
    }
    x.sendResponseHeaders(200, bytes.length);
    x.getResponseBody().write(bytes);
  }
}
