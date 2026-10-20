# 免费发布操作手册 · Render + Neon

状态：发布候选包，尚未填写正式链接。账号可用 Gmail 注册，不要求 Gmail、GitHub 与两平台采用某种特殊绑定。Codex 插件授权是另一条连接链路；插件故障不影响在两平台网页手动部署。

## 1. Neon：建立独立的课程数据库

1. 登录 [Neon Console](https://console.neon.tech)，建立 Free 项目 `adc-nexus-course`。不要开启付费计划。
2. 区域优先选择与 Render 新加坡相近的可用区域；以控制台 Free 的实际选项为准。
3. 使用这个专用新项目的默认分支和空数据库即可，默认名称 `neondb` 可保留；不需要为了部署改名。不要把已有个人或其他业务数据库交给程序初始化。
4. 在 Connect 选择 PostgreSQL 连接串，启用连接池选项。复制完整的 `postgresql://...` 地址，并保留 `sslmode=require`（以及页面生成的其他安全参数）。
5. 连接串含密码，只能粘贴进 Render 的 Environment / Secret 字段。不要发到聊天、放入 README、提交 Git 或展示在截图里。不要在 Neon SQL Editor 手工执行 SQLite 的原始 DDL。

首次启动由 JDBC 事务创建数据库结构并导入合成数据；以后启动只检查迁移，不重复插入或清空已有业务。

## 2. Render：创建 Docker Web Service

登录 [Render Dashboard](https://dashboard.render.com)，选择 New → Web Service。可连接自己的 GitHub 仓库；若不想授予 GitHub 应用访问权限，使用 Public Git Repository 方式导入已经公开的仓库：

`https://github.com/zongdajiang/adc-nexus-system-analysis-design`

使用以下配置（代码必须已包含 `system/` 目录）：

| 字段 | 值 |
|---|---|
| Name | `adc-nexus-jdbc`（如重名，添加个人后缀） |
| Branch | `main` |
| Root Directory | `system` |
| Language / Runtime | `Docker` |
| Dockerfile Path | `./Dockerfile`，相对 Root Directory |
| Docker Build Context | `.`，相对 Root Directory |
| Region | Singapore（或与 Neon 相近的免费可用区域） |
| Instance Type | **Free**，不要选付费实例 |
| Health Check Path | `/api/health` |
| Auto Deploy | Off；新版本验收后手动部署 |

环境变量：

| Key | Value / 设置方式 |
|---|---|
| `DATABASE_URL` | Neon 完整连接串，按秘密保存 |
| `ADMIN_PASSWORD` | 在 Render 中生成或自行设置至少 12 位高强度随机密码，私下保存 |
| `DEMO_MODE` | `true`，仅用于公开课程合成环境 |
| `SEED_DATA` | `true` |
| `APP_ENV` | `PRODUCTION` |
| `TZ` | `Asia/Shanghai` |
| `PORT` | `10000` |

不添加磁盘，不建立 Render Postgres，不添加付费 Worker/Cron。`system/render.yaml` 提供同一配置的 Blueprint；采用 Blueprint 时将 Blueprint Path 指向该文件，仍需私下填入 `DATABASE_URL`。开始前确认账单估算为 $0。首次镜像构建和迁移可能需要几分钟。

如果 Render 要求新增付款承诺或信用卡验证，停下来核对，不擅自开通付费资源。

## 3. 首次部署后核对

1. 等待状态变为 Live，复制平台实际分配的 `https://...onrender.com` 链接，不自行猜测域名。
2. 打开 `<正式地址>/api/health`，核对 `ok: true`、`database: PostgreSQL`、`data_access: JAVA_JDBC`、版本 `1.0.0-rc1`。
3. 打开首页，依次试用前台、医师、收费员、患者角色，确认菜单不同。患者不应出现全体患者列表，收费员不应出现病历签署。
4. 完成 [试用主路径](REVIEW_GUIDE.md)，刷新页面验证记录保留，再执行 Render 手动重启，验证数据库记录依旧存在。
5. 用无痕窗口打开公开链接，确认不依赖你的本机、Google 登录态或 Codex。
6. 验证完成后才把正式链接、云端验收结果和实际实施差异加入最终分析设计报告。

可用 `python tools/smoke_remote.py https://实际地址` 做只读线上冒烟；不会向托管业务数据库写入。业务写入验收按指南人工记录，不能用只读检查替代。

## 4. 管理员与数据保护

管理员使用员工入口，用户名 `owner`，密码来自首次初始化时的 `ADMIN_PASSWORD`。后续只改环境变量不会自动改写数据库中的密码：请登录账号安全页变更密码，或通过受控数据库恢复流程处理。不要向教师发送管理员秘密；普通岗位可使用显式合成演示入口。

免费环境不接收真实患者、影像或付款凭据。所有页面与数据均为课程用途。提交评分前，将专用 Neon 数据库导出备份并妥善保存在本地，备份也不要放入公开 GitHub。`tools/verify_pg_backup.py` 是隔离数据库恢复验收脚本，不会操作 Neon。

## 5. 常见问题

- **OAuth State not found**：发生在插件连接回调，不是 JDBC 数据库错误。关闭旧回调页，从插件页面重新发起一条新授权；不要同时连接两家，也不要刷新或复用旧回调链接。若持续失败，直接使用本手册网页流程，不需要交出密钥给聊天。
- **首次访问等待**：Render Free 可能休眠，Neon 也可缩容至零。等待唤醒并重试；不能把免费方案描述为无冷启动或具有付费 SLA。
- **连接失败**：在 Render 私密环境页核对连接串、数据库与 SSL 参数，查看日志的错误类型；截图前隐藏环境值、密码和回调查询参数。
- **看板为空**：日期采用实际上海日期。可切换“最近有记录的日期”；不要把历史预约改成今日来制造演示数据。
- **季度不能关闭**：未到期、实际成本未核实、费用未完整归属、输入摘要变化均会阻断。按提示补全业务依据，不能绕过校验。

平台规则以部署时官方页面为准：[Render Free](https://render.com/docs/free)、[Docker 部署](https://render.com/docs/deploy-docker)、[Blueprint](https://render.com/docs/blueprint-spec)、[Neon Java](https://neon.com/docs/guides/java)、[Neon Free](https://neon.com/docs/introduction/plans)。

开发者只读验证 Blueprint：先用 `python -m pip install --target .deps/qa-python PyYAML==6.0.2 jsonschema==4.25.1` 安装本地 QA 依赖，再执行 `python tools/validate_deployment.py`。该检查不创建资源，也不能代替 Render 的真实容器构建和上线检查。
