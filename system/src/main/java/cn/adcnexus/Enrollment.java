package cn.adcnexus;

import static cn.adcnexus.Db.*;
import static cn.adcnexus.Support.*;
import com.sun.net.httpserver.HttpExchange;
import java.security.*;
import java.sql.*;
import java.time.LocalDate;
import java.util.*;

/** Unified enrollment: verified contact ownership is separate from clinical identity and role grants. */
final class Enrollment {
  private final Db db;
  private final Auth auth;
  static final Map<String,String> POSITIONS = Map.of(
      "FD", "FRONT_DESK", "DR", "DENTIST", "CS", "CASHIER", "MG", "CLINIC_MANAGER",
      "OP", "HQ_OPERATIONS", "FN", "HQ_FINANCE", "AD", "ADMIN");
  Enrollment(Db db, Auth auth) { this.db = db; this.auth = auth; }

  static String contact(String channel, String value) {
    value = value.trim();
    if (channel.equals("EMAIL")) {
      value = value.toLowerCase(Locale.ROOT);
      check(value.length() <= 254 && value.matches("[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\\.[a-z]{2,63}"),
          422, "EMAIL_FORMAT", "请输入有效的邮箱地址");
    } else {
      check(channel.equals("PHONE"), 422, "CHANNEL", "请选择手机或邮箱验证");
      value = value.replaceAll("[ ()-]", "");
      if (value.matches("1[3-9][0-9]{9}")) value = "+86" + value;
      check(value.matches("\\+[1-9][0-9]{7,14}"), 422, "PHONE_FORMAT", "请输入带国家区号的手机号，例如 +8613800000000");
    }
    return value;
  }

  static Map<String,Object> contactUser(Connection c, String channel, String destination) throws Exception {
    return one(c, "SELECT u.* FROM app_users u JOIN auth_identities i ON i.user_id=u.id WHERE i.provider=? AND i.provider_subject=?",
        "VERIFIED_" + channel, destination);
  }
  static Map<String,Object> lookup(Connection c, String identifier) throws Exception {
    var direct = one(c, "SELECT * FROM app_users WHERE username=?", identifier);
    if (direct != null) return direct;
    if (identifier.matches("(?i)ADC-(FD|DR|CS|MG|OP|FN|AD)-[0-9]{6}"))
      return one(c, "SELECT u.* FROM app_users u JOIN staff_directory s ON s.claimed_user_id=u.id WHERE s.employee_code=? AND s.status='ACTIVE'",
          identifier.toUpperCase(Locale.ROOT));
    try {
      String channel = identifier.contains("@") ? "EMAIL" : "PHONE";
      return contactUser(c, channel, contact(channel, identifier));
    } catch (Problem ignored) { return null; }
  }

  Object config() throws Exception {
    return map("demo", auth.demo, "sms", Delivery.configured("PHONE"), "email", Delivery.configured("EMAIL"),
        "registration_ready", Delivery.configured("PHONE") && Delivery.configured("EMAIL"),
        "wechat", false, "roles", Seed.GRANTS.keySet().stream().filter(r -> !r.equals("ADMIN"))
            .map(r -> map("code", r, "name", Seed.roleName(r))).toList(),
        "service_notice", "课程合成数据环境；密码登录可用。手机及邮箱验证须由机构配置真实发送服务。不存在公开通用验证码。");
  }

