# 1.5 诊所基础配置与复诊跟进

实施日期：2026-10-30。此文件是软件增量规格，原 83 页分析设计报告尚未改写。来源、决定和逐项追踪见 [升级工作台](../upgrade-workbench/2026-10-30/README.md) 及 [变更台账](../upgrade-workbench/2026-10-30/CHANGE_LEDGER.md)。

## 来源与取舍

完整解析老师给出的 Open Dental 26.2 XML：430 表、4493 列、875 个文档声明的引用列。这些是文档结构事实，不等同于实际数据库已执行的外键。以官方预约、临床、计划、管理和设置手册核对含义；只读进入 DentalPin 公开演示，观察首页任务、设置分组、诊室、人员、治疗目录及复诊联系清单。未安装 Open Dental Windows 试用版，也未复制第三方品牌、素材或病例。

采用“基础配置影响真实业务”“建议、联系、正式预约分别留痕”的逻辑。保留本系统更严格的岗位权限、接诊完成与财务期间守卫；不移植美国保险、CDT 或欧洲税法。

## 基础配置

现有 `/api/resources` 增加以下显式操作；所有请求使用现有事务锁、CSRF、幂等及重新授权。禁止由客户端指定任意表名或列名。

| action | 授权 / 范围 | 合同 |
|---|---|---|
| clinic_profile | clinic.manage；新建须总部范围，编辑限授权诊所 | 代码创建后不可变；名称、城市、地址、联系、容量和状态；容量不能低于已配置的有效牙椅数 |
| dentist_profile | workforce.manage + 总部范围 | 新建编号 ADC-DR-六位数字；独立医师档案，不自动创建账号或授予岗位；邮箱唯一，编号不可变 |
| chair_profile | resource.manage + 牙椅所属诊所 | 资料、诊室、设备数组、无障碍与状态；不能通过编辑转移诊所；数量受容量约束 |
| opening_hours | resource.manage + 诊所 | 每周逐日时段及时间粒度；变更会使有效预约失去营业覆盖时整笔拒绝 |
| catalog_version | catalog.manage + 总部范围 | 全局目录新建或追加版本，整数分金额、时长、生效期、逐项必需资质；替换版本须未来生效 |
| catalog_retire | catalog.manage + 总部范围 | 保留版本与引用；有受影响预约或未结束计划时拒绝停用 |

编辑以完整行指纹检查并发，新增/变更记录审计前值、后值及修改理由。诊所/医师/牙椅停用之前检查现有预约及在诊记录；开始接诊再次核对医师与诊所处于有效状态。旧目录截断日期之前检查已约服务；受影响时要求先协调改约，不自动更换既有预约项目。实际治疗和已开单金额保持原快照。

界面沿用现有“组织与资源”的六个分区。诊所表下逐店查看每周营业时间；医师档案与跨店任职分表；牙椅设备不显示原始 JSON；目录标明版本、有效期、估算成本及资质要求。新建诊所不会编造营业时间、牙椅或人员。

## 预约联系确认

`POST /api/appointments/{id}` action=`confirmation`，字段 `version`、`confirmation_state`、`channel`、`reason`。仅未到诊的有效预约可登记。结果 PENDING / CONFIRMED / UNREACHABLE 与预约状态独立；实际联系途径 PHONE / EMAIL / SMS / IN_PERSON。该接口不发送消息，必须记录已发生的联系依据。每次登记增加预约版本并追加状态历史；改期重置联系确认为 PENDING。

## 复诊建议与跟进

新增 `patient_followups`、`followup_contact_events` 两表，合计实施模型 **71 表 / 146 外键**。原 61 表 / 730 字段 / 119 外键依然是独立的原报告基线，不改写其统计。

`GET /api/followups` 返回授权范围的建议列表（最多 600 条）；`GET /api/followups/{id}` 返回建议、联系许可和追加事件。负责医师限本人建议；有跟进权的前台才取得联系号码。管理员、收费员、患者不因此获得随访查询权限。

`POST /api/followups` 使用以下动作，更新请求统一用 `version` 比对建议 `revision`：

| action | 岗位 / 主要输入 | 守卫与结果 |
|---|---|---|
| recommend | followup.recommend + clinical.write；visit_id、due_on、priority、reason、contact_allowed | 负责医师基于非取消就诊提出，不自动推算间隔；不得早于今日；同来源同日期不能重复建立有效建议 |
| contact | followup.manage；id、version、channel、outcome、note、next_contact_on | 未获联系许可只允许当面沟通；未接通/另约联系须下次日期；患者婉拒进入 DECLINED |
| link | followup.manage；id、version、appointment_id、note | 仅待安排建议；预约须本人同店、状态有效且服务日期不早于建议日期；原来源就诊不能充当后续复诊；不创建预约 |
| complete | followup.manage；id、version、note | 已关联预约和对应临床就诊均完成，方可进入 COMPLETED |
| reopen | followup.manage；id、version、note | 关联预约已取消/未到诊才可重新安排；保留旧关联事件 |
| cancel | followup.manage；id、version、note | 终止跟进不取消已有预约；原建议和全部联系历史保留 |

前台在“候补与复诊 → 复诊跟进”按状态、联系日期、关键词筛选并处理。医师从就诊页提出建议。界面联系记录不冒充短信或邮件送达，建议不冒充正式预约。初次建议的联系许可是医师核实登记，不能视为第三方法律电子同意证书。

新权限：catalog.manage（总部运营、综合合成演示）；followup.read（前台、医师、经理、总部运营、综合演示）；followup.manage（前台、综合演示）；followup.recommend（医师、综合演示）。管理员仍只负责账号治理。配置与临床等混合岗位以具体权限计算范围，不借总部身份扩大本店修改权。

## 上线与报告同步

本地数据迁移 006 只追加两表及四项权限，不重置账号。迁移前完整备份；迁移后只读比较原有业务行内容与账号凭据，并校验完整性和外键。实际双数据库、浏览器与恢复证据见 `qa/`；云端 HTTPS、重启持久化和正式链接须另行验证。

发布完成后，按台账逐项更新用例、角色矩阵、状态、内部序列、类图、ERD、数据字典、表示层、部署与验收；更新图号、目录和交叉引用，再做系统—报告差异核查。现在不能宣称最终报告已经 100% 同步。
