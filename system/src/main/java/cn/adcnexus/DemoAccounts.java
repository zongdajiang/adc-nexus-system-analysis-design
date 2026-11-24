package cn.adcnexus;

import static cn.adcnexus.Db.*;
import static cn.adcnexus.Support.*;
import java.sql.Connection;
import java.util.*;

/** Public credentials are solely for the six named synthetic evaluation identities. */
final class DemoAccounts {
  static final String PASSWORD="AdcDemo2026!";
  private record Account(String role,String username,String label) {
    String id(){return "jdbc-demo-"+role.toLowerCase(Locale.ROOT);}
    String key(){return "demo:public-password:v1:"+id();}
  }
  private static final List<Account> ACCOUNTS=List.of(
      new Account("CLINIC_MANAGER","demo.manager","诊所经营者"),
      new Account("DENTIST","demo.doctor","医师"),
      new Account("FRONT_DESK","demo.frontdesk","前台接待"),
      new Account("CASHIER","demo.cashier","收费员"),
      new Account("HQ_OPERATIONS","demo.operations","总部运营"),
      new Account("HQ_FINANCE","demo.finance","总部财务"));
  static boolean enabled(){return Boolean.parseBoolean(System.getenv().getOrDefault("DEMO_MODE","false"));}
  static boolean isAccount(String id){return ACCOUNTS.stream().anyMatch(a->a.id().equals(id));}
  private static String fingerprint(Map<String,Object> u){return hash(s(u,"username")+":"+s(u,"password_salt")+":"+s(u,"password_hash"));}

  static void ensure(Connection c) throws Exception {
    if(!enabled())return;
    for(var a:ACCOUNTS) {
      var u=one(c,"SELECT * FROM app_users WHERE id=?",a.id());
      if(u==null||!s(u,"status").equals("ACTIVE"))continue;
      if(one(c,"SELECT setting_key FROM system_settings WHERE organization_id='org-adc' AND setting_key=?",a.key())!=null)continue;
      // Never overwrite an already configured password or another employee's username.
      if(!s(u,"password_hash").isBlank()||count(c,"SELECT COUNT(*) FROM app_users WHERE username=? AND id<>?",a.username(),a.id())>0)continue;
      String salt=salt();
      update(c,"app_users",a.id(),map("username",a.username(),"password_salt",salt,
          "password_hash",password(PASSWORD,salt,600000),"password_iterations",600000,"password_set_at",wallNow()));
      u=one(c,"SELECT * FROM app_users WHERE id=?",a.id());
      insert(c,"system_settings",map("organization_id","org-adc","setting_key",a.key(),"value_json",json(fingerprint(u))));
    }
  }
  static List<Map<String,Object>> catalog(Connection c) throws Exception {
    if(!enabled())return List.of();
    List<Map<String,Object>> out=new ArrayList<>();
    for(var a:ACCOUNTS) {
      var u=one(c,"SELECT * FROM app_users WHERE id=? AND status='ACTIVE'",a.id());
      var marker=one(c,"SELECT value_json FROM system_settings WHERE organization_id='org-adc' AND setting_key=?",a.key());
      if(u==null||marker==null||!json(fingerprint(u)).equals(s(marker,"value_json")))continue;
      out.add(map("role",a.role(),"username",u.get("username"),"name",a.label(),"person_name",u.get("display_name")));
    }
    return out;
  }
}
