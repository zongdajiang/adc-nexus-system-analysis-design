package cn.adcnexus;

import static cn.adcnexus.Db.*;
import static cn.adcnexus.Support.*;

import java.sql.*;
import java.util.*;

final class Finance {
  static final String SELECT =
      "SELECT i.*,p.name_zh patient_name,c.name_zh clinic_name,v.visit_code,d.name_zh dentist_name"
          + " FROM invoices i JOIN patients p ON p.id=i.patient_id JOIN clinics c ON"
          + " c.id=i.clinic_id JOIN clinical_visits v ON v.id=i.visit_id JOIN dentists d ON"
          + " d.id=v.dentist_id ";

  static Object list(Connection c, Auth.Principal p) throws Exception {
    p.need("finance.read");
    return rows(
        c,
        SELECT + " WHERE " + p.scope("i.clinic_id") + " ORDER BY i.created_at DESC LIMIT 400",
        p.scopeArgs());
  }

  static Map<String, Object> get(Connection c, Auth.Principal p, String id) throws Exception {
    p.need("finance.read");
    var i = one(c, SELECT + " WHERE i.id=?", id);
    check(i != null, 404, "NOT_FOUND", "结算单不存在");
    p.clinic(s(i, "clinic_id"));
    return i;
  }

  static Object detail(Connection c, Auth.Principal p, String id) throws Exception {
    var i = get(c, p, id);
    return map(
        "invoice",
        i,
        "lines",
        rows(c, "SELECT * FROM invoice_lines WHERE invoice_id=? ORDER BY line_number", id),
        "payments",
        rows(
            c,
            "SELECT p.*,(SELECT COALESCE(SUM(r.amount_fen),0) FROM payment_refunds r WHERE"
                + " r.payment_id=p.id AND r.status='COMPLETED') refunded_amount_fen FROM payments p"
                + " WHERE p.invoice_id=? ORDER BY p.received_at",
            id),
        "refunds",
        rows(
            c,
            "SELECT r.* FROM payment_refunds r JOIN payments p ON p.id=r.payment_id WHERE"
                + " p.invoice_id=? ORDER BY r.refunded_at",
            id),
        "adjustments",
        rows(c, "SELECT * FROM invoice_adjustments WHERE invoice_id=?", id));
  }

  static Map<String, Object> periodFor(Connection c, String date) throws Exception {
    var r =
        one(
            c,
            "SELECT * FROM financial_reporting_periods WHERE starts_on<=? AND ends_on>=?",
            date,
            date);
    check(r != null, 409, "PERIOD_MISSING", "该业务日期没有财务期间，请先建立期间");
    return r;
  }

  static void openPeriod(Connection c, String date) throws Exception {
    check(
        s(periodFor(c, date), "status").equals("OPEN"),
        409,
        "PERIOD_LOCKED",
        "业务日期所属期间已关闭，请按授权流程重开");
  }