  Object challenge(HttpExchange x, Map<String,Object> b) throws Exception {
    String channel = req(b, "channel"), destination = contact(channel, req(b, "destination")), purpose = req(b, "purpose");
    check(Set.of("REGISTER", "LOGIN", "RECOVER").contains(purpose), 422, "PURPOSE", "验证用途无效");
    check(Delivery.configured(channel), 503, "PROVIDER_NOT_CONFIGURED", channel.equals("EMAIL")
        ? "邮箱发送服务尚未配置，请使用账号密码登录，或联系管理员开通" : "短信发送服务尚未配置，请使用账号密码登录，或联系管理员开通");
    String id = uuid(), code = String.format(Locale.ROOT, "%06d", new SecureRandom().nextInt(1000000)), salt = salt();
    // Socket peer only, never a caller-forged X-Forwarded-For. Destination/global caps also protect shared proxies.
    String ip = hash(x.getRemoteAddress().getAddress().getHostAddress());
    db.tx(c -> {
      String minute = dateTime(now()).minusSeconds(60).format(DT), window = dateTime(now()).minusMinutes(15).format(DT);
      check(count(c, "SELECT COUNT(*) FROM verification_challenges WHERE channel=? AND destination=? AND created_at>?", channel, destination, minute) == 0,
          429, "OTP_COOLDOWN", "请等待 60 秒后再次获取验证码");
      check(count(c, "SELECT COUNT(*) FROM verification_challenges WHERE channel=? AND destination=? AND created_at>=?", channel, destination, window) < 5
          && count(c, "SELECT COUNT(*) FROM verification_challenges WHERE request_ip_hash=? AND created_at>=?", ip, window) < 30
          && count(c, "SELECT COUNT(*) FROM verification_challenges WHERE created_at>=?", window) < 100,
          429, "OTP_RATE_LIMIT", "验证码请求过于频繁，请稍后重试");
      int dailyLimit;
      try { dailyLimit = Integer.parseInt(Delivery.env("AUTH_DAILY_SEND_LIMIT").isBlank() ? "50" : Delivery.env("AUTH_DAILY_SEND_LIMIT")); }
      catch (NumberFormatException e) { throw error(503,"PROVIDER_NOT_CONFIGURED","发送额度配置无效"); }
      check(dailyLimit > 0 && dailyLimit <= 5000,503,"PROVIDER_NOT_CONFIGURED","发送额度配置无效");
      check(count(c,"SELECT COUNT(*) FROM verification_challenges WHERE created_at>=?",today()+" 00:00:00") < dailyLimit,
          429,"OTP_DAILY_LIMIT","今日验证码发送额度已用完，请使用账号密码登录或联系机构管理员");
      var user = purpose.equals("REGISTER") ? null : contactUser(c, channel, destination);
      insert(c, "verification_challenges", map("id", id, "channel", channel, "destination", destination, "purpose", purpose,
          "user_id", user == null ? null : user.get("id"), "code_hash", password(code, salt, 120000), "code_salt", salt,
          "status", "PENDING", "request_ip_hash", ip, "expires_at", dateTime(now()).plusMinutes(5).format(DT), "created_at", now()));
      return null;
    });
    try {
      // Network I/O must not hold the SQLite write lock / PostgreSQL transaction lock.
      Delivery.send(channel, destination, code);
      db.tx(c -> {
        execute(c, "UPDATE verification_challenges SET consumed_at=? WHERE channel=? AND destination=? AND purpose=? AND id<>? AND consumed_at IS NULL", now(), channel, destination, purpose, id);
        update(c, "verification_challenges", id, map("status", "SENT"));
        return null;
      });
    } catch (Exception e) {
      db.tx(c -> { update(c, "verification_challenges", id, map("status", "FAILED")); return null; });
      throw error(503, "DELIVERY_FAILED", "发送服务暂未接受请求，请稍后重试或使用密码登录");
    }
    return map("challenge_id", id, "expires_in", 300, "retry_after", 60,
        "message", "验证请求已受理。验证码仅用于本人操作；账号是否可用须在验证后确认。");
  }

  private static boolean verify(Connection c, String id, String channel, String destination, String purpose, String code) throws Exception {
    var row = one(c, "SELECT * FROM verification_challenges WHERE id=?", id);
    if (row == null || !s(row,"channel").equals(channel) || !s(row,"destination").equals(destination)
        || !s(row,"purpose").equals(purpose) || !s(row,"status").equals("SENT")
        || row.get("consumed_at") != null || s(row,"expires_at").compareTo(now()) <= 0 || val(row,"attempt_count") >= 5) return false;
    update(c, "verification_challenges", id, map("attempt_count", val(row,"attempt_count") + 1));
    return code.matches("[0-9]{6}") && MessageDigest.isEqual(password(code, s(row,"code_salt"), 120000).getBytes(java.nio.charset.StandardCharsets.UTF_8),
        s(row,"code_hash").getBytes(java.nio.charset.StandardCharsets.UTF_8));
  }
  private static void consume(Connection c, String id) throws Exception {
    update(c, "verification_challenges", id, map("consumed_at", now()));
  }
  static void passwordPolicy(String value) {
    check(value.length() >= 12 && value.length() <= 128 && !value.isBlank(), 422, "PASSWORD_POLICY", "密码长度需为 12 至 128 个字符，建议使用不重复的长密码");
  }
  static Map<String,Object> invalid() { return map("verification_failed", true); }

