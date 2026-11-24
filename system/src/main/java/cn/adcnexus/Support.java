package cn.adcnexus;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.*;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

public final class Support {
  public static final String VERSION = "1.9.0-rc1";
  public static final ObjectMapper JSON =
      new ObjectMapper()
          .enable(JsonParser.Feature.STRICT_DUPLICATE_DETECTION)
          .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
  public static final ZoneId ZONE = ZoneId.of("Asia/Shanghai");
  public static final DateTimeFormatter DT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

  private static final ThreadLocal<String> BUSINESS_TIME = new ThreadLocal<>();

  static boolean production() {
    return "PRODUCTION".equals(System.getenv("APP_ENV"));
  }

  static boolean seedData() {
    return Boolean.parseBoolean(System.getenv().getOrDefault("SEED_DATA", production() ? "false" : "true"));
  }

  static void validateEnvironment() {
    String profile = System.getenv().getOrDefault("APP_ENV","LOCAL");
    check(Set.of("LOCAL","DEVELOPMENT","DEMO","TEST","PRODUCTION").contains(profile),
        500,"APP_ENV","运行环境配置无效");
    if (!production()) {
      if ("DEMO".equals(System.getenv("APP_ENV")))
        check(DemoAccounts.enabled(), 500, "DEMO_CONFIG", "DEMO 环境须显式配置 DEMO_MODE=true");
      return;
    }
    check(!DemoAccounts.enabled() && !seedData(), 500, "PRODUCTION_ISOLATION",
        "生产环境不得开启演示账号或样例初始化");
    check(!System.getenv().getOrDefault("DATABASE_URL", "").isBlank(), 500, "DATABASE_REQUIRED",
        "生产环境必须配置 PostgreSQL DATABASE_URL");
    String origin = System.getenv().getOrDefault("PUBLIC_ORIGIN", "");
    check(origin.matches("https://[a-zA-Z0-9][a-zA-Z0-9.-]*(?::[0-9]{1,5})?"), 500,
        "PUBLIC_ORIGIN", "生产环境必须配置 HTTPS PUBLIC_ORIGIN，末尾不带斜线");
  }

  public static String wallNow() {
    String fixed = System.getenv("ADC_TEST_NOW");
    if("TEST".equals(System.getenv("APP_ENV")) && System.getenv("ADC_TEST_NOW_FILE")!=null) {
      try { fixed=java.nio.file.Files.readString(java.nio.file.Path.of(System.getenv("ADC_TEST_NOW_FILE"))).trim(); }
      catch(java.io.IOException e) { throw new IllegalStateException("Cannot read isolated test clock",e); }
    }
    return "TEST".equals(System.getenv("APP_ENV")) && fixed != null
        ? LocalDateTime.parse(fixed).format(DT)
        : LocalDateTime.now(ZONE).format(DT);
  }

  public static String now() {
    return BUSINESS_TIME.get() == null ? wallNow() : BUSINESS_TIME.get();
  }

  public static <T> T at(String time, java.util.concurrent.Callable<T> work) throws Exception {
    String previous = BUSINESS_TIME.get();
    BUSINESS_TIME.set(time);
    try { return work.call(); }
    finally { if (previous == null) BUSINESS_TIME.remove(); else BUSINESS_TIME.set(previous); }
  }

  public static <T> T business(boolean demo, java.util.concurrent.Callable<T> work) throws Exception {
    return demo && DailyDemo.enabled() ? at(wallNow().substring(0,10)+" 15:00:00",work) : work.call();
  }

  public static String today() {
    return now().substring(0, 10);
  }

  public static String uuid() {
    return UUID.randomUUID().toString();
  }

  public static String random() {
    byte[] b = new byte[32];
    new SecureRandom().nextBytes(b);
    return Base64.getUrlEncoder().withoutPadding().encodeToString(b);
  }

