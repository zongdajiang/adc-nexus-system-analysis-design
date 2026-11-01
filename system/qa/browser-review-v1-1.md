# 1.1 页面实查记录

2026-10-21，实际运行 Java 21 打包 JAR，http://localhost:8087 。在本机浏览器实查 1280×900 和 390×871 两种断点，完成后恢复浏览器原视口。

- 统一密码登录无岗位选择；手机号/邮箱验证码为登录方式，不是角色入口。
- 未配置真实通道时按钮禁用并明确提示，不显示验证码或假发送成功。
- 独立患者注册、员工激活、手机/邮箱找回页面字段、跳转及说明均可见。
- 注册桌面按姓名、身份、手机、邮箱、密码分组对齐；手机端单列，未发现页面横向溢出。
- 原 trial.dentist 密码登录自动进入临床工作台，无收费/账号管理导航；查看既有就诊，牙位、方案、实施、风险和签署仍可见。
- 原 trial.patient 登录仅有“我的诊疗”和“账号安全”；本人预约、就诊摘要及账单可见。手机导航可收起/展开，宽表格在容器内滚动。
- 退出回统一入口；账号说明弹窗可关闭，不产生“保存业务成功”提示。
- 保留原 7 个密码账号另经真实 HTTP 回归，见 local-migration-v1-1.json。

截图位于 docs/images/：unified-login-desktop.png、unified-login-mobile.png、patient-registration-desktop.png、employee-activation-desktop.png、clinical-workspace-v1-1.png、patient-portal-v1-1.png、patient-portal-mobile-v1-1.png。

新注册/验证码/找回的提交由隔离数据库 HTTP 测试覆盖，不在浏览器里设置新密码或向真实服务发送验证码。界面观测、接口测试、真实供应商送达、托管发布是四种不同证据；不能互相替代。
