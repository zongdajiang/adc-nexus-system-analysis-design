# 首次发布 · 两个账号，两步配置

适用于已注册 Neon、Render，但尚未创建项目的情况。可在平时使用的 Chrome / Edge 中完成，不需要 Codex 插件、Google 密码或 API Key。

## 第一步：创建专用免费数据库

打开 [Neon 控制台](https://console.neon.tech)。看到 `Create project` 或 `New project` 后，输入名称 `adc-nexus-course`，保持 Free，区域优先选择 Singapore 或相近可用区域。默认数据库 `neondb` 无需改名。若已存在专用空项目，不重复创建。

创建成功后进入项目，点 `Connect`。启用连接池（Pooling），选 PostgreSQL 连接串并复制。内容通常以 `postgresql://` 开头，包含密码及 `sslmode=require`。连接串只在下一步粘贴到 Render 的秘密变量；不要放进聊天、GitHub、说明文档或截图。

## 第二步：用预填配置发布 Java 系统

在同一普通浏览器打开 [Deploy to Render](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2Fzongdajiang%2Fadc-nexus-system-analysis-design)。登录后，审核仓库 `zongdajiang/adc-nexus-system-analysis-design`、分支 `main`，配置文件为根目录 `render.yaml`。

服务应为一个名叫 `adc-nexus-jdbc` 的 Docker Web Service，实例类型 **Free**。在 `DATABASE_URL` 输入框粘贴上一步的 Neon 连接串。管理员随机密码由 Render 生成，不需要填 Google 密码。其他环境变量、构建目录和健康检查由文件预填。核对费用为 $0，再启动部署；如出现银行卡或付费要求，暂不继续。

等待服务状态变为 `Live`，打开平台实际给出的 `https://…onrender.com` 地址。这个地址才是待验收的公网系统链接，不使用 localhost 交给老师。

如果按钮要求先连接 GitHub，且你不想授权 GitHub 应用，可改用 [完整手册](DEPLOYMENT.md) 的 `New → Web Service → Public Git Repository` 方法，手动录入同一配置。

## 发布后交接

只需把公开系统网址告诉协作者；不要提供数据库连接串或管理员密码。之后执行 HTTPS、角色范围、完整业务路径、刷新、托管重启与数据持久化验收。`Live` 不等于所有业务已验收，最终报告在这些检查完成后更新。

平台界面会调整，以实际免费套餐和控制台字段为准。说明依据：[Render 部署按钮](https://render.com/docs/deploy-to-render)、[Blueprint 及秘密变量](https://render.com/docs/blueprint-spec)、[Neon 控制台](https://console.neon.tech)。