  static Object issue(Connection c, Auth.Principal p, Map<String, Object> b) throws Exception {
    p.need("finance.manage");
    String vid = req(b, "visit_id");
    var v = one(c, "SELECT * FROM clinical_visits WHERE id=?", vid);
    check(v != null, 404, "NOT_FOUND", "就诊不存在");
    p.clinic(s(v, "clinic_id"));
    var existing = one(c, "SELECT id FROM invoices WHERE visit_id=?", vid);
    if (existing != null) return detail(c, p, s(existing, "id"));
    check(s(v, "status").equals("COMPLETED"), 409, "CLINICAL_NOT_COMPLETE", "只有已完成的临床就诊可以生成结算单");
    String date = s(v, "completed_at").substring(0, 10);
    var period = periodFor(c, date);
    check(s(period, "status").equals("OPEN"), 409, "PERIOD_LOCKED", "服务期间已锁定");
    var actual =
        rows(
            c,
            "SELECT a.*,t.code,t.name_en,t.name_zh,t.estimated_cost_fen FROM actual_treatment_items"
                + " a JOIN treatment_catalog t ON t.id=a.treatment_id WHERE a.visit_id=? AND"
                + " a.status='RECORDED' ORDER BY a.performed_at,a.id",
            vid);
    check(!actual.isEmpty(), 409, "NO_ACTUAL", "没有可核对的实施项目");
    long total = 0;
    for (var a : actual) {
      check(
          val(a, "line_amount_fen")
              == Math.multiplyExact(val(a, "units"), val(a, "effective_unit_price_fen")),
          409,
          "LINE_MISMATCH",
          "实施行金额与数量单价不一致");
      total = Math.addExact(total, val(a, "line_amount_fen"));
    }
    check(total > 0, 409, "ZERO_INVOICE", "应收金额必须大于零");
    String id = uuid();
    insert(
        c,
        "invoices",
        map(
            "id",
            id,
            "invoice_code",
            "BILL-" + today().replace("-", "") + "-" + id.substring(0, 6).toUpperCase(Locale.ROOT),
            "visit_id",
            vid,
            "patient_id",
            v.get("patient_id"),
            "clinic_id",
            v.get("clinic_id"),
            "reporting_period_id",
            period.get("id"),
            "status",
            "ISSUED",
            "currency",
            "CNY",
            "subtotal_fen",
            total,
            "total_fen",
            total,
            "balance_fen",
            total,
            "issued_at",
            now(),
            "created_by_user_id",
            p.userId()));
    int n = 1;
    for (var a : actual) {
      long cost = Math.multiplyExact(val(a, "estimated_cost_fen"), val(a, "units"));
      insert(
          c,
          "invoice_lines",
          map(
              "id",
              uuid(),
              "invoice_id",
              id,
              "actual_treatment_item_id",
              a.get("id"),
              "line_number",
              n++,
              "treatment_code_snapshot",
              a.get("code"),
              "description_en_snapshot",
              a.get("name_en"),
              "description_zh_snapshot",
              a.get("name_zh"),
              "tooth_code_snapshot",
              a.get("tooth_code"),
              "surfaces_json_snapshot",
              a.get("surfaces_json"),
              "units_snapshot",
              a.get("units"),
              "unit_price_fen_snapshot",
              a.get("effective_unit_price_fen"),
              "amount_fen_snapshot",
              a.get("line_amount_fen"),
              "cost_fen_snapshot",
              cost,
              "performed_at_snapshot",
              a.get("performed_at")));
      if (count(
              c,
              "SELECT COUNT(*) FROM treatment_cost_entries WHERE actual_treatment_item_id=?",
              a.get("id"))
          == 0)
        insert(
            c,
            "treatment_cost_entries",
            map(
                "id",
                uuid(),
                "actual_treatment_item_id",
                a.get("id"),
                "visit_id",
                vid,
                "clinic_id",
                v.get("clinic_id"),
                "reporting_period_id",
                period.get("id"),
                "catalog_estimated_cost_fen",
                cost,
                "materials_cost_fen",
                0,
                "laboratory_cost_fen",
                0,
                "provider_cost_fen",
                0,
                "total_cost_fen",
                0,
                "cost_date",
                date,
                "source",
                "PENDING_VERIFICATION"));
    }
    Service.audit(c, p, "INVOICE_ISSUE", "invoices", id, s(v, "clinic_id"));
    return detail(c, p, id);
  }

