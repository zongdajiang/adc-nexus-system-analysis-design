# ADC Nexus 系统源码

安德鲁牙科连锁运营管理系统使用 Java 21、JDBC 和原生网页界面。Java 服务及业务权限在 `src/main/java`，数据库迁移在 `src/main/resources/db`，网页资源在 `src/main/resources/web`。

## 构建与本地运行

使用 Java 21 或更新版本，以及 Maven 3.9。先运行 `mvn -B -ntp package`。Windows 上运行 `powershell -File tools/local-server.ps1 -Port 8100 -DailyDemo`，打开 `http://127.0.0.1:8100/#/login`。首次启动使用本地 SQLite 和合成数据。

浏览器复验需要 Python 3、Node.js 和 Chrome。已构建后运行 `python tools/run_responsive_check.py responsive-result`，脚本启动一次性样例库并输出结果。业务回归脚本使用隔离的测试数据库，运行前按脚本配置本机 Java 路径。

## 交付与部署

`deploy/demo/部署指南.md` 对应课程演示。可直接使用服务器部署包中已经核验的 JAR，或自行构建后把 `target/adc-nexus.jar` 放入 `deploy/demo`。需要真实机构部署时另建生产环境，参照根目录的 `DEPLOYMENT.md`。

正式报告和可编辑模型见[项目交付入口](../README.md)。