  Object codeLogin(HttpExchange x, Map<String,Object> b, boolean recover) throws Exception {
    String channel = req(b,"channel"), dest = contact(channel, req(b,"destination")), id = req(b,"challenge_id"), code = req(b,"code");
    String fresh = recover ? req(b,"new_password") : "";
    if (recover) passwordPolicy(fresh);
    return db.tx(c -> {
      if (!verify(c, id, channel, dest, recover ? "RECOVER" : "LOGIN", code)) return invalid();
      var row = one(c, "SELECT user_id FROM verification_challenges WHERE id=?", id);
      var user = contactUser(c, channel, dest);
      consume(c, id);
      if (user == null || !s(user,"id").equals(s(row,"user_id")) || !s(user,"status").equals("ACTIVE")) return invalid();
      String uid = s(user,"id");
      if (recover) {
        String salt = salt();
        update(c, "app_users", uid, map("password_hash", password(fresh, salt, 600000), "password_salt", salt,
            "password_iterations", 600000, "password_set_at", now(), "failed_login_count", 0, "locked_until", null));
        execute(c, "UPDATE auth_sessions SET revoked_at=? WHERE user_id=? AND revoked_at IS NULL", now(), uid);
        return map("ok", true, "reauthenticate", true);
      }
      update(c, "app_users", uid, map("last_sign_in_at", now(), "failed_login_count", 0, "locked_until", null));
      return auth.issue(c, x, uid, channel + "_OTP");
    });
  }

