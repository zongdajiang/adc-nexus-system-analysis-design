package cn.adcnexus;

import static cn.adcnexus.Db.*;
import static cn.adcnexus.Support.*;
import java.sql.Connection;
import java.time.LocalDate;
import java.util.*;
import java.util.regex.Pattern;

/** Opt-in, isolated course dataset. Each day is seeded once; prior work is never rewritten. */
final class DailyDemo {
  static boolean enabled() {
    return DemoData.enabled() && "daily".equals(System.getenv("DEMO_SCENARIO_MODE"));
  }
  private static final Set<String> MASTERS=Set.of("organizations","clinics","roles","permissions",
      "role_permissions","app_users","user_role_assignments","clinic_chairs","clinic_operating_hours",
      "dentists","dentist_clinic_assignments","qualification_types","dentist_qualifications",
      "dentist_availability_rules","patients","patient_allergies","patient_consents","emergency_contacts",
      "treatment_catalog","treatment_qualification_requirements",
      "expansion_scenarios","expansion_assumptions","expansion_candidate_clinics","expansion_scenario_results");
  static boolean masterStatement(String sql) {
    var m=Pattern.compile("(?is)\\b(?:INSERT(?: OR (?:IGNORE|REPLACE))? INTO|UPDATE)\\s+[\"`]?([a-z_]+)").matcher(sql.trim());
    return m.find() && MASTERS.contains(m.group(1).toLowerCase(Locale.ROOT));
  }
  static boolean needed(Connection c) throws Exception {
    return enabled() && !DemoData.marked(c,"demo:daily-rhythm:"+wallNow().substring(0,10));
  }
  static void ensure(Connection c) throws Exception {
    if(!needed(c))return;
    LocalDate day=LocalDate.parse(wallNow().substring(0,10));
    boolean existingDay=DemoData.marked(c,"demo:daily:"+day);
    if(!existingDay) seedDay(c,day.toString());
    at(day+" 15:00:00",()->{
      // Bring an already populated demo day forward without changing any stored appointment or encounter.
      if(existingDay) addDistinctAppointments(c,day,true,true);
      if(!DemoData.marked(c,"demo:adjacent:"+day)) {
        seedAdjacent(c,day);
        DemoData.mark(c,"demo:adjacent:"+day);
      }
      DemoData.mark(c,"demo:daily-rhythm:"+day);
      return null;
    });
  }

