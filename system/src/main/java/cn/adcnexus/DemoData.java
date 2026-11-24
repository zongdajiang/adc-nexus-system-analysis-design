package cn.adcnexus;

import static cn.adcnexus.Db.*;
import static cn.adcnexus.Support.*;
import java.sql.*;
import java.time.LocalDate;
import java.util.*;

/** Explicit synthetic course fixtures. Never reset user edits or widen a user's grants. */
final class DemoData {
  static void normalizeContacts(Connection c) throws Exception {
    String key = "demo:non-routable-fixture-contacts:v2";
    if (marked(c, key)) return;
    int patients = 0, contacts = 0, consents = 0;
    for (var row : rows(c, "SELECT id,phone,email FROM patients WHERE id LIKE 'pat-%'")) {
      String id = s(row,"id");
      if (!id.matches("pat-[0-9]{4}") || !s(row,"email").endsWith("@example.test")) continue;
      String suffix = id.substring(4);
      String phone = s(row,"phone");
      boolean seededPhone = phone.equals("1390000"+suffix)
          || phone.equals("1380000"+(2000+Integer.parseInt(suffix)))
          || ("pat-0010".equals(id) && "13800002991".equals(phone));
      if (!seededPhone) continue;
      patients += execute(c,"UPDATE patients SET phone=? WHERE id=? AND phone=?", "0000000"+suffix,id,phone);
    }
    for (var row : rows(c,"SELECT id,contact_name,phone FROM emergency_contacts WHERE id LIKE 'ec-00%'")) {
      String id=s(row,"id"), phone=s(row,"phone"), name=s(row,"contact_name");
      if (!id.matches("ec-00[1-7]") || !phone.matches("138000030(01|02|03|04|05|08|11)")) continue;
      name = switch (name) {
        case "Chen Wen" -> "陈雯";
        case "Lin Hui" -> "林慧";
        default -> name;
      };
      contacts += execute(c,"UPDATE emergency_contacts SET phone=?,contact_name=? WHERE id=? AND phone=?",
          "0000000"+phone.substring(7),name,id,phone);
    }
    consents += execute(c, "UPDATE patient_consents SET source='SYNTHETIC_FIXTURE'"
        + " WHERE id IN ('con-001','con-002','con-003','con-004','con-005','con-006')"
        + " AND source IN ('PATIENT_PORTAL','FRONT_DESK') AND policy_version='2026.1'");
    insert(c,"system_settings",map("organization_id","org-adc","setting_key",key,
        "value_json",json(map("synthetic",true,"patients",patients,"contacts",contacts,"consents",consents)),
        "updated_at",wallNow()));
  }
  static final String RELEASE = "demo:business:20261113-v1";
  static boolean enabled() {
    return Boolean.parseBoolean(System.getenv().getOrDefault("DEMO_MODE", "false"))
        && (!"TEST".equals(System.getenv("APP_ENV")) || "true".equals(System.getenv("ADC_TEST_FULL_DEMO")));
  }
  static Auth.Principal actor(String role) {
    Set<String> permissions=new HashSet<>(Seed.GRANTS.get(role));
    if(role.equals("DENTIST"))permissions.addAll(List.of("followup.recommend","followup.read"));
    if(Set.of("DENTIST","CLINIC_MANAGER","FRONT_DESK","REVIEWER").contains(role))permissions.add("waitlist.manage");
    return new Auth.Principal("jdbc-demo-"+role.toLowerCase(Locale.ROOT), person(role),
        permissions, Set.of("cln-tianhe"),
        Set.of("HQ_FINANCE","HQ_OPERATIONS").contains(role), null,
        role.equals("DENTIST") ? "dnt-lin-wei" : null, List.of(), false);
  }
  static String person(String role) {
    return switch(role) {
      case "DENTIST" -> "林玮"; case "CLINIC_MANAGER" -> "周文静";
      case "FRONT_DESK" -> "许佳宁"; case "CASHIER" -> "陈思敏";
      case "HQ_OPERATIONS" -> "赵明远"; case "HQ_FINANCE" -> "何嘉宁";
      default -> Seed.roleName(role);
    };
  }
  static void mark(Connection c,String key) throws Exception {
    insert(c,"system_settings",map("organization_id","org-adc","setting_key",key,
        "value_json",json(map("synthetic",true,"created_at",now()))));
  }
  static boolean marked(Connection c,String key) throws Exception {
    return count(c,"SELECT COUNT(*) FROM system_settings WHERE organization_id='org-adc' AND setting_key=?",key)>0;
  }
  static void ensure(Connection c) throws Exception {
    if(!enabled() || count(c,"SELECT COUNT(*) FROM app_users WHERE id='jdbc-demo-dentist'")==0) return;
    if(!DailyDemo.enabled() && !marked(c,"demo:legacy-cleanup:v1")) {
      for(int h:new int[]{9,11,14,16}) {
        var a=one(c,"SELECT * FROM appointments WHERE appointment_code=? AND created_by_user_id='jdbc-demo-front_desk'","ADC-TODAY-"+h);
        if(a==null)continue;
        String action=s(a,"status").equals("CONFIRMED")?"cancel":"";
        if(s(a,"status").equals("CHECKED_IN")) {
          var v=one(c,"SELECT * FROM clinical_visits WHERE appointment_id=?",a.get("id"));
          if(v!=null && s(v,"safety_gate_status").equals("PENDING")
              && count(c,"SELECT COUNT(*) FROM odontogram_observations WHERE visit_id=?",v.get("id"))==0
              && count(c,"SELECT COUNT(*) FROM treatment_plans WHERE visit_id=?",v.get("id"))==0
              && count(c,"SELECT COUNT(*) FROM clinical_notes WHERE visit_id=?",v.get("id"))==0)
            action="revoke_arrival";
        }
        if(!action.isEmpty())Scheduling.command(c,actor("FRONT_DESK"),s(a,"id"),map("action",action,
            "version",a.get("appointment_version"),"reason","演示日程更新：由新的多患者预约样例替代，保留原预约记录。"));
      }
      for(String[] mapping:new String[][]{{"review.frontdesk","许佳宁"},{"review.cashier","陈思敏"},{"review.operations","赵明远"},{"review.finance","何嘉宁"}})
        execute(c,"UPDATE app_users SET display_name=? WHERE username=? AND display_name LIKE '%合成试用%'",mapping[1],mapping[0]);
      execute(c,"UPDATE app_users SET display_name='郑子谦' WHERE id='jdbc-owner' AND display_name='系统管理员'");
      mark(c,"demo:legacy-cleanup:v1");
    }
    if(!marked(c, RELEASE)) {
      for(String role:Auth.WEB_DEMO_ROLES)
        execute(c,"UPDATE app_users SET display_name=? WHERE id=?",person(role),"jdbc-demo-"+role.toLowerCase(Locale.ROOT));
      // Upgrade only untouched, known fixtures from the old four-slot sample.
      String[] samplePatients={"pat-0001","pat-0002","pat-0015","pat-0029"}; int n=0;
      for(int h:new int[]{9,11,14,16}) {
        var a=one(c,"SELECT * FROM appointments WHERE appointment_code=?","ADC-TODAY-"+h);
        String patient=samplePatients[n++];
        if(a!=null && s(a,"status").equals("CONFIRMED")
            && s(a,"created_by_user_id").equals("jdbc-demo-front_desk")
            && count(c,"SELECT COUNT(*) FROM clinical_visits WHERE appointment_id=?",a.get("id"))==0)
          update(c,"appointments",s(a,"id"),map("patient_id",patient));
      }
      // A coherent completed-care chain, containing unbilled, unpaid, partial, paid, refund and void cases.
      var historicalPatients=rows(c,"SELECT id FROM patients WHERE primary_clinic_id='cln-tianhe' AND status='ACTIVE' ORDER BY patient_code LIMIT 14");
      LocalDate cursor=LocalDate.parse(today());
      for(int index=0;index<14;index++) {
        LocalDate day=cursor.minusDays(1);
        while(day.getDayOfWeek().getValue()>5)day=day.minusDays(1);
        cursor=day;
        String patient=DailyDemo.enabled()?s(historicalPatients.get(13-index),"id"):index%2==0?"pat-0001":"pat-0002";
        String aid=appointment(c,"DEMO-CARE-"+index,patient,"cln-tianhe","dnt-lin-wei",day,
            index%2==0?"09:30":"14:30",index%3==0?"trt-exam-v1":"trt-clean-v1");
        if(aid==null) continue;
        String vid=visit(c,aid,"COMPLETED",day);
        if(index%7==0) continue; // Ready for the cashier to issue a bill.
        var issued=(Map<String,Object>)Finance.issue(c,actor("CASHIER"),map("visit_id",vid));
        var invoice=(Map<String,Object>)issued.get("invoice");String iid=s(invoice,"id");
        long total=val(invoice,"total_fen"); int mode=index%7;
        if(mode>=2 && mode<=5) pay(c,iid,mode==2?total/2:total,"DEMO-PAY-"+index);
        if(mode==4 || mode==5) {
          var bill=one(c,"SELECT * FROM invoices WHERE id=?",iid);
          Finance.command(c,actor("CASHIER"),iid,map("action","refund","version",bill.get("invoice_version"),
              "payment_id",one(c,"SELECT id FROM payments WHERE invoice_id=?",iid).get("id"),
              "amount_fen",mode==4?total/4:total,"authorized",true,
              "reason","合成退款演示：核实原收款凭据后退回，原治疗记录和应收保留。"));
        }
        if(mode==6) Finance.command(c,actor("CASHIER"),iid,map("action","void","version",invoice.get("invoice_version"),
            "reason","合成作废演示：未收款的错误开单，保留原单及原因。"));
        retimeBilling(c,iid,day);
        if(index<4) Followups.command(c,actor("DENTIST"),map("action","recommend","visit_id",vid,
            "due_on",LocalDate.parse(today()).plusDays(7+index).toString(),"reason","洁治后复查牙龈情况并评估家庭清洁情况。",
            "priority","ROUTINE","contact_allowed",true));
      }
      // Real finance commands produce the current quarter's expense and allocation examples.
      for(String clinic:List.of("cln-tianhe","cln-nanshan")) {
        var result=(Map<String,Object>)Finance.periodCommand(c,actor("HQ_FINANCE"),map("action","expense",
            "clinic_id",clinic,"incurred_on",today(),"category","SUPPLIES","vendor","华南齿科耗材（模拟供应商）",
            "amount_fen",96000,"evidence","合成入库及领用凭据：一次性检查用品，按领用数量归属。"));
        Finance.periodCommand(c,actor("HQ_FINANCE"),map("action","allocate","expense_id",result.get("id"),
            "dentist_id",clinic.equals("cln-tianhe")?"dnt-lin-wei":"dnt-chen-yu","amount_fen",96000,
            "basis","合成领用登记：本批全部用于该医师诊室。"));
      }
      // Include both pending and verified actual-cost examples, without treating catalogue estimates as facts.
      for(var cost:rows(c,"SELECT x.* FROM treatment_cost_entries x JOIN clinical_visits v ON v.id=x.visit_id"
          +" JOIN appointments a ON a.id=v.appointment_id WHERE a.appointment_code LIKE 'DEMO-CARE-%' ORDER BY a.appointment_code LIMIT 4"))
        Finance.periodCommand(c,actor("HQ_FINANCE"),map("action","cost","cost_id",cost.get("id"),
            "materials_fen",3500,"laboratory_fen",0,"provider_fen",5000,"evidence","合成成本核验：耗材领用单及本次服务成本记录。"));
      mark(c, RELEASE);
    }
    if(DailyDemo.enabled())return;
    // Create a rolling working-week window once per service date. Repeated starts preserve edits.
    for(int offset=0;offset<=9;offset++) {
      LocalDate day=LocalDate.parse(today()).plusDays(offset);String key="demo:calendar:"+day;
      if(marked(c,key))continue;
      int weekday=day.getDayOfWeek().getValue()%7;
      int patientIndex=0;
      for(String clinic:List.of("cln-tianhe")) {
        var doctors=rows(c,"SELECT DISTINCT dentist_id FROM dentist_availability_rules WHERE clinic_id=? AND day_of_week=?"
            +" AND status='ACTIVE' ORDER BY dentist_id DESC",clinic,weekday);
        if(doctors.isEmpty())continue;
        var patients=rows(c,"SELECT id FROM patients WHERE primary_clinic_id=? AND status='ACTIVE' ORDER BY patient_code LIMIT 12",clinic);
        for(int slot=0;slot<6;slot++) {
          String patient=s(patients.get((slot+offset)%patients.size()),"id");
          String doctor=s(doctors.get(slot%doctors.size()),"dentist_id");
          String aid=appointment(c,"DEMO-AGENDA-"+day+"-"+clinic+"-"+slot,patient,clinic,doctor,day,
              new String[]{"09:30","10:30","11:30","14:30","15:30","16:30"}[slot],slot%2==0?"trt-exam-v1":"trt-clean-v1");
          if(aid!=null && offset==0 && clinic.equals("cln-tianhe") && doctor.equals("dnt-lin-wei") && slot<=4)
            visit(c,aid,slot==0?"SAFETY_REVIEW":slot==2?"WAITING":"IN_PROGRESS",day);
          patientIndex++;
        }
      }
      // Current, actionable waiting-list records, rather than expired September examples only.
      if(offset==0)for(int i=0;i<3;i++)Scheduling.waitlistCommand(c,actor("FRONT_DESK"),map("action","add",
          "patient_id",new String[]{"pat-0001","pat-0002","pat-0015"}[i],"treatment_id","trt-exam-v1",
          "clinic_id","cln-tianhe","earliest_date",day.plusDays(1).toString(),"latest_date",day.plusDays(8).toString(),
          "notice_hours",2,"priority_score",50+i));
      mark(c,key);
    }
    String workday="demo:workday:"+today();
    if(!marked(c,workday)) {
      var todayVisits=rows(c,"SELECT id FROM appointments WHERE appointment_code LIKE 'DEMO-AGENDA-%'"
          +" AND clinic_id='cln-tianhe' AND dentist_id='dnt-lin-wei' AND scheduled_start_at LIKE ? AND status='CONFIRMED' ORDER BY scheduled_start_at",today()+"%");
      int stage=0;
      for(var a:todayVisits) {
        visit(c,s(a,"id"),new String[]{"SAFETY_REVIEW","WAITING","IN_PROGRESS"}[Math.min(stage++,2)],LocalDate.parse(today()));
      }
      var patients=rows(c,"SELECT id FROM patients WHERE primary_clinic_id='cln-tianhe' AND status='ACTIVE' ORDER BY patient_code LIMIT 12");
      for(int i=0;i<2;i++) {
        String aid=appointment(c,"DEMO-DAY-END-"+today()+"-"+i,s(patients.get(7+i),"id"),"cln-tianhe","dnt-lin-wei",
            LocalDate.parse(today()),i==0?"12:30":"13:30","trt-clean-v1");
        if(aid==null)continue;
        String vid=visit(c,aid,"COMPLETED",LocalDate.parse(today()));
        if(i==0) {
          var invoice=(Map<String,Object>)((Map<String,Object>)Finance.issue(c,actor("CASHIER"),map("visit_id",vid))).get("invoice");
          pay(c,s(invoice,"id"),val(invoice,"total_fen"),"DEMO-DAY-PAY-"+today());
        }
      }
      mark(c,workday);
    }
    String returns="demo:returns:"+today();
    if(!marked(c,returns)) {
      LocalDate next=LocalDate.parse(today()).plusDays(1);
      while(next.getDayOfWeek().getValue()>5)next=next.plusDays(1);
      for(int i=0;i<2;i++)appointment(c,"DEMO-RETURN-"+today()+"-"+i,i==0?"pat-0001":"pat-0002",
          "cln-tianhe","dnt-lin-wei",next,i==0?"17:00":"17:30","trt-exam-v1");
      String expected=s(one(c,"SELECT id FROM patients WHERE primary_clinic_id='cln-tianhe' AND status='ACTIVE' ORDER BY patient_code LIMIT 1 OFFSET 6"),"id");
      appointment(c,"DEMO-EXPECTED-"+today(),expected,"cln-tianhe","dnt-lin-wei",LocalDate.parse(today()),"17:30","trt-exam-v1");
      mark(c,returns);
    }
  }