  Object register(Map<String,Object> b) throws Exception {
    String kind = req(b,"kind"), name = req(b,"name"), phone = contact("PHONE", req(b,"phone")), email = contact("EMAIL", req(b,"email")), pass = req(b,"password");
    check(Set.of("EMPLOYEE","PATIENT").contains(kind), 422, "ACCOUNT_KIND", "请选择内部员工或患者");
    check(name.length() <= 60, 422, "NAME", "姓名过长");
    passwordPolicy(pass);
    check(Boolean.TRUE.equals(b.get("accepted_terms")), 422, "CONSENT", "请先阅读账号使用与隐私说明");
    String phoneId = req(b,"phone_challenge"), emailId = req(b,"email_challenge");
    if (kind.equals("PATIENT")) {
      LocalDate dob = LocalDate.parse(req(b,"date_of_birth"));
      check(!dob.isBefore(LocalDate.of(1900,1,1)) && !dob.isAfter(LocalDate.parse(today())), 422, "DATE_OF_BIRTH", "出生日期不在合理范围内");
      check(Set.of("MALE","FEMALE","OTHER","UNKNOWN").contains(req(b,"gender")), 422, "GENDER", "请选择有效的性别记录");
    }
    return db.tx(c -> {
      // Return a denial marker, not an exception: failed-attempt increments must commit.
      boolean pv = verify(c, phoneId, "PHONE", phone, "REGISTER", req(b,"phone_code"));
      boolean ev = verify(c, emailId, "EMAIL", email, "REGISTER", req(b,"email_code"));
      if (!pv || !ev) return invalid();
      check(count(c, "SELECT COUNT(*) FROM app_users WHERE lower(email)=? OR phone_e164=?", email, phone) == 0,
          409, "CONTACT_IN_USE", "此联系方式已被占用，请登录原账号或联系机构核实");
      var staff = kind.equals("EMPLOYEE") ? one(c, "SELECT s.* FROM staff_directory s JOIN roles r ON r.id=s.role_id WHERE s.employee_code=? AND s.status='ACTIVE' AND r.status='ACTIVE'", req(b,"employee_id").toUpperCase(Locale.ROOT)) : null;
      Map<String,Object> invitation = null;
      if (kind.equals("EMPLOYEE")) {
        check(staff != null && staff.get("claimed_user_id") == null && s(staff,"phone_e164").equals(phone)
            && s(staff,"email").equals(email) && s(staff,"display_name").equals(name),
            422, "STAFF_IDENTITY", "员工编号、姓名或联系方式与在职名册不匹配，请联系机构核实");
        invitation = one(c, "SELECT * FROM account_invitations WHERE staff_directory_id=? AND token_hash=? AND status='PENDING' AND expires_at>?",
            staff.get("id"), hash(req(b,"activation_code")), now());
        check(invitation != null, 422, "INVITATION", "激活码无效或已过期，请联系管理员重新签发");
      } else {
        // Contact ownership alone is not evidence of ownership of an existing medical record.
        check(count(c, "SELECT COUNT(*) FROM patients WHERE phone IN (?,?) OR (name_zh=? AND date_of_birth=?)",
            phone, phone.startsWith("+86") ? phone.substring(3) : phone, name, req(b,"date_of_birth")) == 0,
            409, "PATIENT_REVIEW_REQUIRED", "资料可能与机构现有档案相符，请到诊所核实并绑定原档案；系统不会自动开放既有病历");
      }
      String uid = uuid(), username = staff == null ? "ADC-PT-" + uuid().replace("-", "").substring(0,12).toUpperCase(Locale.ROOT) : s(staff,"employee_code"), salt = salt();
      insert(c, "app_users", map("id", uid, "auth_subject", "local:" + uid, "email", email, "phone_e164", phone,
          "display_name", name, "username", username, "status", "ACTIVE", "password_hash", password(pass, salt, 600000),
          "password_salt", salt, "password_iterations", 600000, "password_set_at", now(), "created_at", now(), "updated_at", now()));
      for (String ch : List.of("PHONE","EMAIL")) insert(c, "auth_identities", map("id", uuid(), "user_id", uid,
          "provider", "VERIFIED_" + ch, "provider_subject", ch.equals("PHONE") ? phone : email,
          "profile_json", json(map("verified_at", now(), "source", "OTP_REGISTRATION")), "created_at", now(), "updated_at", now()));
      String role = staff == null ? "jdbc-role-PATIENT" : s(staff,"role_id");
      insert(c, "user_role_assignments", map("id", uuid(), "user_id", uid, "role_id", role, "clinic_id", staff == null ? null : staff.get("clinic_id"),
          "effective_from", today(), "status", "ACTIVE", "granted_by_user_id", staff == null ? null : staff.get("created_by_user_id"), "created_at", now()));
      if (staff != null) {
        update(c, "staff_directory", s(staff,"id"), map("claimed_user_id", uid, "updated_at", now()));
        update(c, "account_invitations", s(invitation,"id"), map("status", "ACCEPTED", "target_user_id", uid, "accepted_at", now()));
        if (staff.get("dentist_id") != null) insert(c, "system_settings", map("organization_id", "org-adc", "setting_key", "dentist_user:" + uid, "value_json", json(staff.get("dentist_id")), "updated_at", now()));
      } else {
        String patient = uuid();
        insert(c, "patients", map("id", patient, "patient_code", username, "name_zh", name, "name_en", name,
            "date_of_birth", req(b,"date_of_birth"), "gender", req(b,"gender"), "phone", phone, "email", email,
            "communication_channel", "EMAIL", "status", "ACTIVE", "created_at", now(), "updated_at", now()));
        insert(c, "patient_account_links", map("id", uuid(), "user_id", uid, "patient_id", patient,
            "verification_method", "SELF_ENROLLED_NEW_RECORD_CONTACTS_VERIFIED", "verified_at", now(), "created_at", now()));
      }
      consume(c, phoneId); consume(c, emailId);
      insert(c, "audit_events", map("request_id", uuid(), "actor_user_id", uid, "actor_subject", uid, "action", "SELF_REGISTER_" + kind,
          "entity_type", "app_users", "entity_id", uid, "outcome", "SUCCESS", "source", "JDBC_API", "occurred_at", now()));
      return map("ok", true, "username", username, "message", "注册成功，请使用新账号、已验证手机或邮箱登录");
    });
  }

