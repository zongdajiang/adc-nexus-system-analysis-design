// Public product information. Illustrations are synthetic; all business permissions stay on the server.
import {createCarousel} from './carousel.js?v=1.4.0-rc1';
export const slides = [
  {image:"home-care-v1.png",alt:"医师与成年患者沟通的原创场景图",tag:"ADC Nexus · 牙科诊所管理",title:["从患者到诊，","到安心离院。"],description:"为前台、医师和收费岗位提供日常工作入口，集中管理患者档案、诊疗记录与费用。",points:["患者档案","临床工作台","诊疗结算"]},
  {image:"home-clinic-v1.png",alt:"牙椅与诊疗设备的原创诊室图",tag:"预约与排班",title:["看日程，也看","医师与牙椅。"],description:"按医师或牙椅查看当日预约，处理到诊、取消和改期；保存前检查人员资质、班次与资源冲突。",points:["时间轴日程","牙椅安排","预约状态"]},
  {image:"home-reception-v1.png",alt:"前台接待人员协助患者核对预约的原创场景图",tag:"接待与服务",title:["从核对预约，","到本次结算。"],description:"前台登记患者到诊，医师记录本次治疗，收费员核对项目与金额。患者登录后可查看本人预约和账单。",points:["到诊登记","逐项账单","患者查询"]},
];
const featureItems = [
  {icon:"calendar",label:"预约与排班",title:"接待队列与预约日程，分别处理",description:"门诊工作台集中查看待到诊、待接诊与诊疗交接；时间表按医师或牙椅排列，保存前核对人员、时段和资源。",bullets:["前一天、今天、后一天快捷切换","医师、状态及患者关键词筛选","改期、取消、未到诊与候补处理"],type:"schedule"},
  {icon:"tooth",label:"接诊与病历",title:"风险在眼前，记录按接诊顺序展开",description:"患者身份与过敏提示始终可见。风险、检查、方案、实施和病历分区填写，完成前明确列出服务端待核验项。",bullets:["32 个 FDI 恒牙牙位记录入口","治疗计划与本次实际项目区分记录","病历签署、版本与附理由补记"],type:"clinical"},
  {icon:"chart",label:"收费与报表",title:"待开单与待收款，不再逐条翻找",description:"已完成但未开单的就诊形成独立工作清单；从患者直接进入开单核对，再处理未收余额、分次收款与退款。",bullets:["逐项结算单与打印凭据","分次收款、授权退款及原流水追查","诊所经营统计与季度核算"],type:"finance"},
];
const journey = [
  {name:"患者建档",description:"先核实身份，再建立连续资料。",detail:"统一患者编号，区分未知病史和已核实声明。可能重复的身份需要机构人工核实。",facts:["稳定患者身份","联系方式与风险资料","追加病史版本"]},
  {name:"安排预约",description:"服务时间与资源一起确认。",detail:"预约指向患者、诊所、牙医及服务时段。分配牙椅后检查占用，改期与候补也会重新核验。",facts:["资质与任职有效","班次与服务日期","并发冲突保护"]},
  {name:"核实到诊",description:"到诊事实与预约信息对应。",detail:"核对患者身份、风险与资料变化，再建立对应就诊。不把预约建立或时间到达视为患者已经到诊。",facts:["本人身份核对","资料变化声明","唯一关联就诊"]},
  {name:"记录诊疗",description:"观察、方案与实施各有依据。",detail:"医师处理本人负责的就诊，记录风险复核、牙位、计划、患者决定和实施，并在完成前核对签署条件。",facts:["负责医师权限","患者决定与同意","不可变签署版本"]},
  {name:"逐项结算",description:"收费以实际服务为依据。",detail:"已完成就诊产生结算项目，收款和退款保留独立流水。结清状态由净收款重算，不能覆盖原始凭据。",facts:["金额以整数分存储","收退款分别留痕","可打印结算单"]},
  {name:"期间复核",description:"季度结束后，再看经营全貌。",detail:"期间核算不是每次就诊后立即执行。财务核实成本及费用归属，保存核定快照，按明确口径审阅绩效。",facts:["未到期阻断关闭","核定快照与重开记录","利润与激励分别说明"]},
];
export const rolePreviews = [
  {name:"前台接待",icon:"calendar",title:"预约、建档与到诊登记",description:"核对患者身份，安排预约、改期和候补，登记到诊与资料变化；临床记录由负责医师完成。",menus:["患者建档与维护","预约与改期","到诊核实","候补安排"],boundary:"不开放病历签署及资金登记权限。"},
  {name:"医师",icon:"tooth",title:"接诊、治疗与病历签署",description:"从本人接诊队列进入就诊，检查风险资料，记录牙位观察、治疗计划、患者决定和本次实施。",menus:["接诊队列","风险与牙位观察","方案与本次实施","病历版本与签署"],boundary:"临床写入受负责医师及诊所范围约束。"},
  {name:"收费员",icon:"receipt",title:"开具账单与登记收退款",description:"核对已完成就诊的实际治疗项目，开具结算单，登记分次收款及授权退款，打印结算凭据。",menus:["待开单就诊","逐项结算","分次收款","授权退款与打印"],boundary:"患者身份可用于核对，不开放完整病史和临床写入。"},
  {name:"诊所经理",icon:"building",title:"本店日程与资源管理",description:"查看本店业务与经营统计，维护医师班次、停诊和牙椅状态。影响既有预约的变更须先处理冲突。",menus:["本店运营总览","资源与班次维护","诊所经营统计","服务能力协调"],boundary:"经理身份不默认获得收款及病历签署权。"},
  {name:"总部运营",icon:"users",title:"诊所、人员与服务能力",description:"维护全网诊所资源和医师任职、资质，查看绩效指标；扩张情景单独测算，不写入真实业务。",menus:["全网业务概览","医师任职与资质","诊所与资源","绩效及扩张情景"],boundary:"不默认获得财务核定或临床签署权限。"},
  {name:"总部财务",icon:"wallet",title:"成本、费用与期间核算",description:"核实治疗成本、运营费用及其归属，预检季度核算，保存核定结果和重开记录，审阅利润与激励口径。",menus:["期间核算预检","成本与费用归属","季度核定与重开","绩效口径审阅"],boundary:"财务身份不自动授予诊疗或现金收款操作。"},
  {name:"患者本人",icon:"heart",title:"我的预约、就诊与账单",description:"查看经核实绑定的本人预约、就诊摘要及账单。当前不开放患者自行改期；需要调整时联系诊所。",menus:["我的预约","本人就诊摘要","本人诊疗账单","账号安全"],boundary:"不能通过输入他人编号查询其他患者。"},
];

