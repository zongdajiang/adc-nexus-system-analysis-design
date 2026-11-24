# ADC Nexus 部署手册

项目使用 Java 21、JDBC、PostgreSQL 和同源静态前端。生产首次启动运行事务化迁移，只创建机构、角色、当前核算期及权限管理员。诊所、人员、目录和业务数据由授权岗位配置。课程演示使用独立数据库与独立域名，配置 `APP_ENV=DEMO`、`DEMO_MODE=true`、`SEED_DATA=true`。演示环境禁用真实验证码发送。

课程演示可设置 `DEMO_SCENARIO_MODE=daily`，启用连续三日的合成日程。公开试用时确认昨天、今天和明天均能在预约日历切换，并抽查已完成的样例和其病历、收费单。生产环境由真实预约决定日历内容。

## 1. 构建与准备

```sh
mvn -B -ntp package
docker build -t adc-nexus:release .
```

也可用 Java 21 直接运行 `target/adc-nexus.jar`。项目为原生 JavaScript，前端静态资源随 JAR 提供。

- **Pending** 准备域名、HTTPS 证书、Java 或 Docker 主机、独立 PostgreSQL 和备份存储。为应用分配专用非超级用户，授予目标数据库、目标 schema 及应用表所需权限。首次迁移要求该角色可创建 schema 中的表与索引。
- 将 [.env.example](.env.example) 复制到服务器私有配置目录并限制读取权限。用基础设施秘密管理或受保护的环境文件传入。JAR 自身不读取 `.env`。
- **Pending** 设置 `PUBLIC_ORIGIN` 为外部 HTTPS 源，含协议和域名，末尾不带斜线。设置 `DATABASE_URL`、机构名称和独有的随机管理员密码。数据库密码如含 URL 保留字符，应按 URI 规则编码。校验数据库证书和主机名。对于容器，确保 CA 根证书可由 JDBC 在容器内读取。
- 在私有数据库中单独演练初始化及恢复。生产迁移前保存旧 JAR 或镜像、哈希、数据库备份和迁移版本列表。暂停写入、以单实例启动目标构建。迁移失败应先保留日志和数据，检查数据库权限及变更记录。

| 环境变量 | 生产作用 |
| --- | --- |
| `APP_ENV` | `PRODUCTION`。启用强制 HTTPS Cookie 和显式来源校验 |
| `SEED_DATA`、`DEMO_MODE` | `false`。启动会拒绝开启样例或已有演示账号的库 |
| `DATABASE_URL` | 专用 PostgreSQL 连接串，按秘密保存 |
| `PUBLIC_ORIGIN` | 浏览器访问的唯一 HTTPS 源 |
| `ORGANIZATION_NAME`、`ADMIN_PASSWORD` | 空库初始化所需。初始化后清除密码环境变量 |
| `PORT`、`BIND_ADDRESS` | 容器里监听 10000。用宿主机回环端口发布。直接运行 JAR 时绑定 `127.0.0.1` |
| 邮件及短信 | 可选。完成机构真实通道验证后再启用，参考 [渠道配置](docs/CHANNEL_SETUP.md) |

## 2. 启动、反向代理和账号

```sh
docker run -d --name adc-nexus --restart unless-stopped \
  --env-file /etc/adc-nexus/production.env \
  -p 127.0.0.1:10000:10000 adc-nexus:release

curl -f http://127.0.0.1:10000/api/health
```

反向代理将域名的 HTTPS 请求转给 `127.0.0.1:10000`，原样传递 Host，并由代理设置 `X-Forwarded-Proto https`。公网只开放必要的入口，应用与 PostgreSQL 端口留在回环或私网。代理对登录、验证码等入口做每来源限流并在超限时返回 429。建议先验证代理限流不会影响共同出口下的正常员工。参考 [Nginx 限流说明](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html)。

首次通过 HTTPS 登录 `owner`，更改密码并清除初始化环境变量。管理员负责授权，不默认接诊或收费。分别建立总部和诊所岗位，按实际任职绑定人员、诊所、医师与资质。在系统内配置真实诊所、营业时间、牙椅和项目目录，然后完成账期及权限核对。注册和找回密码只有配置真实校验通道时才能对外承诺交付。

## 3. 监控、备份和恢复

监控 `/api/health`、请求错误率、持续 500、数据库连接与磁盘空间、登录限流及备份年龄。保留受限的服务日志和应用审计，按机构规定设置轮转及保留期。采集请求编号、状态和耗时即可排查多数问题。日志采集规则应排除请求体、Cookie、认证头、查询参数及数据库连接串。

```sh
# 通过受保护的环境或服务配置选择连接。示例使用 PostgreSQL 服务名。
PGSERVICE=adc_prod pg_dump -Fc --file=adc-preflight.dump
PGSERVICE=adc_restore pg_restore --single-transaction --exit-on-error \
  --no-owner --no-privileges --dbname=adc_restore adc-preflight.dump
```

备份写入加密、访问受限的独立存储。恢复目标必须是新建的隔离数据库。验证迁移版本、主外键、就诊与账单关联、流水合计及应用启动。定期做恢复演练，正式启用前确定机构的恢复时间、恢复点目标和生产备份策略。参考 [pg_dump](https://www.postgresql.org/docs/current/app-pgdump.html) 和 [pg_restore](https://www.postgresql.org/docs/current/app-pgrestore.html)。

回滚先暂停业务写入并保护当前数据库。如果旧版本兼容本次迁移，可以切回已校验的旧镜像。否则恢复升级前备份到隔离库并核对升级后的新增交易，再按批准步骤切换。不要把向后恢复直接覆盖已产生新业务的库。

## 4. 发布后 Smoke Test

- **Pending** 在目标域名验证 HTTPS、HTTP 跳转、代理响应、健康检查和 Cookie 标志。确认前端生产登录页没有演示凭据。
- **Pending** 核对权限管理员登录、登出、过期会话，验证六岗位导航、直接访问权限及跨店隔离。
- **Pending** 用预生产专用测试档案走通预约、签到、诊疗、结算、退款与统计。正式库只执行机构批准的核查。
- **Pending** 核对日志、告警、备份和恢复，复核 SMTP/SMS、数据访问规则及机构政策。由机构完成适用的医疗数据和隐私合规评估。