  static Object command(Connection c, Auth.Principal p, String id, Map<String, Object> b)
      throws Exception {
    p.need("finance.manage");
    var i = get(c, p, id);
    Service.version(i, "invoice_version", b);
    String action = req(b, "action");
    check(!s(i, "status").equals("VOID"), 409, "VOID", "单据已作废");
    if (action.equals("pay")) {
      openPeriod(c, today());
      long amount = n(b, "amount_fen");
      check(
          amount > 0 && amount <= val(i, "balance_fen"), 409, "PAYMENT_LIMIT", "收款金额须大于零且不能超过未收余额");
      String method = req(b, "method"), ref = req(b, "reference");
      check(
          Set.of("CASH", "BANK_CARD", "WECHAT", "ALIPAY", "BANK_TRANSFER").contains(method),
          422,
          "METHOD",
          "请选择有效的核实收款方式");
      check(
          count(
                  c,
                  "SELECT COUNT(*) FROM payments WHERE simulated_gateway_reference=? AND"
                      + " status='COMPLETED'",
                  ref)
              == 0,
          409,
          "DUPLICATE_REFERENCE",
          "此凭据已登记，请核对原收款流水");
      String pid = uuid();
      insert(
          c,
          "payments",
          map(
              "id",
              pid,
              "payment_code",
              "PAY-" + pid.substring(0, 10).toUpperCase(Locale.ROOT),
              "invoice_id",
              id,
              "amount_fen",
              amount,
              "method",
              method,
              "status",
              "COMPLETED",
              "simulated_gateway_reference",
              ref,
              "received_at",
              now(),
              "recorded_by_user_id",
              p.userId(),
              "notes",
              s(b, "notes")));
    } else if (action.equals("refund")) {
      openPeriod(c, today());
      String reason = req(b, "reason");
      var payment =
          one(
              c,
              "SELECT * FROM payments WHERE id=? AND invoice_id=? AND status='COMPLETED'",
              req(b, "payment_id"),
              id);
      check(payment != null, 422, "PAYMENT", "原收款不存在或不属于该单据");
      long available =
          val(payment, "amount_fen")
              - count(
                  c,
                  "SELECT COALESCE(SUM(amount_fen),0) FROM payment_refunds WHERE payment_id=? AND"
                      + " status='COMPLETED'",
                  payment.get("id"));
      long amount = n(b, "amount_fen");
      check(amount > 0 && amount <= available, 409, "REFUND_LIMIT", "退款不能超过原收款的剩余可退额");
      check(Boolean.TRUE.equals(b.get("authorized")), 422, "AUTHORIZATION", "请确认已取得退款授权并核实凭据");
      String rid = uuid();
      insert(
          c,
          "payment_refunds",
          map(
              "id",
              rid,
              "refund_code",
              "REF-" + rid.substring(0, 10).toUpperCase(Locale.ROOT),
              "payment_id",
              payment.get("id"),
              "amount_fen",
              amount,
              "reason_code",
              "AUTHORIZED",
              "reason_text",
              reason,
              "status",
              "COMPLETED",
              "authorized_by_user_id",
              p.userId(),
              "refunded_at",
              now()));
    } else if (action.equals("void")) {
      openPeriod(c, s(i, "issued_at").substring(0, 10));
      check(val(i, "paid_fen") - val(i, "refunded_fen") == 0, 409, "NET_PAYMENT", "净收款不为零不能作废");
      update(
          c,
          "invoices",
          id,
          map(
              "status",
              "VOID",
              "void_reason",
              req(b, "reason"),
              "voided_at",
              now(),
              "invoice_version",
              val(i, "invoice_version") + 1,
              "updated_at",
              now()));
      Service.audit(c, p, "INVOICE_VOID", "invoices", id, s(i, "clinic_id"));
      return detail(c, p, id);
    } else throw error(422, "ACTION", "未知结算操作");
    long
        paid =
            count(
                c,
                "SELECT COALESCE(SUM(amount_fen),0) FROM payments WHERE invoice_id=? AND"
                    + " status='COMPLETED'",
                id),
        refund =
            count(
                c,
                "SELECT COALESCE(SUM(r.amount_fen),0) FROM payment_refunds r JOIN payments p ON"
                    + " p.id=r.payment_id WHERE p.invoice_id=? AND r.status='COMPLETED'",
                id),
        net = paid - refund,
        balance = val(i, "total_fen") - net;
    check(balance >= 0 && net >= 0, 409, "BALANCE", "资金流水不平衡");
    update(
        c,
        "invoices",
        id,
        map(
            "paid_fen",
            paid,
            "refunded_fen",
            refund,
            "balance_fen",
            balance,
            "status",
            net == 0 ? "ISSUED" : balance == 0 ? "PAID" : "PARTIALLY_PAID",
            "invoice_version",
            val(i, "invoice_version") + 1,
            "updated_at",
            now()));
    Service.audit(
        c, p, "INVOICE_" + action.toUpperCase(Locale.ROOT), "invoices", id, s(i, "clinic_id"));
    return detail(c, p, id);
  }

