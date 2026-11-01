package cn.adcnexus;

import static cn.adcnexus.Db.*;
import static cn.adcnexus.Support.*;

import java.sql.Connection;
import java.time.LocalDate;
import java.util.*;

/** A clinician's recall advice is separate from contact evidence and a booked appointment. */
final class Followups {
  static final String SELECT="SELECT f.*,p.patient_code,p.name_zh patient_name,d.name_zh dentist_name,"
      + " c.name_zh clinic_name,v.visit_code,a.appointment_code,a.status appointment_status,a.scheduled_start_at"
      + " FROM patient_followups f JOIN patients p ON p.id=f.patient_id JOIN dentists d ON d.id=f.dentist_id"
      + " JOIN clinics c ON c.id=f.clinic_id JOIN clinical_visits v ON v.id=f.source_visit_id"
      + " LEFT JOIN appointments a ON a.id=f.appointment_id";

  static String permission(boolean post, Map<String,Object> b) {
    return !post ? "followup.read" : s(b,"action").equals("recommend") ? "followup.recommend" : "followup.manage";
  }

  static Map<String,Object> get(Connection c,Auth.Principal p,String id) throws Exception {
    var f=one(c,SELECT+" WHERE f.id=?",id);
    check(f!=null,404,"NOT_FOUND","复诊建议不存在"); p.clinic(s(f,"clinic_id"));
    check(p.dentistId()==null||p.dentistId().equals(s(f,"dentist_id")),403,"RESPONSIBLE_DENTIST","只能查看本人负责的复诊建议");
    return f;
  }

  static Object data(Connection c,Auth.Principal p,String id) throws Exception {
    p.need("followup.read");
    if(!id.isBlank()) {
      var f=get(c,p,id);
      var patient=one(c,"SELECT phone FROM patients WHERE id=?",f.get("patient_id"));
      return map("followup",f,"phone",p.permissions().contains("followup.manage")?patient.get("phone"):null,
          "events",rows(c,"SELECT e.*,u.display_name actor_name FROM followup_contact_events e JOIN app_users u ON u.id=e.actor_user_id"
              +" WHERE e.followup_id=? ORDER BY e.occurred_at,e.id",id));
    }
    List<Object> args=new ArrayList<>(List.of(p.scopeArgs()));
    String where=p.scope("f.clinic_id");
    if(p.dentistId()!=null){ where+=" AND f.dentist_id=?";args.add(p.dentistId()); }
    return map("items",rows(c,SELECT+" WHERE "+where+" ORDER BY f.due_on,f.created_at LIMIT 600",args.toArray()),"today",today());
  }

