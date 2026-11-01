# 统一账号与工作台改版规格 · 1.1

2026-10-21。本增量优先于 1.0 的分岗位登录说明；原分析报告保留为基线，最终报告尚待同步。

## 界面及参考边界

已检查 [舒心牙医公开站](https://shuxinyayi.com/) 的首页、注册弹窗、公开 SaaS 登录表单。借鉴单一表单、白色面板、青色主操作和轻灰背景层次，不复制品牌、代码、照片及数据。没有进入其受限后台，不将宣传文案视为已核实的后台功能。

ADC Nexus 使用自有 SVG 与 HTML/CSS：统一登录卡片、独立注册/找回；白色侧栏、位置栏、直接的功能标题、筛选、表格与业务详情。移除大幅宣传语及装饰英文，保留风险和权限提示。移动端收起导航、堆叠表单，宽表格滚动而非缩小文字。

## 身份合同

登录不选择岗位。支持账号、**已验证**手机/邮箱加密码，以及手机/邮箱验证码。每次请求仍由后端按生效角色、诊所、负责牙医和患者绑定核权，不以隐藏菜单代替安全边界。

注册类别仅“内部员工 / 患者”。均填写姓名、手机、邮箱、12–128 位密码并完成双通道验证，确认使用说明。患者另填出生日期及性别记录，获得 `ADC-PT-<12位随机标识>`。仅自动绑定本次新建空白档案；可能与既有患者重复时停止并由机构核实，不凭手机号自动开放历史病历。

员工先由全网 `access.manage` 管理员登记名册及联系方式，签发 48 小时激活码；本人须同时匹配编号、姓名、双联系方式与激活码。账号即员工编号，岗位从**管理员已登记**的编号识别，绝非填写任意岗位代码即可授权。

| 编号例 | 岗位 | 范围及额外条件 |
|---|---|---|
| ADC-FD-000001 | FRONT_DESK 前台 | 有效诊所 |
| ADC-DR-000001 | DENTIST 医师 | 有效诊所及医师档案 |
| ADC-CS-000001 | CASHIER 收费 | 有效诊所 |
| ADC-MG-000001 | CLINIC_MANAGER 店长 | 有效诊所 |
| ADC-OP-000001 | HQ_OPERATIONS 总部运营 | 全网，不默认授予财务/临床签署 |
| ADC-FN-000001 | HQ_FINANCE 总部财务 | 全网，不默认授予临床签署 |
| ADC-AD-000001 | ADMIN 管理员 | 账号治理，不默认获得全部业务权 |

保留旧 `trial.*`、`owner` 账号、密码、业务数据和授权；不把旧邮箱/电话字段视为已经验证。激活码仅返回一次，数据库只保存摘要，不进入普通日志及幂等收据；重签使旧码失效。停用员工名册会停用已认领账号并撤销会话。

## 验证合同

验证码随机六位，独立盐 PBKDF2-SHA256 120,000 次，5 分钟、最多 5 次尝试；绑定通道、地址、用途。失败次数在拒绝响应前提交，不被回滚重置。成功即消费，重发使同用途旧码失效。密码 PBKDF2 600,000 次。找回仅接受签发时关联的已验证身份，更新后撤销全部旧会话，不自动登录。

发送间隔 60 秒；每地址每 15 分钟最多 5 次、直接连接 IP 30 次、全局 100 次；另有默认每日 50 次总预算（AUTH_DAILY_SEND_LIMIT，上海日历日，按机构预算配置）。代理可能共享限额，正式环境需结合可信边缘调整。不信任调用者伪造的转发 IP。网络发送在数据库事务之外；发送失败记录 FAILED，不产生可用挑战。响应无明文验证码、密码、密钥或账号存在标记。“已配置”不等于真实送达。记住账号只存标识，不存密码。验证码登录不是双因素认证。

## 数据增量（迁移 005）

实际由 67 表增加至 **69 表、137 条外键**；原报告 61 表基线不变，不删除旧数据。

| 表及属性 | 键/约束 | 业务目的 |
|---|---|---|
| staff_directory.id / employee_code | PK / UNIQUE，非空 | 名册身份、标准员工编号 |
| role_id / clinic_id / dentist_id | FK → roles / clinics / dentists | 岗位、诊所、临床身份分别关联 |
| claimed_user_id | UNIQUE FK → app_users，可空 | 一名员工最多认领一个账号 |
| display_name / phone_e164 / email | 非空，联系方式规范化 | 机构预登记身份对照 |
| created_by_user_id | FK → app_users，非空 | 登记责任人 |
| status / created_at / updated_at | ACTIVE/INACTIVE；非空时间 | 在职状态及追查 |
| verification_challenges.id | PK，非空 | 手机/邮箱统一挑战 |
| channel / destination / purpose | EMAIL/PHONE；REGISTER/LOGIN/RECOVER | 精确使用上下文 |
| user_id | FK → app_users，可空 | 签发时关联账号 |
| code_hash / code_salt | 非空，无明文 | 验证码摘要 |
| status / expires_at / consumed_at | PENDING/SENT/FAILED；消费可空 | 时效、发送及消费 |
| attempt_count / request_ip_hash / created_at | 非负整数/非空 | 防猜码与发送限流 |
| account_invitations.staff_directory_id | 新增 FK → staff_directory，可空 | 兼容旧邀请 |
| account_invitations.token_hash | 新增 UNIQUE，可空 | 一次性激活码摘要 |
| auth_identities（复用） | UNIQUE(provider,provider_subject) | VERIFIED_PHONE / VERIFIED_EMAIL 绑定 |

原 `auth_otp_challenges` 为报告的手机模型，保留但本版统一验证实际走 `verification_challenges`，不将两者同时称为主通道。

## 接口（/api 前缀）

| 路径 | 方法 | 请求及返回 |
|---|---|---|
| /auth/config | GET | 通道配置、registration_ready，无秘密 |
| /auth/login | POST | username（账号或已验证联系方式）、password；不要求 role |
| /auth/challenge | POST | channel、destination、purpose；返回 challenge_id、expires_in、retry_after |
| /auth/register | POST | kind、name、phone、email、password、accepted_terms、phone_challenge/phone_code、email_challenge/email_code；患者另填 date_of_birth/gender，员工另填 employee_id/activation_code |
| /auth/code-login | POST | channel、destination、challenge_id、code；设置安全会话 |
| /auth/recover | POST | 上述验证字段及 new_password；需重新登录 |
| /admin/staff | GET / POST | 全网账号管理员；create、reissue、deactivate；POST 须 CSRF，返回的激活码不写请求收据 |

所有提交仍要求同源 JSON；角色、唯一性、外键、消费和状态由服务端事务保证。`tools/verify_auth.py` 只使用隔离数据库和回环内存收件器，不实际发送消息，不将测试码写入证据。APP_ENV 非 TEST 时不能启用测试收件器。

真实发送、实际收件、托管网络、反滥用预算及最终报告图表须另验收。见 [发送通道开通](CHANNEL_SETUP.md)。
