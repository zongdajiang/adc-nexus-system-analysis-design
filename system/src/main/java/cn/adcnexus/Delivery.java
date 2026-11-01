package cn.adcnexus;

import static cn.adcnexus.Support.*;
import jakarta.mail.*;
import jakarta.mail.internet.*;
import java.net.*;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.*;

/** Real delivery adapters. No public test code, fallback code, or message-body logging. */
final class Delivery {
  static String env(String key) { return System.getenv().getOrDefault(key, "").trim(); }
  static boolean testSink() {
    if (!"TEST".equals(env("APP_ENV")) || env("AUTH_TEST_DELIVERY_URL").isBlank()) return false;
    URI u = URI.create(env("AUTH_TEST_DELIVERY_URL"));
    return "http".equals(u.getScheme()) && Set.of("127.0.0.1", "localhost").contains(u.getHost());
  }
  static boolean configured(String channel) {
    if (testSink()) return true;
    return channel.equals("EMAIL")
        ? (env("MAIL_PROVIDER").equals("BREVO")
            ? !env("BREVO_API_KEY").isBlank() && !env("MAIL_FROM").isBlank()
            : !env("SMTP_HOST").isBlank() && !env("SMTP_USER").isBlank()
                && !env("SMTP_PASSWORD").isBlank() && !env("SMTP_FROM").isBlank())
        : !env("TWILIO_ACCOUNT_SID").isBlank() && !env("TWILIO_AUTH_TOKEN").isBlank()
            && !env("TWILIO_FROM").isBlank();
  }
  static void send(String channel, String destination, String code) throws Exception {
    if (testSink()) {
      // Isolated acceptance receiver, allowed only in APP_ENV=TEST on loopback.
      var response = client().send(HttpRequest.newBuilder(URI.create(env("AUTH_TEST_DELIVERY_URL")))
          .timeout(Duration.ofSeconds(10)).header("Content-Type", "application/json")
          .POST(HttpRequest.BodyPublishers.ofString(json(map("channel", channel, "destination", destination, "code", code))))
          .build(), HttpResponse.BodyHandlers.discarding());
      if (response.statusCode() != 204) throw new IllegalStateException("Test delivery rejected");
      return;
    }
    String message = "ADC Nexus 验证码：" + code + "，5 分钟内有效。请勿向他人透露。若非本人操作，请忽略。";
    if (channel.equals("EMAIL") && env("MAIL_PROVIDER").equals("BREVO")) {
      var response = client().send(HttpRequest.newBuilder(URI.create("https://api.brevo.com/v3/smtp/email"))
          .timeout(Duration.ofSeconds(15)).header("api-key", env("BREVO_API_KEY"))
          .header("Content-Type", "application/json").header("Accept", "application/json")
          .POST(HttpRequest.BodyPublishers.ofString(json(map("sender", map("email", env("MAIL_FROM"), "name", "ADC Nexus"),
              "to", List.of(map("email", destination)), "subject", "ADC Nexus 账号验证", "textContent", message))))
          .build(), HttpResponse.BodyHandlers.discarding());
      if (response.statusCode() != 201) throw new IllegalStateException("Mail provider rejected message");
      return;
    }
    if (channel.equals("EMAIL")) {
      Properties props = new Properties();
      boolean ssl = env("SMTP_PORT").equals("465");
      props.setProperty("mail.smtp.host", env("SMTP_HOST"));
      props.setProperty("mail.smtp.port", env("SMTP_PORT").isBlank() ? "587" : env("SMTP_PORT"));
      props.setProperty("mail.smtp.auth", "true");
      props.setProperty("mail.smtp.ssl.checkserveridentity", "true");
      props.setProperty("mail.smtp.ssl.enable", Boolean.toString(ssl));
      props.setProperty("mail.smtp.starttls.enable", Boolean.toString(!ssl));
      props.setProperty("mail.smtp.starttls.required", Boolean.toString(!ssl));
      props.setProperty("mail.smtp.connectiontimeout", "10000");
      props.setProperty("mail.smtp.timeout", "10000");
      props.setProperty("mail.smtp.writetimeout", "10000");
      Session session = Session.getInstance(props, new jakarta.mail.Authenticator() {
        @Override protected jakarta.mail.PasswordAuthentication getPasswordAuthentication() {
          return new jakarta.mail.PasswordAuthentication(env("SMTP_USER"), env("SMTP_PASSWORD"));
        }
      });
      MimeMessage mail = new MimeMessage(session);
      mail.setFrom(new InternetAddress(env("SMTP_FROM"), "ADC Nexus", "UTF-8"));
      mail.setRecipient(Message.RecipientType.TO, new InternetAddress(destination));
      mail.setSubject("ADC Nexus 账号验证", "UTF-8");
      mail.setText(message, "UTF-8");
      Transport.send(mail);
    } else {
      String sid = env("TWILIO_ACCOUNT_SID");
      check(sid.matches("AC[a-fA-F0-9]{32}"), 503, "PROVIDER_NOT_CONFIGURED", "短信通道配置无效");
      String body = "To=" + enc(destination) + "&From=" + enc(env("TWILIO_FROM")) + "&Body=" + enc(message);
      String basic = Base64.getEncoder().encodeToString((sid + ":" + env("TWILIO_AUTH_TOKEN")).getBytes(StandardCharsets.UTF_8));
      var response = client().send(HttpRequest.newBuilder(URI.create("https://api.twilio.com/2010-04-01/Accounts/" + sid + "/Messages.json"))
          .timeout(Duration.ofSeconds(15)).header("Authorization", "Basic " + basic)
          .header("Content-Type", "application/x-www-form-urlencoded")
          .POST(HttpRequest.BodyPublishers.ofString(body)).build(), HttpResponse.BodyHandlers.discarding());
      if (response.statusCode() != 201) throw new IllegalStateException("SMS provider rejected message");
    }
  }
  private static HttpClient client() {
    return HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(8))
        .followRedirects(HttpClient.Redirect.NEVER).build();
  }
  private static String enc(String v) { return URLEncoder.encode(v, StandardCharsets.UTF_8); }
}
