# Open Dental 26.2 结构研究

完整 XML 已解析：430 张表、4493 列。以下仅列公开结构事实；属性 fk 是文档声明，不等同于已核验的数据库约束。

| 表 | 列数 | 文档标注主键 | 文档引用目标 |
|---|---:|---|---|
| adjustment | 15 | AdjNum | clinic, definition, patient, procedurelog, provider, statement, userod |
| appointment | 36 | AptNum | appointment, appointmenttype, clinic, definition, employee, insplan, operatory, patient, provider, userod |
| asapcomm | 24 | AsapCommNum | appointment, clinic, emailmessage, patient, schedule, smstomobile, userod |
| clinic | 42 | ClinicNum | definition, emailaddress, medlab, provider |
| commlog | 17 | CommlogNum | definition, patient, program, referral, userod |
| confirmationrequest | 21 |  | appointment, apptreminderrule, clinic, patient, smsfrommobile, smstomobile |
| definition | 8 | DefNum |  |
| grouppermission | 6 | GroupPermNum | usergroup |
| operatory | 14 | OperatoryNum | clinic, definition, provider |
| patient | 84 | PatNum | clinic, county, definition, employer, feesched, patient, provider, site, userod |
| payment | 23 | PayNum | clinic, definition, deposit, patient, userod |
| paysplit | 21 | SplitNum | adjustment, clinic, definition, patient, payment, payplan, payplancharge, procedurelog, provider, userod |
| procedurecode | 37 | ProcCode | definition, procedurecode, provider |
| procedurelog | 68 | ProcNum | appointment, clinic, definition, patient, procedurecode, procedurelog, provider, referral, repeatcharge, site, statement, userod |
| procnote | 11 | ProcNoteNum | patient, procedurelog, userod |
| provider | 48 | ProvNum | claimform, definition, feesched, glidewellacct, provider, schoolclass |
| recall | 16 | RecallNum | definition, patient, recalltype |
| recalltype | 6 | RecallTypeNum |  |
| schedule | 12 | ScheduleNum | clinic, definition, employee, provider |
| scheduleop | 3 | ScheduleOpNum | operatory, schedule |
| securitylog | 12 | SecurityLogNum | patient, userod |
| treatplan | 21 | TreatPlanNum | document, mobileappdevice, patient, userod |
| treatplanattach | 4 | TreatPlanAttachNum | definition, procedurelog, treatplan |
| usergroup | 3 | UserGroupNum | usergroup |
| userod | 24 | UserNum | clinic, employee, provider, tasklist, userod |

本系统迁移原则：机构、场地、人员、排班和项目目录分开；临床计划与实施、收款及分摊分开；复诊/联系和预约状态分开；权限与审计独立。海外保险和收费代码不能直接移植。

原始来源：https://www.opendental.com/OpenDentalDocumentation26-2.xml
SHA256：882c84880af7d6ecc347b9b0ca758f0a4126d028f7d051219a113e6358d78834
