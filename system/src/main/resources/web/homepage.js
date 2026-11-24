// Public product information. Illustrations are synthetic; all business permissions stay on the server.
import {createCarousel} from './carousel.js?v=20261120-release';
export const slides = [
  {image:"home-care-v1.png",alt:"医师与成年患者沟通的原创场景图",title:["牙科诊所工作台","从预约到结算"],description:"查看预约和候诊，记录诊疗与收费，并按诊所查看运营情况。",points:["患者档案","临床工作台","诊疗结算"]},
  {image:"home-clinic-v1.png",alt:"牙椅与诊疗设备的原创诊室图",title:["预约日历","按医师或牙椅查看"],description:"先核对排班和可用牙椅，再安排预约。患者到店后，前台可办理签到。",points:["时间轴日程","牙椅安排","预约状态"]},
  {image:"home-reception-v1.png",alt:"前台接待人员协助患者核对预约的原创场景图",title:["诊疗记录","与收费结算"],description:"签署病历并完成诊疗后，收费员核对实际项目、开单并登记收退款。",points:["实际治疗项目","逐项账单","收退款流水"]},
];
const featureItems = [
  {icon:"calendar",label:"预约与排班",title:"预约日历与前台签到",description:"前台可按日期筛选候诊和预约，按医师或牙椅切换日历视图。",bullets:["前一天、今天、后一天快捷切换","医师、状态及患者关键词筛选","改期、取消、未到诊与候补处理"],type:"schedule"},
  {icon:"tooth",label:"接诊与病历",title:"病史、牙位检查和治疗记录",description:"接诊时查看过敏记录，填写检查、治疗和病历。",bullets:["在恒牙牙位图上记录检查所见","治疗计划与本次实际项目区分记录","病历签署、补记与记录追查"],type:"clinical"},
  {icon:"chart",label:"收费与报表",title:"待开单与待收款",description:"从待开单列表核对治疗和金额。按权限登记收款、退款，并打印结算单。",bullets:["按实际治疗项目开具结算单","分次收款、授权退款及原流水追查","诊所经营统计与季度核算"],type:"finance"},
];
const journey = [
  {name:"患者建档",description:"填写姓名、出生日期和联系电话",detail:"保存后生成患者编号。如果找到可能重复的档案，先核对再建档。",facts:["患者编号","联系方式","病史记录"]},
  {name:"安排预约",description:"选择项目、医师和时间",detail:"选好诊所和项目后，查看可安排的医师与牙椅。保存时检查排班、资质和时段冲突。",facts:["医师资质","诊所排班","检查重复预约"]},
  {name:"核实到诊",description:"核对患者身份并签到",detail:"患者到店后，前台核对身份并登记资料变化。签到后，医师可在接诊列表找到这次就诊。",facts:["核对患者身份","登记资料变化","加入候诊名单"]},
  {name:"记录诊疗",description:"填写检查、治疗和病历",detail:"医师核对过敏和病史，记录牙位检查与实际治疗，完成前签署病历。",facts:["病史与过敏","治疗计划与同意","查看病历签名"]},
  {name:"逐项结算",description:"按已完成的治疗开单",detail:"收费员核对实际治疗后开单。分次收款和退款分别登记，可查原始单据。",facts:["查看收费项目与金额","收退款分别留痕","可打印结算单"]},
  {name:"季度核算",description:"按季度核对收入和费用",detail:"财务按季度核对各店的收入、治疗成本和运营费用，保存核定结果。",facts:["核对核算期间","核定与重开","利润与绩效"]},
];
export const rolePreviews = [
  {name:"前台接待",icon:"calendar",title:"预约、建档与到诊登记",description:"核对患者身份，安排预约、改期和候补，登记到诊与资料变化；临床记录由负责医师完成。",menus:["患者建档与维护","预约与改期","到诊核实","候补安排"],boundary:"不开放病历签署及资金登记权限。"},
  {name:"医师",icon:"tooth",title:"接诊、治疗与病历签署",description:"从本人接诊队列进入就诊，检查风险资料，记录牙位观察、治疗计划、患者决定和本次实施。",menus:["接诊队列","风险与牙位观察","方案与本次实施","病历版本与签署"],boundary:"临床写入受负责医师及诊所范围约束。"},
  {name:"收费员",icon:"receipt",title:"开具账单与登记收退款",description:"核对已完成就诊的实际治疗项目，开具结算单，登记分次收款及授权退款，打印结算凭据。",menus:["待开单就诊","逐项结算","分次收款","授权退款与打印"],boundary:"患者身份可用于核对，不开放完整病史和临床写入。"},
  {name:"诊所经理",icon:"building",title:"本店接待、收费与资源管理",description:"办理本店预约、到诊和收费，查看经营统计，安排医师班次、停诊和牙椅资源。",menus:["接待与收费","资源与班次维护","诊所经营统计","候补与复诊"],boundary:"临床记录由负责医师签署，期间核定由总部财务办理。"},
  {name:"总部运营",icon:"users",title:"诊所、人员与服务能力",description:"维护诊所资源、医师任职与资质以及治疗项目目录，查看经营统计和扩张测算。",menus:["诊所与资源","医师任职与资质","治疗项目与收费标准","经营统计与扩张测算"],boundary:"临床签署由负责医师办理，期间核定由总部财务办理。"},
  {name:"总部财务",icon:"wallet",title:"成本、费用与期间核算",description:"核实治疗成本、运营费用及其归属，预检季度核算，保存核定结果和重开记录，审阅利润与激励口径。",menus:["期间核算预检","成本与费用归属","季度核定与重开","绩效口径审阅"],boundary:"收退款由诊所获准岗位登记。"},
];

