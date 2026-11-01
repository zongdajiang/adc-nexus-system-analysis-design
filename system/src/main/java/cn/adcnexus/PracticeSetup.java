package cn.adcnexus;

import static cn.adcnexus.Db.*;
import static cn.adcnexus.Support.*;

import java.sql.Connection;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.*;

/** Master data is edited through explicit contracts, never arbitrary table/column input. */
final class PracticeSetup {
  static boolean handles(String action) {
    return Set.of("clinic_profile", "dentist_profile", "chair_profile", "opening_hours",
        "catalog_version", "catalog_retire").contains(action);
  }

  static String permission(String action) {
    return switch (action) {
      case "clinic_profile" -> "clinic.manage";
      case "dentist_profile" -> "workforce.manage";
      case "catalog_version", "catalog_retire" -> "catalog.manage";
      default -> "resource.manage";
    };
  }

  static List<Map<String, Object>> fingerprints(List<Map<String, Object>> values) {
    for (var row : values) row.put("fingerprint", hash(json(row)));
    return values;
  }

  static void current(Map<String, Object> row, Map<String, Object> body) {
    check(row != null, 404, "NOT_FOUND", "资料不存在");
    check(req(body, "fingerprint").equals(hash(json(row))), 409, "VERSION_CONFLICT", "资料已变化，请刷新后重试");
  }

  static void network(Auth.Principal p) {
    check(p.network(), 403, "NETWORK_REQUIRED", "此项基础配置需要总部业务授权");
  }

  static String bounded(Map<String, Object> body, String field, int max, boolean optional) {
    String value = optional ? s(body, field) : req(body, field);
    check(value.length() <= max, 422, "FIELD_LENGTH", field + " 内容过长");
    return value;
  }

  static String code(Map<String, Object> body, String key) {
    String value = req(body, key).toUpperCase(Locale.ROOT);
    check(value.matches("[A-Z0-9][A-Z0-9_-]{2,39}"), 422, "CODE", "代码为 3 至 40 位英文、数字、下划线或连字符");
    return value;
  }

  static String selected(Map<String, Object> body, String key, Set<String> allowed) {
    String value = req(body, key);
    check(allowed.contains(value), 422, "STATUS", "请选择有效的 " + key);
    return value;
  }

  static void noAffected(Connection c, String where, Object... args) throws Exception {
    List<Object> values = new ArrayList<>(Arrays.asList(args));
    values.add(now());
    var affected = rows(c, "SELECT appointment_code,scheduled_start_at FROM appointments WHERE "
        + where + " AND status IN ('CONFIRMED','CHECKED_IN','IN_PROGRESS')"
        + " AND (scheduled_end_at>=? OR status IN ('CHECKED_IN','IN_PROGRESS')) ORDER BY scheduled_start_at", values.toArray());
    if (!affected.isEmpty()) throw new Problem(409, "AFFECTED_APPOINTMENTS",
        "变更会影响既有预约或接诊，请先协调后再修改",
        affected.stream().map(a -> s(a, "appointment_code") + " " + s(a, "scheduled_start_at")).toList());
  }

