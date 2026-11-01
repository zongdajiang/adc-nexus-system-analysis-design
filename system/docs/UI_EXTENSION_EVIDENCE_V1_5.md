# 1.5 既有工作台扩展：视觉继承与证据

记录日期：2026-10-30。对象为组织资源维护、治疗目录版本、复诊建议与跟进，以及预约详情中的独立患者联系确认。本文记录本地完成态与既有视觉体系的关系，不构成公网发布、真实通道送达或最终报告同步的验收。

## 文档方式与边界

依据 [PRODUCT.md](../PRODUCT.md)、[本轮 UI brief](../upgrade-workbench/2026-10-30/UI_BRIEF.md) 和 Impeccable `new-work.md` 第 7 节的 ordinary extension 路径：沿用既有体系，比较完成态，保留体系文件并报告检查证据。本轮没有创建或替换视觉世界，也没有获批的持久体系变更；不新增 `DESIGN.md` 或 `.impeccable/design.json`，不把局部扩展提升为另一套规范。`document.md` 的扫描规则用于识别现有来源，而非启动视觉命名或身份选择。

本次文档工作只新增本文。未改源代码、QA 门槛、SDS、API 文档、报告 PDF、截图或既有宣传素材。最终报告 PDF 仍冻结至系统发布后。

## 检查方法与来源

- 读取入口样式加载顺序、四份既有样式、扩展样式及三个业务模块与 `app.js` 集成；下文数值为源代码声明和可见截图的交叉记录，未采集浏览器 computed style，不把源声明称作运行时测量。
- 逐一打开本文列出的八张本地截图，确认其内容对应文件所述视图；以图片文件头读取像素尺寸。未重新打开浏览器、重新运行交互、检测器或视觉缺陷搜索。
- 阅读 [finish review](../qa/finish-review-v1-5.md) 的初审及同一问题的 verdict pass；其 `ship` 结论按原有范围保留。
- 读取 [1.4 素材说明](VISUAL_ASSETS_V1_4.md)，保持首页既有图片与来源说明。未生成或引入新的营销位图。

## 样式权威与实际继承

`src/main/resources/web/index.html:13–18` 的顺序是 `app.css` → `product.css` → `studio.css` → `homepage.css` → `practice.css` → `setup.css`。业务工作台以较晚的 `practice.css` 作为当前视觉覆盖层，并继承早期文件中未被覆盖的结构、状态与响应式规则；`setup.css` 添加局部布局，没有重新声明根色板、全局字体或公共按钮。

下表记录与本轮有关的既有值，不另立设计 token 的源头。

| 观察项 | 源代码中的既有值 | 主要来源 |
| --- | --- | --- |
| 根文字、辅助文字 | `--ink: #20333f`；`--muted: #60717a` | `practice.css:2` |
| 主动作与页面底 | `--teal: #087d83`；`--bg: #f2f4f5` | `practice.css:2` |
| 分隔线 | `--line: #dce2e5`，公共容器细边框 | `practice.css:2,18` |
| 侧栏 | `#172f3e`；普通导航 `#c4d4df`；选中底 `#294b5a`，左侧内嵌 `3px #63c0be` | `practice.css:7,10–11` |
| 字体 | `"Segoe UI","Microsoft YaHei UI","PingFang SC",sans-serif`；正文 `14px`；表头 `12px`；表格正文 `13px` | `practice.css:2–4,19` |
| 标题层级 | 工作区标题 `25px / 600`；卡片标题 `15px`；弹窗标题 `18px` | `practice.css:16,18,21` |
| 普通 / 小按钮 | 圆角 `4px`；普通最小高 `35px`、内边距 `7px 12px`、字 `13px`；小按钮最小高 `30px`、`5px 9px`、字 `12px` | `practice.css:17` |
| 主按钮状态 | 默认 `#087d83`，可用态 hover `#06686e`；disabled 透明度 `.5` | `practice.css:17` |
| 分区选中按钮 | 继承浅青底 `#edf7fb`、字 `#137f9d`、边 `#b3dbe8` | `studio.css:54` |
| 表面 | 白色卡片、`5px` 圆角、无卡片阴影；卡片内容 `20px`，表头容器 `17px 20px` | `app.css:193–200`；`practice.css:18` |
| 表格 | 表头 `#f6f8f9`，`11px 16px`；正文 `13px 16px`、行高 `1.7`；辅助行 `12px` | `practice.css:19` |
| 输入 | `4px` 圆角、最小高 `37px`、字 `13px`；focus 边 `#16868b`、`2px #16868b2b` 外框 | `practice.css:18` |
| 键盘焦点 | 按钮、链接、summary 使用 `2px #138aa6`，offset `4px`；滚动表格使用 `2px #56a4bf`，offset `-2px` | `studio.css:4,79` |
| 状态标签 | `3px` 圆角、`11px`、`2px 7px`；蓝 `#eaf2f8 / #315f83`，绿 `#e5f2ed / #286b55`，琥珀 `#fcf0da / #8e631d`，红 `#fbeae7 / #9f3d35` | `practice.css:19` |
| 对话框 | `6px` 圆角；`0 18px 80px #0b263332` 阴影；头尾底 `#f7f9fa`；正文继承 `#fcfdf9` | `practice.css:21`；`app.css:1223–1231` |