function preview(type,icon) {
  const scenes={schedule:["reception","前台预约列表"],clinical:["clinical","医师接诊记录"],finance:["billing","收费待办列表"]};
  const [file,caption]=scenes[type];
  const source = `/images/workspace-${file}-hd.png?v=20261121-final`;
  return `<figure class="lp-real-preview"><a href="${source}" target="_blank" rel="noopener" aria-label="${caption}，查看大图（新窗口）"><img src="${source}" alt="${caption}，操作示例" width="2880" height="2000" loading="lazy" decoding="async"></a><figcaption><span>${caption} · 合成数据示例</span><span>点击图片查看大图 ↗</span></figcaption></figure>`;
}

export function renderHomepage({app,esc,icon,config,workspaceHref=null}) {
  let index=0, feature=0, step=0, role=0, destroyed=false;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  document.title="ADC Nexus · 安德鲁牙科连锁运营管理系统";
  document.body.classList.add("public-home");
  const intro=(name,copy)=>`<div class="lp-section-intro"><h2>${name}</h2>${copy?`<p>${copy}</p>`:""}</div>`;
  const nav=(name,id)=>`<a href="#/home/${id}" data-scroll="${id}">${id==='trust'?'资料与权限':name}</a>`;
  app.innerHTML=`<div class="lp"><a class="lp-skip" href="#/home" data-scroll="lp-main">跳至主要内容</a><header class="lp-header"><div class="lp-container lp-header-inner"><a href="#/home" data-scroll="top" class="lp-brand"><img src="/mark.svg" width="38" height="38" alt=""><span>ADC Nexus<small>安德鲁牙科连锁</small></span></a><nav class="lp-desktop-nav" aria-label="首页导航">${nav("产品功能","features")}${nav("业务流程","journey")}${nav("岗位功能","roles")}${nav("资料与权限","trust")}${nav("常见问题","faq")}</nav><div class="lp-header-actions">${workspaceHref?`<a href="${esc(workspaceHref)}" class="lp-button primary compact">进入工作台${icon("arrow")}</a>`:`<a href="#/login" class="lp-button primary compact">登录</a>`}<button type="button" class="lp-nav-toggle" aria-label="展开首页导航" aria-expanded="false">${icon("menu")}</button></div></div><nav class="lp-mobile-nav" aria-label="手机首页导航" hidden>${nav("产品功能","features")}${nav("业务流程","journey")}${nav("岗位功能","roles")}${nav("资料与权限","trust")}${nav("常见问题","faq")}</nav></header><main id="lp-main"><section class="lp-hero" id="top" role="region" aria-roledescription="轮播" aria-label="ADC Nexus 产品场景"><div class="lp-hero-images">${slides.map((s,i)=>`<img src="/images/${s.image}" alt="${i===1?"原创诊室空间示意图":"原创医患沟通场景示意图"}" class="lp-hero-image ${i===0?"active":""}" ${i===0?'fetchpriority="high"':'loading="lazy"'} aria-hidden="${i!==0}">`).join("")}</div><div class="lp-hero-veil"></div><div class="lp-container lp-hero-inner"><div class="lp-hero-copy"><h1 id="lp-slide-title"></h1><p id="lp-slide-description"></p><div class="lp-hero-actions"><a class="lp-button primary" href="${esc(workspaceHref||'#/login')}">${workspaceHref?"进入我的工作台":"登录工作台"}${icon("arrow")}</a><a class="lp-button secondary" data-scroll="journey" href="#/home/journey">了解业务流程</a></div><ul id="lp-slide-points" class="lp-hero-points"></ul></div></div><div class="lp-hero-bottom lp-container"><a class="lp-scroll-hint" href="#/home/features" data-scroll="features">向下了解${icon("chevron")}</a><div class="lp-carousel-controls"><button type="button" data-slide-prev aria-label="上一张场景">${icon("chevron")}</button><span class="lp-slide-number" aria-live="off">01 <i>/ 03</i></span><div class="lp-slide-dots">${slides.map((_,i)=>`<button type="button" data-slide="${i}" aria-label="查看第 ${i+1} 张场景" aria-pressed="${i===0}"><span></span></button>`).join("")}</div><button type="button" data-slide-next aria-label="下一张场景">${icon("chevron")}</button><button class="lp-play-toggle" type="button" aria-label="暂停自动轮播"><span aria-hidden="true">Ⅱ</span></button></div></div></section>
  <section class="lp-foundation"><div class="lp-container lp-foundation-inner"><div><h2>接待、诊疗与经营管理</h2></div><div class="lp-work-links">${[["calendar","预约日程","医师 / 牙椅 / 到诊"],["tooth","临床接诊","病史 / 牙位 / 病历"],["receipt","收费结算","项目 / 收款 / 退款"]].map(([i,a,b],featureIndex)=>`<a href="#/home/features" data-scroll="features" data-feature-target="${featureIndex}">${icon(i)}<span><strong>${a}</strong><small>${b}</small></span>${icon('chevron')}</a>`).join('')}</div></div></section>
  <section class="lp-section lp-features" id="features"><div class="lp-container">${intro("主要功能","")}<div class="lp-feature-layout"><div class="lp-feature-tabs" role="tablist" aria-label="产品能力">${featureItems.map((f,i)=>`<button id="lp-feature-tab-${i}" role="tab" type="button" data-feature="${i}" aria-controls="lp-feature-panel" aria-selected="${i===0}" tabindex="${i===0?0:-1}"><span class="lp-feature-icon">${icon(f.icon)}</span><span><strong>${f.label}</strong><small>${["预约、到诊与资源安排","患者风险、方案与病历","结算、收退款与经营统计"][i]}</small></span>${icon("chevron")}</button>`).join("")}</div><div id="lp-feature-panel" role="tabpanel" aria-labelledby="lp-feature-tab-0"></div></div></div></section>
  <section class="lp-section lp-journey" id="journey"><div class="lp-container">${intro("就诊流程","从建档、预约到结算。")}<div class="lp-journey-tabs" role="tablist" aria-label="业务流程步骤">${journey.map((s,i)=>`<button id="lp-journey-tab-${i}" type="button" data-step="${i}" role="tab" aria-controls="lp-journey-panel" aria-selected="${i===0}" tabindex="${i===0?0:-1}"><span>0${i+1}</span><strong>${s.name}</strong></button>`).join("")}</div><div id="lp-journey-panel" role="tabpanel" aria-labelledby="lp-journey-tab-0"></div></div></section>
  <section class="lp-section lp-roles" id="roles"><div class="lp-container">${intro("岗位功能","按岗位查看常用操作。")}<div class="lp-role-tabs" role="tablist" aria-label="岗位预览">${rolePreviews.map((r,i)=>`<button id="lp-role-tab-${i}" type="button" data-role="${i}" role="tab" aria-controls="lp-role-panel" aria-selected="${i===0}" tabindex="${i===0?0:-1}">${r.name}</button>`).join("")}</div><div id="lp-role-panel" role="tabpanel" aria-labelledby="lp-role-tab-0"></div></div></section>
  <section class="lp-section lp-trust" id="trust"><div class="lp-container lp-trust-grid"><figure class="lp-clinic-photo"><img src="/images/home-reception-v1.png" alt="牙科诊所前台接待原创示意图" loading="lazy"><figcaption>前台接待场景</figcaption></figure><div class="lp-trust-copy">${intro("资料与权限","查看资料和办理业务时，系统同时检查岗位权限和诊所授权。")}<div class="lp-trust-items">${[["shield","岗位与诊所授权","员工只能查看授权范围内的资料。诊疗记录由负责医师填写和签署。"],["file","变更与流水可追查","获准员工可查预约改期、病历补记以及收款、退款的原始记录。"]].map(([i,a,b])=>`<article><span>${icon(i)}</span><div><h3>${a}</h3><p>${b}</p></div></article>`).join("")}</div></div></div></section>
  <section class="lp-section lp-faq" id="faq"><div class="lp-container lp-faq-grid">${intro("账号与访问","了解员工登录、账号激活和权限范围。")}<div class="lp-faq-items">${[
    ["如何登录？是否需要先选择职位？","诊所员工使用同一个登录窗口。可用账号、已验证的手机号或邮箱加密码登录。开通相应服务后，也可用验证码登录。"],
    ["员工怎样激活账号？","员工须提供机构预登记的编号、姓名和联系方式，领取激活码并验证手机号和邮箱。当前"+(config.registration_ready?"可以获取验证码。":"验证码服务尚未开通。已有账号可用密码登录。")],
    ["为什么不同账号看到的内容不同？","网页工作台按内部岗位及诊所授权显示功能。医师可处理由本人负责的就诊。患者服务规划通过微信小程序提供。"],
    ["系统可以发起付款吗？","收费模块用于开单及登记已发生的收款或退款。患者实际付款通过诊所的收款方式完成。"],
    ...(/^(localhost|127\.0\.0\.1)$/.test(location.hostname) ? [["本地链接无法连接时怎么办？","打开桌面 ADC 文件夹，双击 ADC Nexus - Start。看到 ONLINE 后刷新网页。"]] : [])
  ].map(([a,b])=>`<details><summary>${a}<span>+</span></summary><p>${b}</p></details>`).join("")}</div></div></section>
  <section class="lp-final"><div class="lp-container"><div><h2>登录 ADC Nexus</h2></div><div class="lp-final-actions"><a href="${esc(workspaceHref||'#/login')}" class="lp-button primary">${workspaceHref?"进入工作台":"登录工作台"}${icon("arrow")}</a>${workspaceHref ? "" : config.demo ? `<a class="lp-button secondary" href="#/login">查看演示账号</a>` : `<a class="lp-button secondary" href="#/register">激活员工账号</a>`}</div></div></section></main><footer class="lp-footer"><div class="lp-container"><div class="lp-footer-top"><a class="lp-brand" href="#/home" data-scroll="top"><img src="/mark.svg" alt="" width="36" height="36"><span>ADC Nexus<small>安德鲁牙科连锁运营管理系统</small></span></a><div>${nav("产品功能","features")}${nav("业务流程","journey")}${nav("岗位功能","roles")}${nav("账号与使用说明","faq")}</div></div><div class="lp-footer-bottom"><span>© ${new Date().getFullYear()} ADC Nexus · 安德鲁牙科连锁</span><span>诊所管理系统</span></div></div></footer><button class="lp-back-top" type="button" aria-label="返回页面顶部" hidden>${icon("arrow")}</button></div>`;
  const q=s=>app.querySelector(s);
  const qa=s=>[...app.querySelectorAll(s)];
  q('.lp-carousel-controls').insertAdjacentHTML('beforeend','<span class="lp-sr-only" data-slide-announcement role="status" aria-live="polite"></span>');
  qa('.lp-work-links>a').forEach((a,i)=>a.dataset.featureTarget=String(i));
  function select(group,id,panel,prefix) {
    qa(`[data-${group}]`).forEach((b,i)=>{b.setAttribute('aria-selected',i===id);b.tabIndex=i===id?0:-1;});
    q(panel).setAttribute('aria-labelledby',`${prefix}-${id}`);
  }
  function paintSlide() {
    const s=slides[index];

    q('#lp-slide-title').innerHTML=s.title.map(x=>`<span>${esc(x)}</span>`).join('');
    q('#lp-slide-description').textContent=s.description;
    q('#lp-slide-points').innerHTML=s.points.map(x=>`<li>${icon('check')}${esc(x)}</li>`).join('');
    qa('.lp-hero-image').forEach((el,i)=>{el.classList.toggle('active',i===index);el.setAttribute('aria-hidden',i!==index);});
    qa('[data-slide]').forEach((el,i)=>el.setAttribute('aria-pressed',i===index));
    q('.lp-slide-number').innerHTML=`0${index+1} <i>/ 03</i>`;
  }
  const carousel=createCarousel({count:slides.length,onChange:n=>{index=n;paintSlide();},onState:paintPause});
  function moveSlide(n){carousel.move(n);q('[data-slide-announcement]').textContent=`第 ${index+1} 张，共 ${slides.length} 张。${slides[index].title.join('')}`;}
  function paintFeature(){const f=featureItems[feature];select('feature',feature,'#lp-feature-panel','lp-feature-tab');q('#lp-feature-panel').innerHTML=`<div class="lp-feature-copy"><h3>${f.title}</h3><p>${f.description}</p><ul>${f.bullets.map(x=>`<li>${icon('check')}${x}</li>`).join('')}</ul></div><div class="lp-product-preview">${preview(f.type,icon)}</div>`;}
  function paintStep(){const s=journey[step];select('step',step,'#lp-journey-panel','lp-journey-tab');q('#lp-journey-panel').innerHTML=`<div class="lp-step-number">0${step+1}</div><div class="lp-step-copy"><span>${s.name}</span><h3>${s.description}</h3><p>${s.detail}</p></div><ul>${s.facts.map(x=>`<li>${icon('check')}${x}</li>`).join('')}</ul>`;}
  function paintRole(){const r=rolePreviews[role];select('role',role,'#lp-role-panel','lp-role-tab');q('#lp-role-panel').innerHTML=`<div class="lp-role-copy"><span class="lp-role-symbol">${icon(r.icon)}</span><h3>${r.title}</h3><p>${r.description}</p><a class="lp-text-link" href="${esc(workspaceHref||'#/login')}">从统一入口登录${icon('arrow')}</a></div><div class="lp-role-preview"><div class="lp-role-preview-heading"><span>${icon('shield')} ${r.name}工作空间</span><small>岗位职责示意</small></div>${r.menus.map((m,i)=>`<div class="lp-menu-preview"><span>0${i+1}</span><strong>${m}</strong>${icon('chevron')}</div>`).join('')}<p>${icon('lock')}${r.boundary}</p></div>`;}
  function tabKeys(group,callback){qa(`[data-${group}]`).forEach((el,i)=>{el.addEventListener('keydown',e=>{let n=i;if(e.key==='ArrowRight'||e.key==='ArrowDown')n=(i+1)%qa(`[data-${group}]`).length;else if(e.key==='ArrowLeft'||e.key==='ArrowUp')n=(i-1+qa(`[data-${group}]`).length)%qa(`[data-${group}]`).length;else if(e.key==='Home')n=0;else if(e.key==='End')n=qa(`[data-${group}]`).length-1;else return;e.preventDefault();callback(n);qa(`[data-${group}]`)[n].focus();});});}
  qa('[data-feature]').forEach((b,i)=>b.onclick=()=>{feature=i;paintFeature();});
  qa('[data-step]').forEach((b,i)=>b.onclick=()=>{step=i;paintStep();});
  qa('[data-role]').forEach((b,i)=>b.onclick=()=>{role=i;paintRole();});
  tabKeys('feature',n=>{feature=n;paintFeature();});tabKeys('step',n=>{step=n;paintStep();});tabKeys('role',n=>{role=n;paintRole();});
  q('[data-slide-prev]').onclick=()=>moveSlide(index-1);q('[data-slide-next]').onclick=()=>moveSlide(index+1);
  qa('[data-slide]').forEach((b,i)=>b.onclick=()=>moveSlide(i));
  const play=q('.lp-play-toggle');
  let paused=false;
  function paintPause(s){paused=s.paused;play.disabled=s.reduced;play.setAttribute('aria-label',s.reduced?'减少动态效果已开启，自动轮播关闭':s.paused?'开启自动轮播':'暂停自动轮播');play.setAttribute('aria-pressed',String(s.paused));play.innerHTML=`<span aria-hidden="true">${s.paused||s.reduced?'▷':'Ⅱ'}</span>`;}
  play.onclick=()=>carousel.pause(!paused);
  // Pointer hover and mouse focus do not silently disable playback. Keyboard readers can pause explicitly.
  const visibility=()=>carousel.visibility(document.hidden);document.addEventListener('visibilitychange',visibility);
  const reduceChanged=()=>carousel.reduced(reduced.matches);reduced.addEventListener('change',reduceChanged);
  const mobile=q('.lp-mobile-nav'), toggle=q('.lp-nav-toggle');toggle.onclick=()=>{mobile.hidden=!mobile.hidden;toggle.setAttribute('aria-expanded',!mobile.hidden);toggle.setAttribute('aria-label',mobile.hidden?'展开首页导航':'收起首页导航');};
  const closeMobile=()=>{mobile.hidden=true;toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-label','展开首页导航');};
  const mobileKeys=e=>{if(e.key==='Escape'&&!mobile.hidden){e.preventDefault();closeMobile();toggle.focus();}};q('.lp-header').addEventListener('keydown',mobileKeys);
  qa('[data-scroll]').forEach(a=>a.addEventListener('click',e=>{const target=q('#'+a.dataset.scroll);if(target){e.preventDefault();if(a.dataset.featureTarget!==undefined){feature=Number(a.dataset.featureTarget);paintFeature();}closeMobile();target.tabIndex=-1;target.focus({preventScroll:true});target.scrollIntoView({behavior:reduced.matches?'instant':'smooth',block:'start'});history.replaceState(null,'',a.getAttribute('href'));}}));
  const headerLinks=qa('.lp-header nav [data-scroll]');
  const sections=qa('main .lp-section[id]');
  let currentSection;
  const onScroll=()=>{
    q('.lp-back-top').hidden=scrollY<700;
    q('.lp-header').classList.toggle('scrolled',scrollY>24);
    const top=innerHeight*.31;
    const section=sections.findLast(el=>el.getBoundingClientRect().top<=top)?.id;
    if(section===currentSection) return;
    currentSection=section;
    for(const link of headerLinks) {
      if(link.dataset.scroll===section) link.setAttribute('aria-current','location');
      else link.removeAttribute('aria-current');
    }
  };
  window.addEventListener('scroll',onScroll,{passive:true});
  window.addEventListener('resize',onScroll);
  q('.lp-back-top').onclick=()=>scrollTo({top:0,behavior:reduced.matches?'instant':'smooth'});
  qa('.lp-hero-image').forEach((img,i)=>img.alt=slides[i].alt);
  paintSlide();paintFeature();paintStep();paintRole();carousel.reduced(reduced.matches);visibility();onScroll();
  const section=location.hash.replace(/^#\/?/,'').split('/')[1];
  requestAnimationFrame(()=>{if(destroyed)return;if(["features","journey","roles","trust","faq"].includes(section))q('#'+section)?.scrollIntoView({block:'start'});else scrollTo({top:0,behavior:'instant'});});
  return ()=>{destroyed=true;carousel.dispose();document.body.classList.remove('public-home');document.removeEventListener('visibilitychange',visibility);window.removeEventListener('scroll',onScroll);window.removeEventListener('resize',onScroll);reduced.removeEventListener('change',reduceChanged);};
}