  private static void seedDay(Connection c,String date) throws Exception {
    check(count(c,"SELECT COUNT(*) FROM appointments WHERE appointment_code LIKE 'ADC-TODAY-%'")==0,
        500,"DEMO_DATABASE","每日演示请使用独立的新数据目录；旧数据目录继续保留。");
    at(date+" 15:00:00",()->{
      LocalDate serviceDay=LocalDate.parse(date);
      int quarter=(serviceDay.getMonthValue()-1)/3+1;
      LocalDate periodStart=LocalDate.of(serviceDay.getYear(),(quarter-1)*3+1,1);
      if(one(c,"SELECT id FROM financial_reporting_periods WHERE starts_on<=? AND ends_on>=?",date,date)==null)
        insert(c,"financial_reporting_periods",map("id","period-"+serviceDay.getYear()+"-Q"+quarter,
            "period_code",serviceDay.getYear()+"-Q"+quarter,"name_zh",serviceDay.getYear()+"年第"+quarter+"季度",
            "name_en",serviceDay.getYear()+" Q"+quarter,"starts_on",periodStart.toString(),"ends_on",periodStart.plusMonths(3).minusDays(1).toString()));
      if(!DemoData.marked(c,"demo:daily:setup")) {
        // Seven-day teaching clinic, still checked by the normal scheduling validator.
        for(var clinic:rows(c,"SELECT DISTINCT clinic_id FROM dentist_availability_rules WHERE status='ACTIVE'")) {
          String cid=s(clinic,"clinic_id");
          for(int weekday=0;weekday<7;weekday++) {
            var hours=one(c,"SELECT clinic_id FROM clinic_operating_hours WHERE clinic_id=? AND day_of_week=?",cid,weekday);
            if(hours==null)insert(c,"clinic_operating_hours",map("clinic_id",cid,"day_of_week",weekday,"opens_at","09:00","closes_at","18:30","is_closed",0));
            else execute(c,"UPDATE clinic_operating_hours SET opens_at='09:00',closes_at='18:30',is_closed=0 WHERE clinic_id=? AND day_of_week=?",cid,weekday);
            for(var doctor:rows(c,"SELECT DISTINCT dentist_id FROM dentist_availability_rules WHERE clinic_id=? AND status='ACTIVE'",cid))
              if(count(c,"SELECT COUNT(*) FROM dentist_availability_rules WHERE clinic_id=? AND dentist_id=? AND day_of_week=? AND status='ACTIVE'",cid,doctor.get("dentist_id"),weekday)==0)
                insert(c,"dentist_availability_rules",map("id",uuid(),"clinic_id",cid,"dentist_id",doctor.get("dentist_id"),"day_of_week",weekday,"starts_at","09:00","ends_at","18:30","effective_from","2026-01-01","status","ACTIVE"));
          }
        }
        execute(c,"UPDATE dentist_availability_rules SET starts_at='09:00',ends_at='18:30' WHERE status='ACTIVE'");
        DemoData.mark(c,"demo:daily:setup");
      }
      DemoData.ensure(c); // coherent historical treatment / billing / cost / recall chains only
      LocalDate day=LocalDate.parse(date);
      var people=rows(c,"SELECT id FROM patients WHERE primary_clinic_id='cln-tianhe' AND status='ACTIVE'"
          +" AND id LIKE 'pat-%' ORDER BY patient_code LIMIT 18");
      DayRhythm rhythm=dayRhythm(day);
      String[] times={rhythm.exam(),rhythm.cleaning(),rhythm.missed(),"15:00","15:30",rhythm.inCare(),"16:00","16:30","17:00","17:30"};
      String[] stages={"COMPLETED","COMPLETED","NO_SHOW","SAFETY_REVIEW","WAITING","IN_PROGRESS","CONFIRMED","CONFIRMED","CONFIRMED","CANCELLED"};
      for(int i=0;i<times.length;i++) {
        final int index=i;
        if(!standardSlot(day,index)) continue;
        at(date+" "+(i<3?times[i]:"14:45")+":00",()->{
          String code=bookingCode(day,index);
          if(count(c,"SELECT COUNT(*) FROM appointments WHERE appointment_code=?",code)>0) return null;
          String patient=index>=6 && index<=8 ? advancePatient(c,day,index)
              : people.isEmpty() ? "" : s(people.get(Math.floorMod(day.toEpochDay()*5+index,people.size())),"id");
          String aid=DemoData.appointment(c,code,patient,"cln-tianhe","dnt-lin-wei",day,times[index],index%2==0?"trt-exam-v1":"trt-clean-v1");
          if(aid==null)return null; // A user's existing booking wins over fixture creation.
          if(Set.of("COMPLETED","SAFETY_REVIEW","WAITING","IN_PROGRESS").contains(stages[index])) {
            String vid=DemoData.visit(c,aid,stages[index],day);
            if(index==0) registerDemoPayment(c,day,times[index],vid,"DAY-PAY-"+date);
          } else if(stages[index].equals("NO_SHOW"))at(dateTime(date+" "+times[index]+":00").plusMinutes(50).format(DT),()->{
            var a=one(c,"SELECT * FROM appointments WHERE id=?",aid);
            Scheduling.command(c,DemoData.actor("FRONT_DESK"),aid,map("action","no_show","version",a.get("appointment_version"),"reason","预约结束后仍未到店，电话暂未接通。"));return null;
          });
          else if(stages[index].equals("CANCELLED")) {
            var a=one(c,"SELECT * FROM appointments WHERE id=?",aid);
            Scheduling.command(c,DemoData.actor("FRONT_DESK"),aid,map("action","cancel","version",a.get("appointment_version"),"reason","患者来电因临时有事取消，已确认取消本次预约。","initiator","PATIENT"));
          }
          DemoData.historyTimeline(c,aid,date+" "+times[index]+":00");
          return null;
        });
      }
      addSecondDoctor(c,day);
      addDistinctAppointments(c,day,rhythm.extraCompleted(),rhythm.extraBooking());
      for(int i=0;i<3 && 15+i<people.size();i++) {
        Object patient=people.get(15+i).get("id");
        if(count(c,"SELECT COUNT(*) FROM waitlist_entries WHERE patient_id=? AND treatment_id='trt-exam-v1' AND preferred_clinic_id='cln-tianhe' AND status='WAITING' AND latest_date>=?",patient,date)>0)continue;
        Scheduling.waitlistCommand(c,DemoData.actor("FRONT_DESK"),map("action","add",
          "patient_id",patient,"treatment_id","trt-exam-v1","clinic_id","cln-tianhe",
          "earliest_date",date,"latest_date",day.plusDays(7).toString(),"notice_hours",2,"priority_score",50+i*20));
      }
      if(openPeriod(c,day)) at(date+" 11:00:00",()->{
        Finance.periodCommand(c,DemoData.actor("HQ_FINANCE"),map("action","expense","clinic_id","cln-tianhe",
            "incurred_on",date,"category","SUPPLIES","vendor","华南齿科耗材","amount_fen",36000,
            "evidence","当日领用一次性检查用品，已核对领用登记与采购凭据。"));return null;
      });
      DemoData.mark(c,"demo:daily:"+date);
      return null;
    });
  }