function preview(type,icon) {
  const scenes={schedule:["reception","门诊工作台：按服务日期查看接待与交接"],clinical:["clinical","临床工作区：风险、检查、方案、实施及病历分区"],finance:["billing","结算工作清单：待开单、待收款与单据追查"]};
  const [file,caption]=scenes[type];
  return `<figure class="lp-real-preview"><a href="/images/workspace-${file}-v14.jpg" target="_blank" rel="noopener" aria-label="${caption}，查看大图（新窗口）"><img src="/images/workspace-${file}-v14.jpg" alt="${caption}，本地合成环境实际界面" loading="lazy"></a><figcaption><span>${caption} · 合成数据界面</span><span>点击图片查看大图 ↗</span></figcaption></figure>`;
}

export function renderHomepage({app,esc,icon,config,workspaceHref=null,onDemo}) {
  let index=0, feature=0, step=0, role=0, destroyed=false;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  document.title="ADC Nexus · 安德鲁牙科连锁运营管理系统";
  document.body.classList.add("public-home");
  const intro=(label,name,copy)=>`<div class="lp-section-intro"><span class="lp-kicker">${label}</span><h2>${name}</h2><p>${copy}</p></div>`;
  const nav=(name,id)=>`<a href="#/home/${id}" data-scroll="${id}">${id==='trust'?'资料与权限':name}</a>`;
  app.innerHTML=`<div class="lp"><a class="lp-skip" href="#/home" data-scroll="lp-main">跳至主要内容</a><header class="lp-header"><div class="lp-container lp-header-inner"><a href="#/home" data-scroll="top" class="lp-brand"><img src="/mark.svg" width="38" height="38" alt=""><span>ADC Nexus<small>安德鲁牙科连锁</small></span></a><nav class="lp-desktop-nav" aria-label="首页导航">${nav("产品功能","features")}${nav("业务流程","journey")}${nav("岗位空间","roles")}${nav("设计与边界","trust")}${nav("常见问题","faq")}</nav><div class="lp-header-actions">${workspaceHref?`<a href="${esc(workspaceHref)}" class="lp-button primary compact">进入工作台${icon("arrow")}</a>`:`<a href="#/login" class="lp-login-link">登录</a><a href="#/register" class="lp-button primary compact">注册账号</a>`}<button type="button" class="lp-nav-toggle" aria-label="展开首页导航" aria-expanded="false">${icon("menu")}</button></div></div><nav class="lp-mobile-nav" aria-label="手机首页导航" hidden>${nav("产品功能","features")}${nav("业务流程","journey")}${nav("岗位空间","roles")}${nav("设计与边界","trust")}${nav("常见问题","faq")}</nav></header><main id="lp-main"><section class="lp-hero" id="top" role="region" aria-roledescription="轮播" aria-label="ADC Nexus 产品场景"><div class="lp-hero-images">${slides.map((s,i)=>`<img src="/images/${s.image}" alt="${i===1?"原创诊室空间示意图":"原创医患沟通场景示意图"}" class="lp-hero-image ${i===0?"active":""}" ${i===0?'fetchpriority="high"':'loading="lazy"'} aria-hidden="${i!==0}">`).join("")}</div><div class="lp-hero-veil"></div><div class="lp-container lp-hero-inner"><div class="lp-hero-copy"><div class="lp-hero-tag"><i></i><span id="lp-slide-tag"></span></div><h1 id="lp-slide-title"></h1><p id="lp-slide-description"></p><div class="lp-hero-actions"><a class="lp-button primary" href="${esc(workspaceHref||'#/login')}">${workspaceHref?"进入我的工作台":"登录工作台"}${icon("arrow")}</a><a class="lp-button secondary" data-scroll="journey" href="#/home/journey">了解业务流程</a></div><ul id="lp-slide-points" class="lp-hero-points"></ul></div></div><div class="lp-hero-bottom lp-container"><a class="lp-scroll-hint" href="#/home/features" data-scroll="features">向下了解${icon("chevron")}</a><div class="lp-carousel-controls"><button type="button" data-slide-prev aria-label="上一张场景">${icon("chevron")}</button><span class="lp-slide-number" aria-live="off">01 <i>/ 03</i></span><div class="lp-slide-dots">${slides.map((_,i)=>`<button type="button" data-slide="${i}" aria-label="查看第 ${i+1} 张场景" aria-pressed="${i===0}"><span></span></button>`).join("")}</div><button type="button" data-slide-next aria-label="下一张场景">${icon("chevron")}</button><button class="lp-play-toggle" type="button" aria-label="暂停自动轮播"><span aria-hidden="true">Ⅱ</span></button></div></div><span class="lp-image-disclosure">原创生成场景 · 非真实诊所照片</span></section>
  <section class="lp-foundation"><div class="lp-container lp-foundation-inner"><div><span class="lp-kicker">日常工作</span><h2>接待、诊疗与经营管理</h2><p>选择工作内容，了解对应的功能。登录后仅显示获授权的菜单与记录。</p></div><div class="lp-work-links">${[["calendar","预约日程","医师 / 牙椅 / 到诊"],["tooth","临床接诊","病史 / 牙位 / 病历"],["receipt","收费结算","项目 / 收款 / 退款"]].map(([i,a,b])=>`<a href="#/home/features" data-scroll="features">${icon(i)}<span><strong>${a}</strong><small>${b}</small></span>${icon('chevron')}</a>`).join('')}</div></div></section>
  <section class="lp-section lp-features" id="features"><div class="lp-container">${intro("功能介绍","诊所每天要用的功能","预约、接诊与收费各有工作台，患者资料和本次业务通过编号关联。")}<div class="lp-feature-layout"><div class="lp-feature-tabs" role="tablist" aria-label="产品能力">${featureItems.map((f,i)=>`<button id="lp-feature-tab-${i}" role="tab" type="button" data-feature="${i}" aria-controls="lp-feature-panel" aria-selected="${i===0}" tabindex="${i===0?0:-1}"><span class="lp-feature-icon">${icon(f.icon)}</span><span><strong>${f.label}</strong><small>${["预约、到诊与资源安排","患者风险、方案与病历","结算、收退款与经营统计"][i]}</small></span>${icon("chevron")}</button>`).join("")}</div><div id="lp-feature-panel" role="tabpanel" aria-labelledby="lp-feature-tab-0"></div></div></div></section>
  <section class="lp-section lp-journey" id="journey"><div class="lp-container">${intro("就诊流程","一次就诊，如何在系统中处理","从患者建档开始，依次查看前台、医师和收费岗位的处理步骤；期间核算另行开展。")}<div class="lp-journey-tabs" role="tablist" aria-label="业务流程步骤">${journey.map((s,i)=>`<button id="lp-journey-tab-${i}" type="button" data-step="${i}" role="tab" aria-controls="lp-journey-panel" aria-selected="${i===0}" tabindex="${i===0?0:-1}"><span>0${i+1}</span><strong>${s.name}</strong></button>`).join("")}</div><div id="lp-journey-panel" role="tabpanel" aria-labelledby="lp-journey-tab-0"></div></div></section>
  <section class="lp-section lp-roles" id="roles"><div class="lp-container">${intro("岗位与权限","登录后，进入自己的工作台","前台处理预约，医师负责接诊，收费员核对账单。机构授权决定菜单和数据范围；患者只能查看本人资料。")}<div class="lp-role-tabs" role="tablist" aria-label="岗位预览">${rolePreviews.map((r,i)=>`<button id="lp-role-tab-${i}" type="button" data-role="${i}" role="tab" aria-controls="lp-role-panel" aria-selected="${i===0}" tabindex="${i===0?0:-1}">${r.name}</button>`).join("")}</div><div id="lp-role-panel" role="tabpanel" aria-labelledby="lp-role-tab-0"></div></div></section>
  <section class="lp-section lp-trust" id="trust"><div class="lp-container lp-trust-grid"><figure class="lp-clinic-photo"><img src="/images/home-reception-v1.png" alt="牙科诊所前台接待原创示意图" loading="lazy"><figcaption>前台接待场景<small>原创生成图片，非真实诊所</small></figcaption></figure><div>${intro("资料管理","权限、记录与使用范围","系统按岗位限制操作，并保存病历版本、预约变更及收退款记录。")}<div class="lp-trust-items">${[["shield","岗位与诊所范围","员工按机构授权访问，患者按本人绑定查看。服务端对每次请求重新检查。"],["file","业务记录与变更历史","已签署病历通过补记追加版本；退款关联原收款，不改写历史凭据。"],["lock","当前为课程演示环境","使用合成患者数据。短信与邮箱服务须另行配置；不执行真实支付，不接收真实病历。"]].map(([i,a,b])=>`<article><span>${icon(i)}</span><div><h3>${a}</h3><p>${b}</p></div></article>`).join("")}</div></div></div></section>
  <section class="lp-section lp-faq" id="faq"><div class="lp-container lp-faq-grid">${intro("使用帮助","账号与访问","登录、注册和课程环境的使用说明。")}<div class="lp-faq-items">${[
    ["如何登录？是否需要先选择职位？","所有人员使用同一个登录窗口。支持账号或已验证手机、邮箱加密码；手机和邮箱验证码方式需配置真实发送通道。岗位由后台授权识别，无需在登录时选择。"],
    ["患者与内部员工如何注册？","患者完成手机和邮箱验证后自动分配账号。员工须填写机构预登记编号和激活码，并匹配姓名及联系方式。当前"+(config.registration_ready?"已具备通道配置，实际送达仍应核对。":"手机或邮箱发送服务尚未配置，不能假装完成双通道验证；现有账号仍可密码登录。")],
    ["为什么不同账号看到的内容不同？","前台、医师、收费、经理、总部岗位及患者的职责不同。权限由服务端核验；患者只看本人经核实绑定的记录，医师临床操作还受负责关系限制。"],
    ["可以上传真实患者资料或直接付款吗？","不可以。当前是课程合成数据系统，不是已经通过真实医疗合规验收的生产平台。收退款功能登记业务凭据，不执行银行或支付机构资金划转。"],
    ["本地链接无法连接时怎么办？","本机需运行 Java 后台。可双击桌面的 ADC Nexus - Start 启动，Status 检查状态，Stop 停止服务。电脑关机后需要重新启动；本地地址不等于持续在线的公网部署。"]
  ].map(([a,b])=>`<details><summary>${a}<span>+</span></summary><p>${b}</p></details>`).join("")}</div></div></section>
  <section class="lp-final"><div class="lp-container"><div><span class="lp-kicker">ADC NEXUS</span><h2>登录系统，开始今天的工作。</h2><p>进入与您身份相符的工作空间。所有业务演示均使用合成数据。</p></div><div class="lp-final-actions"><a href="${esc(workspaceHref||'#/login')}" class="lp-button primary">${workspaceHref?"进入工作台":"登录工作台"}${icon("arrow")}</a>${config.demo?`<button class="lp-button secondary" type="button" data-home-demo>课程综合演示</button>`:`<a class="lp-button secondary" href="#/register">注册账号</a>`}<p id="lp-demo-feedback" role="alert"></p></div></div></section></main><footer class="lp-footer"><div class="lp-container"><div class="lp-footer-top"><a class="lp-brand" href="#/home" data-scroll="top"><img src="/mark.svg" alt="" width="36" height="36"><span>ADC Nexus<small>安德鲁牙科连锁运营管理系统</small></span></a><div>${nav("产品功能","features")}${nav("业务流程","journey")}${nav("岗位空间","roles")}${nav("账号与使用说明","faq")}</div></div><div class="lp-footer-bottom"><span>© ${new Date().getFullYear()} ADC Nexus · 系统分析与设计课程项目</span><span>Java / JDBC · 合成数据演示 · 正式发布及外部通道另行验收</span></div></div></footer><button class="lp-back-top" type="button" aria-label="返回页面顶部" hidden>${icon("arrow")}</button></div>`;
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
    q('#lp-slide-tag').textContent=s.tag;
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
  function paintPause(s){paused=s.paused;play.disabled=s.reduced;play.setAttribute('aria-label',s.reduced?'减少动态效果已开启，自动轮播关闭':s.paused?'开启自动轮播':'暂停自动轮播');play.setAttribute('aria-pressed',String(s.paused));play.innerHTML=`<span aria-hidden="true">${s.paused||s.reduced?'▷':'Ⅱ'}</span>`;q('.lp-carousel-controls').dataset.playback=s.reduced?'减少动态效果':s.paused?'已暂停':'自动播放 · 5.5 秒';}
  play.onclick=()=>carousel.pause(!paused);
  // Pointer hover and mouse focus do not silently disable playback. Keyboard readers can pause explicitly.
  const visibility=()=>carousel.visibility(document.hidden);document.addEventListener('visibilitychange',visibility);
  const reduceChanged=()=>carousel.reduced(reduced.matches);reduced.addEventListener('change',reduceChanged);
  const mobile=q('.lp-mobile-nav'), toggle=q('.lp-nav-toggle');toggle.onclick=()=>{mobile.hidden=!mobile.hidden;toggle.setAttribute('aria-expanded',!mobile.hidden);toggle.setAttribute('aria-label',mobile.hidden?'展开首页导航':'收起首页导航');};
  const closeMobile=()=>{mobile.hidden=true;toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-label','展开首页导航');};
  const mobileKeys=e=>{if(e.key==='Escape'&&!mobile.hidden){e.preventDefault();closeMobile();toggle.focus();}};q('.lp-header').addEventListener('keydown',mobileKeys);
  qa('[data-scroll]').forEach(a=>a.addEventListener('click',e=>{const target=q('#'+a.dataset.scroll);if(target){e.preventDefault();if(a.dataset.featureTarget!==undefined){feature=Number(a.dataset.featureTarget);paintFeature();}closeMobile();target.tabIndex=-1;target.focus({preventScroll:true});target.scrollIntoView({behavior:reduced.matches?'instant':'smooth',block:'start'});history.replaceState(null,'',a.getAttribute('href'));}}));
  const onScroll=()=>{q('.lp-back-top').hidden=scrollY<700;q('.lp-header').classList.toggle('scrolled',scrollY>24);};window.addEventListener('scroll',onScroll,{passive:true});
  q('.lp-back-top').onclick=()=>scrollTo({top:0,behavior:reduced.matches?'instant':'smooth'});
  q('[data-home-demo]')?.addEventListener('click',async e=>{const button=e.currentTarget;button.disabled=true;try{await onDemo();}catch(error){if(!destroyed){q('#lp-demo-feedback').textContent=error.message;button.disabled=false;}}});
  qa('.lp-hero-image').forEach((img,i)=>img.alt=slides[i].alt);
  paintSlide();paintFeature();paintStep();paintRole();carousel.reduced(reduced.matches);visibility();onScroll();
  const section=location.hash.replace(/^#\/?/,'').split('/')[1];
  requestAnimationFrame(()=>{if(destroyed)return;if(["features","journey","roles","trust","faq"].includes(section))q('#'+section)?.scrollIntoView({block:'start'});else scrollTo({top:0,behavior:'instant'});});
  return ()=>{destroyed=true;carousel.dispose();document.body.classList.remove('public-home');document.removeEventListener('visibilitychange',visibility);window.removeEventListener('scroll',onScroll);reduced.removeEventListener('change',reduceChanged);};
}