  static String appointment(Connection c,String code,String patient,String clinic,String dentist,LocalDate day,String time,String treatment) throws Exception {
    if(patient.isBlank())return null;
    var old=one(c,"SELECT id FROM appointments WHERE appointment_code=?",code);if(old!=null)return s(old,"id");
    var b=map("patient_id",patient,"clinic_id",clinic,"dentist_id",dentist,"treatment_id",treatment,
        "scheduled_start_at",day+" "+time+":00","duration_minutes",30);
    // A real available chair and all scheduling rules, including provider/patient conflicts.
    for(var chair:rows(c,"SELECT id FROM clinic_chairs WHERE clinic_id=? AND status='AVAILABLE' ORDER BY code",clinic)) {
      b.put("chair_id",chair.get("id"));
      if(!Scheduling.validate(c,actor("FRONT_DESK"),b,null,false).isEmpty())continue;
      String id=uuid(); b.put("id",id);b.put("appointment_code",code);b.put("status","CONFIRMED");
      b.put("confirmation_state","CONFIRMED");b.put("created_by_user_id","jdbc-demo-front_desk");
      b.put("notes","已电话确认就诊项目与时间。");
      b.put("created_at",day.minusDays(1)+" 10:00:00");b.put("updated_at",b.get("created_at"));
      insert(c,"appointments",b);
      at(s(b,"created_at"),()->{
        Scheduling.history(c,actor("FRONT_DESK"),id,null,"CONFIRMED","已与患者确认就诊日期及时间。");
        return null;
      });
      return id;
    }
    return null;
  }
  static String visit(Connection c,String aid,String target,LocalDate day) throws Exception {
    var old=one(c,"SELECT id FROM clinical_visits WHERE appointment_id=?",aid);if(old!=null)return s(old,"id");
    var a=one(c,"SELECT * FROM appointments WHERE id=?",aid);String vid=uuid(), start=s(a,"scheduled_start_at");
    boolean cleaning="trt-clean-v1".equals(s(a,"treatment_id"));
    String complaint=cleaning?"自觉后牙清洁困难，来诊洁治。":"例行口腔检查，目前无急性牙痛。";
    String finding=cleaning?"16 牙邻面可见菌斑及少量牙石。":"16 牙邻面见菌斑，牙面未见明显缺损。";
    String procedure=cleaning?"完成本次超声洁治，复核清洁情况。":"完成本次口腔检查并记录检查所见。";
    String arrival=start.compareTo(now())>0?now():start;
    insert(c,"clinical_visits",map("id",vid,"visit_code","DEMO-V-"+vid.substring(0,8).toUpperCase(Locale.ROOT),
        "appointment_id",aid,"patient_id",a.get("patient_id"),"clinic_id",a.get("clinic_id"),
        "dentist_id",a.get("dentist_id"),"chair_id",a.get("chair_id"),"status","SAFETY_REVIEW","safety_gate_status","PENDING",
        "chief_complaint_zh",complaint,"started_at",arrival,
        "created_at",arrival,"updated_at",arrival,"created_by_user_id","jdbc-demo-front_desk"));
    update(c,"appointments",aid,map("status","CHECKED_IN"));
    Scheduling.history(c,actor("FRONT_DESK"),aid,"CONFIRMED","CHECKED_IN","已核对患者身份并签到。");
    historyTimeline(c,aid,start);
    if(target.equals("SAFETY_REVIEW"))return vid;
    timedStep(c,vid,arrival,2,map("action","safety","history_confirmed",true,"evidence","已当面询问病史和过敏，逐项核对已登记资料并记录注意事项。"));
    if(target.equals("WAITING"))return vid;
    timedStep(c,vid,arrival,5,map("action","start"));
    historyTimeline(c,aid,start);
    timedStep(c,vid,arrival,6,map("action","observation","tooth_code","16","observation_type","EXAMINATION","finding",finding,"severity","LOW"));
    timedStep(c,vid,arrival,7,map("action","plan","treatment_id",a.get("treatment_id"),"units",1,"tooth_code","16","rationale",
        cleaning?"已说明洁治范围及费用。":"已说明本次检查项目及费用。"));
    String item=s(one(c,"SELECT id FROM requested_treatment_items WHERE visit_id=?",vid),"id");
    timedStep(c,vid,arrival,8,map("action","consent","item_id",item,"decision","ACCEPTED","evidence","已说明本次项目及费用，患者明确表示同意。"));
    timedStep(c,vid,arrival,12,map("action","actual","treatment_id",a.get("treatment_id"),"units",1,"tooth_code","16","requested_treatment_item_id",item,"notes",procedure));
    if(target.equals("IN_PROGRESS"))return vid;
    timedStep(c,vid,arrival,25,map("action","note","content","主诉："+complaint+" 检查："+finding+
        " 处理："+procedure+" 已向患者说明检查结果和复查安排。","sign",true));
    timedStep(c,vid,arrival,30,map("action","complete"));
    update(c,"clinical_visits",vid,map("started_at",start,"completed_at",dateTime(start).plusMinutes(30).format(DT)));
    historyTimeline(c,aid,start);
    return vid;
  }
  static void historyTimeline(Connection c,String aid,String start) throws Exception {
    String booked=s(one(c,"SELECT created_at FROM appointments WHERE id=?",aid),"created_at");
    var visit=one(c,"SELECT started_at FROM clinical_visits WHERE appointment_id=?",aid);
    String arrival=visit==null?start:s(visit,"started_at");
    if(booked.compareTo(now())>0)booked=now();
    for(var h:rows(c,"SELECT id,to_status FROM appointment_status_history WHERE appointment_id=?",aid)) {
      String at=switch(s(h,"to_status")) {
        case "CONFIRMED" -> booked; case "CHECKED_IN" -> arrival;
        case "IN_PROGRESS" -> dateTime(arrival).plusMinutes(5).format(DT);
        case "COMPLETED" -> dateTime(start).plusMinutes(30).format(DT);
        default -> now();
      };
      update(c,"appointment_status_history",s(h,"id"),map("occurred_at",at));
    }
  }
  static void step(Connection c,String vid,Map<String,Object> b) throws Exception {
    b.put("version",one(c,"SELECT visit_version FROM clinical_visits WHERE id=?",vid).get("visit_version"));
    Clinical.command(c,actor("DENTIST"),vid,b);
  }
  static void timedStep(Connection c,String vid,String arrival,int minutes,Map<String,Object> b) throws Exception {
    at(dateTime(arrival).plusMinutes(minutes).format(DT),()->{step(c,vid,b);return null;});
  }
  static void pay(Connection c,String iid,long amount,String ref) throws Exception {
    var bill=one(c,"SELECT * FROM invoices WHERE id=?",iid);
    Finance.command(c,actor("CASHIER"),iid,map("action","pay","version",bill.get("invoice_version"),"amount_fen",amount,"method","CASH","reference",ref,"notes","合成收款凭据，未执行真实支付。"));
  }
  static void retimeBilling(Connection c,String iid,LocalDate day)throws Exception {
    String completed=s(one(c,"SELECT v.completed_at FROM clinical_visits v JOIN invoices i ON i.visit_id=v.id WHERE i.id=?",iid),"completed_at");
    String issued=dateTime(completed).plusMinutes(5).format(DT),paid=dateTime(completed).plusMinutes(10).format(DT),refunded=dateTime(completed).plusMinutes(15).format(DT);
    update(c,"invoices",iid,map("issued_at",issued,"created_at",issued));
    execute(c,"UPDATE payments SET received_at=?,created_at=? WHERE invoice_id=?",paid,paid,iid);
    execute(c,"UPDATE payment_refunds SET refunded_at=?,created_at=? WHERE payment_id IN (SELECT id FROM payments WHERE invoice_id=?)",refunded,refunded,iid);
  }
  static void retime(Connection c,String table,String where,Object[] args,String timestamp)throws Exception {
    Set<String> stamps=Set.of("created_at","updated_at","performed_at","accepted_at","signed_at","captured_at","acknowledged_at","observed_at","occurred_at");
    List<String> assignments=new ArrayList<>(); List<Object> values=new ArrayList<>();
    try(var columns=c.getMetaData().getColumns(null,null,table,null)) {
      while(columns.next())if(stamps.contains(columns.getString("COLUMN_NAME"))){assignments.add(columns.getString("COLUMN_NAME")+"=?");values.add(timestamp);}
    }
    if(assignments.isEmpty())return;values.addAll(Arrays.asList(args));
    execute(c,"UPDATE "+table+" SET "+String.join(",",assignments)+" WHERE "+where,values.toArray());
  }
}