  static Map<String, Object> summary(Connection c, Auth.Principal p, String from, String to)
      throws Exception {
    var args = Service.join(new Object[] {from, to}, p.scopeArgs());
    long paid =
        count(
            c,
            "SELECT COALESCE(SUM(p.amount_fen),0) FROM payments p JOIN invoices i ON"
                + " i.id=p.invoice_id WHERE p.status='COMPLETED' AND substr(p.received_at,1,10)>=?"
                + " AND substr(p.received_at,1,10)<=? AND "
                + p.scope("i.clinic_id"),
            args);
    long refunds =
        count(
            c,
            "SELECT COALESCE(SUM(r.amount_fen),0) FROM payment_refunds r JOIN payments p ON"
                + " p.id=r.payment_id JOIN invoices i ON i.id=p.invoice_id WHERE"
                + " r.status='COMPLETED' AND substr(r.refunded_at,1,10)>=? AND"
                + " substr(r.refunded_at,1,10)<=? AND "
                + p.scope("i.clinic_id"),
            args);
    return map(
        "paid_fen",
        paid,
        "refunded_fen",
        refunds,
        "net_cash_fen",
        paid - refunds,
        "receivable_fen",
        count(
            c,
            "SELECT COALESCE(SUM(balance_fen),0) FROM invoices WHERE status<>'VOID' AND "
                + p.scope("clinic_id"),
            p.scopeArgs()),
        "basis",
        "收退款发生日；应收余额为授权范围当前未收总额");
  }

  static Object periods(Connection c, Auth.Principal p) throws Exception {
    p.need("finance.read");
    Map<String, Object> out =
        map(
            "periods",
            rows(c, "SELECT * FROM financial_reporting_periods ORDER BY starts_on DESC"),
            "expenses",
            rows(
                c,
                "SELECT e.*,c.name_zh clinic_name FROM operating_expenses e JOIN clinics c ON"
                    + " c.id=e.clinic_id WHERE "
                    + p.scope("e.clinic_id")
                    + " ORDER BY e.incurred_on DESC LIMIT 300",
                p.scopeArgs()),
            "costs",
            rows(
                c,
                "SELECT x.*,t.name_zh treatment_name FROM treatment_cost_entries x JOIN"
                    + " actual_treatment_items a ON a.id=x.actual_treatment_item_id JOIN"
                    + " treatment_catalog t ON t.id=a.treatment_id WHERE "
                    + p.scope("x.clinic_id")
                    + " ORDER BY x.cost_date DESC LIMIT 200",
                p.scopeArgs()));
    out.put(
        "results",
        rows(
            c,
            "SELECT * FROM financial_period_results WHERE "
                + p.scope("clinic_id")
                + " ORDER BY calculated_at DESC LIMIT 100",
            p.scopeArgs()));
    out.put(
        "allocations",
        rows(
            c,
            "SELECT a.* FROM dentist_expense_allocations a JOIN operating_expenses e ON"
                + " e.id=a.expense_id WHERE "
                + p.scope("e.clinic_id"),
            p.scopeArgs()));
    if (p.network())
      out.put("pools", rows(c, "SELECT * FROM incentive_pools ORDER BY created_at DESC LIMIT 30"));
    return out;
  }

