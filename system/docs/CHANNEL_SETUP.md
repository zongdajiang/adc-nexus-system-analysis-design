# 验证码发送通道开通

本轮没有替你开通服务、产生费用或发送真实消息。不要将密码、验证码、API Key、连接串发到聊天、截图或 GitHub。只填本机进程环境或 Render 秘密设置。

## 免费托管先看这里

[Render 官方](https://render.com/docs/free) 当前禁止 Free 服务出站 SMTP 端口 25、465、587，不能把“Gmail SMTP 本地可用”当作“上线可用”。Render Free 优先用 HTTPS 邮件 API；SMTP 留给可出站的本地/其他部署。免费服务不承诺医疗生产级可用性。

## 邮件：HTTPS API 路径

已实现 Brevo 事务邮件适配器。先在 [Brevo](https://www.brevo.com/) 查看当前 Free 条件，不开付费方案；免费限额和发送资格以控制台为准。

1. 自行注册、完成邮箱及账号审核。用于本人请求的验证码，而非营销群发。
2. 创建并验证发件人；如要求域名认证，只有控制该域名才设置 DNS。无域名时先向平台确认可用发件身份，不借用他人域名，也不假定 Gmail 天然能通过认证。
3. 本人创建事务邮件 API Key，私下保存至 Render Environment；不要发给我。
4. 设置 `MAIL_PROVIDER=BREVO`、`BREVO_API_KEY=<秘密>`、`MAIL_FROM=<已批准发件邮箱>`，重启应用。
5. 先只向自己的收件箱测试，检查垃圾箱及平台状态。请求受理不等于实际送达。

依据：[Brevo 官方事务邮件接口](https://developers.brevo.com/docs/send-a-transactional-email)。服务地址固定为 HTTPS 官方 API，不向任意网关发送秘密。

## 本机 SMTP 备选

设置 `SMTP_HOST`、`SMTP_PORT`、`SMTP_USER`、`SMTP_PASSWORD`、`SMTP_FROM`；不设置 MAIL_PROVIDER=BREVO。587 强制 STARTTLS，465 强制 TLS，均验证服务器身份，不允许跳过证书校验。

如用 Gmail，通常需先启用两步验证，再由本人创建应用专用密码，且受组织策略限制。不是填写普通 Google 密码。见 [Google 官方说明](https://support.google.com/accounts/answer/185833?hl=zh-Hans)。常见主机 smtp.gmail.com、端口 587；这条路径不适用 Render Free 的上述限制。

## 手机：暂不承诺免费或国内可靠送达

本版提供 Twilio HTTPS Messages 适配器，配置 `TWILIO_ACCOUNT_SID`、`TWILIO_AUTH_TOKEN`、`TWILIO_FROM`。实际发件身份、目的地许可、额度、实名或签名审核须先具备。不要默认充值、买号码或开订阅。

针对 +86，[Twilio 中国短信指引](https://www.twilio.com/en-us/guidelines/cn/sms) 明确不保证送达。若供国内用户使用，应先确认国内短信平台主体实名、验证码模板/签名和计费，再选定供应商增加对应适配器；现阶段不能声称这一步已完成。

不愿付费时可先用原账号密码和邮件功能评审。按本次严格“双联系方式验证”规格，自助注册需要两通道均配置；缺一明确暂停，不能用固定验证码、公开万能码或假发送替代。若以后改为“仅邮箱验证、手机待绑定”，需要明确需求变更，不静默降低标准。

## 开通后验收顺序

默认每日发送总预算 50 次（上海日历日，包含失败请求），可用 AUTH_DAILY_SEND_LIMIT 按实际预算调整。此限额不能替代服务商账单上限和反滥用控制；开通付费短信前务必核对。

1. 自己的手机/邮箱实际收到验证码；失败查看请求编号及服务商状态，不反复点击。
2. 错误、过期、重发前旧码、重复使用均被拒绝。
3. 新患者双验证注册得到自动账号，只能看本人空间。
4. 管理员预登记合成员工，安全交付激活码；本人激活后核对岗位与诊所。
5. 手机/邮箱密码登录及验证码登录；找回后旧密码和旧会话失效。
6. 核对发送额度、账单保护、HTTPS、安全 Cookie、日志脱敏和数据库备份。

建议先完成邮件，再决定短信。只需告诉我“已注册 / 发件人已批准 / 已填秘密 / 已收到测试邮件”等进度，不需要任何密钥。