整体仍是深蓝导航、青白业务工作面、清晰文字层级与细线资料表。色彩表达选中、动作与状态；本轮新增的是业务对象和记录身份，没有新增品牌色、字体资产、图像皮肤或阴影语言。

## 布局、响应式与局部模式

既有桌面框架使用 `222px minmax(0,1fr)`，侧栏 `222px`；工作区最大宽度 `1920px`、内边距 `28px`，居中；顶栏高 `60px`（`practice.css:6–7,14,16`）。窄屏 `max-width:760px` 沿用抽屉导航，侧栏 `240px`，主区 `22px 15px`，顶栏 `58px`（`practice.css` 的同名 media block；抽屉状态继承 `studio.css:144–145`）。这次没有统一或重设历史断点。

表格沿用 `app.css:430–432` 的容器横向滚动；`max-width:720px` 时表格最小宽度 `640px`（`app.css:1396–1399`）。`app.js:152–155` 继续输出带 `tabindex="0"`、区域说明与列头语义的公共表格，并在窄屏显示“左右滑动查看完整表格”。本轮使用此容器保留真实列信息。

弹窗继承纵向 flex、正文 `overflow-y:auto`、不收缩的头尾及 `92vh` 最大高（`app.css:1223–1275`），字段在 `max-width:720px` 切换单列（`app.css:1514–1516`）。截图中可见的窄屏弹窗正文滚动和底部提交区来自既有组件。

`setup.css:2–19` 的局部新增沿用上述语汇：

- 营业时间 disclosure 与资质 fieldset 使用 `5px` 圆角、`var(--line)` 边框；资质选择使用 `var(--teal)`。操作行按需换行，间隔 `6px`。
- 跟进筛选条使用 flex 换行、`12px` 间隔、`18px` 内边距；`max-width:680px` 时输入、选择与筛选按钮占满本行，内边距 `14px`。
- 详情事实使用两列 `17px 24px` 间隔；首项占满整行；`max-width:680px` 改单列。说明文本使用 `max-width:42ch`、行高 `1.8` 与 `overflow-wrap:anywhere`。

## 业务组件如何接入

| 完成态 | 继承方式与语义证据 | 源码 |
| --- | --- | --- |
| 诊所、医师、牙椅维护 | 复用公共 panel、table、button 与 modal；新增操作在所属表头；档案、任职和登录授权分开说明 | `practice-setup.js:1–32,55–89`；`app.js:2689–2697,3688` |
| 治疗目录与版本 | 资料表保留项目、版本、金额、有效期、必需资质与状态；追加版本及停用属于各行操作；资质使用带 legend 的 fieldset | `practice-setup.js:33–39,90–107` |
| 复诊建议与清单 | 位于既有候补区的分区导航；按患者、状态、联系安排筛选；以医师建议和复诊日期组织资料 | `followups.js:1–22`；`app.js:1955–1958,3689` |
| 复诊详情与联系 | 明确来源就诊、责任医师、联系许可、正式预约与逐次追加记录；使用原弹窗、表格、按钮和日期展示 | `followups.js:24–66` |
| 预约患者联系确认 | 独立确认表单说明“登记已发生的实际联系”，不宣称发送消息；历史投影区分预约建立、预约状态变更、改期与患者联系确认 | `app.js:1484–1487,1508–1528`；`practice-workflow.js:3–21` |

预约历史修复是只读展示投影：`appointmentHistoryEvent` 优先识别结构化事件，兼容此前 reason 中的渠道/结果编码，输出中文事件名、联系途径及确认结果。时间、人员和依据仍单独展示。本文未推断或改变其服务端写入、授权及临床规则。

## 已查看的截图

以下均为本机合成课程环境的浏览器截图；不是第三方界面或真实病例资料。本次只读检查文件及对应视图，没有修改这些图片。尺寸为文件像素，不能直接等同于 CSS viewport；文件名保留原捕获记录。