  static Map<String, Object> calculate(Connection c, Auth.Principal p, String periodId)
      throws Exception {
    p.need("period.manage");
    check(p.network(), 403, "NETWORK_REQUIRED", "期间核定需总部范围");
    var period = one(c, "SELECT * FROM financial_reporting_periods WHERE id=?", periodId);
    check(period != null, 404, "NOT_FOUND", "期间不存在");
    String from = s(period, "starts_on"), to = s(period, "ends_on");
    List<String> blockers = new ArrayList<>();
    if (today().compareTo(to) < 0) blockers.add("期间尚未到期；当前计算仅供预览，不能提前关闭");
    if (count(
            c,
            "SELECT COUNT(*) FROM operating_expenses WHERE reporting_period_id=? AND"
                + " status<>'APPROVED'",
            periodId)
        > 0) blockers.add("存在未核实运营费用");
    if (count(
            c,
            "SELECT COUNT(*) FROM treatment_cost_entries WHERE reporting_period_id=? AND source NOT"
                + " IN ('VERIFIED','VERIFIED_MANUAL')",
            periodId)
        > 0) blockers.add("存在未核实治疗成本；目录估算不可充当实际成本");
    for (var e :
        rows(
            c,
            "SELECT e.id,e.amount_fen,COALESCE(SUM(a.amount_fen),0) allocated FROM"
                + " operating_expenses e LEFT JOIN dentist_expense_allocations a ON"
                + " a.expense_id=e.id WHERE e.reporting_period_id=? AND e.status='APPROVED' GROUP"
                + " BY e.id,e.amount_fen",
            periodId))
      if (val(e, "amount_fen") != val(e, "allocated")) blockers.add("运营费用尚未完整归属：" + e.get("id"));
    List<Map<String, Object>> results = new ArrayList<>();
    long revenue = 0, cost = 0, expense = 0;
    for (var clinic :
        rows(c, "SELECT id,name_zh FROM clinics WHERE status='ACTIVE' ORDER BY code")) {
      String cid = s(clinic, "id");
      long r =
          count(
                  c,
                  "SELECT COALESCE(SUM(p.amount_fen),0) FROM payments p JOIN invoices i ON"
                      + " i.id=p.invoice_id WHERE i.clinic_id=? AND p.status='COMPLETED' AND"
                      + " substr(p.received_at,1,10)>=? AND substr(p.received_at,1,10)<=?",
                  cid,
                  from,
                  to)
              - count(
                  c,
                  "SELECT COALESCE(SUM(r.amount_fen),0) FROM payment_refunds r JOIN payments p ON"
                      + " p.id=r.payment_id JOIN invoices i ON i.id=p.invoice_id WHERE"
                      + " i.clinic_id=? AND r.status='COMPLETED' AND substr(r.refunded_at,1,10)>=?"
                      + " AND substr(r.refunded_at,1,10)<=?",
                  cid,
                  from,
                  to);
      long
          mc =
              count(
                  c,
                  "SELECT COALESCE(SUM(total_cost_fen),0) FROM treatment_cost_entries WHERE"
                      + " clinic_id=? AND reporting_period_id=?",
                  cid,
                  periodId),
          oe =
              count(
                  c,
                  "SELECT COALESCE(SUM(amount_fen),0) FROM operating_expenses WHERE clinic_id=? AND"
                      + " reporting_period_id=? AND status='APPROVED'",
                  cid,
                  periodId);
      results.add(
          map(
              "clinic_id",
              cid,
              "clinic_name",
              clinic.get("name_zh"),
              "revenue_fen",
              r,
              "cost_fen",
              mc,
              "expense_fen",
              oe,
              "profit_fen",
              r - mc - oe));
      revenue += r;
      cost += mc;
      expense += oe;
    }
    var dentists =
        rows(
            c,
            "SELECT d.id,d.name_zh,COALESCE((SELECT SUM(p.amount_fen) FROM payments p JOIN invoices"
                + " i ON i.id=p.invoice_id JOIN clinical_visits v ON v.id=i.visit_id WHERE"
                + " v.dentist_id=d.id AND p.status='COMPLETED' AND substr(p.received_at,1,10)>=?"
                + " AND substr(p.received_at,1,10)<=?),0)-COALESCE((SELECT SUM(r.amount_fen) FROM"
                + " payment_refunds r JOIN payments p ON p.id=r.payment_id JOIN invoices i ON"
                + " i.id=p.invoice_id JOIN clinical_visits v ON v.id=i.visit_id WHERE"
                + " v.dentist_id=d.id AND r.status='COMPLETED' AND substr(r.refunded_at,1,10)>=?"
                + " AND substr(r.refunded_at,1,10)<=?),0) revenue_fen,COALESCE((SELECT"
                + " SUM(x.total_cost_fen) FROM treatment_cost_entries x JOIN clinical_visits v ON"
                + " v.id=x.visit_id WHERE v.dentist_id=d.id AND x.reporting_period_id=?),0)"
                + " cost_fen,COALESCE((SELECT SUM(a.amount_fen) FROM dentist_expense_allocations a"
                + " JOIN operating_expenses e ON e.id=a.expense_id WHERE a.dentist_id=d.id AND"
                + " e.reporting_period_id=?),0) expense_fen FROM dentists d WHERE"
                + " d.employment_status='ACTIVE' ORDER BY d.employee_code",
            from,
            to,
            from,
            to,
            periodId,
            periodId);
    for (var d : dentists)
      d.put("profit_fen", val(d, "revenue_fen") - val(d, "cost_fen") - val(d, "expense_fen"));
    String fingerprint =
        hash(
            json(
                map(
                    "period",
                    period,
                    "payments",
                    rows(
                        c,
                        "SELECT p.id,p.amount_fen,p.status,p.received_at FROM payments p WHERE"
                            + " substr(p.received_at,1,10)>=? AND substr(p.received_at,1,10)<=?"
                            + " ORDER BY p.id",
                        from,
                        to),
                    "refunds",
                    rows(
                        c,
                        "SELECT id,amount_fen,status,refunded_at FROM payment_refunds WHERE"
                            + " substr(refunded_at,1,10)>=? AND substr(refunded_at,1,10)<=? ORDER"
                            + " BY id",
                        from,
                        to),
                    "expenses",
                    rows(
                        c,
                        "SELECT * FROM operating_expenses WHERE reporting_period_id=? ORDER BY id",
                        periodId),
                    "allocations",
                    rows(
                        c,
                        "SELECT a.* FROM dentist_expense_allocations a JOIN operating_expenses e ON"
                            + " e.id=a.expense_id WHERE e.reporting_period_id=? ORDER BY a.id",
                        periodId),
                    "costs",
                    rows(
                        c,
                        "SELECT * FROM treatment_cost_entries WHERE reporting_period_id=? ORDER BY"
                            + " id",
                        periodId))));
    return map(
        "period",
        period,
        "blockers",
        blockers,
        "clinics",
        results,
        "dentists",
        dentists,
        "revenue_fen",
        revenue,
        "cost_fen",
        cost,
        "expense_fen",
        expense,
        "profit_fen",
        revenue - cost - expense,
        "pool_fen",
        Math.max(0, revenue - cost - expense) / 10,
        "fingerprint",
        fingerprint,
        "policy",
        "课程核算选用收付实现口径：收入按收退款发生日；治疗成本按实施日期；费用按归属期间。此口径需机构另行批准后用于正式核算。个人贡献不是个人奖金分配。",
        "generated_at",
        now());
  }

