# 将本地新版更新到 GitHub

本地仓库已配置远程地址和提交身份，不要重新运行`git init`，也不必再添加`origin`。本次文件已更新，但尚未暂存、提交或推送。

## 1. 打开 PowerShell 并进入仓库

```powershell
cd "C:\Users\Jiangzongda\Desktop\adc-nexus-system-analysis-design"
git status --short
```

看到较多修改、新增和删除是正常的：本轮包含完整新版及过期图源清理。更新前的完整仓库备份位于桌面相邻文件夹`adc-nexus-system-analysis-design_更新前备份_20261020`，不要将它复制进当前仓库。

## 2. 将更新保存为一次提交

依次执行，每条完成后再执行下一条：

```powershell
git add -A
git commit -m "Update complete design report and diagrams to 2026-10-20"
```

`git add`成功时通常没有输出。LF/CRLF提示是换行符提示，不等于失败；仓库已新增换行规则，后续文本统一使用LF。

## 3. 上传到已有仓库

```powershell
git push origin main
```

如弹出浏览器授权，使用`zongdajiang`账号完成授权。不要将密码、验证码或令牌发到聊天中。

看到类似`main -> main`即表示远程分支已更新。再执行：

```powershell
git status
```

正常情况下会显示工作区干净，并与`origin/main`同步。

## 4. 网页核对

打开[仓库首页](https://github.com/zongdajiang/adc-nexus-system-analysis-design)，刷新后检查：

- README显示2026-10-20版本和83页报告。
- 打开“完整设计报告”，确认PDF共83页；PDF第41–44页为四张新状态图。
- “分析设计文档”中出现九张类图和六张内部分析序列的两个新图册。

无需建立新仓库或重新上传ZIP。原报告文件路径未改变，旧链接仍指向新版；旧内容保存在Git提交历史中。

## 遇到错误时

- `non-fast-forward`或`rejected`：先停止，将完整报错发来核对远程变更；不要使用`--force`。
- 连接失败或超时：保留本地提交，网络恢复后再次执行`git push origin main`即可，无须重新添加文件或重复提交。
- `nothing to commit`：检查是否已经提交；这不是上传成功的证明，还要看`git push`结果。
- 推送成功但PDF预览未更新：刷新，或下载文件后核对83页；不要因此删除重建仓库。

上述提交与推送流程对应[GitHub官方说明](https://docs.github.com/en/get-started/using-git/pushing-commits-to-a-remote-repository)。