  private record DayRhythm(String exam,String cleaning,String missed,String inCare,
      boolean extraCompleted,boolean extraBooking) {}

  private static DayRhythm dayRhythm(LocalDate day) {
    return switch(day.getDayOfWeek()) {
      case MONDAY -> new DayRhythm("09:00","10:20","11:20","14:10",true,false);
      case TUESDAY -> new DayRhythm("09:20","10:00","11:10","14:30",false,true);
      case WEDNESDAY -> new DayRhythm("09:10","10:40","11:50","14:20",false,false);
      case THURSDAY -> new DayRhythm("09:40","10:30","11:40","14:00",true,true);
      case FRIDAY -> new DayRhythm("09:50","10:50","11:30","14:20",false,false);
      case SATURDAY -> new DayRhythm("09:30","10:30","11:30","14:30",false,false);
      case SUNDAY -> new DayRhythm("09:40","10:40","11:40","14:20",false,false);
    };
  }

  private static boolean standardSlot(LocalDate day,int index) {
    return index!=8 || day.getDayOfWeek()!=java.time.DayOfWeek.SUNDAY;
  }

  private static void addDistinctAppointments(Connection c,LocalDate day,boolean completed,
      boolean futureBooking) throws Exception {
    if(completed) {
      String start="13:00";
      String code=bookingCode(day,11);
      String aid=at(day+" "+start+":00",()->DemoData.appointment(c,code,advancePatient(c,day,11),
          "cln-tianhe","dnt-lin-wei",day,start,"trt-clean-v1"));
      if(aid!=null) {
        String vid=at(day+" "+start+":00",()->DemoData.visit(c,aid,"COMPLETED",day));
        registerDemoPayment(c,day,start,vid,"DAY-PAY-EXTRA-"+day);
      }
    }
    if(futureBooking) DemoData.appointment(c,bookingCode(day,12),advancePatient(c,day,12),
        "cln-tianhe","dnt-lin-wei",day,"18:00","trt-exam-v1");
  }

  @SuppressWarnings("unchecked")
  private static void registerDemoPayment(Connection c,LocalDate day,String start,String vid,String reference)
      throws Exception {
    if(!openPeriod(c,day)) return;
    var time=dateTime(day+" "+start+":00");
    var issued=at(time.plusMinutes(35).format(DT),()->(Map<?,?>)
        Finance.issue(c,DemoData.actor("CASHIER"),map("visit_id",vid)));
    var invoice=(Map<String,Object>)issued.get("invoice");
    at(time.plusMinutes(40).format(DT),()->{
      DemoData.pay(c,s(invoice,"id"),val(invoice,"total_fen"),reference);
      return null;
    });
  }

  private static String bookingCode(LocalDate day,int index) {
    return "APT-"+day.toString().replace("-","")+"-"+String.format(Locale.ROOT,"%03d",index+1);
  }