  static Object periodCommand(Connection c, Auth.Principal p, Map<String, Object> b)
      throws Exception {
    String action = req(b, "action");
    if (action.equals("expense")) {
      p.need("expense.manage");
      String clinic = req(b, "clinic_id");
      p.clinic(clinic);
      var period = periodFor(c, req(b, "incurred_on"));
      check(s(period, "status").equals("OPEN"), 409, "PERIOD_LOCKED", "期间已锁定");
      long amount = n(b, "amount_fen");
      check(amount > 0 && amount < 100_000_000_000L, 422, "AMOUNT", "费用金额无效");
      String id = uuid();
      insert(
          c,
          "operating_expenses",
          map(
              "id",
              id,
              "clinic_id",
              clinic,
              "reporting_period_id",
              period.get("id"),
              "category",
              req(b, "category"),
              "vendor_name",
              req(b, "vendor"),
              "amount_fen",
              amount,
              "incurred_on",
              b.get("incurred_on"),
              "description_zh",
              req(b, "evidence"),
              "description_en",
              "",
              "status",
              "APPROVED",
              "entered_by_user_id",
              p.userId(),
              "approved_by_user_id",
              p.userId()));
      Service.audit(c, p, "EXPENSE_APPROVE", "operating_expenses", id, clinic);
      return map("id", id);
    }
    if (action.equals("allocate")) {
      p.need("expense.manage");
      var e = one(c, "SELECT * FROM operating_expenses WHERE id=?", req(b, "expense_id"));
      check(e != null, 404, "NOT_FOUND", "费用不存在");
      p.clinic(s(e, "clinic_id"));
      check(
          s(
                  one(
                      c,
                      "SELECT status FROM financial_reporting_periods WHERE id=?",
                      e.get("reporting_period_id")),
                  "status")
              .equals("OPEN"),
          409,
          "PERIOD_LOCKED",
          "期间已锁定");
      String did = req(b, "dentist_id");
      long amount = n(b, "amount_fen"),
          allocated =
              count(
                  c,
                  "SELECT COALESCE(SUM(amount_fen),0) FROM dentist_expense_allocations WHERE"
                      + " expense_id=?",
                  e.get("id"));
      check(
          amount > 0 && allocated + amount <= val(e, "amount_fen"),
          409,
          "ALLOCATION_LIMIT",
          "分摊总额不能超过原费用");
      check(
          count(
                  c,
                  "SELECT COUNT(*) FROM dentist_clinic_assignments WHERE dentist_id=? AND"
                      + " clinic_id=?",
                  did,
                  e.get("clinic_id"))
              > 0,
          422,
          "DENTIST_ASSIGNMENT",
          "该牙医不属于费用归属诊所");
      insert(
          c,
          "dentist_expense_allocations",
          map(
              "id",
              uuid(),
              "expense_id",
              e.get("id"),
              "dentist_id",
              did,
              "amount_fen",
              amount,
              "basis",
              req(b, "basis"),
              "approved_by_user_id",
              p.userId(),
              "created_at",
              now()));
      return map("ok", true);
    }
    if (action.equals("cost")) {
      p.need("expense.manage");
      var x = one(c, "SELECT * FROM treatment_cost_entries WHERE id=?", req(b, "cost_id"));
      check(x != null, 404, "NOT_FOUND", "成本条目不存在");
      p.clinic(s(x, "clinic_id"));
      openPeriod(c, s(x, "cost_date"));
      long m = n(b, "materials_fen"), l = n(b, "laboratory_fen"), pr = n(b, "provider_fen");
      check(m >= 0 && l >= 0 && pr >= 0, 422, "AMOUNT", "成本不能为负");
      String evidence = req(b, "evidence");
      var verified =
          map(
              "materials_cost_fen",
              m,
              "laboratory_cost_fen",
              l,
              "provider_cost_fen",
              pr,
              "total_cost_fen",
              Math.addExact(Math.addExact(m, l), pr),
              "source",
              "VERIFIED_MANUAL");
      update(c, "treatment_cost_entries", s(x, "id"), verified);
      insert(
          c,
          "audit_events",
          map(
              "request_id",
              uuid(),
              "actor_user_id",
              p.userId(),
              "actor_subject",
              p.userId(),
              "action",
              "COST_VERIFY",
              "entity_type",
              "treatment_cost_entries",
              "entity_id",
              x.get("id"),
              "clinic_id",
              x.get("clinic_id"),
              "outcome",
              "SUCCESS",
              "source",
              "JDBC_API",
              "reason",
              evidence,
              "before_json",
              json(x),
              "after_json",
              json(verified),
              "occurred_at",
              now()));
      return map("ok", true);
    }
    p.need("period.manage");
    String pid = req(b, "period_id");
    var r = calculate(c, p, pid);
    var period = (Map<String, Object>) r.get("period");
    Service.version(period, "period_version", b);
    if (action.equals("close")) {
      check(s(period, "status").equals("OPEN"), 409, "STATE", "期间已经关闭");
      var blockers = (List<?>) r.get("blockers");
      if (!blockers.isEmpty()) throw new Problem(409, "CLOSE_BLOCKERS", "期间尚不能关闭", blockers);
      check(
          req(b, "fingerprint").equals(r.get("fingerprint")),
          409,
          "INPUT_CHANGED",
          "核算输入已变化，请重新预检");
      check(Boolean.TRUE.equals(b.get("policy_confirmed")), 422, "POLICY", "请确认本次核算口径与分摊依据");
      var all = new ArrayList<Map<String, Object>>((List<Map<String, Object>>) r.get("clinics"));
      all.add(
          map(
              "clinic_id",
              null,
              "revenue_fen",
              r.get("revenue_fen"),
              "cost_fen",
              r.get("cost_fen"),
              "expense_fen",
              r.get("expense_fen"),
              "profit_fen",
              r.get("profit_fen")));
      String networkId = null;
      for (var row : all) {
        String id = uuid(), scope = row.get("clinic_id") == null ? "NETWORK" : s(row, "clinic_id");
        if (scope.equals("NETWORK")) networkId = id;
        insert(
            c,
            "financial_period_results",
            map(
                "id",
                id,
                "reporting_period_id",
                pid,
                "clinic_id",
                row.get("clinic_id"),
                "scope_key",
                scope + ":v" + (val(period, "period_version") + 1),
                "recognized_revenue_fen",
                row.get("revenue_fen"),
                "treatment_cost_fen",
                row.get("cost_fen"),
                "operating_expense_fen",
                row.get("expense_fen"),
                "net_profit_fen",
                row.get("profit_fen"),
                "net_margin_basis_points",
                val(row, "revenue_fen") == 0
                    ? 0
                    : val(row, "profit_fen") * 10000 / val(row, "revenue_fen"),
                "invoice_count",
                0,
                "open_exception_count",
                0,
                "calculation_inputs_json",
                json(r),
                "status",
                "APPROVED",
                "calculated_at",
                now(),
                "approved_at",
                now(),
                "approved_by_user_id",
                p.userId()));
      }
      var poolValues =
          map(
              "network_result_id",
              networkId,
              "rate_basis_points",
              1000,
              "eligible_net_profit_fen",
              Math.max(0, val(r, "profit_fen")),
              "pool_amount_fen",
              r.get("pool_fen"),
              "formula_evidence",
              "floor(max(network_profit_fen,0)*0.10); " + r.get("fingerprint"),
              "status",
              "APPROVED",
              "approved_at",
              now(),
              "approved_by_user_id",
              p.userId());
      var previousPool = one(c, "SELECT * FROM incentive_pools WHERE reporting_period_id=?", pid);
      if (previousPool == null) {
        var fresh = new LinkedHashMap<String, Object>(poolValues);
        fresh.put("id", uuid());
        fresh.put("reporting_period_id", pid);
        insert(c, "incentive_pools", fresh);
      } else {
        update(c, "incentive_pools", s(previousPool, "id"), poolValues);
        insert(
            c,
            "audit_events",
            map(
                "request_id",
                uuid(),
                "actor_user_id",
                p.userId(),
                "actor_subject",
                p.userId(),
                "action",
                "INCENTIVE_POOL_REAPPROVE",
                "entity_type",
                "incentive_pools",
                "entity_id",
                previousPool.get("id"),
                "outcome",
                "SUCCESS",
                "source",
                "JDBC_API",
                "before_json",
                json(previousPool),
                "after_json",
                json(poolValues),
                "occurred_at",
                now()));
      }
      update(
          c,
          "financial_reporting_periods",
          pid,
          map(
              "status",
              "CLOSED",
              "locked_at",
              now(),
              "locked_by_user_id",
              p.userId(),
              "period_version",
              val(period, "period_version") + 1,
              "updated_at",
              now()));
    } else if (action.equals("reopen")) {
      check(s(period, "status").equals("CLOSED"), 409, "STATE", "期间未关闭");
      update(
          c,
          "financial_reporting_periods",
          pid,
          map(
              "status",
              "OPEN",
              "reopened_at",
              now(),
              "reopened_by_user_id",
              p.userId(),
              "reopen_reason",
              req(b, "reason"),
              "period_version",
              val(period, "period_version") + 1,
              "updated_at",
              now()));
    } else throw error(422, "ACTION", "未知期间操作");
    Service.audit(
        c,
        p,
        "PERIOD_" + action.toUpperCase(Locale.ROOT),
        "financial_reporting_periods",
        pid,
        null);
    return map("ok", true);
  }
}
