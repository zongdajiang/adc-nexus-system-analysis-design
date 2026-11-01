// Original ADC Nexus authentication UI. Reference: public form hierarchy, not copied assets/code.
export const loginMethods = [["password","密码登录"],["phone","手机验证码"],["email","邮箱验证码"]];
export function authModeAvailable(config,{register=false,recover=false,method="password",channel="PHONE"}={}) {
  if(register) return config.registration_ready === true;
  if(recover && !["PHONE","EMAIL"].includes(channel))return false;
  if(!recover && !loginMethods.some(([id])=>id===method))return false;
  if(!recover && method === "password") return true;
  const selected = recover ? channel : method === "phone" ? "PHONE" : "EMAIL";
  return config[selected === "PHONE" ? "sms" : "email"] === true;
}
export function renderAuthPage({ app, config, api, enter, esc, errorBox, modal }) {
  const route = location.hash.split("/")[1];
  const register = route === "register", recover = route === "recover";
  let method = "password", kind = "PATIENT", channel = "PHONE", pending = false, destroyed = false;
  const timers = new Set();
  const clearTimers = () => { timers.forEach(clearInterval); timers.clear(); };
  const available = () => authModeAvailable(config,{register,recover,method,channel});
  const challenges = {};
  const q = s => app.querySelector(s);
  const input = (name, label, type = "text", attrs = "") => `<div class="auth-field"><label for="auth-${name}">${label}</label>${type === "password" ? '<div class="password-input">' : ''}<input id="auth-${name}" name="${name}" type="${type}" required ${attrs}>${type === "password" ? `<button type="button" class="password-toggle" data-password-toggle="${name}" aria-controls="auth-${name}" aria-pressed="false" aria-label="显示${label}">显示</button></div>` : ''}</div>`;
  function codeField(ch) {
    const phone = ch === "PHONE", name = phone ? "phone" : "email";
    return `<div class="auth-field"><label for="auth-${name}">${phone ? "手机号" : "邮箱"}</label><input id="auth-${name}" name="${name}" type="${phone ? "tel" : "email"}" required autocomplete="${phone ? "tel" : "email"}" placeholder="${phone ? "+86 手机号码" : "name@example.com"}"></div>
      <div class="auth-field"><label for="auth-${name}-code">${phone ? "手机" : "邮箱"}验证码</label><div class="code-input"><input id="auth-${name}-code" name="${name}_code" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" autocomplete="one-time-code" required placeholder="6 位验证码"><button class="btn" type="button" data-send="${ch}" ${config[phone ? "sms" : "email"] ? "" : "disabled"}>获取验证码</button></div></div>`;
  }
  function notice(ch) {
    return config[ch === "PHONE" ? "sms" : "email"] ? "" : `<div class="auth-notice" id="auth-channel-notice"><span class="status-pip"></span>${ch === "PHONE" ? "短信" : "邮箱"}验证服务尚未开通。${recover ? "暂不能在线重设密码，请联系机构管理员核实账号。" : "请使用密码登录；验证码登录暂不可用。"}</div>`;
  }
  function paint() {
    clearTimers();
    document.title = `${register ? "注册账号" : recover ? "找回密码" : "登录"} · ADC Nexus`;
    app.innerHTML = `<div class="auth-layout"><header class="auth-header"><a class="auth-brand" href="#/home"><img src="/mark.svg" alt="" width="34" height="34"><span>ADC Nexus<small>安德鲁牙科连锁</small></span></a><a class="auth-header-note" href="#/home">返回网站首页 ↗</a></header><main class="auth-main"><aside class="auth-story"><span>ANDREW’S DENTAL CHAIN</span><h2>让接待更从容，<br>让诊疗有据可循。</h2><p>从预约安排、临床记录到费用核对，为每个岗位保留清楚的工作入口。</p><ol><li>前台核对患者，安排本次服务</li><li>医师记录检查、方案与实际治疗</li><li>收费核对项目，保留收退款凭据</li></ol></aside><section class="auth-card ${register ? "registration-card" : ""}" aria-labelledby="auth-title"><div class="auth-card-heading"><img src="/mark.svg" alt="" width="42" height="42"><h1 id="auth-title">${register ? "创建 ADC Nexus 账号" : recover ? "找回密码" : "登录工作台"}</h1><p>${register ? "验证联系方式，建立与您身份相符的账号" : recover ? "使用已验证的手机号或邮箱重设密码" : "一个账号，进入您的诊疗与工作空间"}</p></div>
      ${register ? `<div class="auth-segment" aria-label="注册类型"><button type="button" data-kind="PATIENT" class="${kind === "PATIENT" ? "selected" : ""}">患者注册</button><button type="button" data-kind="EMPLOYEE" class="${kind === "EMPLOYEE" ? "selected" : ""}">内部员工激活</button></div>` : recover ? `<div class="auth-segment" aria-label="验证方式"><button type="button" data-channel="PHONE" class="${channel === "PHONE" ? "selected" : ""}">手机验证</button><button type="button" data-channel="EMAIL" class="${channel === "EMAIL" ? "selected" : ""}">邮箱验证</button></div>` : `<div class="auth-methods" role="tablist" aria-label="登录方式">${[["password","密码登录"],["phone","手机验证码"],["email","邮箱验证码"]].map(([v,label]) => `<button role="tab" type="button" aria-selected="${method === v}" data-method="${v}" class="${method === v ? "selected" : ""}">${label}</button>`).join("")}</div>`}
      <form id="unified-auth-form"><div class="auth-fields ${register ? "two-column" : ""}">${register ? `${input("name","真实姓名","text",'maxlength="60" autocomplete="name"')}${kind === "EMPLOYEE" ? input("employee_id","内部员工编号","text",'placeholder="ADC-DR-000001" pattern="ADC-(FD|DR|CS|MG|OP|FN|AD)-[0-9]{6}" maxlength="13"') + input("activation_code","机构激活码","text",'autocomplete="off" placeholder="向机构管理员领取"') : input("date_of_birth","出生日期","date",`min="1900-01-01" max="${new Date().toLocaleDateString("en-CA")}"`) + `<div class="auth-field"><label for="auth-gender">性别记录</label><select name="gender" id="auth-gender" required><option value="UNKNOWN">未说明</option><option value="FEMALE">女</option><option value="MALE">男</option><option value="OTHER">其他</option></select></div>`}${codeField("PHONE")}${codeField("EMAIL")}${input("password","设置密码","password",'minlength="12" maxlength="128" autocomplete="new-password" placeholder="12–128 位，建议使用长密码"')}${input("confirm","确认密码","password",'minlength="12" maxlength="128" autocomplete="new-password"')}` : recover ? codeField(channel) + input("new_password","新密码","password",'minlength="12" maxlength="128" autocomplete="new-password"') + input("confirm","确认新密码","password",'minlength="12" maxlength="128" autocomplete="new-password"') : method === "password" ? input("username","账号 / 手机号 / 邮箱","text",'maxlength="254" autocomplete="username" placeholder="请输入账号或已验证的联系方式"') + `<div class="auth-field"><label for="auth-password">密码</label><div class="password-input"><input id="auth-password" type="password" name="password" required maxlength="128" autocomplete="current-password" placeholder="请输入密码"><button type="button" class="password-toggle" aria-label="显示密码">显示</button></div></div>` : codeField(method === "phone" ? "PHONE" : "EMAIL")}</div>
      ${register ? `<p class="auth-explain">${kind === "EMPLOYEE" ? "员工编号、姓名及联系方式须与机构名册一致。岗位权限由机构预先授权，激活码 48 小时有效。" : "新患者将自动分配账号。如已有就诊档案，请联系诊所核实绑定，避免重复建档。"}</p>${!config.registration_ready ? `<div class="auth-notice">注册流程已就绪；机构尚未配置${!config.sms && !config.email ? "手机与邮箱" : !config.sms ? "手机" : "邮箱"}发送服务，暂不能完成双通道验证。</div>` : ""}<label class="auth-check"><input name="accepted_terms" type="checkbox" required><span>我已阅读并同意<button type="button" class="auth-link" data-privacy>账号使用与隐私说明</button></span></label>` : recover ? notice(channel) : method === "password" ? `<div class="auth-options"><label class="auth-check"><input type="checkbox" id="remember-identifier"><span>记住账号</span></label><a href="#/recover">忘记密码？</a></div>` : notice(method === "phone" ? "PHONE" : "EMAIL")}
      <div id="auth-feedback" role="alert" aria-live="polite"></div><button type="submit" class="auth-submit" ${register && !config.registration_ready ? "disabled" : ""}>${register ? "完成注册" : recover ? "重设密码" : "登 录"}</button></form><div class="auth-bottom">${register || recover ? `<a href="#/login">返回登录</a>` : `还没有账号？<a href="#/register">注册账号</a>`}</div>
      ${!register && !recover && config.demo ? `<div class="auth-review"><button type="button" id="review-demo">进入课程综合演示</button><span>合成数据 · 不代表真实医疗服务</span></div>` : ""}</section><div class="auth-footnote">ADC Nexus · 课程设计系统<span>请勿上传真实患者资料</span></div></main><footer class="auth-footer"><span>安德鲁牙科连锁运营管理系统</span><button type="button" class="auth-link" data-privacy>隐私与账号说明</button></footer></div>`;
    app.querySelectorAll("[data-privacy]").forEach(el => el.onclick = privacy);
    app.querySelectorAll("[data-method]").forEach((el,i) => {
      el.id = "auth-method-" + el.dataset.method;
      el.setAttribute("aria-controls","unified-auth-form");
      el.tabIndex = method === el.dataset.method ? 0 : -1;
      el.onclick = () => { if(pending)return; method = el.dataset.method; paint(); q(`[data-method="${method}"]`).focus({preventScroll:true}); };
      el.onkeydown = e => { let n=i; if(e.key==="ArrowRight"||e.key==="ArrowDown")n=(i+1)%loginMethods.length;else if(e.key==="ArrowLeft"||e.key==="ArrowUp")n=(i+loginMethods.length-1)%loginMethods.length;else if(e.key==="Home")n=0;else if(e.key==="End")n=loginMethods.length-1;else return;e.preventDefault();if(pending)return;method=loginMethods[n][0];paint();q(`[data-method="${method}"]`).focus({preventScroll:true}); };
    });
    if(!register&&!recover){q("#unified-auth-form").setAttribute("role","tabpanel");q("#unified-auth-form").setAttribute("aria-labelledby","auth-method-"+method);}
    app.querySelectorAll("[data-kind]").forEach(el => {el.setAttribute("aria-pressed",String(kind===el.dataset.kind));el.onclick = () => { if(pending)return;kind = el.dataset.kind; Object.keys(challenges).forEach(k => delete challenges[k]); paint();q(`[data-kind="${kind}"]`).focus({preventScroll:true}); };});
    app.querySelectorAll("[data-channel]").forEach(el => {el.setAttribute("aria-pressed",String(channel===el.dataset.channel));el.onclick = () => {if(pending)return; channel = el.dataset.channel; paint();q(`[data-channel="${channel}"]`).focus({preventScroll:true}); };});
    q(".auth-submit").disabled = !available();
    if(register&&!available()&&q(".auth-notice"))q(".auth-notice").textContent=`${!config.sms&&!config.email?"手机与邮箱":!config.sms?"手机":"邮箱"}验证服务尚未开通，暂不能完成注册。已有账号可直接登录。`;
    if(!available()&&q(".auth-notice")){q(".auth-notice").id="auth-channel-notice";q(".auth-submit").setAttribute("aria-describedby","auth-channel-notice");}
    q("[name=confirm]")?.addEventListener("input",e=>e.currentTarget.removeAttribute("aria-invalid"));
    try {const saved = localStorage.getItem("adc-remembered-identifier");if (q("[name=username]") && saved) { q("[name=username]").value = saved; q("#remember-identifier").checked = true; }}catch{/* Remembering an identifier is optional. */}
    app.querySelectorAll(".password-toggle").forEach(el => {
      el.setAttribute("aria-controls","auth-"+(el.dataset.passwordToggle||"password"));
      el.setAttribute("aria-pressed","false");
      el.addEventListener("click", e => {
      const field = q("#auth-"+(el.dataset.passwordToggle||"password")), show = field.type === "password";
      field.type = show ? "text" : "password";
      e.currentTarget.textContent = show ? "隐藏" : "显示";
      e.currentTarget.setAttribute("aria-controls",field.id);
      e.currentTarget.setAttribute("aria-pressed",String(show));
      e.currentTarget.setAttribute("aria-label", (show ? "隐藏" : "显示")+q(`label[for="${field.id}"]`).textContent);
      });
    });
    app.querySelectorAll("[data-send]").forEach(el => el.onclick = async () => {
      const ch = el.dataset.send, name = ch === "PHONE" ? "phone" : "email", field = q(`[name=${name}]`);
      if (!field.reportValidity()) return;
      el.disabled = true;
      try {
        const response = await api("/auth/challenge", {channel: ch, destination: field.value, purpose: register ? "REGISTER" : recover ? "RECOVER" : "LOGIN"});
        if(destroyed||!el.isConnected)return;
        challenges[ch] = {id: response.challenge_id, destination: field.value};
        q("#auth-feedback").innerHTML = `<p class="auth-success">${esc(response.message)}</p>`;
        let seconds = response.retry_after;
        el.textContent = `${seconds} 秒后重发`;
        const interval = setInterval(() => {
          if (!el.isConnected) { clearInterval(interval); timers.delete(interval); return; }
          if (--seconds <= 0) { clearInterval(interval); timers.delete(interval); el.disabled = false; el.textContent = "重新获取"; }
          else el.textContent = `${seconds} 秒后重发`;
        }, 1000);
        timers.add(interval);
      } catch (e) { if(!destroyed&&el.isConnected){q("#auth-feedback").innerHTML = errorBox(e); el.disabled = false;} }
    });
    q("#review-demo")?.addEventListener("click", async e => {
      if(pending)return;
      pending=true;
      e.currentTarget.disabled = true;
      const button=e.currentTarget;
      button.textContent="正在进入演示…";
      try { await api("/auth/demo", {role: "REVIEWER"}); if(!destroyed)await enter(); }
      catch (error) { if(!destroyed&&button.isConnected){q("#auth-feedback").innerHTML = errorBox(error);button.disabled = false;} }
      finally {pending=false;if(button.isConnected)button.textContent="进入课程综合演示";}
    });
    q("#unified-auth-form").onsubmit = submit;
  }
  function privacy() {
    modal({informational: true, name: "账号使用与隐私说明", body: `<div class="prose"><p>本系统为系统分析与设计课程的合成数据演示，不接收真实病历，不执行真实支付划转，也不提供医疗建议。</p><p>注册需验证手机与邮箱归属。员工身份须匹配机构预登记名册与激活码；患者新账号仅能访问绑定本人的档案。既有病历须经机构核实后绑定。</p><p>密码以带盐 PBKDF2 哈希保存；验证码有时效与尝试次数限制，不会通过公共页面显示。访问和业务变更留有审计记录。</p><p>请勿向他人提供密码、验证码或激活码。账号资料更正与停用请联系机构管理员。</p></div>`, submit: "已了解", onSubmit: async () => {}});
  }
  async function submit(e) {
    e.preventDefault();
    if(pending||!available())return;
    const data = Object.fromEntries(new FormData(e.currentTarget)), button = q(".auth-submit");
    q("#auth-feedback").innerHTML = "";
    if ((register || recover) && (data.password || data.new_password) !== data.confirm) {
      q("#auth-feedback").textContent = "两次输入的密码不一致，请核对。";q("[name=confirm]").setAttribute("aria-invalid","true");q("[name=confirm]").focus();return;
    }
    const savedLabel=button.textContent,form=e.currentTarget,remember=q("#remember-identifier")?.checked;
    const methods=[...app.querySelectorAll("[data-method],[data-kind],[data-channel]")];
    pending=true;methods.forEach(el=>el.disabled=true);form.setAttribute("aria-busy","true");
    button.disabled = true;
    button.textContent=register?"正在注册…":recover?"正在更新…":"正在登录…";
    try {
      if (register) {
        const result = await api("/auth/register", {...data, kind, accepted_terms: data.accepted_terms === "on",
          phone_challenge: challenges.PHONE?.id || "", email_challenge: challenges.EMAIL?.id || ""});
        if(destroyed)return;
        app.querySelector(".auth-card").innerHTML = `<div class="auth-card-heading"><h1>注册成功</h1><p>请妥善保存您的账号</p></div><div class="registered-account">${esc(result.username)}</div><p class="auth-explain">可使用此账号、已验证手机号或邮箱登录。密码不会在此页面再次展示。</p><a class="auth-submit auth-login-link" href="#/login">前往登录</a>`;
      } else if (!recover && method === "password") {
        await api("/auth/login", {username: data.username, password: data.password});
        if(destroyed)return;
        try{if (remember) localStorage.setItem("adc-remembered-identifier", data.username);else localStorage.removeItem("adc-remembered-identifier");}catch{/* Password login does not depend on local storage. */}
        await enter();
      } else {
        const ch = recover ? channel : method === "phone" ? "PHONE" : "EMAIL", name = ch === "PHONE" ? "phone" : "email";
        await api(recover ? "/auth/recover" : "/auth/code-login", {channel: ch, destination: data[name], challenge_id: challenges[ch]?.id || "", code: data[name + "_code"], new_password: data.new_password});
        if(destroyed)return;
        if (recover) { paint(); q("#auth-feedback").innerHTML = '<p class="auth-success">密码已更新，原登录会话已失效。请返回登录。</p>'; }
        else await enter();
      }
    } catch (error) { if (!destroyed&&q("#auth-feedback")){q("#auth-feedback").innerHTML = errorBox(error);q("#auth-feedback").setAttribute("tabindex","-1");q("#auth-feedback").focus({preventScroll:true});q("#auth-feedback").scrollIntoView({block:"nearest"});} }
    finally { pending=false;if (button.isConnected){button.disabled = !available();button.textContent=savedLabel;form.removeAttribute("aria-busy");methods.forEach(el=>el.disabled=false);} }
  }
  paint();
  return()=>{destroyed=true;clearTimers();};
}