  private static boolean openPeriod(Connection c,LocalDate day) throws Exception {
    return count(c,"SELECT COUNT(*) FROM financial_reporting_periods WHERE starts_on<=? AND ends_on>=? AND status='OPEN'",
        day.toString(),day.toString())>0;
  }

  private static String advancePatient(Connection c,LocalDate day,int slot) throws Exception {
    var people=rows(c,"SELECT id FROM patients WHERE primary_clinic_id='cln-tianhe' AND status='ACTIVE'"
        +" AND id LIKE 'pat-%' ORDER BY patient_code LIMIT 32 OFFSET 18");
    return people.isEmpty() ? "" : s(people.get(Math.floorMod(day.toEpochDay()*5+slot,people.size())),"id");
  }

  private static void addSecondDoctor(Connection c,LocalDate day) throws Exception {
    var doctor=one(c,"SELECT dentist_id FROM dentist_availability_rules WHERE clinic_id='cln-tianhe'"
        +" AND dentist_id<>'dnt-lin-wei' AND day_of_week=? AND status='ACTIVE' ORDER BY dentist_id LIMIT 1",
        day.getDayOfWeek().getValue()%7);
    if(doctor!=null) DemoData.appointment(c,bookingCode(day,10),advancePatient(c,day,10),
        "cln-tianhe",s(doctor,"dentist_id"),day,"16:00","trt-exam-v1");
  }

  private static void seedAdjacent(Connection c,LocalDate day) throws Exception {
    LocalDate past=day.minusDays(1), next=day.plusDays(1);
    // Historical examples use independent patients and are never added to a previously used workday.
    if(!DemoData.marked(c,"demo:daily:"+past)) {
      String[] starts={"09:00","10:00","11:00","13:30","15:00"};
      for(int slot=0;slot<starts.length;slot++) {
        int index=slot;
        String code="DEMO-PRIOR-"+past+"-"+slot;
        if(count(c,"SELECT COUNT(*) FROM appointments WHERE appointment_code=?",code)>0) continue;
        String start=starts[slot];
        boolean seen=slot<3, paid=slot<2;
        String aid=at(past+" "+start+":00",()->DemoData.appointment(c,code,advancePatient(c,past,index),
            "cln-tianhe","dnt-lin-wei",past,start,paid?"trt-clean-v1":"trt-exam-v1"));
        if(aid==null) continue;
        if(seen) {
          String vid=at(past+" "+start+":00",()->DemoData.visit(c,aid,"COMPLETED",past));
          if(paid && openPeriod(c,past)) at(dateTime(past+" "+start+":00").plusMinutes(40).format(DT),()->{
            var issued=(Map<?,?>)Finance.issue(c,DemoData.actor("CASHIER"),map("visit_id",vid));
            var invoice=(Map<String,Object>)issued.get("invoice");
            DemoData.pay(c,s(invoice,"id"),val(invoice,"total_fen"),code+"-PAY");
            return null;
          });
        } else {
          boolean missed=slot==3;
          at(dateTime(past+" "+start+":00").plusMinutes(missed?50:-55).format(DT),()->{
            var a=one(c,"SELECT appointment_version FROM appointments WHERE id=?",aid);
            Scheduling.command(c,DemoData.actor("FRONT_DESK"),aid,map("action",missed?"no_show":"cancel",
                "version",a.get("appointment_version"),"initiator","PATIENT","reason",
                missed?"预约结束后仍未到店，电话未接通。":"患者来电另有安排，取消本次预约。"));
            return null;
          });
        }
      }
    }
    if(!DemoData.marked(c,"demo:daily:"+next)) {
      String[] future={"16:00","16:30","17:00"};
      for(int i=0;i<future.length;i++) {
        int slot=i+6;
        if(!standardSlot(next,slot)) continue;
        DemoData.appointment(c,bookingCode(next,slot),advancePatient(c,next,slot),
            "cln-tianhe","dnt-lin-wei",next,future[i],slot%2==0?"trt-exam-v1":"trt-clean-v1");
      }
      addSecondDoctor(c,next);
    }
  }
}