| 文件 | 实测像素 | 可见证据 |
| --- | --- | --- |
| `.impeccable/review/desktop.png` | `1440 × 1000` | 复诊跟进桌面清单；既有侧栏、页头、检索与状态筛选、患者及医师信息 |
| `.impeccable/review/mobile.png` | `375 × 812` | 复诊筛选垂直排列，提示与表内横向滚动条可见 |
| `.impeccable/review/mobile-dialog.png` | `390 × 844` | 复诊详情单列、联系许可与业务动作、独立正文滚动及底部关闭区 |
| `.impeccable/review/mobile-catalog-form.png` | `390 × 844` | 目录新增表单、可见输入焦点、单列字段与底部取消/保存区；截图未展示表单底部全部字段 |
| `.impeccable/review/catalog-desktop.png` | `1425 × 990` | 目录项目/版本、标准价、估算成本、有效期、资质与行操作 |
| `.impeccable/review/tablet-768.png` | `753 × 1004` | 平板牙椅资料表；既有桌面导航与表格仍可读；`768` 是文件标签，图片本身为 `753px` 宽 |
| `.impeccable/review/user-2560-full.jpg` | `2560 × 1440` | 用户指定宽度的完整窗口，从文档顶部开始显示组织资源及营业时间入口 |
| `.impeccable/review/confirmation-dialog.png` | `1440 × 1000` | 修复后预约详情分别显示“预约建立 / 已预约”与“患者联系确认 / 电话 · 患者已确认”；各自保留时间、人员和依据 |

已弃用的 `user-2560.png` 不在本次证据集内。截图可以支持其可见状态的继承关系，不能单独证明全部交互、全部错误态、全部数据长度或服务端验收。

## 审阅结论的实际范围

[`qa/finish-review-v1-5.md`](../qa/finish-review-v1-5.md) 初审的唯一 material fix 是：预约建立与独立患者联系事件不应共用“已确认”标题，渠道和结果应使用自然语言，并与依据分别展示。

该 reviewer 已在原 `confirmation-dialog.png` 路径的有效重拍上将这一项评分为 `resolved`，最终 disposition 为 **ship**。这是针对该项修复的 verdict pass；不代表再次完成全表面的审阅，不扩展为“全局没有缺陷”，也不是部署许可或公网已发布的证明。其余初审对既有字体、材料、底色、导航、目录、复诊内容及窄屏适配的记录仍按原证据范围阅读。

## 既有分层差异与保留事项

扫描发现既有 `app.css`、`product.css`、`studio.css` 仍保留不同阶段的根色、按钮、卡片与导航定义，`studio.css` 本身也有后续覆盖段。入口最终加载的 `practice.css` 提供本轮所继承的青白/深蓝工作台。记录较早一层的色板或圆角会与当前画面产生差异，因此本文按加载顺序注明来源，不合并、不重命名、不清理这些既有样式。

具体保留的差异包括：根 `--muted` 与表格 `.second` 的实用色并不相同；分区选中按钮继续来自 `studio.css` 的浅青状态；对话框正文继承 `app.css` 的微暖底，而头尾来自 `practice.css` 的浅灰青底；`680px`、`720px`、`760px` 断点各有作用。它们是当前实现的来源事实，不是在本轮悄然获批的新全局 token，也不触发未经请求的修补。

首页已有图片沿用 [VISUAL_ASSETS_V1_4.md](VISUAL_ASSETS_V1_4.md) 及其链接的 1.3 来源。本轮没有新增产品交付位图；本地审阅截图的来源为上述合成环境。最终报告、公网发布和真实外部通道仍按 PRODUCT.md 的未完成边界处理。

## 本次源快照

SHA-256 只标识文档检查时的文件；后续实现再变动时应重新核对相应证据。

| 文件（均位于 `src/main/resources/web/`） | SHA-256 |
| --- | --- |
| `app.css` | `34A8B280A1B03C48312FBFD731E911382D72334A2E2C90718E7CB26002E7417A` |
| `product.css` | `5F4ACCEFDEDC2946575ECF2E17F3A8A482AC04B912A233E5F64F217C2BD93D56` |
| `studio.css` | `BA37B28B63F087D559537C3ACB02B7BE2789C5FB08944F637472BF9ED95DE269` |
| `practice.css` | `5D7D0F73FE397DB628805D7C5EA1A5B319C8A58E5FA84E7699683066C07B4780` |
| `setup.css` | `F58FB8693F77841CF98E3467DD1C9C02EC7059EAAA86A89281E6293A2FD536E5` |
| `practice-setup.js` | `0D4E3170FD789F94EDC1971ADB69D5CDEA53414452771904B19C285CBD636470` |
| `followups.js` | `2289A3F81301EFDE9876AD672C7B87C7C47A08448198F80EDC101A4EBC9B6B95` |
| `practice-workflow.js` | `D9AE2D1FAA4EA44E7E5D7CA355CC6FCCD64696142E8AF252F3977B3F9E9C3A58` |
| `app.js` | `DD5F9FC2ABD8228EBB786DBB8F49CD01782DA6030C3B56A4E3E0A94E89B2A020` |