  static Object command(Connection c, Auth.Principal p, Map<String, Object> b) throws Exception {
    String action = req(b, "action");
    p.need(permission(action));
    String id = s(b, "id"), table, clinic = null;
    Map<String, Object> before = null, values;
    boolean create = id.isBlank();
    switch (action) {
      case "clinic_profile" -> {
        table = "clinics";
        if (create) { network(p); id = uuid(); }
        else { p.clinic(id); before = one(c, "SELECT * FROM clinics WHERE id=?", id); current(before, b); }
        clinic = id;
        long capacity = n(b, "chair_capacity");
        check(capacity >= 1 && capacity <= 100, 422, "CAPACITY", "牙椅容量需为 1 至 100");
        check(count(c, "SELECT COUNT(*) FROM clinic_chairs WHERE clinic_id=? AND status<>'INACTIVE'", id) <= capacity,
            409, "CAPACITY", "容量不能少于已配置的有效牙椅数量");
        String status = selected(b, "status", Set.of("ACTIVE", "INACTIVE"));
        if (!status.equals("ACTIVE")) noAffected(c, "clinic_id=?", id);
        String email = bounded(b, "email", 200, true);
        check(email.isBlank() || email.matches("[^\\s@]+@[^\\s@]+\\.[^\\s@]+"), 422, "EMAIL", "邮箱格式无效");
        values = map("name_zh", bounded(b, "name_zh", 120, false), "name_en", bounded(b, "name_en", 160, true),
            "city_zh", bounded(b, "city_zh", 80, false), "city_en", bounded(b, "city_en", 100, true),
            "address_zh", bounded(b, "address_zh", 300, false), "phone", bounded(b, "phone", 40, true),
            "email", email.isBlank() ? null : email, "chair_capacity", capacity, "status", status, "updated_at", now());
        if (create) values.putAll(map("id", id, "organization_id", "org-adc", "code", code(b, "code")));
      }
      case "dentist_profile" -> {
        network(p); table = "dentists";
        if (create) id = uuid();
        else { before = one(c, "SELECT * FROM dentists WHERE id=?", id); current(before, b); }
        String status = selected(b, "employment_status", Set.of("ACTIVE", "INACTIVE"));
        if (!status.equals("ACTIVE")) noAffected(c, "dentist_id=?", id);
        String email = bounded(b, "email", 200, false).toLowerCase(Locale.ROOT);
        check(email.matches("[^\\s@]+@[^\\s@]+\\.[^\\s@]+"), 422, "EMAIL", "邮箱格式无效");
        String hire = LocalDate.parse(req(b, "hire_date")).toString();
        values = map("name_zh", bounded(b, "name_zh", 80, false), "name_en", bounded(b, "name_en", 120, true),
            "title_zh", bounded(b, "title_zh", 80, false), "title_en", "", "email", email,
            "phone", bounded(b, "phone", 40, true), "hire_date", hire, "employment_status", status,
            "biography_zh", bounded(b, "biography_zh", 2000, true), "updated_at", now());
        if (create) {
          String employee = code(b, "employee_code");
          check(employee.matches("ADC-DR-\\d{6}"), 422, "EMPLOYEE_CODE", "医师编号采用 ADC-DR-六位数字；档案不自动授予登录权限");
          values.putAll(map("id", id, "employee_code", employee));
        }
      }
      case "chair_profile" -> {
        table = "clinic_chairs";
        if (create) { id = uuid(); clinic = req(b, "clinic_id"); }
        else {
          before = one(c, "SELECT * FROM clinic_chairs WHERE id=?", id); current(before, b);
          clinic = s(before, "clinic_id");
        }
        p.clinic(clinic);
        var location = one(c, "SELECT * FROM clinics WHERE id=?", clinic);
        check(location != null, 404, "NOT_FOUND", "诊所不存在");
        String status = selected(b, "status", Set.of("AVAILABLE", "MAINTENANCE", "INACTIVE"));
        if (!status.equals("AVAILABLE")) noAffected(c, "chair_id=?", id);
        if (!status.equals("INACTIVE")) check(count(c,
            "SELECT COUNT(*) FROM clinic_chairs WHERE clinic_id=? AND id<>? AND status<>'INACTIVE'", clinic, id) < val(location, "chair_capacity"),
            409, "CAPACITY", "有效牙椅数量已达到本店容量，请先核对容量设置");
        List<String> equipment = Arrays.stream(s(b, "equipment").split("[,，\\n]"))
            .map(String::trim).filter(v -> !v.isEmpty()).distinct().toList();
        check(equipment.size() <= 20 && equipment.stream().allMatch(v -> v.length() <= 80), 422, "EQUIPMENT", "设备最多 20 项，每项不超过 80 字");
        values = map("name_zh", bounded(b, "name_zh", 80, false), "name_en", bounded(b, "name_en", 100, true),
            "room_name_zh", bounded(b, "room_name_zh", 80, false), "room_name_en", "",
            "equipment_json", json(equipment), "is_accessible", Boolean.TRUE.equals(b.get("is_accessible")) ? 1 : 0,
            "status", status, "updated_at", now());
        if (create) values.putAll(map("id", id, "clinic_id", clinic, "code", code(b, "code")));
      }
      case "opening_hours" -> {
        clinic = req(b, "clinic_id"); p.clinic(clinic);
        check(count(c, "SELECT COUNT(*) FROM clinics WHERE id=?", clinic) == 1, 404, "NOT_FOUND", "诊所不存在");
        long day = n(b, "day_of_week"), slot = n(b, "slot_minutes");
        check(day >= 0 && day <= 6 && Set.of(5L, 10L, 15L, 20L, 30L, 60L).contains(slot), 422, "HOURS", "星期或时间粒度无效");
        before = one(c, "SELECT * FROM clinic_operating_hours WHERE clinic_id=? AND day_of_week=?", clinic, day);
        if (before != null) current(before, b);
        String opens = req(b, "opens_at"), closes = req(b, "closes_at");
        check(opens.matches("\\d{2}:\\d{2}") && closes.matches("\\d{2}:\\d{2}"), 422, "HOURS", "时间使用 HH:mm");
        check(LocalTime.parse(opens).isBefore(LocalTime.parse(closes)), 422, "HOURS", "结束时间需晚于开始时间");
        boolean closed = Boolean.TRUE.equals(b.get("is_closed"));
        for (var a : rows(c, "SELECT * FROM appointments WHERE clinic_id=? AND status IN ('CONFIRMED','CHECKED_IN','IN_PROGRESS')"
            + " AND (scheduled_end_at>=? OR status IN ('CHECKED_IN','IN_PROGRESS'))", clinic, now())) {
          if (dateTime(s(a, "scheduled_start_at")).getDayOfWeek().getValue() % 7 != day) continue;
          check(!closed && s(a, "scheduled_start_at").substring(11,16).compareTo(opens) >= 0
              && s(a, "scheduled_end_at").substring(11,16).compareTo(closes) <= 0,
              409, "AFFECTED_APPOINTMENTS", "营业时间变更将影响预约 " + s(a, "appointment_code"));
        }
        values = map("clinic_id", clinic, "day_of_week", day, "opens_at", opens, "closes_at", closes,
            "slot_minutes", slot, "is_closed", closed ? 1 : 0, "updated_at", now());
        execute(c, "DELETE FROM clinic_operating_hours WHERE clinic_id=? AND day_of_week=?", clinic, day);
        insert(c, "clinic_operating_hours", values);
        evidence(c,p,action,"clinic_operating_hours",clinic+":"+day,clinic,before,values,req(b,"reason"));
        return map("ok",true,"id",clinic);
      }
      case "catalog_version" -> { return catalog(c,p,b); }
      case "catalog_retire" -> {
        network(p); table="treatment_catalog"; before=one(c,"SELECT * FROM treatment_catalog WHERE id=?",req(b,"id")); current(before,b);
        noAffected(c,"treatment_id=?",id);
        check(count(c,"SELECT COUNT(*) FROM requested_treatment_items r JOIN clinical_visits v ON v.id=r.visit_id"
            + " WHERE r.treatment_id=? AND v.status NOT IN ('COMPLETED','CANCELLED')",id)==0,
            409,"OPEN_PLAN","未结束就诊仍有此版本的治疗计划，请先协调");
        values=map("status","INACTIVE","updated_at",now()); create=false;
      }
      default -> throw error(422,"ACTION","未知基础配置操作");
    }
    if (create) insert(c,table,values); else update(c,table,id,values);
    evidence(c,p,action,table,id,clinic,before,values,req(b,"reason"));
    return map("ok",true,"id",id);
  }

