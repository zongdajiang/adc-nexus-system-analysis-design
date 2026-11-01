# 实施追踪台账

用户于 2026-10-30 确认本轮边界。最终 PDF 未修改。状态以实际验收为准。

| 编号 | 来源及业务决定 | 关联用例 / 角色 | 实施范围与兼容规则 | 状态 / 证据 | 报告待同步位置 |
|---|---|---|---|---|---|
| UP-001 | OD-05、DP-02：配置能维护真实诊所、牙医、场地与服务 | UC-11/18；运营维护全网，店长限本店资源；管理员只管账号授权 | 诊所资料及营业时间、牙医档案、牙椅资料；无硬删除；并发指纹；停用/缩时检查既有预约；不自动授予登录角色 | planned | 组织/资源类图、资源内部序列、权限表、API、操作手册 |
| UP-002 | OD-04/05、DentalPin 目录：治疗项目与价格必须有版本 | UC-02/06/07/09/11；总部运营 | 新项目、追加版本及资质要求；版本不覆盖历史金额；截止旧版本前检查已约服务；资质不得任意放宽既有版本 | planned | 目录类图、业务规则、数据字典、目录/临床流程 |
| UP-003 | OD-02、DP-01：患者是否确认应独立于预约占位状态 | UC-02/03；前台 | 复用 confirmation_state；记录电话/邮箱/短信/当面联系结果与依据；改期重置待确认；不冒充真实发送 | planned | 预约状态说明、确认流程、字段字典、界面截图 |
| UP-004 | OD-02、DentalPin Recalls：复诊建议、联系任务和正式预约分开 | UC-01/02/06 的增量；负责牙医提出建议、前台跟进 | 人工制定复诊日期及依据；独立随访与追加联系日志；患者拒绝可终止；关联本人同店有效预约前复核；不自动开约或推断医学间隔 | planned | 新随访用例、类图/ERD、字典、角色矩阵、内部序列与验收 |
| UP-005 | 用户要求及本轮调研：公开部署必须可核验 | 全部用例、教师评审 | Render Java 容器+外部 PostgreSQL；不使用临时磁盘 SQLite；角色试用、重启持久化、恢复与 HTTPS 验收 | planned | 部署图、运行环境、正式链接、限制及验收表 |

## 2026-10-30 验收更新

UP-001—004 状态更新为 **verified（本地）**，上表 planned 为立项记录，非当前验收状态；未标记 released。当前被测 JAR SHA256 `2b257a54540f95353048f64b20e3a25aad36d72bcdb40c9b1f6e4e2006ca6e3a`。

| 编号 | 主要实现文件 | 验收证据 |
|---|---|---|
| UP-001 | PracticeSetup.java、Workforce.java、practice-setup.js；Clinical.start 增加有效医师/诊所复核 | qa/acceptance-results.json、acceptance-postgres.json 的 UP01；local-preservation-v1-5.json |
| UP-002 | PracticeSetup.catalog、treatment_catalog 与既有资质要求；目录版本选择明确代码、版本和生效期 | 两套数据库 UP02；setup-ui-tests.json；浏览器新增 ¥123.45 与追加 ¥234.56 版本均留存 |
| UP-003 | Scheduling.command/history、practice-workflow.appointmentHistoryEvent、app.js | 两套数据库 UP03；结构化 event_type/channel/confirmation_state；初审发现历史标题混淆后已修复，qa/finish-review-v1-5.md 的一项修复判为 resolved / ship |
| UP-004 | migration 006、Followups.java、followups.js、Main 路由及 Seed.practicePermissions | 两套数据库 UP04；来源不能充当后续复诊、患者/诊所/负责医师/联系许可/并发/真实完成守卫；浏览器缺日期错误及联系留痕 |
| UP-005 | Dockerfile、render.yaml、docs/DEPLOYMENT.md | **pending external access**：账号连接未在当前会话生效，托管页面仍需用户登录。无可验证公网链接，不能标记发布完成 |

实际模型：71 表、820 字段、146 外键；仅结构元数据见 IMPLEMENTED_SCHEMA.json。原 PDF 校验值再次确认未变化。自动化与浏览器证据分列，不以本台账替代测试。历史 CR-001—015 继续见 `docs/CHANGE_CONTROL.md`。

## 2026-11-02 发布准备续接

- 重新核对现有 JAR 与 607 项自动化证据的绑定关系，恢复本地 8087 服务；未变更既有业务规则或数据。
- 新增安全源码同步工具，限定目标为本人 GitHub 仓库的 `system/`，排除数据库、凭据、会话、日志、构建缓存和第三方原始 XML；同步前保留桌面仓库备份。
- 校正线上只读检查脚本：从 `pom.xml` 读取预期版本，检查新增静态模块及未登录接口隔离。此修订避免新版本被旧版本常量误判，并不表示已做公网验收。
- 打包及更新仓库说明、自动检查流程和校验清单。原报告仍冻结；公网状态须由实际 Render 地址、PostgreSQL 健康检查和上线验收共同确认。
- 用户确认能在普通浏览器进入 Neon、Render 控制台。采用普通网页部署流程，不依赖插件 OAuth，不索取 Google 密码或验证码。
- GitHub 提交 `8375465d2b0221e771f0cfd6a1cfc6374248f468` 的 Linux SQLite / PostgreSQL 两组流水线已全部通过，运行编号 `41336925617`。此为 CI，不是 Render / Neon 上线证明。
- 续接增加仓库根目录部署入口与两步发布卡；校验两份 Blueprint 等价、强制 Free、单服务和秘密不入仓库。Docker 构建上下文排除文档、工作台及其他非运行资料。
- 新增独立 Linux 容器验收：生产模式缺数据库时拒绝启动；非 root 用户、512 MiB 限制、静态模块、未登录隔离、重启及替换容器后的外部数据库内容。必须等待实际 CI 结果，未运行前不计入 607 项或写为通过。
