# API 合同 · 1.5.0-rc1

1.5 增量：基础配置的六种 action、预约联系确认及复诊跟进接口与字段见 [1.5 业务合同](PRACTICE_UPGRADE_V1_5.md)。复诊更新沿用统一的请求字段 `version`，比对服务端建议 `revision`。最终报告尚未同步。

1.1 增量：登录不再要求 role；手机/邮箱须有验证过的身份绑定。注册、挑战、验证码登录、找回及员工名册的完整字段见 [统一身份合同](AUTH_AND_UI_V1_1.md)。旧 `/auth/sms*`、微信占位仍返回 503，不应当作新验证码接口。

所有业务接口位于 `/api`，仅使用同源 Cookie 会话。响应为 UTF-8 JSON；错误结构为 `error.code/message/details/request_id`。写接口使用 POST、`X-CSRF-Token` 及可选的 `Idempotency-Key`（12–100 位字母、数字或连字符）。同一操作与请求标识重试返回原结果，不允许用同一标识提交不同内容。禁止跨站写入。

| 路径 | 方法 | 语义 / 授权 |
|---|---|---|
| `/health` | GET | 不带秘密的就绪状态、数据库类型及版本 |
| `/auth/config` | GET | 登录入口与外部通道配置状态 |
| `/auth/login` | POST | `{username,password}`；标识为账号或已验证联系方式，不选择岗位；旧 role 参数仅保留兼容校验，不授予权限 |
| `/auth/demo` | POST | `{role}`；仅显式 DEMO_MODE 环境，非正式认证通道 |
| `/auth/session` | GET | 当前身份、权限、范围及 CSRF |
| `/auth/logout` | POST | 撤销当前会话并清除 Cookie |
| `/auth/password` | POST | `{oldPassword,newPassword}`；撤销该用户全部会话 |
| `/bootstrap` | GET | 当前岗位的界面启动数据，不包含密码摘要 |
| `/dashboard` | GET | 日期及授权范围运营汇总，财务部分独立检查财务范围 |
| `/patients` | GET / POST | 搜索分页 / 建档；写需 patient.manage |
| `/patients/{id}` | GET / POST | 档案 / update、history、allergy、contact、privacy_consent、duplicate_decision |
| `/appointments` | GET / POST | 日期和范围日程 / 事务内创建 |
| `/appointments/{id}` | GET / POST | 含历史 / reschedule、cancel、no_show、check_in、revoke_arrival |
| `/scheduling/validate` | POST | 检查候选方案，不占位；提交预约仍重新检查 |
| `/waitlist` | GET / POST | 候补与邀请 / add、offer、accept、decline |
| `/visits` | GET | 诊疗队列；医师限本人负责病例 |
| `/visits/{id}` | GET / POST | 临床证据 / safety、start、observation、plan、consent、actual、reconcile_actual、note、complete |
| `/finance/unbilled` | GET | 已完成未开单就诊的收费摘要，不返回病历正文 |
| `/finance/invoices` | GET / POST | 结算单 / 按 visit_id 唯一开单 |
| `/finance/invoices/{id}` | GET / POST | 明细及流水 / pay、refund、void |
| `/finance/periods` | GET / POST | 期间、成本、费用与快照 / cost、expense、allocate、close、reopen |
| `/finance/preflight` | GET | `{period_id}` 查询参数；输入摘要、阻断项及计算口径 |
| `/resources` | GET / POST | 诊所、人员、目录和资源 / chair、closure、exception、availability、credential、assignment |
| `/analytics` | GET | 范围内绩效、牙椅容量与服务日资质覆盖 |
| `/expansion` | GET / POST | 情景及候选数据 / 保存参数与计算结果 |
| `/admin/access` | GET / POST | create_user、grant、revoke、status、patient_link；需 access.manage |
| `/audit` | GET | 范围内操作及拒绝审计 |
| `/portal` | GET | 绑定本人摘要；不接受客户端指定患者 ID |

常用筛选：`clinic_id`、`from`、`to`；患者支持 `q`、`offset`，预约支持 `dentist_id`、`patient_id`、`status`。日期为 `YYYY-MM-DD`，业务时间为上海本地 `YYYY-MM-DD HH:mm:ss`，金额字段后缀 `_fen` 均为整数分。

预约、就诊、结算、期间的变更须携带最新 `version`；字段分别由读接口返回 `appointment_version`、`visit_version`、`invoice_version`、`period_version`。排班更新使用 `fingerprint`，牙椅更新使用 `updated_at`。缺失或过时返回 409，不静默覆盖。

典型错误：401 未登录/会话失效；403 岗位、范围、负责牙医、CSRF 或来源不符；409 状态/并发/资源/财务条件冲突；422 格式或业务参数错误；503 外部通道未配置或容量繁忙。手机号与病历正文不能写入普通技术日志，SQL 错误不直接返回客户端。

字段级示例及真实提交顺序以 `tools/verify.py` 为可执行合同。该脚本只向隔离合成数据库发出业务写入，不是任意线上测试工具。前端 CSV 由已授权读取的数据生成；当前没有独立服务端导出审计，不应在报告中声称所有下载已逐次审计。
## 1.4 开单预览增量

`GET /api/finance/unbilled/{visitId}`：需要 `finance.read` 并校验该就诊诊所范围，仅支持已完成就诊。返回最小化患者/就诊身份、负责医师、完成时间、实际项目、数量、牙位、单价快照、行金额、整数分合计与服务期间状态。不会返回病史、过敏、观察或病历正文；不建立单据或成本，不更改就诊。POST 返回 405。预览不是授权开单凭据；确认时 `POST /api/finance/invoices` 仍重验权限、期间、实际行金额和唯一单据约束。即使预览后已被另一位人员开单，重复确认也返回原单，不重复计费。
