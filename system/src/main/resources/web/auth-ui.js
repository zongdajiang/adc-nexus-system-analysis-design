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
export function renderAuthPage({ app, config, api, enter, esc, icon, errorBox, modal }) {
  const route = location.hash.split("/")[1];
  const register = route === "register", recover = route === "recover";
  let method = "password", channel = "PHONE", pending = false, destroyed = false;
  const accounts=Array.isArray(config.demo_accounts)?config.demo_accounts:[];
  const showDemo=!register&&!recover&&config.demo===true&&accounts.length>0;
  const accountRow=(account,index)=>`<div class="auth-credential-row">
    <div><strong>${esc(account.name)}<span> · ${esc(account.person_name)}</span></strong><code id="demo-account-${index}">${esc(account.username)}</code></div>
    <button type="button" class="auth-copy" data-copy-account="${index}" aria-label="复制${esc(account.person_name)}的账号">复制账号</button>
  </div>`;
  const demo=()=>`<section class="auth-demo-accounts" aria-labelledby="demo-accounts-title">
    <div class="auth-directory-heading"><h2 id="demo-accounts-title">演示账号</h2><p>复制账号和密码，在上方登录。</p></div>
    <div class="auth-credential-list">${accounts.slice(0,2).map(accountRow).join('')}</div>
    <div class="auth-demo-password"><div><span>通用密码</span><code id="demo-password-value">${esc(config.demo_password)}</code></div><button type="button" class="auth-copy" data-copy-password aria-label="复制演示密码">复制密码</button></div>
    ${accounts.length>2?`<details class="auth-other-accounts"><summary>其他岗位账号<span>${accounts.length-2}</span></summary><div class="auth-credential-list">${accounts.slice(2).map((a,i)=>accountRow(a,i+2)).join('')}</div></details>`:''}
    <p id="demo-copy-status" class="auth-copy-status" role="status" aria-live="polite"></p>
  </section>`;
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
    document.title = `${register ? "员工激活" : recover ? "找回密码" : "员工登录"} · ADC Nexus`;
    app.innerHTML = `<div class="auth-layout"><header class="auth-header"><a class="auth-brand" href="#/home"><img src="/mark.svg" alt="" width="34" height="34"><span>ADC Nexus<small>安德鲁牙科连锁</small></span></a><a class="auth-header-note" href="#/home">返回首页</a></header><main class="auth-main auth-main-simple auth-main-centered"><section class="auth-card ${register ? "registration-card" : ""}" aria-labelledby="auth-title"><div class="auth-card-heading"><img src="/mark.svg" alt="" width="42" height="42"><h1 id="auth-title">${register ? "员工激活" : recover ? "找回密码" : "员工登录"}</h1><p>${register ? "请使用诊所预登记的员工资料" : recover ? "使用已验证的手机号或邮箱重设密码" : ""}</p></div>
      ${register ? "" : recover ? `<div class="auth-segment" aria-label="验证方式"><button type="button" data-channel="PHONE" class="${channel === "PHONE" ? "selected" : ""}">手机验证</button><button type="button" data-channel="EMAIL" class="${channel === "EMAIL" ? "selected" : ""}">邮箱验证</button></div>` : `<div class="auth-methods" role="tablist" aria-label="登录方式">${[["password","密码登录"],["phone","手机验证码"],["email","邮箱验证码"]].map(([v,label]) => `<button role="tab" type="button" aria-selected="${method === v}" data-method="${v}" class="${method === v ? "selected" : ""}">${label}</button>`).join("")}</div>`}
      <form id="unified-auth-form"><div class="auth-fields ${register ? "two-column" : ""}">${register ? `${input("name","真实姓名","text",'maxlength="60" autocomplete="name"')}${input("employee_id","内部员工编号","text",'placeholder="ADC-DR-000001" pattern="ADC-(FD|DR|CS|MG|OP|FN|AD)-[0-9]{6}" maxlength="13"')}${input("activation_code","机构激活码","text",'autocomplete="off" placeholder="向机构管理员领取"')}${codeField("PHONE")}${codeField("EMAIL")}${input("password","设置密码","password",'minlength="12" maxlength="128" autocomplete="new-password" placeholder="12–128 位，建议使用长密码"')}${input("confirm","确认密码","password",'minlength="12" maxlength="128" autocomplete="new-password"')}` : recover ? codeField(channel) + input("new_password","新密码","password",'minlength="12" maxlength="128" autocomplete="new-password"') + input("confirm","确认新密码","password",'minlength="12" maxlength="128" autocomplete="new-password"') : method === "password" ? input("username","账号 / 手机号 / 邮箱","text",'maxlength="254" autocomplete="username" placeholder="请输入账号或已验证的联系方式"') + `<div class="auth-field"><label for="auth-password">密码</label><div class="password-input"><input id="auth-password" type="password" name="password" required maxlength="128" autocomplete="current-password" placeholder="请输入密码"><button type="button" class="password-toggle" aria-label="显示密码">显示</button></div></div>` : codeField(method === "phone" ? "PHONE" : "EMAIL")}</div>
      ${register ? `<p class="auth-explain">请使用登记在诊所名册上的姓名和联系方式。激活码有效期为 48 小时。</p>${!config.registration_ready ? `<div class="auth-notice">诊所尚未开通${!config.sms && !config.email ? "手机与邮箱" : !config.sms ? "手机" : "邮箱"}验证码，暂不能注册。</div>` : ""}<label class="auth-check"><input name="accepted_terms" type="checkbox" required><span>我已阅读并同意<button type="button" class="auth-link" data-privacy>账号使用与隐私说明</button></span></label>` : recover ? notice(channel) : method === "password" ? `<div class="auth-options"><label class="auth-check"><input type="checkbox" id="remember-identifier"><span>记住账号</span></label><a href="#/recover">忘记密码？</a></div>` : notice(method === "phone" ? "PHONE" : "EMAIL")}
      <div id="auth-feedback" role="alert" aria-live="polite"></div><button type="submit" class="auth-submit" ${register && !config.registration_ready ? "disabled" : ""}>${register ? "完成注册" : recover ? "重设密码" : "登录"}</button></form><div class="auth-bottom">${register || recover ? `<a href="#/login">返回登录</a>` : `<a href="#/register">激活员工账号</a>`}</div>
      </section>${showDemo ? demo() : ""}</main><footer class="auth-footer"><span>安德鲁牙科连锁运营管理系统</span><button type="button" class="auth-link" data-privacy>隐私与账号说明</button></footer></div>`;
    app.querySelectorAll("[data-privacy]").forEach(el => el.onclick = privacy);
    app.querySelectorAll("[data-method]").forEach((el,i) => {
      el.id = "auth-method-" + el.dataset.method;
      el.setAttribute("aria-controls","unified-auth-form");
      el.tabIndex = method === el.dataset.method ? 0 : -1;
      el.onclick = () => { if(pending)return; method = el.dataset.method; paint(); q(`[data-method="${method}"]`).focus({preventScroll:true}); };
      el.onkeydown = e => { let n=i; if(e.key==="ArrowRight"||e.key==="ArrowDown")n=(i+1)%loginMethods.length;else if(e.key==="ArrowLeft"||e.key==="ArrowUp")n=(i+loginMethods.length-1)%loginMethods.length;else if(e.key==="Home")n=0;else if(e.key==="End")n=loginMethods.length-1;else return;e.preventDefault();if(pending)return;method=loginMethods[n][0];paint();q(`[data-method="${method}"]`).focus({preventScroll:true}); };
    });
    if(!register&&!recover){q("#unified-auth-form").setAttribute("role","tabpanel");q("#unified-auth-form").setAttribute("aria-labelledby","auth-method-"+method);}
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
    app.querySelectorAll('[data-copy-account],[data-copy-password]').forEach(button=>button.onclick=async()=>{
      const isPassword=button.hasAttribute('data-copy-password');
      const index=Number(button.dataset.copyAccount);
      const value=isPassword?config.demo_password:accounts[index]?.username;
      if(typeof value!=='string')return;
      const original=button.textContent;
      const status=q('#demo-copy-status');
      try {
        if(!navigator.clipboard?.writeText)throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(value);
      } catch {
        const node=q(isPassword?'#demo-password-value':'#demo-account-'+index);
        const selection=window.getSelection(),range=document.createRange();
        range.selectNodeContents(node);selection.removeAllRanges();selection.addRange(range);
        if(!document.execCommand('copy')){status.textContent='已选中文本，请按 Ctrl+C 或长按复制。';return;}
      }
      if(destroyed||!button.isConnected)return;
      button.textContent='已复制';
      status.textContent=isPassword?'密码已复制。':'账号已复制。';
      const timer=setTimeout(()=>{timers.delete(timer);if(button.isConnected)button.textContent=original;},2000);timers.add(timer);
    });
    q("#unified-auth-form").onsubmit = submit;
  }
  function privacy() {
    modal({informational: true, name: "账号使用与隐私说明", body: `<div class="prose"><p>本系统为系统分析与设计课程的合成数据演示，不接收真实病历，不执行真实支付划转，也不提供医疗建议。</p><p>员工激活需验证手机与邮箱，并核对机构预登记名册和激活码。患者端规划通过微信小程序提供服务。</p><p>密码以带盐 PBKDF2 哈希保存；验证码有时效与尝试次数限制，不会通过公共页面显示。访问和业务变更留有审计记录。</p><p>请勿向他人提供密码、验证码或激活码。账号资料更正与停用请联系机构管理员。</p></div>`, submit: "已了解", onSubmit: async () => {}});
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
    const methods=[...app.querySelectorAll("[data-method],[data-channel]")];
    pending=true;methods.forEach(el=>el.disabled=true);form.setAttribute("aria-busy","true");
    button.disabled = true;
    button.textContent=register?"正在注册…":recover?"正在更新…":"正在登录…";
    try {
      if (register) {
        const result = await api("/auth/register", {...data, kind: "EMPLOYEE", accepted_terms: data.accepted_terms === "on",
          phone_challenge: challenges.PHONE?.id || "", email_challenge: challenges.EMAIL?.id || ""});
        if(destroyed)return;
        app.querySelector(".auth-card").innerHTML = `<div class="auth-card-heading"><h1>注册成功</h1><p>请妥善保存您的账号</p></div><div class="registered-account">${esc(result.username)}</div><p class="auth-explain">可以用账号、已验证的手机号或邮箱登录。</p><a class="auth-submit auth-login-link" href="#/login">前往登录</a>`;
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
