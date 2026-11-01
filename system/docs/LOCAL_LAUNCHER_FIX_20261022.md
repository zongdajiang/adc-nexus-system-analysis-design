# 桌面启动器修复 · 2026-10-22

修复范围仅为 Windows 本地启动器，不改变 Java 程序、数据库模型、账户、权限或业务数据，也不设置 Windows 自动登录启动。

## 已修正的问题

旧 `Start` 成功分支未执行 `KeepOpen`，导致启动完成即关闭结果窗口；快捷方式没有 `-NoExit`，脚本加载或参数等早期错误也可能来不及看清。用户现有三个入口位于桌面 `ADC` 文件夹，原位置保持不变。

- 三个快捷方式均改为 Windows 自带 `WindowsPowerShell/v1.0/powershell.exe`，不再依赖 Codex 缓存目录中的 PowerShell 可执行文件。
- 添加 `-NoLogo -NoProfile -NoExit`，执行完成及出错后保留结果窗口，并显式设置普通可见窗口。
- 统一显示操作、项目位置、健康状态、版本及关闭窗口说明；诊断文本另存到 `%LOCALAPPDATA%\ADC-Nexus\logs`。
- 修正直接调用 `local-server.ps1 -KeepOpen` 时成功启动不等待的问题。
- 兼容 Windows PowerShell 5.1 的 Java 版本检测：Java 将版本写到 stderr，正常版本输出不应被误判为运行失败。没有放宽系统执行策略。
- 安装脚本保留已有桌面/ADC 归档位置，不重复创建入口，不覆盖其他项目配置或无关快捷方式。

## 如何使用

打开桌面 `ADC` 文件夹：

1. `ADC Nexus - Start`：启动网站。看到 `ONLINE http://localhost:8087` 表示服务已就绪。
2. `ADC Nexus - Status`：只检查当前状态；`OFFLINE` 表示服务尚未运行，不代表数据被删除。
3. `ADC Nexus - Stop`：确实不再使用网站时才点击，会停止本启动器拥有的 Java 服务。

读完结果后点击窗口右上角 X 即可。**关闭 Start / Status 的结果窗口不会停止已运行的网站；不要为了关窗口点击 Stop。** 如果看到红色 `ERROR`，窗口不会自动消失，可提供错误文字；不要上传口令或完整患者资料。

电脑重启后仍需使用 Start；本次没有擅自设置系统自动启动。`localhost` 仍是本机地址，不是公网持续在线的托管链接。

## 验证边界

已在 Windows PowerShell 5.1 中执行与快捷方式相同的目标程序及脚本参数（测试追加 `NoBrowser` 防止重复打开浏览器），确认 Start / Status / Stop 的结果和交互命令行仍保持；退出启动结果会话后通过真实 HTTP 健康接口验证 Java 后台仍在线。另以独立缺失项目配置测试出错留屏和日志，不修改实际配置。

未通过鼠标自动双击桌面快捷方式，不将命令行集成检查冒充鼠标 UI 检查。快捷方式实际保存的路径、NoExit 参数和普通窗口设置已通过 Windows Shell COM 读回核验。核心入口仍只停止通过 PID、可执行路径、JAR 路径和进程开始时间共同识别的自有 Java 进程。