  static Object catalog(Connection c, Auth.Principal p, Map<String,Object> b) throws Exception {
    network(p);
    String code=code(b,"code"), start=LocalDate.parse(req(b,"effective_from")).toString();
    String end=s(b,"effective_to");
    if(!end.isBlank()) LocalDate.parse(end);
    check(start.compareTo(today())>=0 && (end.isBlank()||end.compareTo(start)>=0),422,"VALIDITY","生效日期不能早于今日，截止日期不能早于生效日期");
    var previous=one(c,"SELECT * FROM treatment_catalog WHERE code=? ORDER BY version DESC LIMIT 1",code);
    long version=1;
    if(previous!=null){
      current(previous,b); version=val(previous,"version")+1;
      check(start.compareTo(today())>0 && start.compareTo(s(previous,"effective_from"))>0,409,"VERSION_DATE","新版本须从未来日期生效，且晚于上一版本起始日");
      String cutoff=LocalDate.parse(start).minusDays(1).toString();
      for(var old:rows(c,"SELECT * FROM treatment_catalog WHERE code=?",code)){
        check(s(old,"effective_from").compareTo(start)<0,409,"VERSION_DATE","已存在更晚生效版本");
        if(s(old,"effective_to").isBlank()||s(old,"effective_to").compareTo(start)>=0){
          noAffected(c,"treatment_id=? AND substr(scheduled_start_at,1,10)>=?",old.get("id"),start);
          update(c,"treatment_catalog",s(old,"id"),map("effective_to",cutoff,"updated_at",now()));
        }
      }
    }
    long duration=n(b,"duration_minutes"), price=n(b,"standard_price_fen"), cost=n(b,"estimated_cost_fen");
    check(duration>=10&&duration<=480&&price>=0&&price<=100000000&&cost>=0&&cost<=100000000,422,"CATALOG_VALUES","时长需 10–480 分钟，价格和估算成本在允许范围内");
    String id=uuid();
    var values=map("id",id,"code",code,"name_zh",bounded(b,"name_zh",120,false),"name_en",bounded(b,"name_en",160,true),
        "category",bounded(b,"category",80,false),"description_zh",bounded(b,"description_zh",2000,true),
        "description_en","","duration_minutes",duration,"standard_price_fen",price,"estimated_cost_fen",cost,
        "version",version,"effective_from",start,"effective_to",end.isBlank()?null:end,"status","ACTIVE","updated_at",now());
    insert(c,"treatment_catalog",values);
    check(b.get("qualification_ids") instanceof List<?>,422,"QUALIFICATIONS","请明确提供资质要求列表");
    var qualifications=(List<?>)b.get("qualification_ids");
    check(qualifications.size()<=30,422,"QUALIFICATIONS","资质要求过多");
    for(String q:new LinkedHashSet<>(qualifications.stream().map(Object::toString).toList())){
      check(count(c,"SELECT COUNT(*) FROM qualification_types WHERE id=?",q)==1,422,"QUALIFICATIONS","资质类型不存在");
      insert(c,"treatment_qualification_requirements",map("treatment_id",id,"qualification_type_id",q,"requirement_level","REQUIRED"));
    }
    evidence(c,p,"catalog_version","treatment_catalog",id,null,previous,values,req(b,"reason"));
    return map("ok",true,"id",id,"version",version);
  }

  static void evidence(Connection c, Auth.Principal p, String action, String table, String id,
      String clinic, Map<String,Object> before, Map<String,Object> after, String reason) throws Exception {
    insert(c,"audit_events",map("request_id",uuid(),"actor_user_id",p.userId(),"actor_subject",p.userId(),
        "action","SETUP_"+action.toUpperCase(Locale.ROOT),"entity_type",table,"entity_id",id,"clinic_id",clinic,
        "reason",reason,"before_json",before==null?null:json(before),"after_json",json(after),"occurred_at",now()));
  }
}