  static Object command(Connection c,Auth.Principal p,Map<String,Object> b) throws Exception {
    String action=req(b,"action"); p.need(permission(true,b));
    String id=s(b,"id"); Map<String,Object> f;
    if(action.equals("recommend")){
      p.need("clinical.write");
      var v=Clinical.get(c,p,req(b,"visit_id"));
      check(!s(v,"status").equals("CANCELLED"),409,"STATE","已取消就诊不能追加复诊建议");
      String due=LocalDate.parse(req(b,"due_on")).toString();
      check(due.compareTo(today())>=0,422,"DUE_DATE","复诊日期不能早于今日");
      check(count(c,"SELECT COUNT(*) FROM patient_followups WHERE source_visit_id=? AND due_on=? AND status IN ('PENDING','SCHEDULED')",v.get("id"),due)==0,
          409,"DUPLICATE_FOLLOWUP","本次就诊在同一天已有待处理复诊建议，请核对现有记录");
      id=uuid();
      f=map("id",id,"patient_id",v.get("patient_id"),"clinic_id",v.get("clinic_id"),"source_visit_id",v.get("id"),
          "dentist_id",v.get("dentist_id"),"due_on",due,"reason",PracticeSetup.bounded(b,"reason",1500,false),
          "priority",PracticeSetup.selected(b,"priority",Set.of("ROUTINE","PRIORITY")),
          "contact_allowed",Boolean.TRUE.equals(b.get("contact_allowed"))?1:0,"next_contact_on",due,
          "status","PENDING","revision",1,"created_by_user_id",p.userId(),"created_at",now(),"updated_at",now());
      insert(c,"patient_followups",f);
      event(c,p,id,"RECOMMEND","IN_PERSON","RECORDED",s(f,"reason"),null,due);
    }else{
      f=get(c,p,req(b,"id")); Service.version(f,"revision",b);
      String old=s(f,"status"),status=old,appointment=s(f,"appointment_id"),next=s(f,"next_contact_on");
      String channel="INTERNAL",outcome=action.toUpperCase(Locale.ROOT),note=PracticeSetup.bounded(b,"note",1500,false);
      switch(action){
        case "contact" -> {
          check(Set.of("PENDING","SCHEDULED").contains(old),409,"STATE","已结束建议不能追加联系任务");
          channel=PracticeSetup.selected(b,"channel",Set.of("PHONE","EMAIL","SMS","IN_PERSON"));
          check(channel.equals("IN_PERSON")||val(f,"contact_allowed")==1,409,"CONTACT_PERMISSION","尚无患者同意联系记录，请当面沟通或先由负责医师核实");
          outcome=PracticeSetup.selected(b,"outcome",Set.of("NO_ANSWER","REQUESTED_CALLBACK","AGREED","DECLINED"));
          if(outcome.equals("DECLINED")) status="DECLINED";
          next=s(b,"next_contact_on");
          if(!next.isBlank()) check(LocalDate.parse(next).toString().compareTo(today())>=0,422,"CONTACT_DATE","下次联系日期不能早于今日");
          if(Set.of("NO_ANSWER","REQUESTED_CALLBACK").contains(outcome)) check(!next.isBlank(),422,"CONTACT_DATE","请安排下次联系日期");
        }
        case "link" -> {
          check(old.equals("PENDING"),409,"STATE","只有待安排建议可以关联预约");
          var a=one(c,"SELECT * FROM appointments WHERE id=?",req(b,"appointment_id"));
          check(a!=null&&s(a,"patient_id").equals(s(f,"patient_id"))&&s(a,"clinic_id").equals(s(f,"clinic_id")),422,"APPOINTMENT_LINK","请选择该患者在同一诊所的预约");
          check(count(c,"SELECT COUNT(*) FROM clinical_visits WHERE id=? AND appointment_id=?",f.get("source_visit_id"),a.get("id"))==0,
              409,"SOURCE_APPOINTMENT","不能把提出建议的原就诊当作后续复诊");
          check(Set.of("CONFIRMED","CHECKED_IN","IN_PROGRESS","COMPLETED").contains(s(a,"status"))
              &&s(a,"scheduled_start_at").substring(0,10).compareTo(s(f,"created_at").substring(0,10))>=0,
              409,"APPOINTMENT_LINK","关联预约须有效，且服务日期不早于建议建立日期");
          appointment=s(a,"id");status="SCHEDULED";next="";
        }
        case "complete" -> {
          check(old.equals("SCHEDULED")&&!appointment.isBlank(),409,"STATE","须先关联正式预约");
          check(count(c,"SELECT COUNT(*) FROM appointments a JOIN clinical_visits v ON v.appointment_id=a.id WHERE a.id=? AND a.status='COMPLETED' AND v.status='COMPLETED'",appointment)==1,
              409,"CARE_NOT_COMPLETED","关联预约尚未完成临床就诊，不能标记复诊已完成");
          status="COMPLETED";next="";
        }
        case "reopen" -> {
          check(old.equals("SCHEDULED"),409,"STATE","仅能重新安排已关联但失效的预约");
          check(count(c,"SELECT COUNT(*) FROM appointments WHERE id=? AND status IN ('CANCELLED','NO_SHOW')",appointment)==1,
              409,"APPOINTMENT_ACTIVE","关联预约仍有效，请先核对预约记录");
          status="PENDING";next=today();
        }
        case "cancel" -> { check(Set.of("PENDING","SCHEDULED").contains(old),409,"STATE","建议已结束");status="CANCELLED";next=""; }
        default -> throw error(422,"ACTION","未知复诊操作");
      }
      event(c,p,id,action.toUpperCase(Locale.ROOT),channel,outcome,note,appointment.isBlank()?null:appointment,next);
      update(c,"patient_followups",id,map("status",status,"appointment_id",action.equals("reopen")?null:appointment.isBlank()?null:appointment,
          "next_contact_on",next.isBlank()?null:next,"revision",val(f,"revision")+1,"updated_at",now()));
    }
    Service.audit(c,p,"FOLLOWUP_"+action.toUpperCase(Locale.ROOT),"patient_followups",id,s(f,"clinic_id"));
    return map("ok",true,"id",id);
  }

  static void event(Connection c,Auth.Principal p,String id,String type,String channel,String outcome,String note,String appointment,String next) throws Exception {
    insert(c,"followup_contact_events",map("id",uuid(),"followup_id",id,"actor_user_id",p.userId(),"event_type",type,
        "channel",channel,"outcome",outcome,"note",note,"appointment_id",appointment,
        "next_contact_on",next==null||next.isBlank()?null:next,"occurred_at",now()));
  }
}
