package cn.adcnexus;

import static cn.adcnexus.Db.*;
import static cn.adcnexus.Support.*;

import java.sql.*;
import java.time.*;
import java.util.*;

final class Analytics {
  static Object metrics(Connection c, Auth.Principal p, Map<String, String> q) throws Exception {
    p.need("analytics.read");
    String from = q.getOrDefault("from", LocalDate.parse(today()).minusDays(90).toString()),
        to = q.getOrDefault("to", today());
    LocalDate first = LocalDate.parse(from), last = LocalDate.parse(to);
    check(
        !first.isAfter(last) && java.time.temporal.ChronoUnit.DAYS.between(first, last) <= 730,
        422,
        "RANGE",
        "请选择不超过两年的有效日期范围");
    var args = Service.join(p.scopeArgs(), new Object[] {from, to});
    String filter =
        p.scope("a.clinic_id")
            + " AND substr(a.scheduled_start_at,1,10)>=? AND substr(a.scheduled_start_at,1,10)<=?";
    long total = count(c, "SELECT COUNT(*) FROM appointments a WHERE " + filter, args),
        cancel =
            count(
                c,
                "SELECT COUNT(*) FROM appointments a WHERE " + filter + " AND status='CANCELLED'",
                args),
        noShow =
            count(
                c,
                "SELECT COUNT(*) FROM appointments a WHERE " + filter + " AND status='NO_SHOW'",
                args),
        fulfilled =
            count(
                c,
                "SELECT COUNT(*) FROM appointments a WHERE " + filter + " AND status='COMPLETED'",
                args);
    var clinics = rows(c, "SELECT id,name_zh FROM clinics WHERE " + p.scope("id"), p.scopeArgs());
    List<Map<String, Object>> utilization = new ArrayList<>();
    for (var clinic : clinics) {
      String cid = s(clinic, "id");
      var hours =
          rows(c, "SELECT * FROM clinic_operating_hours WHERE clinic_id=? AND is_closed=0", cid);
      var closures =
          rows(
              c,
              "SELECT starts_at,ends_at FROM clinic_closures WHERE clinic_id=? AND status='ACTIVE'",
              cid);
      long
          chairs =
              count(
                  c,
                  "SELECT COUNT(*) FROM clinic_chairs WHERE clinic_id=? AND status='AVAILABLE'",
                  cid),
          available = 0,
          occupied = 0;
      var bookings =
          rows(
              c,
              "SELECT chair_id,scheduled_start_at,scheduled_end_at FROM appointments WHERE"
                  + " clinic_id=? AND chair_id IS NOT NULL AND status NOT IN"
                  + " ('CANCELLED','NO_SHOW','HOLD') AND substr(scheduled_start_at,1,10)>=? AND"
                  + " substr(scheduled_start_at,1,10)<=?",
              cid,
              from,
              to);
      for (LocalDate date = first; !date.isAfter(last); date = date.plusDays(1)) {
        int day = date.getDayOfWeek().getValue() % 7;
        final LocalDate serviceDate = date;
        for (var h : hours) {
          if (val(h, "day_of_week") != day) continue;
          LocalDateTime open = LocalDateTime.of(date, LocalTime.parse(s(h, "opens_at"))),
              close = LocalDateTime.of(date, LocalTime.parse(s(h, "closes_at")));
          long minutes = Duration.between(open, close).toMinutes();
          List<long[]> closed = new ArrayList<>();
          for (var closure : closures) {
            LocalDateTime a = dateTime(s(closure, "starts_at")),
                b = dateTime(s(closure, "ends_at"));
            if (a.isBefore(close) && b.isAfter(open))
              closed.add(
                  new long[] {
                    Math.max(0, Duration.between(open, a).toMinutes()),
                    Math.min(minutes, Duration.between(open, b).toMinutes())
                  });
          }
          available += (minutes - union(closed)) * chairs;
          Map<String, List<long[]>> byChair = new LinkedHashMap<>();
          for (var booking : bookings) {
            LocalDateTime a = dateTime(s(booking, "scheduled_start_at")),
                b = dateTime(s(booking, "scheduled_end_at"));
            if (a.toLocalDate().equals(serviceDate) && a.isBefore(close) && b.isAfter(open)) {
              long st = Math.max(0, Duration.between(open, a).toMinutes()),
                  et = Math.min(minutes, Duration.between(open, b).toMinutes());
              List<long[]> segments = new ArrayList<>();
              segments.add(new long[] {st, et});
              for (long[] gap : closed) segments = subtract(segments, gap);
              byChair
                  .computeIfAbsent(s(booking, "chair_id"), key -> new ArrayList<>())
                  .addAll(segments);
            }
          }
          for (var intervals : byChair.values()) occupied += union(intervals);
        }
      }
      utilization.add(
          map(
              "clinic_id",
              cid,
              "clinic_name",
              clinic.get("name_zh"),
              "available_chair_minutes",
              available,
              "occupied_chair_minutes",
              occupied,
              "rate",
              available == 0 ? null : occupied * 1.0 / available));
    }
    var dentistRows =
        rows(
            c,
            "SELECT d.id,d.name_zh,COUNT(a.id) appointments,SUM(CASE WHEN a.status='COMPLETED' THEN"
                + " 1 ELSE 0 END) completed,SUM(CASE WHEN a.status='CANCELLED' THEN 1 ELSE 0 END)"
                + " cancelled FROM dentists d LEFT JOIN appointments a ON a.dentist_id=d.id AND "
                + filter
                + " GROUP BY d.id,d.name_zh ORDER BY appointments DESC",
            args);
    var treatmentRows =
        rows(
            c,
            "SELECT t.code,t.name_zh,COUNT(x.id) treatments,COALESCE(SUM(x.units),0) units FROM"
                + " actual_treatment_items x JOIN treatment_catalog t ON t.id=x.treatment_id JOIN"
                + " clinical_visits a ON a.id=x.visit_id WHERE "
                + p.scope("a.clinic_id")
                + " AND substr(x.performed_at,1,10)>=? AND substr(x.performed_at,1,10)<=? GROUP BY"
                + " t.code,t.name_zh ORDER BY units DESC",
            args);
    long
        visits =
            count(
                c,
                "SELECT COUNT(*) FROM clinical_visits a WHERE "
                    + p.scope("a.clinic_id")
                    + " AND substr(a.started_at,1,10)>=? AND substr(a.started_at,1,10)<=? AND"
                    + " a.status<>'CANCELLED'",
                args),
        completedVisits =
            count(
                c,
                "SELECT COUNT(*) FROM clinical_visits a WHERE "
                    + p.scope("a.clinic_id")
                    + " AND substr(a.started_at,1,10)>=? AND substr(a.started_at,1,10)<=? AND"
                    + " a.status='COMPLETED'",
                args);
    var catalog =
        rows(
            c,
            "SELECT id,code,name_zh,effective_from,effective_to FROM treatment_catalog WHERE"
                + " status='ACTIVE'");
    var assignments =
        rows(
            c,
            "SELECT DISTINCT dentist_id,clinic_id FROM dentist_clinic_assignments WHERE"
                + " status='ACTIVE' AND effective_from<=? AND (effective_to IS NULL OR"
                + " effective_to>=?)",
            to,
            to);
    var credentials =
        rows(
            c,
            "SELECT dentist_id,qualification_type_id FROM dentist_qualifications WHERE"
                + " verification_status='VERIFIED' AND issued_on<=? AND (expires_on IS NULL OR"
                + " expires_on>=?)",
            to,
            to);
    var requirements =
        rows(
            c,
            "SELECT treatment_id,qualification_type_id FROM treatment_qualification_requirements"
                + " WHERE requirement_level='REQUIRED'");
    List<Map<String, Object>> coverage = new ArrayList<>();
    for (var clinic : clinics)
      for (var treatment : catalog) {
        int qualified = 0;
        if (s(treatment, "effective_from").compareTo(to) <= 0
            && (s(treatment, "effective_to").isBlank()
                || s(treatment, "effective_to").compareTo(to) >= 0))
          for (var d : assignments) {
            if (!d.get("clinic_id").equals(clinic.get("id"))) continue;
            boolean eligible = true;
            for (var requirement : requirements) {
              if (!requirement.get("treatment_id").equals(treatment.get("id"))) continue;
              boolean valid = false;
              for (var credential : credentials)
                if (credential.get("dentist_id").equals(d.get("dentist_id"))
                    && credential
                        .get("qualification_type_id")
                        .equals(requirement.get("qualification_type_id"))) {
                  valid = true;
                  break;
                }
              if (!valid) {
                eligible = false;
                break;
              }
            }
            if (eligible) qualified++;
          }
        coverage.add(
            map(
                "clinic_name",
                clinic.get("name_zh"),
                "treatment_name",
                treatment.get("name_zh"),
                "qualified_dentists",
                qualified,
                "service_date",
                to));
      }
    return map(
        "from",
        from,
        "to",
        to,
        "generated_at",
        now(),
        "appointments",
        total,
        "completed",
        fulfilled,
        "cancellations",
        cancel,
        "no_shows",
        noShow,
        "cancellation_rate",
        total == 0 ? null : cancel * 1.0 / total,
        "no_show_rate",
        total - cancel == 0 ? null : noShow * 1.0 / (total - cancel),
        "clinical_completion_rate",
        visits == 0 ? null : completedVisits * 1.0 / visits,
        "utilization",
        utilization,
        "dentists",
        dentistRows,
        "treatments",
        treatmentRows,
        "coverage",
        coverage,
        "definitions",
        List.of(
            "预约按计划服务日计数；取消率=取消/同期计划服务预约，未到诊率=未到诊/(计划服务预约-取消)。",
            "牙椅利用率=有效预约占用分钟并集/营业且未停诊的当前可用牙椅分钟；历史牙椅状态未形成独立有效期，因此历史分母按当前可用配置估算，不能作为已批准考核。",
            "临床完成率=完成就诊/同期已建立且未撤销就诊；无分母显示不适用。",
            "资质覆盖按结束日期的有效任职和项目必需证书计数，不等于该时刻可立即接诊。"));
  }

  static long union(List<long[]> intervals) {
    if (intervals.isEmpty()) return 0;
    intervals.sort(Comparator.comparingLong(a -> a[0]));
    long total = 0, start = intervals.getFirst()[0], end = intervals.getFirst()[1];
    for (int i = 1; i < intervals.size(); i++) {
      long[] a = intervals.get(i);
      if (a[0] <= end) end = Math.max(end, a[1]);
      else {
        total += Math.max(0, end - start);
        start = a[0];
        end = a[1];
      }
    }
    return total + Math.max(0, end - start);
  }

  static List<long[]> subtract(List<long[]> segments, long[] gap) {
    List<long[]> out = new ArrayList<>();
    for (long[] s : segments) {
      if (gap[0] >= s[1] || gap[1] <= s[0]) out.add(s);
      else {
        if (gap[0] > s[0]) out.add(new long[] {s[0], gap[0]});
        if (gap[1] < s[1]) out.add(new long[] {gap[1], s[1]});
      }
    }
    return out;
  }
}
