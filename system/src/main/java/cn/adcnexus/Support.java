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
  public static final String VERSION = "1.0.0-rc1";
  public static final ObjectMapper JSON =
      new ObjectMapper()
          .enable(JsonParser.Feature.STRICT_DUPLICATE_DETECTION)
          .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
  public static final ZoneId ZONE = ZoneId.of("Asia/Shanghai");
  public static final DateTimeFormatter DT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

  public static String now() {
    String fixed = System.getenv("ADC_TEST_NOW");
    return "TEST".equals(System.getenv("APP_ENV")) && fixed != null
        ? LocalDateTime.parse(fixed).format(DT)
        : LocalDateTime.now(ZONE).format(DT);
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
    check(!s.isBlank() && s.length() <= 8000, 422, "REQUIRED", "请填写有效的 " + k);
    return s;
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