  public static String hash(String value) {
    try {
      return HexFormat.of()
          .formatHex(
              MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8)));
    } catch (Exception e) {
      throw new IllegalStateException(e);
    }
  }

  public static Map<String, Object> map(Object... pairs) {
    Map<String, Object> m = new LinkedHashMap<>();
    for (int i = 0; i < pairs.length; i += 2) m.put((String) pairs[i], pairs[i + 1]);
    return m;
  }

  public static String s(Map<String, Object> m, String k) {
    Object v = m.get(k);
    return v == null ? "" : String.valueOf(v).trim();
  }

  public static String req(Map<String, Object> m, String k) {
    String s = s(m, k);
    check(!s.isBlank() && s.length() <= 8000, 422, "REQUIRED", "请填写有效的" + fieldLabel(k));
    return s;
  }

  public static String fieldLabel(String key) {
    return switch(key){
      case "username"->"账号";case "password","newPassword","oldPassword"->"密码";case "name","name_zh","display_name"->"姓名或名称";
      case "phone"->"手机号";case "email"->"邮箱";case "patient_id"->"患者";case "clinic_id"->"诊所";case "dentist_id"->"负责医师";
      case "chair_id"->"牙椅";case "treatment_id","qualification_type_id"->"项目或资质类型";case "visit_id"->"就诊记录";case "payment_id"->"原收款记录";
      case "period_id"->"核算期间";case "role_id"->"岗位";case "user_id"->"员工账号";case "employee_id","employee_code"->"员工编号";
      case "scheduled_start_at","starts_at"->"开始时间";case "ends_at"->"结束时间";case "effective_from"->"生效日期";case "date_of_birth"->"出生日期";
      case "issued_on"->"颁发日期";case "due_on"->"复诊日期";case "incurred_on"->"费用日期";case "reason","note","evidence"->"办理说明";
      case "fingerprint","updated_at"->"最新记录信息，请刷新后重试";case "reference","reference_number"->"凭据编号";case "issuing_body"->"颁发机构";
      case "status","employment_status"->"状态";case "priority"->"优先级";case "category"->"类别";case "code"->"代码";case "action"->"操作类型";
      case "amount_fen"->"金额";default->"相关资料";
    };
  }

  public static long n(Map<String, Object> m, String k) {
    Object v = m.get(k);
    if (v == null) return 0;
    try {
      return Long.parseLong(v.toString());
    } catch (Exception e) {
      throw error(422, "INTEGER_REQUIRED", k + " 必须是整数");
    }
  }

  public static String text(Object o) {
    return o == null ? "" : o.toString();
  }

  public static String json(Object o) {
    try {
      return JSON.writeValueAsString(o);
    } catch (Exception e) {
      throw new IllegalStateException(e);
    }
  }

  public static Map<String, Object> parse(String s) {
    try {
      Map<String, Object> value = JSON.readValue(s, new TypeReference<>() {});
      check(value != null, 422, "INVALID_JSON", "提交内容必须为 JSON 对象");
      return value;
    } catch (Exception e) {
      throw error(422, "INVALID_JSON", "数据格式无效");
    }
  }

  public static long val(Map<String, Object> row, String col) {
    return ((Number) row.getOrDefault(col, 0)).longValue();
  }

  public static String password(String password, String salt, int rounds) throws Exception {
    return Base64.getEncoder()
        .encodeToString(
            SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
                .generateSecret(
                    new PBEKeySpec(
                        password.toCharArray(), Base64.getDecoder().decode(salt), rounds, 256))
                .getEncoded());
  }

  public static String salt() {
    byte[] b = new byte[16];
    new SecureRandom().nextBytes(b);
    return Base64.getEncoder().encodeToString(b);
  }

  public static LocalDateTime dateTime(String value) {
    try {
      return LocalDateTime.parse(
          value.replace('T', ' ').length() == 16
              ? value.replace('T', ' ') + ":00"
              : value.replace('T', ' '),
          DT);
    } catch (Exception e) {
      throw error(422, "INVALID_TIME", "时间必须为有效的诊所本地日期时间");
    }
  }

  public static void check(boolean good, int status, String code, String message) {
    if (!good) throw error(status, code, message);
  }

  public static Problem error(int status, String code, String message) {
    return new Problem(status, code, message, List.of());
  }

  public static class Problem extends RuntimeException {
    public final int status;
    public final String code;
    public final List<?> details;

    public Problem(int status, String code, String msg, List<?> details) {
      super(msg);
      this.status = status;
      this.code = code;
      this.details = details;
    }
  }
}