  static Object roster(Connection c, Auth.Principal p, Map<String,Object> b, boolean post) throws Exception {
    p.need("access.manage");
    check(p.network(), 403, "NETWORK_REQUIRED", "员工身份名册仅限机构账户管理员维护");
    if (!post) return rows(c, "SELECT s.*,r.name_zh role_name,cl.name_zh clinic_name FROM staff_directory s JOIN roles r ON r.id=s.role_id LEFT JOIN clinics cl ON cl.id=s.clinic_id ORDER BY s.employee_code");
    String action = req(b,"action");
    if (action.equals("deactivate")) {
      var row = one(c, "SELECT * FROM staff_directory WHERE id=?", req(b,"id"));
      check(row != null, 404, "NOT_FOUND", "员工名册记录不存在");
      check(!p.userId().equals(s(row,"claimed_user_id")), 409, "SELF_LOCKOUT", "不能停用本人名册");
      update(c, "staff_directory", s(row,"id"), map("status", "INACTIVE", "updated_at", now()));
      execute(c, "UPDATE account_invitations SET status='REVOKED' WHERE staff_directory_id=? AND status='PENDING'", row.get("id"));
      if (row.get("claimed_user_id") != null) {
        update(c, "app_users", s(row,"claimed_user_id"), map("status", "DISABLED", "updated_at", now()));
        execute(c, "UPDATE auth_sessions SET revoked_at=? WHERE user_id=? AND revoked_at IS NULL", now(), row.get("claimed_user_id"));
      }
      Service.audit(c,p,"STAFF_DEACTIVATE","staff_directory",s(row,"id"),null);
      return map("ok",true);
    }
    Map<String,Object> staff;
    if (action.equals("create")) {
      String code = req(b,"employee_id").toUpperCase(Locale.ROOT);
      check(code.matches("ADC-(FD|DR|CS|MG|OP|FN|AD)-[0-9]{6}"), 422, "EMPLOYEE_ID", "员工编号格式为 ADC-岗位代码-六位数字，例如 ADC-DR-000001");
      String role = POSITIONS.get(code.split("-")[1]), cid = s(b,"clinic_id"), did = s(b,"dentist_id");
      boolean local = Set.of("FRONT_DESK","DENTIST","CASHIER","CLINIC_MANAGER").contains(role);
      check(!local || count(c,"SELECT COUNT(*) FROM clinics WHERE id=? AND status='ACTIVE'",cid)==1,422,"CLINIC_REQUIRED","诊所岗位须指定有效诊所");
      check(local || cid.isBlank(),422,"ROLE_SCOPE","总部岗位不应绑定单个诊所");
      if (role.equals("DENTIST")) check(count(c,"SELECT COUNT(*) FROM dentists WHERE id=? AND employment_status='ACTIVE'",did)==1,422,"DENTIST_REQUIRED","医师岗位须关联有效医师档案");
      else check(did.isBlank(),422,"DENTIST_SCOPE","非医师岗位不能关联医师档案");
      String id = uuid();
      insert(c,"staff_directory",map("id",id,"employee_code",code,"display_name",req(b,"name"),"role_id","jdbc-role-"+role,
          "clinic_id",cid.isBlank()?null:cid,"dentist_id",did.isBlank()?null:did,"phone_e164",contact("PHONE",req(b,"phone")),
          "email",contact("EMAIL",req(b,"email")),"status","ACTIVE","created_by_user_id",p.userId(),"created_at",now(),"updated_at",now()));
      staff=one(c,"SELECT * FROM staff_directory WHERE id=?",id);
    } else {
      check(action.equals("reissue"),422,"ACTION","未知员工名册操作");
      staff=one(c,"SELECT * FROM staff_directory WHERE id=? AND status='ACTIVE' AND claimed_user_id IS NULL",req(b,"id"));
      check(staff!=null,409,"STAFF_CLAIMED","只能为有效且未激活的员工重新签发激活码");
    }
    execute(c,"UPDATE account_invitations SET status='REVOKED' WHERE staff_directory_id=? AND status='PENDING'",staff.get("id"));
    String token=random(), expiry=dateTime(now()).plusHours(48).format(DT);
    insert(c,"account_invitations",map("id",uuid(),"staff_directory_id",staff.get("id"),"token_hash",hash(token),"phone_e164",staff.get("phone_e164"),
        "role_id",staff.get("role_id"),"clinic_id",staff.get("clinic_id"),"status","PENDING","expires_at",expiry,"created_by_user_id",p.userId(),"created_at",now()));
    Service.audit(c,p,"STAFF_INVITE","staff_directory",s(staff,"id"),null);
    return map("ok",true,"employee_id",staff.get("employee_code"),"activation_code",token,"expires_at",expiry,
        "message","激活码仅显示一次，请经机构认可的渠道交给本人；48 小时有效。重新签发会使旧码失效。");
  }
}
