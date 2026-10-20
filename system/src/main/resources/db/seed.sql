-- ADC Nexus deterministic platform seed.
-- This is application seed data, not a migration. It is safe to re-run.

INSERT OR IGNORE INTO organizations
  (id, code, name_en, name_zh, timezone, currency, status)
VALUES
  ('org-adc', 'ADC', 'Andrew''s Dental Clinics', '安德鲁牙科连锁诊所', 'Asia/Shanghai', 'CNY', 'ACTIVE');

INSERT OR IGNORE INTO clinics
  (id, organization_id, code, name_en, name_zh, city_en, city_zh, address_en, address_zh, chair_capacity, status)
VALUES
  ('cln-tianhe', 'org-adc', 'GZ-TH', 'Tianhe Flagship', '天河旗舰诊所', 'Guangzhou', '广州', 'Tianhe District', '天河区', 12, 'ACTIVE'),
  ('cln-nanshan', 'org-adc', 'SZ-NS', 'Nanshan Coastal', '南山滨海诊所', 'Shenzhen', '深圳', 'Nanshan District', '南山区', 10, 'ACTIVE'),
  ('cln-chancheng', 'org-adc', 'FS-CC', 'Chancheng Central', '禅城中心诊所', 'Foshan', '佛山', 'Chancheng District', '禅城区', 8, 'ACTIVE'),
  ('cln-xiangzhou', 'org-adc', 'ZH-XZ', 'Xiangzhou Bay', '香洲湾诊所', 'Zhuhai', '珠海', 'Xiangzhou District', '香洲区', 7, 'ACTIVE');

INSERT OR IGNORE INTO clinics
  (id, organization_id, code, name_en, name_zh, city_en, city_zh, address_en, address_zh, phone, email, chair_capacity, status, opened_on)
VALUES
  ('cln-yuexiu', 'org-adc', 'GZ-YX', 'Yuexiu Heritage', '越秀臻选诊所', 'Guangzhou', '广州', '18 Huanshi East Road, Yuexiu', '越秀区环市东路18号', '020-8768-2101', 'yuexiu@adc.example', 8, 'ACTIVE', '2016-03-18'),
  ('cln-haizhu', 'org-adc', 'GZ-HZ', 'Haizhu Riverside', '海珠江畔诊所', 'Guangzhou', '广州', '88 Xingang Central Road, Haizhu', '海珠区新港中路88号', '020-8768-2102', 'haizhu@adc.example', 7, 'ACTIVE', '2018-07-09'),
  ('cln-panyu', 'org-adc', 'GZ-PY', 'Panyu Family', '番禺家庭诊所', 'Guangzhou', '广州', '36 Hanxi Avenue, Panyu', '番禺区汉溪大道36号', '020-8768-2103', 'panyu@adc.example', 6, 'ACTIVE', '2021-11-22'),
  ('cln-futian', 'org-adc', 'SZ-FT', 'Futian Central', '福田中心诊所', 'Shenzhen', '深圳', '208 Fuhua Road, Futian', '福田区福华路208号', '0755-2668-3101', 'futian@adc.example', 11, 'ACTIVE', '2017-05-12'),
  ('cln-luohu', 'org-adc', 'SZ-LH', 'Luohu Gateway', '罗湖口岸诊所', 'Shenzhen', '深圳', '66 Renmin South Road, Luohu', '罗湖区人民南路66号', '0755-2668-3102', 'luohu@adc.example', 7, 'ACTIVE', '2019-09-16'),
  ('cln-baoan', 'org-adc', 'SZ-BA', 'Baoan Innovation', '宝安创新诊所', 'Shenzhen', '深圳', '128 Chuangye First Road, Baoan', '宝安区创业一路128号', '0755-2668-3103', 'baoan@adc.example', 8, 'ACTIVE', '2022-06-08'),
  ('cln-shunde', 'org-adc', 'FS-SD', 'Shunde Harmony', '顺德和悦诊所', 'Foshan', '佛山', '52 Daliang East Road, Shunde', '顺德区大良东路52号', '0757-8338-4101', 'shunde@adc.example', 6, 'ACTIVE', '2020-01-10'),
  ('cln-nanhai', 'org-adc', 'FS-NH', 'Nanhai Lakeside', '南海湖畔诊所', 'Foshan', '佛山', '99 Guicheng South Road, Nanhai', '南海区桂城南路99号', '0757-8338-4102', 'nanhai@adc.example', 6, 'ACTIVE', '2021-04-26'),
  ('cln-pengjiang', 'org-adc', 'JM-PJ', 'Pengjiang Wellness', '蓬江康健诊所', 'Jiangmen', '江门', '27 Baishi Avenue, Pengjiang', '蓬江区白石大道27号', '0750-3888-5101', 'pengjiang@adc.example', 6, 'ACTIVE', '2022-10-17'),
  ('cln-nancheng', 'org-adc', 'DG-NC', 'Nancheng Horizon', '南城天际诊所', 'Dongguan', '东莞', '168 Hongfu Road, Nancheng', '南城街道鸿福路168号', '0769-2288-6101', 'nancheng@adc.example', 8, 'ACTIVE', '2023-02-13'),
  ('cln-shiqi', 'org-adc', 'ZS-SQ', 'Shiqi Family', '石岐家庭诊所', 'Zhongshan', '中山', '45 Sunwen East Road, Shiqi', '石岐街道孙文东路45号', '0760-8888-7101', 'shiqi@adc.example', 6, 'ACTIVE', '2023-08-21');

UPDATE clinics SET phone = '020-8768-2001', email = 'tianhe@adc.example', address_en = '228 Tianhe North Road, Tianhe', address_zh = '天河区天河北路228号', opened_on = '2013-05-06' WHERE id = 'cln-tianhe';
UPDATE clinics SET phone = '0755-2668-3001', email = 'nanshan@adc.example', address_en = '1008 Houhai Avenue, Nanshan', address_zh = '南山区后海大道1008号', opened_on = '2015-10-19' WHERE id = 'cln-nanshan';
UPDATE clinics SET phone = '0757-8338-4001', email = 'chancheng@adc.example', address_en = '72 Jihua Fifth Road, Chancheng', address_zh = '禅城区季华五路72号', opened_on = '2018-03-12' WHERE id = 'cln-chancheng';
UPDATE clinics SET phone = '0756-3888-5001', email = 'xiangzhou@adc.example', address_en = '51 Lovers Central Road, Xiangzhou', address_zh = '香洲区情侣中路51号', opened_on = '2019-12-02' WHERE id = 'cln-xiangzhou';

INSERT OR IGNORE INTO roles
  (id, code, name_en, name_zh, description_en, description_zh, is_system, status)
VALUES
  ('rol-hq-admin', 'HQ_ADMINISTRATOR', 'HQ Administrator', '总部系统管理员', 'Governs platform configuration and access.', '负责平台配置和访问治理。', 1, 'ACTIVE'),
  ('rol-hq-ops', 'HQ_OPERATIONS_DIRECTOR', 'HQ Operations Director', '总部运营总监', 'Optimizes the full clinic network.', '负责优化整个诊所网络。', 1, 'ACTIVE'),
  ('rol-clinic-manager', 'CLINIC_MANAGER', 'Clinic Manager', '诊所经理', 'Runs one or more authorized clinics.', '负责一个或多个获授权诊所。', 1, 'ACTIVE'),
  ('rol-receptionist', 'RECEPTIONIST', 'Receptionist', '前台接待', 'Coordinates patient access and scheduling.', '负责患者接待与预约协调。', 1, 'ACTIVE'),
  ('rol-dentist', 'DENTIST', 'Dentist', '牙科医生', 'Delivers and documents clinical care.', '提供并记录临床诊疗。', 1, 'ACTIVE'),
  ('rol-finance', 'FINANCE_ANALYST', 'Finance Analyst', '财务分析师', 'Assures financial completeness and close.', '负责财务完整性和季度结算。', 1, 'ACTIVE'),
  ('rol-patient', 'PATIENT', 'Patient', '患者', 'Accesses personal appointments and records.', '访问本人的预约与记录。', 1, 'ACTIVE'),
  ('rol-demo', 'EXTERNAL_REVIEWER', 'External Reviewer', '外部审阅者', 'Restricted read-only operational review access.', '受限的只读运营审阅权限。', 1, 'ACTIVE');

INSERT OR IGNORE INTO permissions
  (id, code, domain, description_en, description_zh)
VALUES
  ('prm-dashboard-read', 'dashboard.read', 'dashboard', 'View operational dashboards.', '查看运营仪表板。'),
  ('prm-clinic-read', 'clinic.read', 'organization', 'View clinic records.', '查看诊所信息。'),
  ('prm-clinic-manage', 'clinic.manage', 'organization', 'Manage clinic configuration.', '管理诊所配置。'),
  ('prm-patient-read', 'patient.read', 'patient', 'View authorized patient records.', '查看获授权的患者记录。'),
  ('prm-patient-manage', 'patient.manage', 'patient', 'Create and maintain patient records.', '创建并维护患者记录。'),
  ('prm-appointment-read', 'appointment.read', 'appointment', 'View appointment schedules.', '查看预约日程。'),
  ('prm-appointment-manage', 'appointment.manage', 'appointment', 'Create and change appointments.', '创建和修改预约。'),
  ('prm-clinical-read', 'clinical.read', 'clinical', 'View authorized clinical records.', '查看获授权的临床记录。'),
  ('prm-clinical-write', 'clinical.write', 'clinical', 'Document clinical care.', '记录临床诊疗。'),
  ('prm-workforce-read', 'workforce.read', 'workforce', 'View workforce and qualifications.', '查看人员与资质。'),
  ('prm-workforce-manage', 'workforce.manage', 'workforce', 'Manage assignments and qualifications.', '管理人员分配与资质。'),
  ('prm-finance-read', 'finance.read', 'finance', 'View authorized financial information.', '查看获授权的财务信息。'),
  ('prm-finance-manage', 'finance.manage', 'finance', 'Manage invoices, payments and close.', '管理发票、付款与结算。'),
  ('prm-analytics-read', 'analytics.read', 'analytics', 'View network analytics.', '查看网络分析。'),
  ('prm-expansion-manage', 'expansion.manage', 'analytics', 'Create and compare expansion scenarios.', '创建并比较扩张方案。'),
  ('prm-audit-read', 'audit.read', 'governance', 'Inspect the audit trail.', '查看审计记录。'),
  ('prm-access-manage', 'access.manage', 'governance', 'Manage roles and access scope.', '管理角色和访问范围。');

INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 'rol-hq-admin', id FROM permissions;

INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 'rol-hq-ops', id FROM permissions
WHERE code IN (
  'dashboard.read', 'clinic.read', 'clinic.manage', 'patient.read',
  'appointment.read', 'appointment.manage', 'clinical.read',
  'workforce.read', 'workforce.manage', 'finance.read', 'analytics.read',
  'expansion.manage', 'audit.read'
);

INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 'rol-demo', id FROM permissions
WHERE code IN ('dashboard.read', 'clinic.read', 'patient.read', 'appointment.read', 'clinical.read', 'workforce.read', 'finance.read', 'analytics.read', 'audit.read');

INSERT OR IGNORE INTO app_users
  (id, auth_subject, email, display_name, preferred_language, status)
VALUES
  ('usr-local-ops', 'local_seedy', 'seedy@sites.test', 'Andrew Zhang', 'zh', 'ACTIVE');

INSERT OR IGNORE INTO user_role_assignments
  (id, user_id, role_id, clinic_id, status, effective_from)
VALUES
  ('ura-local-ops', 'usr-local-ops', 'rol-hq-ops', NULL, 'ACTIVE', '2026-01-01');

INSERT OR REPLACE INTO system_settings
  (organization_id, setting_key, value_json, updated_by_user_id)
VALUES
  ('org-adc', 'supported_languages', '["zh","en"]', 'usr-local-ops'),
  ('org-adc', 'default_language', '"zh"', 'usr-local-ops'),
  ('org-adc', 'incentive_pool_rate', '0.10', 'usr-local-ops');

INSERT OR IGNORE INTO audit_events
  (request_id, actor_user_id, actor_subject, action, entity_type, entity_id, outcome, source, metadata_json)
VALUES
  ('seed-platform-v1', 'usr-local-ops', 'local_seedy', 'PLATFORM_BOOTSTRAPPED', 'ORGANIZATION', 'org-adc', 'SUCCESS', 'SYSTEM', '{"version":"0.2.0","synthetic":true}');

-- Milestone 3: organization capacity, workforce, catalog and Patient 360.
WITH RECURSIVE chair_source(clinic_id, clinic_code, n, max_n) AS (
  SELECT id, lower(replace(code, '-', '')), 1, chair_capacity
  FROM clinics WHERE organization_id = 'org-adc'
  UNION ALL
  SELECT clinic_id, clinic_code, n + 1, max_n
  FROM chair_source WHERE n < max_n
)
INSERT OR IGNORE INTO clinic_chairs
  (id, clinic_id, code, name_en, name_zh, room_name_en, room_name_zh, equipment_json, is_accessible, status)
SELECT
  'chr-' || clinic_code || '-' || printf('%02d', n), clinic_id, printf('C%02d', n),
  'Dental Chair ' || printf('%02d', n), '牙椅 ' || printf('%02d', n),
  'Surgery ' || printf('%02d', ((n - 1) / 2) + 1), '诊室 ' || printf('%02d', ((n - 1) / 2) + 1),
  CASE WHEN n % 4 = 0 THEN '["intraoral-scanner","digital-xray"]' ELSE '["digital-xray"]' END,
  CASE WHEN n = 1 THEN 1 ELSE 0 END, 'ACTIVE'
FROM chair_source;

INSERT OR IGNORE INTO qualification_types
  (id, code, name_en, name_zh, category, description_en, description_zh, status)
VALUES
  ('qlf-general', 'GENERAL_DENTISTRY', 'General Dentistry Registration', '口腔全科执业资格', 'REGISTRATION', 'Core registration for general dental care.', '开展一般口腔诊疗的基础执业资格。', 'ACTIVE'),
  ('qlf-implant', 'IMPLANTOLOGY', 'Implant Dentistry Credential', '种植牙专业资质', 'SPECIALTY', 'Credential for surgical implant placement.', '开展种植体植入手术的专业资质。', 'ACTIVE'),
  ('qlf-ortho', 'ORTHODONTICS', 'Orthodontics Credential', '正畸专业资质', 'SPECIALTY', 'Credential for comprehensive orthodontic care.', '开展综合正畸治疗的专业资质。', 'ACTIVE'),
  ('qlf-endo', 'ENDODONTICS', 'Endodontics Credential', '牙体牙髓专业资质', 'SPECIALTY', 'Advanced endodontic and microscope treatment.', '开展显微根管等牙体牙髓治疗的专业资质。', 'ACTIVE'),
  ('qlf-pedo', 'PEDIATRIC_DENTISTRY', 'Paediatric Dentistry Credential', '儿童口腔专业资质', 'SPECIALTY', 'Credential for paediatric behaviour and care.', '儿童行为管理与口腔诊疗专业资质。', 'ACTIVE'),
  ('qlf-sedation', 'CONSCIOUS_SEDATION', 'Conscious Sedation Permit', '清醒镇静许可', 'PERMIT', 'Permit for approved conscious sedation protocols.', '按规范实施清醒镇静的许可。', 'ACTIVE'),
  ('qlf-cbct', 'CBCT_OPERATOR', 'CBCT Operator Certification', 'CBCT操作认证', 'CERTIFICATION', 'Certification for cone-beam CT operation.', '锥形束CT设备操作认证。', 'ACTIVE');

INSERT OR IGNORE INTO dentists
  (id, employee_code, name_en, name_zh, title_en, title_zh, email, phone, hire_date, employment_status, languages_json, biography_en, biography_zh)
VALUES
  ('dnt-lin-wei', 'ADC-D001', 'Dr. Wei Lin', '林玮医生', 'Chief Clinical Officer', '首席医疗官', 'wei.lin@adc.example', '13800001001', '2013-05-06', 'ACTIVE', '["zh","en"]', 'Implant and restorative lead with network clinical governance responsibility.', '种植与修复学科带头人，负责全网医疗质量治理。'),
  ('dnt-chen-yu', 'ADC-D002', 'Dr. Yu Chen', '陈瑜医生', 'Senior Orthodontist', '资深正畸医生', 'yu.chen@adc.example', '13800001002', '2015-10-19', 'ACTIVE', '["zh","en"]', 'Focuses on digital orthodontics and interdisciplinary planning.', '专注数字化正畸与多学科联合治疗设计。'),
  ('dnt-wang-jie', 'ADC-D003', 'Dr. Jie Wang', '王杰医生', 'Senior Endodontist', '资深牙体牙髓医生', 'jie.wang@adc.example', '13800001003', '2017-02-13', 'ACTIVE', '["zh"]', 'Microscope endodontics and complex retreatment specialist.', '擅长显微根管与复杂再治疗。'),
  ('dnt-li-xin', 'ADC-D004', 'Dr. Xin Li', '李昕医生', 'Paediatric Dentist', '儿童口腔医生', 'xin.li@adc.example', '13800001004', '2018-08-20', 'ACTIVE', '["zh","en"]', 'Paediatric prevention and behaviour management practitioner.', '专注儿童预防保健与行为管理。'),
  ('dnt-zhou-rui', 'ADC-D005', 'Dr. Rui Zhou', '周睿医生', 'Implant Dentist', '种植医生', 'rui.zhou@adc.example', '13800001005', '2016-06-01', 'ACTIVE', '["zh","en"]', 'Implant surgery and guided restoration practitioner.', '擅长种植外科与数字化导板修复。'),
  ('dnt-huang-min', 'ADC-D006', 'Dr. Min Huang', '黄敏医生', 'General Dentist', '全科医生', 'min.huang@adc.example', '13800001006', '2019-04-15', 'ACTIVE', '["zh"]', 'General dentistry with periodontal maintenance focus.', '全科诊疗，重点关注牙周维护。'),
  ('dnt-luo-yi', 'ADC-D007', 'Dr. Yi Luo', '罗毅医生', 'Orthodontist', '正畸医生', 'yi.luo@adc.example', '13800001007', '2020-09-07', 'ACTIVE', '["zh","en"]', 'Clear aligner and adolescent orthodontic care.', '擅长隐形矫治与青少年正畸。'),
  ('dnt-zhang-ning', 'ADC-D008', 'Dr. Ning Zhang', '张宁医生', 'Endodontist', '牙体牙髓医生', 'ning.zhang@adc.example', '13800001008', '2019-12-02', 'ACTIVE', '["zh"]', 'Painless endodontics and vital pulp therapy.', '专注无痛根管与活髓保存。'),
  ('dnt-sun-lan', 'ADC-D009', 'Dr. Lan Sun', '孙岚医生', 'General Dentist', '全科医生', 'lan.sun@adc.example', '13800001009', '2021-03-22', 'ACTIVE', '["zh","en"]', 'Preventive, restorative and family dentistry.', '开展预防、修复与家庭口腔诊疗。'),
  ('dnt-xu-tao', 'ADC-D010', 'Dr. Tao Xu', '徐涛医生', 'Implant Dentist', '种植医生', 'tao.xu@adc.example', '13800001010', '2020-11-09', 'ACTIVE', '["zh"]', 'Full-arch planning and complex implant rehabilitation.', '擅长全口种植规划与复杂重建。'),
  ('dnt-he-qing', 'ADC-D011', 'Dr. Qing He', '何晴医生', 'Paediatric Dentist', '儿童口腔医生', 'qing.he@adc.example', '13800001011', '2022-02-14', 'ACTIVE', '["zh","en"]', 'Child-friendly care and conscious sedation pathways.', '提供儿童友好诊疗与清醒镇静路径。'),
  ('dnt-guo-fan', 'ADC-D012', 'Dr. Fan Guo', '郭帆医生', 'General Dentist', '全科医生', 'fan.guo@adc.example', '13800001012', '2022-07-04', 'ACTIVE', '["zh"]', 'Digital restorative and emergency dental care.', '擅长数字化修复与口腔急诊。'),
  ('dnt-tang-ya', 'ADC-D013', 'Dr. Ya Tang', '唐雅医生', 'Orthodontist', '正畸医生', 'ya.tang@adc.example', '13800001013', '2023-01-09', 'ACTIVE', '["zh","en"]', 'Early orthodontic intervention and aligner therapy.', '专注早期矫治与隐形矫治。'),
  ('dnt-mao-lei', 'ADC-D014', 'Dr. Lei Mao', '毛磊医生', 'General Dentist', '全科医生', 'lei.mao@adc.example', '13800001014', '2023-06-19', 'ACTIVE', '["zh"]', 'Comprehensive general and preventive dentistry.', '提供综合全科与预防性口腔诊疗。');

INSERT OR IGNORE INTO dentist_qualifications
  (id, dentist_id, qualification_type_id, issuing_body, reference_number, issued_on, expires_on, verification_status, verified_at)
VALUES
  ('dq-001','dnt-lin-wei','qlf-general','Guangdong Health Commission','GD-GEN-2013-001','2013-04-18',NULL,'VERIFIED','2026-01-08'),
  ('dq-002','dnt-lin-wei','qlf-implant','Chinese Stomatological Association','CSA-IMP-2018-021','2018-06-20','2028-06-19','VERIFIED','2026-01-08'),
  ('dq-003','dnt-lin-wei','qlf-cbct','ADC Clinical Academy','ADC-CBCT-2024-001','2024-02-12','2027-02-11','VERIFIED','2026-01-08'),
  ('dq-004','dnt-chen-yu','qlf-general','Guangdong Health Commission','GD-GEN-2014-016','2014-07-01',NULL,'VERIFIED','2026-01-08'),
  ('dq-005','dnt-chen-yu','qlf-ortho','Chinese Stomatological Association','CSA-ORT-2019-044','2019-09-18','2029-09-17','VERIFIED','2026-01-08'),
  ('dq-006','dnt-wang-jie','qlf-general','Guangdong Health Commission','GD-GEN-2016-088','2016-05-09',NULL,'VERIFIED','2026-01-08'),
  ('dq-007','dnt-wang-jie','qlf-endo','Chinese Stomatological Association','CSA-END-2020-073','2020-11-12','2026-11-11','VERIFIED','2026-01-08'),
  ('dq-008','dnt-li-xin','qlf-general','Guangdong Health Commission','GD-GEN-2017-103','2017-06-15',NULL,'VERIFIED','2026-01-08'),
  ('dq-009','dnt-li-xin','qlf-pedo','Chinese Stomatological Association','CSA-PED-2021-018','2021-04-20','2031-04-19','VERIFIED','2026-01-08'),
  ('dq-010','dnt-zhou-rui','qlf-general','Guangdong Health Commission','GD-GEN-2015-066','2015-03-02',NULL,'VERIFIED','2026-01-08'),
  ('dq-011','dnt-zhou-rui','qlf-implant','Chinese Stomatological Association','CSA-IMP-2020-066','2020-08-25','2030-08-24','VERIFIED','2026-01-08'),
  ('dq-012','dnt-huang-min','qlf-general','Guangdong Health Commission','GD-GEN-2018-122','2018-10-10',NULL,'VERIFIED','2026-01-08'),
  ('dq-013','dnt-luo-yi','qlf-general','Guangdong Health Commission','GD-GEN-2019-133','2019-07-09',NULL,'VERIFIED','2026-01-08'),
  ('dq-014','dnt-luo-yi','qlf-ortho','Chinese Stomatological Association','CSA-ORT-2022-031','2022-03-14','2032-03-13','VERIFIED','2026-01-08'),
  ('dq-015','dnt-zhang-ning','qlf-general','Guangdong Health Commission','GD-GEN-2018-167','2018-03-19',NULL,'VERIFIED','2026-01-08'),
  ('dq-016','dnt-zhang-ning','qlf-endo','Chinese Stomatological Association','CSA-END-2021-092','2021-12-01','2031-11-30','VERIFIED','2026-01-08'),
  ('dq-017','dnt-sun-lan','qlf-general','Guangdong Health Commission','GD-GEN-2020-201','2020-05-28',NULL,'VERIFIED','2026-01-08'),
  ('dq-018','dnt-xu-tao','qlf-general','Guangdong Health Commission','GD-GEN-2019-212','2019-08-08',NULL,'VERIFIED','2026-01-08'),
  ('dq-019','dnt-xu-tao','qlf-implant','Chinese Stomatological Association','CSA-IMP-2022-087','2022-10-16','2032-10-15','VERIFIED','2026-01-08'),
  ('dq-020','dnt-he-qing','qlf-general','Guangdong Health Commission','GD-GEN-2021-256','2021-07-12',NULL,'VERIFIED','2026-01-08'),
  ('dq-021','dnt-he-qing','qlf-pedo','Chinese Stomatological Association','CSA-PED-2023-044','2023-05-06','2033-05-05','VERIFIED','2026-01-08'),
  ('dq-022','dnt-he-qing','qlf-sedation','Guangdong Dental Quality Center','GDQ-Sed-2025-019','2025-01-15','2026-10-30','VERIFIED','2026-01-08'),
  ('dq-023','dnt-guo-fan','qlf-general','Guangdong Health Commission','GD-GEN-2021-277','2021-11-05',NULL,'VERIFIED','2026-01-08'),
  ('dq-024','dnt-tang-ya','qlf-general','Guangdong Health Commission','GD-GEN-2022-302','2022-08-19',NULL,'VERIFIED','2026-01-08'),
  ('dq-025','dnt-tang-ya','qlf-ortho','Chinese Stomatological Association','CSA-ORT-2024-071','2024-03-01','2034-02-28','VERIFIED','2026-01-08'),
  ('dq-026','dnt-mao-lei','qlf-general','Guangdong Health Commission','GD-GEN-2022-319','2022-09-16',NULL,'VERIFIED','2026-01-08');

INSERT OR IGNORE INTO dentist_clinic_assignments
  (id, dentist_id, clinic_id, is_primary, effective_from, weekly_hours, status)
VALUES
  ('dca-001','dnt-lin-wei','cln-tianhe',1,'2013-05-06',28,'ACTIVE'),
  ('dca-002','dnt-lin-wei','cln-yuexiu',0,'2024-01-01',8,'ACTIVE'),
  ('dca-003','dnt-chen-yu','cln-nanshan',1,'2015-10-19',32,'ACTIVE'),
  ('dca-004','dnt-chen-yu','cln-futian',0,'2025-01-06',8,'ACTIVE'),
  ('dca-005','dnt-wang-jie','cln-chancheng',1,'2017-02-13',32,'ACTIVE'),
  ('dca-006','dnt-wang-jie','cln-nanhai',0,'2025-03-03',8,'ACTIVE'),
  ('dca-007','dnt-li-xin','cln-tianhe',1,'2018-08-20',32,'ACTIVE'),
  ('dca-008','dnt-li-xin','cln-panyu',0,'2023-04-03',8,'ACTIVE'),
  ('dca-009','dnt-zhou-rui','cln-nanshan',1,'2016-06-01',32,'ACTIVE'),
  ('dca-010','dnt-zhou-rui','cln-baoan',0,'2024-07-01',8,'ACTIVE'),
  ('dca-011','dnt-huang-min','cln-yuexiu',1,'2019-04-15',40,'ACTIVE'),
  ('dca-012','dnt-luo-yi','cln-futian',1,'2020-09-07',32,'ACTIVE'),
  ('dca-013','dnt-luo-yi','cln-luohu',0,'2025-02-03',8,'ACTIVE'),
  ('dca-014','dnt-zhang-ning','cln-xiangzhou',1,'2019-12-02',40,'ACTIVE'),
  ('dca-015','dnt-sun-lan','cln-shunde',1,'2021-03-22',32,'ACTIVE'),
  ('dca-016','dnt-sun-lan','cln-nanhai',0,'2024-08-05',8,'ACTIVE'),
  ('dca-017','dnt-xu-tao','cln-nancheng',1,'2020-11-09',32,'ACTIVE'),
  ('dca-018','dnt-xu-tao','cln-shiqi',0,'2025-04-07',8,'ACTIVE'),
  ('dca-019','dnt-he-qing','cln-pengjiang',1,'2022-02-14',40,'ACTIVE'),
  ('dca-020','dnt-guo-fan','cln-haizhu',1,'2022-07-04',40,'ACTIVE'),
  ('dca-021','dnt-tang-ya','cln-baoan',1,'2023-01-09',40,'ACTIVE'),
  ('dca-022','dnt-mao-lei','cln-panyu',1,'2023-06-19',40,'ACTIVE');

INSERT OR IGNORE INTO treatment_catalog
  (id, code, name_en, name_zh, category, description_en, description_zh, duration_minutes, standard_price_fen, estimated_cost_fen, version, effective_from, status)
VALUES
  ('trt-exam-v1','EXAM-001','Comprehensive oral examination','全面口腔检查','PREVENTIVE','Network-standard comprehensive assessment.','全网标准化综合口腔检查。',30,28000,4500,1,'2026-01-01','ACTIVE'),
  ('trt-clean-v1','PERIO-010','Ultrasonic scaling','超声洁治','PERIODONTICS','Routine scaling and oral hygiene guidance.','常规洁治与口腔卫生指导。',45,48000,8200,1,'2026-01-01','ACTIVE'),
  ('trt-fill-v1','REST-020','Composite restoration','复合树脂修复','RESTORATIVE','Direct tooth-coloured restoration per surface.','按牙面计价的直接树脂修复。',45,68000,16500,1,'2026-01-01','ACTIVE'),
  ('trt-rct-v1','ENDO-030','Microscope root canal therapy','显微根管治疗','ENDODONTICS','Microscope-assisted root canal treatment.','显微镜辅助根管治疗。',90,268000,72000,1,'2026-01-01','ACTIVE'),
  ('trt-crown-v1','REST-040','All-ceramic crown','全瓷冠修复','RESTORATIVE','Digital impression and all-ceramic crown.','数字化取模与全瓷冠修复。',75,498000,182000,1,'2026-01-01','ACTIVE'),
  ('trt-implant-v1','IMPL-050','Single implant placement','单颗种植体植入','IMPLANTOLOGY','Guided single implant placement, fixture excluded.','导板辅助单颗种植体植入，不含植体材料。',120,780000,286000,1,'2026-01-01','ACTIVE'),
  ('trt-aligner-v1','ORTH-060','Clear aligner treatment','隐形矫治','ORTHODONTICS','Comprehensive clear aligner treatment pathway.','完整隐形矫治治疗路径。',60,2880000,1060000,1,'2026-01-01','ACTIVE'),
  ('trt-braces-v1','ORTH-061','Fixed appliance orthodontics','固定托槽矫治','ORTHODONTICS','Comprehensive fixed appliance treatment.','完整固定托槽矫治。',60,1980000,580000,1,'2026-01-01','ACTIVE'),
  ('trt-pedo-v1','PEDO-070','Paediatric preventive visit','儿童预防性诊疗','PAEDIATRICS','Child examination, fluoride and guidance.','儿童检查、涂氟与家庭指导。',30,38000,9500,1,'2026-01-01','ACTIVE'),
  ('trt-sedation-v1','SED-080','Conscious sedation support','清醒镇静支持','SEDATION','Monitored conscious sedation service.','经监护的清醒镇静服务。',60,128000,42000,1,'2026-01-01','ACTIVE'),
  ('trt-cbct-v1','IMG-090','CBCT imaging','CBCT影像检查','IMAGING','Cone-beam CT acquisition and report.','锥形束CT采集与报告。',20,58000,12000,1,'2026-01-01','ACTIVE'),
  ('trt-whiten-v1','AESTH-100','Chairside whitening','诊室美白','AESTHETICS','Controlled chairside tooth whitening.','受控诊室牙齿美白。',90,168000,38000,1,'2026-01-01','ACTIVE');

INSERT OR IGNORE INTO treatment_qualification_requirements
  (treatment_id, qualification_type_id, requirement_level)
VALUES
  ('trt-rct-v1','qlf-endo','REQUIRED'),
  ('trt-implant-v1','qlf-implant','REQUIRED'),
  ('trt-aligner-v1','qlf-ortho','REQUIRED'),
  ('trt-braces-v1','qlf-ortho','REQUIRED'),
  ('trt-pedo-v1','qlf-pedo','PREFERRED'),
  ('trt-sedation-v1','qlf-sedation','REQUIRED'),
  ('trt-cbct-v1','qlf-cbct','REQUIRED');

INSERT OR IGNORE INTO patients
  (id, patient_code, name_en, name_zh, date_of_birth, gender, phone, email, government_id_last4, preferred_language, communication_channel, primary_clinic_id, status, last_visit_at)
VALUES
  ('pat-0001','ADC-P000001','Xiaoyu Lin','林晓雨','1992-04-16','FEMALE','13800002001','xiaoyu.lin@example.test','4821','zh','WECHAT','cln-tianhe','ACTIVE','2026-09-19T10:20:00+08:00'),
  ('pat-0002','ADC-P000002','Mia Chen','陈米娅','1988-11-03','FEMALE','13800002002','mia.chen@example.test','1307','en','SMS','cln-tianhe','ACTIVE','2026-09-23T09:20:00+08:00'),
  ('pat-0003','ADC-P000003','Leo Huang','黄乐','1979-06-22','MALE','13800002003','leo.huang@example.test','9012','zh','WECHAT','cln-nanshan','ACTIVE','2026-09-23T09:40:00+08:00'),
  ('pat-0004','ADC-P000004','Sophia Lin','林若曦','1995-01-27','FEMALE','13800002004','sophia.lin@example.test','5620','en','EMAIL','cln-chancheng','ACTIVE','2026-09-23T10:00:00+08:00'),
  ('pat-0005','ADC-P000005','Ethan Wu','吴奕辰','1985-08-14','MALE','13800002005','ethan.wu@example.test','7744','zh','WECHAT','cln-xiangzhou','ACTIVE','2026-09-23T10:20:00+08:00'),
  ('pat-0006','ADC-P000006','Yutong Zhao','赵雨桐','2001-02-09','FEMALE','13800002006','yutong.zhao@example.test','2339','zh','WECHAT','cln-futian','ACTIVE','2026-09-18T16:10:00+08:00'),
  ('pat-0007','ADC-P000007','Jian Wang','王健','1968-12-30','MALE','13800002007','jian.wang@example.test','0441','zh','PHONE','cln-yuexiu','ACTIVE','2026-09-17T11:35:00+08:00'),
  ('pat-0008','ADC-P000008','Xinyi Zhang','张心怡','2014-05-08','FEMALE','13800002008','parent.xinyi@example.test','3188','zh','WECHAT','cln-pengjiang','ACTIVE','2026-09-15T14:00:00+08:00'),
  ('pat-0009','ADC-P000009','An Li','李安','1990-09-12','OTHER','13800002009','an.li@example.test','6713','en','EMAIL','cln-haizhu','ACTIVE','2026-09-12T09:00:00+08:00'),
  ('pat-0010','ADC-P000010','Xiao Yu Lin','林晓雨','1992-04-16','FEMALE','13800002991','linxy.alt@example.test','4821','zh','SMS','cln-yuexiu','REVIEW','2025-12-06T15:30:00+08:00'),
  ('pat-0011','ADC-P000011','Zixuan Guo','郭子轩','2017-03-19','MALE','13800002011','parent.zixuan@example.test','1056','zh','WECHAT','cln-panyu','ACTIVE','2026-09-10T10:45:00+08:00'),
  ('pat-0012','ADC-P000012','Yan Tang','唐燕','1957-07-01','FEMALE','13800002012','yan.tang@example.test','8529','zh','PHONE','cln-nancheng','ACTIVE','2026-09-08T08:50:00+08:00');

WITH RECURSIVE patient_numbers(n) AS (
  SELECT 13
  UNION ALL SELECT n + 1 FROM patient_numbers WHERE n < 512
)
INSERT OR IGNORE INTO patients
  (id, patient_code, name_en, name_zh, date_of_birth, gender, phone, email, preferred_language, communication_channel, primary_clinic_id, status, last_visit_at)
SELECT
  'pat-' || printf('%04d', n), 'ADC-P' || printf('%06d', n),
  CASE (n % 16)
    WHEN 0 THEN 'Olivia' WHEN 1 THEN 'Ethan' WHEN 2 THEN 'Sophia' WHEN 3 THEN 'Lucas'
    WHEN 4 THEN 'Amelia' WHEN 5 THEN 'Noah' WHEN 6 THEN 'Grace' WHEN 7 THEN 'Henry'
    WHEN 8 THEN 'Chloe' WHEN 9 THEN 'Leo' WHEN 10 THEN 'Emma' WHEN 11 THEN 'Daniel'
    WHEN 12 THEN 'Lily' WHEN 13 THEN 'Ryan' WHEN 14 THEN 'Zoe' ELSE 'Kevin' END
  || ' ' ||
  CASE ((n / 16) % 32)
    WHEN 0 THEN 'Chen' WHEN 1 THEN 'Lin' WHEN 2 THEN 'Wang' WHEN 3 THEN 'Li'
    WHEN 4 THEN 'Zhang' WHEN 5 THEN 'Liu' WHEN 6 THEN 'Huang' WHEN 7 THEN 'Wu'
    WHEN 8 THEN 'Zhao' WHEN 9 THEN 'Zhou' WHEN 10 THEN 'Xu' WHEN 11 THEN 'Sun'
    WHEN 12 THEN 'Ma' WHEN 13 THEN 'Zhu' WHEN 14 THEN 'Hu' WHEN 15 THEN 'Guo'
    WHEN 16 THEN 'He' WHEN 17 THEN 'Gao' WHEN 18 THEN 'Luo' WHEN 19 THEN 'Zheng'
    WHEN 20 THEN 'Liang' WHEN 21 THEN 'Xie' WHEN 22 THEN 'Song' WHEN 23 THEN 'Tang'
    WHEN 24 THEN 'Deng' WHEN 25 THEN 'Han' WHEN 26 THEN 'Feng' WHEN 27 THEN 'Cai'
    WHEN 28 THEN 'Pan' WHEN 29 THEN 'Yu' WHEN 30 THEN 'Mo' ELSE 'Qian' END,
  CASE ((n / 16) % 32)
    WHEN 0 THEN '陈' WHEN 1 THEN '林' WHEN 2 THEN '王' WHEN 3 THEN '李'
    WHEN 4 THEN '张' WHEN 5 THEN '刘' WHEN 6 THEN '黄' WHEN 7 THEN '吴'
    WHEN 8 THEN '赵' WHEN 9 THEN '周' WHEN 10 THEN '徐' WHEN 11 THEN '孙'
    WHEN 12 THEN '马' WHEN 13 THEN '朱' WHEN 14 THEN '胡' WHEN 15 THEN '郭'
    WHEN 16 THEN '何' WHEN 17 THEN '高' WHEN 18 THEN '罗' WHEN 19 THEN '郑'
    WHEN 20 THEN '梁' WHEN 21 THEN '谢' WHEN 22 THEN '宋' WHEN 23 THEN '唐'
    WHEN 24 THEN '邓' WHEN 25 THEN '韩' WHEN 26 THEN '冯' WHEN 27 THEN '蔡'
    WHEN 28 THEN '潘' WHEN 29 THEN '余' WHEN 30 THEN '莫' ELSE '钱' END
  ||
  CASE (n % 16)
    WHEN 0 THEN '予安' WHEN 1 THEN '嘉宁' WHEN 2 THEN '思远' WHEN 3 THEN '若溪'
    WHEN 4 THEN '子墨' WHEN 5 THEN '欣怡' WHEN 6 THEN '宇辰' WHEN 7 THEN '雨桐'
    WHEN 8 THEN '书瑶' WHEN 9 THEN '浩然' WHEN 10 THEN '佳琪' WHEN 11 THEN '景行'
    WHEN 12 THEN '语彤' WHEN 13 THEN '明轩' WHEN 14 THEN '安然' ELSE '逸凡' END,
  date('1972-01-01', '+' || ((n * 37) % 15000) || ' days'),
  CASE WHEN n % 3 = 0 THEN 'MALE' ELSE 'FEMALE' END,
  '139' || printf('%08d', n), 'patient' || printf('%03d', n) || '@example.test',
  CASE WHEN n % 7 = 0 THEN 'en' ELSE 'zh' END,
  CASE WHEN n % 4 = 0 THEN 'SMS' ELSE 'WECHAT' END,
  CASE (n % 15)
    WHEN 0 THEN 'cln-tianhe' WHEN 1 THEN 'cln-yuexiu' WHEN 2 THEN 'cln-haizhu'
    WHEN 3 THEN 'cln-panyu' WHEN 4 THEN 'cln-nanshan' WHEN 5 THEN 'cln-futian'
    WHEN 6 THEN 'cln-luohu' WHEN 7 THEN 'cln-baoan' WHEN 8 THEN 'cln-chancheng'
    WHEN 9 THEN 'cln-shunde' WHEN 10 THEN 'cln-nanhai' WHEN 11 THEN 'cln-xiangzhou'
    WHEN 12 THEN 'cln-pengjiang' WHEN 13 THEN 'cln-nancheng' ELSE 'cln-shiqi' END,
  'ACTIVE', datetime('2026-01-01', '+' || (n % 240) || ' days')
FROM patient_numbers;

INSERT OR IGNORE INTO emergency_contacts
  (id, patient_id, contact_name, relationship_en, relationship_zh, phone, priority, is_authorized_contact)
VALUES
  ('ec-001','pat-0001','林嘉禾','Spouse','配偶','13800003001',1,1),
  ('ec-002','pat-0002','Chen Wen','Sibling','兄弟姐妹','13800003002',1,1),
  ('ec-003','pat-0003','黄兰','Spouse','配偶','13800003003',1,1),
  ('ec-004','pat-0004','Lin Hui','Parent','父母','13800003004',1,1),
  ('ec-005','pat-0005','吴晓','Spouse','配偶','13800003005',1,1),
  ('ec-006','pat-0008','张悦','Parent / guardian','父母/监护人','13800003008',1,1),
  ('ec-007','pat-0011','郭宁','Parent / guardian','父母/监护人','13800003011',1,1);

INSERT OR IGNORE INTO patient_allergies
  (id, patient_id, substance_en, substance_zh, reaction_en, reaction_zh, severity, status, verified_at, verified_by_dentist_id, notes_en, notes_zh)
VALUES
  ('alg-001','pat-0001','Penicillin','青霉素','Generalised urticaria and facial swelling','全身荨麻疹及面部肿胀','CRITICAL','ACTIVE','2026-09-19T10:24:00+08:00','dnt-lin-wei','Avoid penicillin-class antibiotics; emergency plan reviewed.','避免青霉素类抗生素；已复核应急预案。'),
  ('alg-002','pat-0001','Latex','乳胶','Contact dermatitis','接触性皮炎','MODERATE','ACTIVE','2026-09-19T10:24:00+08:00','dnt-lin-wei','Use latex-free operatory setup.','使用无乳胶诊室配置。'),
  ('alg-003','pat-0003','Ibuprofen','布洛芬','Wheezing','喘鸣','HIGH','ACTIVE','2026-08-04T09:12:00+08:00','dnt-zhou-rui','NSAID sensitivity reported.','患者报告非甾体抗炎药敏感。'),
  ('alg-004','pat-0007','Chlorhexidine','氯己定','Oral mucosal irritation','口腔黏膜刺激','MODERATE','ACTIVE','2026-06-16T11:44:00+08:00','dnt-huang-min','',''),
  ('alg-005','pat-0012','Epinephrine sensitivity','肾上腺素敏感','Palpitations','心悸','LOW','ACTIVE','2026-05-09T08:58:00+08:00','dnt-xu-tao','Not a confirmed allergy; use cardiac dose and monitor.','非确诊过敏；使用心脏剂量并监测。');

INSERT OR IGNORE INTO patient_consents
  (id, patient_id, consent_type, status, policy_version, captured_at, source)
VALUES
  ('con-001','pat-0001','PRIVACY','GRANTED','2026.1','2026-09-19T09:58:00+08:00','PATIENT_PORTAL'),
  ('con-002','pat-0001','CARE_SHARING','GRANTED','2026.1','2026-09-19T09:59:00+08:00','PATIENT_PORTAL'),
  ('con-003','pat-0001','MARKETING','DECLINED','2026.1','2026-09-19T09:59:00+08:00','PATIENT_PORTAL'),
  ('con-004','pat-0002','PRIVACY','GRANTED','2026.1','2026-02-18T12:10:00+08:00','FRONT_DESK'),
  ('con-005','pat-0003','PRIVACY','GRANTED','2026.1','2026-01-07T10:18:00+08:00','FRONT_DESK'),
  ('con-006','pat-0004','PRIVACY','GRANTED','2026.1','2026-03-11T14:25:00+08:00','PATIENT_PORTAL');

INSERT OR IGNORE INTO patient_timeline_events
  (id, patient_id, clinic_id, event_type, occurred_at, title_en, title_zh, description_en, description_zh, reference_type, reference_id, status, amount_fen, metadata_json)
VALUES
  ('pte-001','pat-0001','cln-tianhe','VISIT','2026-09-19T10:20:00+08:00','Restorative visit completed','修复就诊已完成','Composite restoration on tooth 16; allergy precautions acknowledged.','完成16牙复合树脂修复；已确认过敏防护措施。','VISIT','VIS-260919-008','COMPLETED',NULL,'{"dentistId":"dnt-lin-wei","tooth":"16"}'),
  ('pte-002','pat-0001','cln-tianhe','INVOICE','2026-09-19T11:16:00+08:00','Invoice paid','发票已支付','Invoice INV-260919-041 paid by WeChat Pay.','发票 INV-260919-041 已通过微信支付。','INVOICE','INV-260919-041','PAID',68000,'{}'),
  ('pte-003','pat-0001','cln-nanshan','IMAGING','2026-08-26T15:00:00+08:00','CBCT imaging completed','CBCT影像检查已完成','Cross-clinic imaging referral completed.','跨诊所影像转诊已完成。','VISIT','VIS-260826-032','COMPLETED',58000,'{}'),
  ('pte-004','pat-0001','cln-yuexiu','VISIT','2026-04-12T09:30:00+08:00','Preventive review','预防复查','Periodontal review and ultrasonic scaling.','牙周复查与超声洁治。','VISIT','VIS-260412-017','COMPLETED',48000,'{}'),
  ('pte-005','pat-0001','cln-tianhe','PLAN','2026-01-18T11:00:00+08:00','Treatment plan accepted','治疗计划已接受','Patient accepted restorative plan with three phases.','患者已接受分三阶段实施的修复计划。','TREATMENT_PLAN','TPL-260118-006','ACCEPTED',NULL,'{}'),
  ('pte-006','pat-0001','cln-tianhe','APPOINTMENT','2025-12-22T14:30:00+08:00','Appointment completed','预约已完成','Network patient identity confirmed at check-in.','签到时已确认全网患者身份。','APPOINTMENT','APT-251222-084','COMPLETED',NULL,'{}'),
  ('pte-007','pat-0002','cln-tianhe','VISIT','2026-09-23T09:20:00+08:00','Composite restoration in progress','复合树脂修复进行中','Patient checked in and treatment commenced.','患者已签到并开始治疗。','VISIT','VIS-260923-004','IN_TREATMENT',NULL,'{}'),
  ('pte-008','pat-0003','cln-nanshan','APPOINTMENT','2026-09-23T09:40:00+08:00','Periodontal review arrived','牙周复查已到诊','Patient has arrived and awaits operatory assignment.','患者已到诊，等待分配诊室。','APPOINTMENT','APT-260923-019','ARRIVED',NULL,'{}'),
  ('pte-009','pat-0004','cln-chancheng','APPOINTMENT','2026-09-23T10:00:00+08:00','Root canal appointment confirmed','根管治疗预约已确认','Microscope room and qualified dentist reserved.','已预留显微诊室及合资格医生。','APPOINTMENT','APT-260923-027','CONFIRMED',NULL,'{}'),
  ('pte-010','pat-0005','cln-xiangzhou','APPOINTMENT','2026-09-23T10:20:00+08:00','Digital impression confirmed','数字化取模已确认','Scanner-equipped chair reserved.','已预留配备扫描仪的牙椅。','APPOINTMENT','APT-260923-031','CONFIRMED',NULL,'{}');

INSERT OR IGNORE INTO patient_duplicate_reviews
  (id, source_patient_id, candidate_patient_id, match_score, match_reasons_json, status)
VALUES
  ('pdr-001','pat-0001','pat-0010',96,'["same_chinese_name","same_date_of_birth","same_government_id_last4","similar_romanized_name"]','OPEN');

INSERT OR IGNORE INTO audit_events
  (request_id, actor_user_id, actor_subject, action, entity_type, entity_id, outcome, source, metadata_json)
VALUES
  ('seed-master-data-v1', 'usr-local-ops', 'local_seedy', 'MASTER_DATA_SEEDED', 'ORGANIZATION', 'org-adc', 'SUCCESS', 'SYSTEM', '{"version":"0.3.0","clinics":15,"patients":512,"synthetic":true}');

-- Milestone 4: Smart Scheduling, constraint evidence and cancellation recovery.
WITH RECURSIVE weekdays(day_of_week) AS (
  SELECT 0
  UNION ALL SELECT day_of_week + 1 FROM weekdays WHERE day_of_week < 6
)
INSERT OR IGNORE INTO clinic_operating_hours
  (clinic_id, day_of_week, opens_at, closes_at, slot_minutes, is_closed)
SELECT
  clinics.id,
  weekdays.day_of_week,
  CASE WHEN weekdays.day_of_week = 0 THEN '09:00' ELSE '08:30' END,
  CASE WHEN weekdays.day_of_week = 0 THEN '17:00' ELSE '18:30' END,
  10,
  CASE
    WHEN weekdays.day_of_week = 0 AND clinics.id NOT IN ('cln-tianhe','cln-nanshan','cln-futian') THEN 1
    ELSE 0
  END
FROM clinics CROSS JOIN weekdays
WHERE clinics.organization_id = 'org-adc';

WITH RECURSIVE primary_days(day_of_week) AS (
  SELECT 1
  UNION ALL SELECT day_of_week + 1 FROM primary_days WHERE day_of_week < 5
)
INSERT OR IGNORE INTO dentist_availability_rules
  (id, dentist_id, clinic_id, day_of_week, starts_at, ends_at, effective_from, recurrence_rule, status)
SELECT
  'dav-' || replace(assignments.id, 'dca-', '') || '-' || primary_days.day_of_week,
  assignments.dentist_id,
  assignments.clinic_id,
  primary_days.day_of_week,
  '09:00',
  '18:00',
  '2026-01-01',
  'WEEKLY',
  'ACTIVE'
FROM dentist_clinic_assignments assignments
CROSS JOIN primary_days
WHERE assignments.status = 'ACTIVE' AND assignments.is_primary = 1;

INSERT OR IGNORE INTO dentist_availability_rules
  (id, dentist_id, clinic_id, day_of_week, starts_at, ends_at, effective_from, recurrence_rule, status)
SELECT
  'dav-' || replace(id, 'dca-', '') || '-6',
  dentist_id,
  clinic_id,
  6,
  '09:00',
  '17:00',
  effective_from,
  'WEEKLY',
  'ACTIVE'
FROM dentist_clinic_assignments
WHERE status = 'ACTIVE' AND is_primary = 0;

INSERT OR IGNORE INTO dentist_schedule_exceptions
  (id, dentist_id, clinic_id, starts_at, ends_at, exception_type, reason_en, reason_zh, status)
VALUES
  ('dse-001','dnt-chen-yu','cln-nanshan','2026-09-25 13:00:00','2026-09-25 18:00:00','LEAVE','Academic conference','参加学术会议','ACTIVE'),
  ('dse-002','dnt-wang-jie','cln-chancheng','2026-09-24 09:00:00','2026-09-24 12:00:00','TRAINING','Microscope calibration training','显微设备校准培训','ACTIVE'),
  ('dse-003','dnt-lin-wei','cln-tianhe','2026-09-26 14:00:00','2026-09-26 17:00:00','NETWORK_DUTY','Network clinical governance session','全网医疗质量会议','ACTIVE');

WITH RECURSIVE appointment_numbers(n) AS (
  SELECT 1
  UNION ALL SELECT n + 1 FROM appointment_numbers WHERE n < 70
),
roster(slot, clinic_id, dentist_id, chair_id) AS (
  VALUES
    (0,'cln-tianhe','dnt-lin-wei','chr-gzth-01'),
    (1,'cln-tianhe','dnt-li-xin','chr-gzth-02'),
    (2,'cln-nanshan','dnt-chen-yu','chr-szns-01'),
    (3,'cln-nanshan','dnt-zhou-rui','chr-szns-02'),
    (4,'cln-chancheng','dnt-wang-jie','chr-fscc-01'),
    (5,'cln-yuexiu','dnt-huang-min','chr-gzyx-01'),
    (6,'cln-futian','dnt-luo-yi','chr-szft-01'),
    (7,'cln-xiangzhou','dnt-zhang-ning','chr-zhxz-01'),
    (8,'cln-shunde','dnt-sun-lan','chr-fssd-01'),
    (9,'cln-nancheng','dnt-xu-tao','chr-dgnc-01'),
    (10,'cln-pengjiang','dnt-he-qing','chr-jmpj-01'),
    (11,'cln-haizhu','dnt-guo-fan','chr-gzhz-01'),
    (12,'cln-baoan','dnt-tang-ya','chr-szba-01'),
    (13,'cln-panyu','dnt-mao-lei','chr-gzpy-01')
),
planned AS (
  SELECT
    n,
    roster.clinic_id,
    roster.dentist_id,
    roster.chair_id,
    date('2026-09-21', '+' || (n % 7) || ' days') || ' ' ||
      printf('%02d:%02d:00', 10 + ((n - 1) / 14), CASE WHEN n % 2 = 0 THEN 30 ELSE 0 END) AS start_at
  FROM appointment_numbers
  INNER JOIN roster ON roster.slot = ((appointment_numbers.n - 1) % 14)
)
INSERT OR IGNORE INTO appointments
  (id, appointment_code, patient_id, clinic_id, dentist_id, chair_id, treatment_id, scheduled_start_at, scheduled_end_at, duration_minutes, status, booking_channel, priority, confirmation_state, risk_flag, notes, created_by_user_id)
SELECT
  'apt-gen-' || printf('%03d', n),
  'ADC-A26' || printf('%05d', n),
  'pat-' || printf('%04d', 20 + n),
  clinic_id,
  dentist_id,
  chair_id,
  'trt-exam-v1',
  start_at,
  datetime(start_at, '+30 minutes'),
  30,
  CASE
    WHEN date(start_at) < '2026-09-23' THEN 'COMPLETED'
    WHEN date(start_at) > '2026-09-23' THEN 'CONFIRMED'
    WHEN n % 5 = 0 THEN 'ARRIVED'
    WHEN n % 3 = 0 THEN 'COMPLETED'
    ELSE 'CONFIRMED'
  END,
  CASE WHEN n % 4 = 0 THEN 'PATIENT_PORTAL' WHEN n % 3 = 0 THEN 'PHONE' ELSE 'FRONT_DESK' END,
  'ROUTINE',
  'CONFIRMED',
  'NONE',
  'Deterministic scheduling fixture',
  'usr-local-ops'
FROM planned;

INSERT OR IGNORE INTO appointments
  (id, appointment_code, patient_id, clinic_id, dentist_id, chair_id, treatment_id, scheduled_start_at, scheduled_end_at, duration_minutes, status, booking_channel, priority, confirmation_state, risk_flag, notes, cancellation_reason_code, created_by_user_id)
VALUES
  ('apt-cur-001','ADC-A260923-001','pat-0002','cln-tianhe','dnt-lin-wei','chr-gzth-03','trt-fill-v1','2026-09-23 09:20:00','2026-09-23 10:05:00',45,'IN_TREATMENT','PATIENT_PORTAL','ROUTINE','CONFIRMED','NONE','Composite restoration on tooth 26',NULL,'usr-local-ops'),
  ('apt-cur-002','ADC-A260923-002','pat-0001','cln-tianhe','dnt-lin-wei','chr-gzth-01','trt-exam-v1','2026-09-23 14:30:00','2026-09-23 15:00:00',30,'CONFIRMED','WECHAT','HIGH','CONFIRMED','CRITICAL_ALLERGY','Pre-implant review; latex-free room setup required',NULL,'usr-local-ops'),
  ('apt-cur-003','ADC-A260923-003','pat-0008','cln-tianhe','dnt-li-xin','chr-gzth-04','trt-pedo-v1','2026-09-23 15:30:00','2026-09-23 16:00:00',30,'CONFIRMED','PHONE','ROUTINE','CONFIRMED','NONE','Paediatric preventive review',NULL,'usr-local-ops'),
  ('apt-cur-004','ADC-A260923-004','pat-0003','cln-nanshan','dnt-zhou-rui','chr-szns-01','trt-clean-v1','2026-09-23 09:40:00','2026-09-23 10:25:00',45,'ARRIVED','FRONT_DESK','HIGH','CONFIRMED','HIGH_ALLERGY','Periodontal review; NSAID sensitivity visible',NULL,'usr-local-ops'),
  ('apt-cur-005','ADC-A260923-005','pat-0012','cln-nanshan','dnt-zhou-rui','chr-szns-02','trt-implant-v1','2026-09-23 11:00:00','2026-09-23 13:00:00',120,'CONFIRMED','PHONE','HIGH','CONFIRMED','ALLERGY','Guided implant placement',NULL,'usr-local-ops'),
  ('apt-release-001','ADC-A260923-006','pat-0009','cln-nanshan','dnt-zhou-rui','chr-szns-03','trt-fill-v1','2026-09-23 15:30:00','2026-09-23 16:15:00',45,'CANCELLED','PATIENT_PORTAL','ROUTINE','CONFIRMED','NONE','Released slot for recovery','PATIENT_SCHEDULE_CONFLICT','usr-local-ops'),
  ('apt-cur-007','ADC-A260923-007','pat-0004','cln-chancheng','dnt-wang-jie','chr-fscc-02','trt-rct-v1','2026-09-23 10:00:00','2026-09-23 11:30:00',90,'CONFIRMED','WECHAT','HIGH','CONFIRMED','NONE','Microscope root canal therapy',NULL,'usr-local-ops'),
  ('apt-cur-008','ADC-A260923-008','pat-0005','cln-xiangzhou','dnt-zhang-ning','chr-zhxz-03','trt-crown-v1','2026-09-23 10:20:00','2026-09-23 11:35:00',75,'CONFIRMED','PATIENT_PORTAL','ROUTINE','CONFIRMED','NONE','Digital impression and crown preparation',NULL,'usr-local-ops'),
  ('apt-cur-009','ADC-A260923-009','pat-0006','cln-futian','dnt-luo-yi','chr-szft-02','trt-aligner-v1','2026-09-23 09:30:00','2026-09-23 10:30:00',60,'COMPLETED','FRONT_DESK','ROUTINE','CONFIRMED','NONE','Aligner progress assessment',NULL,'usr-local-ops'),
  ('apt-cur-010','ADC-A260923-010','pat-0007','cln-yuexiu','dnt-huang-min','chr-gzyx-02','trt-clean-v1','2026-09-23 11:00:00','2026-09-23 11:45:00',45,'COMPLETED','PHONE','ROUTINE','CONFIRMED','ALLERGY','Latex-free periodontal maintenance',NULL,'usr-local-ops'),
  ('apt-cur-011','ADC-A260923-011','pat-0011','cln-pengjiang','dnt-he-qing','chr-jmpj-02','trt-pedo-v1','2026-09-23 10:30:00','2026-09-23 11:00:00',30,'ARRIVED','WECHAT','ROUTINE','CONFIRMED','NONE','Child-friendly preventive pathway',NULL,'usr-local-ops'),
  ('apt-cur-012','ADC-A260923-012','pat-0010','cln-yuexiu','dnt-huang-min','chr-gzyx-03','trt-exam-v1','2026-09-23 14:00:00','2026-09-23 14:30:00',30,'HOLD','FRONT_DESK','ROUTINE','PENDING','IDENTITY_REVIEW','Appointment held pending duplicate identity review',NULL,'usr-local-ops'),
  ('apt-cur-013','ADC-A260923-013','pat-0012','cln-nancheng','dnt-xu-tao','chr-dgnc-02','trt-cbct-v1','2026-09-23 09:00:00','2026-09-23 09:20:00',20,'COMPLETED','FRONT_DESK','HIGH','CONFIRMED','ALLERGY','CBCT completed before implant review',NULL,'usr-local-ops'),
  ('apt-cur-014','ADC-A260923-014','pat-0020','cln-haizhu','dnt-guo-fan','chr-gzhz-02','trt-whiten-v1','2026-09-23 13:30:00','2026-09-23 15:00:00',90,'CONFIRMED','PATIENT_PORTAL','ROUTINE','CONFIRMED','NONE','Chairside whitening',NULL,'usr-local-ops'),
  ('apt-cur-015','ADC-A260923-015','pat-0021','cln-baoan','dnt-tang-ya','chr-szba-02','trt-braces-v1','2026-09-23 09:30:00','2026-09-23 10:30:00',60,'COMPLETED','WECHAT','ROUTINE','CONFIRMED','NONE','Fixed appliance adjustment',NULL,'usr-local-ops'),
  ('apt-cur-016','ADC-A260923-016','pat-0022','cln-panyu','dnt-mao-lei','chr-gzpy-02','trt-exam-v1','2026-09-23 16:00:00','2026-09-23 16:30:00',30,'CONFIRMED','PHONE','ROUTINE','CONFIRMED','NONE','Comprehensive assessment',NULL,'usr-local-ops');

INSERT OR IGNORE INTO appointment_status_history
  (id, appointment_id, from_status, to_status, reason_code, reason_text, actor_user_id, occurred_at, metadata_json)
SELECT
  'ash-init-' || id,
  id,
  NULL,
  'CONFIRMED',
  'INITIAL_BOOKING',
  'Appointment created and confirmed',
  'usr-local-ops',
  datetime(scheduled_start_at, '-7 days'),
  '{"synthetic":true}'
FROM appointments;

INSERT OR IGNORE INTO appointment_status_history
  (id, appointment_id, from_status, to_status, reason_code, reason_text, actor_user_id, occurred_at, metadata_json)
SELECT
  'ash-current-' || id,
  id,
  'CONFIRMED',
  status,
  CASE
    WHEN status = 'CANCELLED' THEN 'PATIENT_SCHEDULE_CONFLICT'
    WHEN status = 'COMPLETED' THEN 'CARE_COMPLETED'
    WHEN status = 'ARRIVED' THEN 'PATIENT_CHECKED_IN'
    WHEN status = 'IN_TREATMENT' THEN 'TREATMENT_STARTED'
    WHEN status = 'HOLD' THEN 'IDENTITY_REVIEW'
    ELSE 'UNCHANGED'
  END,
  CASE
    WHEN status = 'CANCELLED' THEN 'Patient cancelled through portal'
    WHEN status = 'COMPLETED' THEN 'Appointment completed'
    WHEN status = 'ARRIVED' THEN 'Patient checked in'
    WHEN status = 'IN_TREATMENT' THEN 'Treatment commenced'
    WHEN status = 'HOLD' THEN 'Identity review hold'
    ELSE 'Confirmed'
  END,
  'usr-local-ops',
  CASE
    WHEN status IN ('COMPLETED','ARRIVED','IN_TREATMENT') THEN scheduled_start_at
    ELSE datetime(scheduled_start_at, '-2 hours')
  END,
  '{"synthetic":true}'
FROM appointments
WHERE status <> 'CONFIRMED';

INSERT OR IGNORE INTO waitlist_entries
  (id, patient_id, treatment_id, preferred_clinic_id, earliest_date, latest_date, preferred_periods_json, acceptable_clinic_ids_json, notice_hours, priority_score, status)
VALUES
  ('wle-001','pat-0023','trt-fill-v1','cln-nanshan','2026-09-22','2026-09-30','["AFTERNOON"]','["cln-nanshan","cln-futian"]',2,92,'ACTIVE'),
  ('wle-002','pat-0024','trt-fill-v1','cln-nanshan','2026-09-20','2026-10-05','["AFTERNOON","EVENING"]','["cln-nanshan"]',4,86,'ACTIVE'),
  ('wle-003','pat-0025','trt-fill-v1','cln-futian','2026-09-23','2026-10-10','["AFTERNOON"]','["cln-futian","cln-nanshan"]',2,81,'ACTIVE'),
  ('wle-004','pat-0026','trt-clean-v1','cln-nanshan','2026-09-21','2026-09-28','["MORNING"]','["cln-nanshan","cln-baoan"]',24,74,'ACTIVE'),
  ('wle-005','pat-0027','trt-exam-v1','cln-tianhe','2026-09-23','2026-09-29','["ANY"]','["cln-tianhe","cln-yuexiu"]',1,70,'ACTIVE'),
  ('wle-006','pat-0028','trt-fill-v1','cln-baoan','2026-09-22','2026-10-02','["AFTERNOON"]','["cln-baoan","cln-nanshan"]',6,68,'ACTIVE'),
  ('wle-007','pat-0029','trt-pedo-v1','cln-pengjiang','2026-09-24','2026-10-08','["AFTER_SCHOOL"]','["cln-pengjiang"]',24,65,'ACTIVE'),
  ('wle-008','pat-0030','trt-rct-v1','cln-chancheng','2026-09-22','2026-09-26','["ANY"]','["cln-chancheng","cln-nanhai"]',2,96,'ACTIVE');

INSERT OR IGNORE INTO waitlist_offers
  (id, waitlist_entry_id, released_appointment_id, clinic_id, dentist_id, chair_id, offered_start_at, offered_end_at, compatibility_score, reasons_json, status, expires_at)
VALUES
  ('wlo-001','wle-001','apt-release-001','cln-nanshan','dnt-zhou-rui','chr-szns-03','2026-09-23 15:30:00','2026-09-23 16:15:00',98,'["TREATMENT_MATCH","PREFERRED_CLINIC","PREFERRED_PERIOD","SHORT_NOTICE_READY"]','PENDING','2026-09-23 13:30:00'),
  ('wlo-002','wle-002','apt-release-001','cln-nanshan','dnt-zhou-rui','chr-szns-03','2026-09-23 15:30:00','2026-09-23 16:15:00',91,'["TREATMENT_MATCH","PREFERRED_CLINIC","PREFERRED_PERIOD"]','PENDING','2026-09-23 13:30:00'),
  ('wlo-003','wle-003','apt-release-001','cln-nanshan','dnt-zhou-rui','chr-szns-03','2026-09-23 15:30:00','2026-09-23 16:15:00',84,'["TREATMENT_MATCH","ACCEPTABLE_CLINIC","PREFERRED_PERIOD","SHORT_NOTICE_READY"]','PENDING','2026-09-23 13:30:00');

INSERT OR IGNORE INTO notification_events
  (id, appointment_id, channel, template_code, recipient_masked, locale, status, idempotency_key, queued_at, sent_at, delivered_at)
VALUES
  ('nte-001','apt-cur-001','WECHAT','APPOINTMENT_REMINDER_24H','138****2002','en','DELIVERED','apt-cur-001-reminder-24h','2026-09-22 09:20:00','2026-09-22 09:20:03','2026-09-22 09:20:08'),
  ('nte-002','apt-cur-002','WECHAT','APPOINTMENT_REMINDER_24H','138****2001','zh','DELIVERED','apt-cur-002-reminder-24h','2026-09-22 14:30:00','2026-09-22 14:30:02','2026-09-22 14:30:06'),
  ('nte-003','apt-cur-004','SMS','APPOINTMENT_REMINDER_24H','138****2003','zh','DELIVERED','apt-cur-004-reminder-24h','2026-09-22 09:40:00','2026-09-22 09:40:02','2026-09-22 09:40:11'),
  ('nte-004','apt-release-001','WECHAT','CANCELLATION_CONFIRMED','138****2009','en','DELIVERED','apt-release-001-cancel','2026-09-23 11:02:00','2026-09-23 11:02:01','2026-09-23 11:02:05'),
  ('nte-005',NULL,'WECHAT','WAITLIST_SLOT_OFFER','139****0023','zh','QUEUED','wlo-001-offer','2026-09-23 11:04:00',NULL,NULL);

INSERT OR IGNORE INTO audit_events
  (request_id, actor_user_id, actor_subject, action, entity_type, entity_id, outcome, source, metadata_json)
VALUES
  ('seed-scheduling-v1', 'usr-local-ops', 'local_seedy', 'SCHEDULING_DATA_SEEDED', 'ORGANIZATION', 'org-adc', 'SUCCESS', 'SYSTEM', '{"version":"0.4.0","appointments":86,"waitlistEntries":8,"synthetic":true}');

-- Milestone 5: Clinical Studio, odontogram and visit-level safety evidence.
INSERT OR IGNORE INTO clinical_visits
  (id, visit_code, appointment_id, patient_id, clinic_id, dentist_id, chair_id, status, chief_complaint_en, chief_complaint_zh, safety_gate_status, started_at, completed_at, visit_version, created_by_user_id)
VALUES
  ('vis-260923-001','ADC-V260923-001','apt-cur-001','pat-0002','cln-tianhe','dnt-lin-wei','chr-gzth-03','IN_TREATMENT','Food trapping and sensitivity around the upper-left molar.','左上后牙食物嵌塞并伴敏感。','CLEARED','2026-09-23 09:20:00',NULL,2,'usr-local-ops'),
  ('vis-260923-002','ADC-V260923-002','apt-cur-004','pat-0003','cln-nanshan','dnt-zhou-rui','chr-szns-01','SAFETY_REVIEW','Bleeding gums and discomfort during brushing.','刷牙出血并伴牙龈不适。','PENDING','2026-09-23 09:42:00',NULL,1,'usr-local-ops'),
  ('vis-260923-003','ADC-V260923-003','apt-cur-009','pat-0006','cln-futian','dnt-luo-yi','chr-szft-02','COMPLETED','Clear-aligner progress assessment.','隐形矫治进度复查。','CLEARED','2026-09-23 09:31:00','2026-09-23 10:24:00',3,'usr-local-ops'),
  ('vis-260923-004','ADC-V260923-004','apt-cur-010','pat-0007','cln-yuexiu','dnt-huang-min','chr-gzyx-02','COMPLETED','Periodontal maintenance and sensitivity review.','牙周维护及敏感复查。','CLEARED','2026-09-23 11:01:00','2026-09-23 11:43:00',2,'usr-local-ops'),
  ('vis-260923-005','ADC-V260923-005','apt-cur-015','pat-0021','cln-baoan','dnt-tang-ya','chr-szba-02','COMPLETED','Fixed-appliance adjustment and hygiene review.','固定托槽调整及口腔卫生复查。','CLEARED','2026-09-23 09:32:00','2026-09-23 10:26:00',2,'usr-local-ops');

INSERT OR IGNORE INTO visit_allergy_acknowledgements
  (id, visit_id, allergy_id, acknowledged_by_user_id, acknowledged_at, precaution_en, precaution_zh, outcome)
VALUES
  ('vaa-001','vis-260923-004','alg-004','usr-local-ops','2026-09-23 11:03:00','Chlorhexidine excluded; saline irrigation selected.','已排除氯己定，改用生理盐水冲洗。','ACKNOWLEDGED');

INSERT OR IGNORE INTO odontogram_observations
  (id, visit_id, patient_id, tooth_code, dentition, surfaces_json, observation_type, severity, finding_en, finding_zh, status, observed_by_dentist_id, observed_at, supersedes_observation_id)
VALUES
  ('odo-001','vis-260923-001','pat-0002','26','PERMANENT','["O","D"]','CARIES','HIGH','Active cavitated lesion on occlusal-distal surfaces.','咬合面及远中面活动性龋坏。','ACTIVE','dnt-lin-wei','2026-09-23 09:28:00',NULL),
  ('odo-002','vis-260923-001','pat-0002','14','PERMANENT','["ALL"]','EXISTING_CROWN','ROUTINE','Existing ceramic crown; margins clinically stable.','既有全瓷冠，边缘临床稳定。','ACTIVE','dnt-lin-wei','2026-09-23 09:29:00',NULL),
  ('odo-003','vis-260923-001','pat-0002','36','PERMANENT','["O"]','WATCH','MODERATE','Early fissure demineralisation; monitor.','窝沟早期脱矿，建议观察。','ACTIVE','dnt-lin-wei','2026-09-23 09:30:00',NULL),
  ('odo-004','vis-260923-001','pat-0002','26','PERMANENT','["O","D"]','RESTORED','ROUTINE','Composite restoration placed with stable contact.','已完成复合树脂修复，邻接关系稳定。','ACTIVE','dnt-lin-wei','2026-09-23 09:56:00','odo-001'),
  ('odo-005','vis-260923-002','pat-0003','36','PERMANENT','["B","L"]','PERIODONTAL','HIGH','Bleeding on probing with subgingival calculus.','探诊出血并见龈下牙石。','ACTIVE','dnt-zhou-rui','2026-09-23 09:49:00',NULL),
  ('odo-006','vis-260923-002','pat-0003','46','PERMANENT','["O"]','CARIES','MODERATE','Non-cavitated occlusal lesion requiring review.','咬合面非洞性龋损，需进一步复查。','ACTIVE','dnt-zhou-rui','2026-09-23 09:51:00',NULL),
  ('odo-007','vis-260923-002','pat-0003','11','PERMANENT','["I"]','FRACTURE','LOW','Small enamel chip without pulpal symptoms.','釉质小范围崩裂，无牙髓症状。','ACTIVE','dnt-zhou-rui','2026-09-23 09:53:00',NULL),
  ('odo-008','vis-260923-003','pat-0006','13','PERMANENT','["ALL"]','ORTHODONTIC_MOVEMENT','ROUTINE','Tracking improved; rotation remains within plan.','牙套贴合改善，扭转仍在计划范围内。','ACTIVE','dnt-luo-yi','2026-09-23 09:42:00',NULL),
  ('odo-009','vis-260923-003','pat-0006','23','PERMANENT','["ALL"]','ORTHODONTIC_MOVEMENT','ROUTINE','Attachment intact and aligner fully seated.','附件完整，牙套完全就位。','ACTIVE','dnt-luo-yi','2026-09-23 09:43:00',NULL),
  ('odo-010','vis-260923-004','pat-0007','31','PERMANENT','["B"]','GINGIVAL_RECESSION','MODERATE','Two-millimetre buccal recession; stable from prior chart.','唇侧牙龈退缩2毫米，与既往记录相比稳定。','ACTIVE','dnt-huang-min','2026-09-23 11:08:00',NULL),
  ('odo-011','vis-260923-004','pat-0007','46','PERMANENT','["O"]','EXISTING_RESTORATION','ROUTINE','Existing composite restoration intact.','既有树脂充填体完整。','ACTIVE','dnt-huang-min','2026-09-23 11:09:00',NULL),
  ('odo-012','vis-260923-005','pat-0021','21','PERMANENT','["ALL"]','ORTHODONTIC_MOVEMENT','ROUTINE','Alignment on target; bracket secure.','排齐进度符合计划，托槽稳固。','ACTIVE','dnt-tang-ya','2026-09-23 09:41:00',NULL);

INSERT OR IGNORE INTO treatment_plans
  (id, visit_id, plan_code, status, clinical_priority, estimated_total_fen, acceptance_status, accepted_at, accepted_by, valid_until, notes_en, notes_zh)
VALUES
  ('tpl-260923-001','vis-260923-001','ADC-TP260923-001','ACTIVE','HIGH',116000,'ACCEPTED','2026-09-23 09:34:00','PATIENT','2026-10-23','Restore tooth 26 today; preventive cleaning may be deferred.','今日修复26牙；预防性洁治可延期实施。'),
  ('tpl-260923-002','vis-260923-002','ADC-TP260923-002','DRAFT','HIGH',116000,'PENDING',NULL,NULL,'2026-10-23','Safety acknowledgement is required before care begins.','开始治疗前必须完成安全确认。'),
  ('tpl-260923-003','vis-260923-003','ADC-TP260923-003','COMPLETED','ROUTINE',28000,'ACCEPTED','2026-09-23 09:48:00','PATIENT','2026-09-23','Progress assessment and next aligner issue.','评估进度并发放下一阶段牙套。'),
  ('tpl-260923-004','vis-260923-004','ADC-TP260923-004','COMPLETED','ROUTINE',48000,'ACCEPTED','2026-09-23 11:12:00','PATIENT','2026-09-23','Periodontal maintenance with chlorhexidine exclusion.','在排除氯己定条件下进行牙周维护。'),
  ('tpl-260923-005','vis-260923-005','ADC-TP260923-005','COMPLETED','ROUTINE',28000,'ACCEPTED','2026-09-23 09:45:00','GUARDIAN','2026-09-23','Orthodontic progress examination.','正畸进度检查。');

INSERT OR IGNORE INTO requested_treatment_items
  (id, plan_id, visit_id, treatment_id, sequence, tooth_code, surfaces_json, units, priority, rationale_en, rationale_zh, status)
VALUES
  ('rti-001','tpl-260923-001','vis-260923-001','trt-fill-v1',1,'26','["O","D"]',1,'HIGH','Definitive restoration of active cavitated lesion.','对活动性洞性龋损进行永久修复。','DELIVERED'),
  ('rti-002','tpl-260923-001','vis-260923-001','trt-clean-v1',2,NULL,'[]',1,'ROUTINE','Preventive maintenance after restorative care.','修复治疗后的预防性维护。','DEFERRED'),
  ('rti-003','tpl-260923-002','vis-260923-002','trt-clean-v1',1,NULL,'[]',1,'HIGH','Subgingival calculus and bleeding on probing.','存在龈下牙石及探诊出血。','PLANNED'),
  ('rti-004','tpl-260923-002','vis-260923-002','trt-fill-v1',2,'46','["O"]',1,'ROUTINE','Review and restore if lesion activity is confirmed.','确认龋损活动性后实施修复。','PLANNED'),
  ('rti-005','tpl-260923-003','vis-260923-003','trt-exam-v1',1,NULL,'[]',1,'ROUTINE','Orthodontic progress and occlusal assessment.','正畸进度及咬合评估。','DELIVERED'),
  ('rti-006','tpl-260923-004','vis-260923-004','trt-clean-v1',1,NULL,'[]',1,'ROUTINE','Periodontal maintenance.','牙周维护。','DELIVERED'),
  ('rti-007','tpl-260923-005','vis-260923-005','trt-exam-v1',1,NULL,'[]',1,'ROUTINE','Orthodontic progress examination.','正畸进度检查。','DELIVERED');

INSERT OR IGNORE INTO actual_treatment_items
  (id, visit_id, requested_treatment_item_id, treatment_id, provider_dentist_id, tooth_code, surfaces_json, units, effective_unit_price_fen, line_amount_fen, price_source, price_override_reason, notes_en, notes_zh, performed_at, status)
VALUES
  ('ati-001','vis-260923-001','rti-001','trt-fill-v1','dnt-lin-wei','26','["O","D"]',1,68000,68000,'CATALOG',NULL,'Caries removed; selective enamel etch and layered composite completed.','去除龋坏后采用选择性釉质酸蚀及分层树脂修复。','2026-09-23 09:56:00','RECORDED'),
  ('ati-002','vis-260923-003','rti-005','trt-exam-v1','dnt-luo-yi',NULL,'[]',1,28000,28000,'CATALOG',NULL,'Progress on target; issued aligners 13–16.','进度符合计划，已发放第13至16副牙套。','2026-09-23 10:08:00','RECORDED'),
  ('ati-003','vis-260923-004','rti-006','trt-clean-v1','dnt-huang-min',NULL,'[]',1,48000,48000,'CATALOG',NULL,'Ultrasonic scaling completed using saline-only irrigation.','使用生理盐水冲洗完成超声洁治。','2026-09-23 11:34:00','RECORDED'),
  ('ati-004','vis-260923-005','rti-007','trt-exam-v1','dnt-tang-ya',NULL,'[]',1,28000,28000,'CATALOG',NULL,'Archwire and bracket review completed.','已完成弓丝及托槽复查。','2026-09-23 10:12:00','RECORDED');

INSERT OR IGNORE INTO clinical_notes
  (id, visit_id, note_type, current_version, status, signed_by_dentist_id, signed_at)
VALUES
  ('cln-note-001','vis-260923-001','SOAP',2,'SIGNED','dnt-lin-wei','2026-09-23 10:02:00'),
  ('cln-note-002','vis-260923-002','SOAP',1,'DRAFT',NULL,NULL),
  ('cln-note-003','vis-260923-003','SOAP',1,'SIGNED','dnt-luo-yi','2026-09-23 10:21:00'),
  ('cln-note-004','vis-260923-004','SOAP',1,'SIGNED','dnt-huang-min','2026-09-23 11:41:00'),
  ('cln-note-005','vis-260923-005','SOAP',1,'SIGNED','dnt-tang-ya','2026-09-23 10:23:00');

INSERT OR IGNORE INTO clinical_note_versions
  (id, clinical_note_id, version_number, content_en, content_zh, amendment_reason, author_user_id, content_checksum, created_at)
VALUES
  ('cnv-001','cln-note-001',1,'S: Food trapping at tooth 26. O: Active OD caries. A: Restorable lesion. P: Composite restoration under rubber dam.','S：26牙食物嵌塞。O：OD面活动性龋坏。A：牙体可修复。P：橡皮障下行复合树脂修复。',NULL,'usr-local-ops','sha256:demo-note-001-v1','2026-09-23 09:37:00'),
  ('cnv-002','cln-note-001',2,'S: Food trapping at tooth 26. O: Active OD caries; tooth 36 early demineralisation. A: 26 restorable, 36 monitor. P: Composite restoration completed; cleaning deferred by patient.','S：26牙食物嵌塞。O：OD面活动性龋坏；36牙早期脱矿。A：26牙可修复，36牙观察。P：已完成树脂修复；患者选择延期洁治。','Added the deferred preventive item and tooth 36 monitoring finding.','usr-local-ops','sha256:demo-note-001-v2','2026-09-23 10:02:00'),
  ('cnv-003','cln-note-002',1,'S: Gingival bleeding. O: Subgingival calculus at 36; active ibuprofen alert. A: Periodontal inflammation. P: Pause for medication-safety acknowledgement.','S：牙龈出血。O：36牙龈下牙石；布洛芬安全提醒有效。A：牙周炎症。P：暂停并等待药物安全确认。',NULL,'usr-local-ops','sha256:demo-note-002-v1','2026-09-23 09:55:00'),
  ('cnv-004','cln-note-003',1,'Aligner tracking is acceptable. Attachments intact. Issued aligners 13–16 and reinforced wear protocol.','牙套贴合情况良好，附件完整。已发放第13至16副牙套并强化佩戴要求。',NULL,'usr-local-ops','sha256:demo-note-003-v1','2026-09-23 10:21:00'),
  ('cnv-005','cln-note-004',1,'Allergy acknowledged. Chlorhexidine excluded. Periodontal maintenance completed with saline irrigation; no adverse event.','已确认过敏风险并排除氯己定。使用生理盐水完成牙周维护，无不良事件。',NULL,'usr-local-ops','sha256:demo-note-004-v1','2026-09-23 11:41:00'),
  ('cnv-006','cln-note-005',1,'Alignment progressing as planned. Brackets secure. Oral hygiene instructions reinforced.','牙列排齐符合计划，托槽稳固，已再次进行口腔卫生指导。',NULL,'usr-local-ops','sha256:demo-note-005-v1','2026-09-23 10:23:00');

INSERT OR IGNORE INTO clinical_attachments
  (id, visit_id, category, file_name, mime_type, storage_key, size_bytes, description_en, description_zh, content_checksum, captured_at, status)
VALUES
  ('cla-001','vis-260923-001','INTRAORAL_IMAGE','tooth-26-preoperative.jpg','image/jpeg','clinical/vis-260923-001/tooth-26-pre.jpg',248320,'Pre-operative image of tooth 26.','26牙术前口内照片。','sha256:demo-image-001','2026-09-23 09:31:00','AVAILABLE'),
  ('cla-002','vis-260923-001','INTRAORAL_IMAGE','tooth-26-postoperative.jpg','image/jpeg','clinical/vis-260923-001/tooth-26-post.jpg',261440,'Post-operative restoration image.','修复完成后的口内照片。','sha256:demo-image-002','2026-09-23 09:58:00','AVAILABLE'),
  ('cla-003','vis-260923-003','SCAN','aligner-progress-scan.stl','model/stl','clinical/vis-260923-003/progress-scan.stl',1843200,'Progress intraoral scan.','矫治进度口内扫描。','sha256:demo-scan-001','2026-09-23 09:50:00','AVAILABLE');

INSERT OR IGNORE INTO patient_timeline_events
  (id, patient_id, clinic_id, event_type, occurred_at, title_en, title_zh, description_en, description_zh, reference_type, reference_id, status, amount_fen, metadata_json)
VALUES
  ('pte-cln-001','pat-0002','cln-tianhe','VISIT','2026-09-23T09:20:00+08:00','Restorative visit in treatment','修复就诊治疗中','Tooth 26 composite restoration recorded.','已记录26牙复合树脂修复。','VISIT','vis-260923-001','IN_TREATMENT',68000,'{"tooth":"26","actualItems":1}'),
  ('pte-cln-002','pat-0003','cln-nanshan','VISIT','2026-09-23T09:42:00+08:00','Visit paused at safety gate','就诊暂停于安全门','Ibuprofen alert requires clinician acknowledgement.','布洛芬风险提醒需要临床医生确认。','VISIT','vis-260923-002','SAFETY_REVIEW',NULL,'{"blockingAlerts":1}'),
  ('pte-cln-003','pat-0006','cln-futian','VISIT','2026-09-23T10:24:00+08:00','Aligner review completed','隐形矫治复查已完成','Progress assessment and next aligners recorded.','已记录进度评估及下一阶段牙套。','VISIT','vis-260923-003','COMPLETED',28000,'{}'),
  ('pte-cln-004','pat-0007','cln-yuexiu','VISIT','2026-09-23T11:43:00+08:00','Periodontal maintenance completed','牙周维护已完成','Allergy precaution acknowledged and treatment completed.','已确认过敏防护并完成治疗。','VISIT','vis-260923-004','COMPLETED',48000,'{}'),
  ('pte-cln-005','pat-0021','cln-baoan','VISIT','2026-09-23T10:26:00+08:00','Orthodontic review completed','正畸复查已完成','Fixed-appliance progress documented.','已记录固定矫治进度。','VISIT','vis-260923-005','COMPLETED',28000,'{}');

INSERT OR IGNORE INTO audit_events
  (request_id, actor_user_id, actor_subject, action, entity_type, entity_id, outcome, source, metadata_json)
VALUES
  ('seed-clinical-v1', 'usr-local-ops', 'local_seedy', 'CLINICAL_DATA_SEEDED', 'ORGANIZATION', 'org-adc', 'SUCCESS', 'SYSTEM', '{"version":"0.5.0","visits":5,"odontogramObservations":12,"synthetic":true}');

-- Milestone 6: Billing, financial close, profitability and incentive evidence.
INSERT OR IGNORE INTO financial_reporting_periods
  (id, period_code, name_en, name_zh, starts_on, ends_on, status, close_checklist_json, locked_at, locked_by_user_id, period_version)
VALUES
  ('per-2026-q1','2026-Q1','2026 Quarter 1','2026年第一季度','2026-01-01','2026-03-31','LOCKED','[{"code":"INVOICES_RECONCILED","status":"PASS"},{"code":"PAYMENTS_RECONCILED","status":"PASS"},{"code":"COSTS_COMPLETE","status":"PASS"},{"code":"EXPENSES_APPROVED","status":"PASS"},{"code":"EXCEPTIONS_RESOLVED","status":"PASS"}]','2026-04-08 18:30:00','usr-local-ops',2),
  ('per-2026-q2','2026-Q2','2026 Quarter 2','2026年第二季度','2026-04-01','2026-06-30','LOCKED','[{"code":"INVOICES_RECONCILED","status":"PASS"},{"code":"PAYMENTS_RECONCILED","status":"PASS"},{"code":"COSTS_COMPLETE","status":"PASS"},{"code":"EXPENSES_APPROVED","status":"PASS"},{"code":"EXCEPTIONS_RESOLVED","status":"PASS"}]','2026-07-08 18:30:00','usr-local-ops',3),
  ('per-2026-q3','2026-Q3','2026 Quarter 3','2026年第三季度','2026-07-01','2026-09-30','OPEN','[{"code":"INVOICES_RECONCILED","status":"IN_PROGRESS"},{"code":"PAYMENTS_RECONCILED","status":"IN_PROGRESS"},{"code":"COSTS_COMPLETE","status":"PASS"},{"code":"EXPENSES_APPROVED","status":"IN_PROGRESS"},{"code":"EXCEPTIONS_RESOLVED","status":"BLOCKED"}]',NULL,NULL,1);

INSERT OR IGNORE INTO actual_treatment_items
  (id, visit_id, requested_treatment_item_id, treatment_id, provider_dentist_id, tooth_code, surfaces_json, units, effective_unit_price_fen, line_amount_fen, price_source, price_override_reason, notes_en, notes_zh, performed_at, status)
VALUES
  ('ati-005','vis-260923-003',NULL,'trt-cbct-v1','dnt-luo-yi',NULL,'[]',1,58000,58000,'CATALOG',NULL,'Limited-field CBCT captured to review root position before refinement.','在精调前拍摄小视野CBCT以复核牙根位置。','2026-09-23 10:11:00','RECORDED');

INSERT OR IGNORE INTO invoices
  (id, invoice_code, visit_id, patient_id, clinic_id, reporting_period_id, status, currency, subtotal_fen, adjustment_total_fen, tax_total_fen, total_fen, paid_fen, refunded_fen, balance_fen, issued_at, due_at, invoice_version, created_by_user_id)
VALUES
  ('inv-260923-001','ADC-INV-260923-001','vis-260923-003','pat-0006','cln-futian','per-2026-q3','PAID','CNY',86000,-6000,0,80000,80000,0,0,'2026-09-23 10:28:00','2026-09-23 18:00:00',3,'usr-local-ops'),
  ('inv-260923-002','ADC-INV-260923-002','vis-260923-004','pat-0007','cln-yuexiu','per-2026-q3','PARTIALLY_PAID','CNY',48000,0,0,48000,30000,10000,28000,'2026-09-23 11:46:00','2026-09-30 18:00:00',3,'usr-local-ops'),
  ('inv-260923-003','ADC-INV-260923-003','vis-260923-005','pat-0021','cln-baoan','per-2026-q3','OVERDUE','CNY',28000,0,0,28000,0,0,28000,'2026-09-23 10:27:00','2026-09-23 10:30:00',2,'usr-local-ops');

INSERT OR IGNORE INTO invoice_lines
  (id, invoice_id, actual_treatment_item_id, line_number, treatment_code_snapshot, description_en_snapshot, description_zh_snapshot, tooth_code_snapshot, surfaces_json_snapshot, units_snapshot, unit_price_fen_snapshot, amount_fen_snapshot, cost_fen_snapshot, performed_at_snapshot)
VALUES
  ('inl-001','inv-260923-001','ati-002',1,'EXAM-001','Comprehensive oral examination','全面口腔检查',NULL,'[]',1,28000,28000,4500,'2026-09-23 10:08:00'),
  ('inl-002','inv-260923-001','ati-005',2,'IMG-090','CBCT imaging','CBCT影像检查',NULL,'[]',1,58000,58000,12000,'2026-09-23 10:11:00'),
  ('inl-003','inv-260923-002','ati-003',1,'PERIO-010','Ultrasonic scaling','超声洁治',NULL,'[]',1,48000,48000,8200,'2026-09-23 11:34:00'),
  ('inl-004','inv-260923-003','ati-004',1,'EXAM-001','Comprehensive oral examination','全面口腔检查',NULL,'[]',1,28000,28000,4500,'2026-09-23 10:12:00');

INSERT OR IGNORE INTO invoice_adjustments
  (id, invoice_id, adjustment_type, amount_fen, reason_code, reason_text, status, authored_by_user_id, approved_by_user_id)
VALUES
  ('iad-001','inv-260923-001','DISCOUNT',-6000,'MEMBERSHIP_BENEFIT','Network membership benefit applied before issue.','ACTIVE','usr-local-ops','usr-local-ops');

INSERT OR IGNORE INTO payments
  (id, payment_code, invoice_id, amount_fen, method, status, simulated_gateway_reference, received_at, recorded_by_user_id, notes)
VALUES
  ('pay-001','ADC-PAY-260923-001','inv-260923-001',50000,'WECHAT_PAY','CAPTURED','SIM-WX-260923-0001','2026-09-23 10:31:00','usr-local-ops','Simulated gateway capture.'),
  ('pay-002','ADC-PAY-260923-002','inv-260923-001',30000,'BANK_CARD','CAPTURED','SIM-CARD-260923-0002','2026-09-23 10:33:00','usr-local-ops','Split tender balance.'),
  ('pay-003','ADC-PAY-260923-003','inv-260923-002',30000,'WECHAT_PAY','CAPTURED','SIM-WX-260923-0003','2026-09-23 11:49:00','usr-local-ops','Partial payment before refund adjustment.');

INSERT OR IGNORE INTO payment_refunds
  (id, refund_code, payment_id, amount_fen, reason_code, reason_text, status, authorized_by_user_id, refunded_at)
VALUES
  ('ref-001','ADC-REF-260923-001','pay-003',10000,'DUPLICATE_CAPTURE_CORRECTION','Patient requested correction of an accidentally duplicated partial amount.','COMPLETED','usr-local-ops','2026-09-23 11:55:00');

INSERT OR IGNORE INTO treatment_cost_entries
  (id, actual_treatment_item_id, visit_id, clinic_id, reporting_period_id, catalog_estimated_cost_fen, materials_cost_fen, laboratory_cost_fen, provider_cost_fen, total_cost_fen, cost_date, source)
VALUES
  ('tce-001','ati-001','vis-260923-001','cln-tianhe','per-2026-q3',16500,7200,0,9300,16500,'2026-09-23','CATALOG_SNAPSHOT'),
  ('tce-002','ati-002','vis-260923-003','cln-futian','per-2026-q3',4500,500,0,4000,4500,'2026-09-23','CATALOG_SNAPSHOT'),
  ('tce-003','ati-003','vis-260923-004','cln-yuexiu','per-2026-q3',8200,2700,0,5500,8200,'2026-09-23','CATALOG_SNAPSHOT'),
  ('tce-004','ati-004','vis-260923-005','cln-baoan','per-2026-q3',4500,500,0,4000,4500,'2026-09-23','CATALOG_SNAPSHOT'),
  ('tce-005','ati-005','vis-260923-003','cln-futian','per-2026-q3',12000,2800,0,9200,12000,'2026-09-23','CATALOG_SNAPSHOT');

WITH ranked_clinics AS (
  SELECT id, code, ROW_NUMBER() OVER (ORDER BY code) AS n
  FROM clinics WHERE organization_id = 'org-adc'
), expense_basis AS (
  SELECT id, code, n, 100000000 + n * 8000000 AS revenue_fen FROM ranked_clinics
), expense_rows AS (
  SELECT id, code, n, revenue_fen, 'RENT' AS category, (revenue_fen * 18) / 100 AS amount_fen, 'Quarterly premises and service charge' AS description_en, '季度场地租赁及物业费用' AS description_zh FROM expense_basis
  UNION ALL
  SELECT id, code, n, revenue_fen, 'PAYROLL', (revenue_fen * 22) / 100, 'Clinical and operations payroll allocation', '临床及运营人员薪酬分摊' FROM expense_basis
  UNION ALL
  SELECT id, code, n, revenue_fen, 'UTILITIES', (revenue_fen * 3) / 100, 'Utilities, sterilisation and facilities', '水电、消毒及设施费用' FROM expense_basis
)
INSERT OR IGNORE INTO operating_expenses
  (id, clinic_id, reporting_period_id, category, vendor_name, amount_fen, incurred_on, description_en, description_zh, status, entered_by_user_id, approved_by_user_id)
SELECT
  'ope-q2-' || lower(replace(code,'-','')) || '-' || lower(category), id, 'per-2026-q2', category,
  CASE category WHEN 'RENT' THEN 'ADC Property Services' WHEN 'PAYROLL' THEN 'ADC Payroll Clearing' ELSE 'Regional Facilities Supplier' END,
  amount_fen, '2026-06-30', description_en, description_zh, 'APPROVED', 'usr-local-ops', 'usr-local-ops'
FROM expense_rows;

INSERT OR IGNORE INTO operating_expenses
  (id, clinic_id, reporting_period_id, category, vendor_name, amount_fen, incurred_on, description_en, description_zh, status, entered_by_user_id, approved_by_user_id)
VALUES
  ('ope-q3-futian-supplies','cln-futian','per-2026-q3','CLINICAL_SUPPLIES','Shenzhen Dental Supply','1260000','2026-09-20','September clinical supplies','九月临床耗材','APPROVED','usr-local-ops','usr-local-ops'),
  ('ope-q3-yuexiu-lab','cln-yuexiu','per-2026-q3','LAB_SERVICES','Guangzhou Digital Lab','980000','2026-09-20','September laboratory services','九月技工服务','APPROVED','usr-local-ops','usr-local-ops'),
  ('ope-q3-baoan-maint','cln-baoan','per-2026-q3','EQUIPMENT_MAINTENANCE','ADC Equipment Care','760000','2026-09-21','Chair and imaging maintenance','牙椅及影像设备维护','PENDING','usr-local-ops',NULL);

INSERT OR IGNORE INTO financial_close_exceptions
  (id, reporting_period_id, clinic_id, exception_type, severity, entity_type, entity_id, description_en, description_zh, status, resolved_at, resolution_note)
VALUES
  ('fce-q2-001','per-2026-q2','cln-nanshan','LATE_EXPENSE_APPROVAL','MEDIUM','OPERATING_EXPENSE','ope-q2-szns-payroll','One payroll allocation required secondary approval.','一项薪酬分摊需要二次审批。','RESOLVED','2026-07-06 14:20:00','Secondary approval completed.'),
  ('fce-q2-002','per-2026-q2','cln-tianhe','PAYMENT_RECONCILIATION','LOW','PAYMENT','legacy-batch-q2-041','Gateway settlement differed by one day.','支付网关结算日期相差一天。','RESOLVED','2026-07-07 10:15:00','Settlement date evidence attached.'),
  ('fce-q3-001','per-2026-q3','cln-baoan','OVERDUE_BALANCE','HIGH','INVOICE','inv-260923-003','Invoice is overdue with the full balance outstanding.','发票已逾期且全部余额未支付。','OPEN',NULL,NULL),
  ('fce-q3-002','per-2026-q3','cln-yuexiu','REFUND_RECONCILIATION','MEDIUM','PAYMENT_REFUND','ref-001','Refund must be reconciled with the simulated gateway batch.','退款需要与模拟网关批次对账。','OPEN',NULL,NULL),
  ('fce-q3-003','per-2026-q3','cln-baoan','EXPENSE_APPROVAL_PENDING','MEDIUM','OPERATING_EXPENSE','ope-q3-baoan-maint','Equipment maintenance expense awaits approval.','设备维护费用等待审批。','OPEN',NULL,NULL);

WITH ranked_clinics AS (
  SELECT id, code, ROW_NUMBER() OVER (ORDER BY code) AS n
  FROM clinics WHERE organization_id = 'org-adc'
), result_basis AS (
  SELECT id, code, n, 100000000 + n * 8000000 AS revenue_fen FROM ranked_clinics
)
INSERT OR IGNORE INTO financial_period_results
  (id, reporting_period_id, clinic_id, scope_key, recognized_revenue_fen, treatment_cost_fen, operating_expense_fen, net_profit_fen, net_margin_basis_points, invoice_count, open_exception_count, calculation_inputs_json, status, calculated_at, approved_at, approved_by_user_id)
SELECT
  'fpr-q2-' || lower(replace(code,'-','')), 'per-2026-q2', id, id,
  revenue_fen, (revenue_fen * 26) / 100, (revenue_fen * 43) / 100, (revenue_fen * 31) / 100,
  3100, 580 + n * 19, 0,
  '{"formula":"recognizedRevenue-treatmentCost-operatingExpense","treatmentCostRate":0.26,"expenseRate":0.43,"source":"validated-ledger"}',
  'APPROVED','2026-07-08 17:45:00','2026-07-08 18:10:00','usr-local-ops'
FROM result_basis;

INSERT OR IGNORE INTO financial_period_results
  (id, reporting_period_id, clinic_id, scope_key, recognized_revenue_fen, treatment_cost_fen, operating_expense_fen, net_profit_fen, net_margin_basis_points, invoice_count, open_exception_count, calculation_inputs_json, status, calculated_at, approved_at, approved_by_user_id)
VALUES
  ('fpr-q1-network','per-2026-q1',NULL,'NETWORK',2180000000,566800000,976640000,636560000,2920,8420,0,'{"formula":"recognizedRevenue-treatmentCost-operatingExpense","source":"locked-ledger","clinicCount":15}','APPROVED','2026-04-08 17:45:00','2026-04-08 18:10:00','usr-local-ops'),
  ('fpr-q3-network','per-2026-q3',NULL,'NETWORK',2650000000,715500000,1139500000,795000000,3000,0,3,'{"formula":"recognizedRevenue-treatmentCost-operatingExpense","source":"current-quarter-projection","advisory":true}','DRAFT','2026-09-23 12:00:00',NULL,NULL);

INSERT OR IGNORE INTO financial_period_results
  (id, reporting_period_id, clinic_id, scope_key, recognized_revenue_fen, treatment_cost_fen, operating_expense_fen, net_profit_fen, net_margin_basis_points, invoice_count, open_exception_count, calculation_inputs_json, status, calculated_at, approved_at, approved_by_user_id)
SELECT
  'fpr-q2-network','per-2026-q2',NULL,'NETWORK',
  SUM(recognized_revenue_fen), SUM(treatment_cost_fen), SUM(operating_expense_fen), SUM(net_profit_fen),
  CAST(ROUND(SUM(net_profit_fen) * 10000.0 / SUM(recognized_revenue_fen)) AS INTEGER),
  SUM(invoice_count), 0,
  '{"formula":"sum(clinicResults)","source":"validated-ledger","clinicCount":15,"exceptionCount":0}',
  'APPROVED','2026-07-08 18:00:00','2026-07-08 18:15:00','usr-local-ops'
FROM financial_period_results
WHERE reporting_period_id = 'per-2026-q2' AND clinic_id IS NOT NULL;

INSERT OR IGNORE INTO incentive_pools
  (id, reporting_period_id, network_result_id, rate_basis_points, eligible_net_profit_fen, pool_amount_fen, formula_evidence, status, approved_at, approved_by_user_id)
VALUES
  ('inc-2026-q1','per-2026-q1','fpr-q1-network',1000,636560000,63656000,'max(0, CNY 6,365,600 validated net profit) × 10% = CNY 636,560','PAID','2026-04-08 18:25:00','usr-local-ops');

INSERT OR IGNORE INTO incentive_pools
  (id, reporting_period_id, network_result_id, rate_basis_points, eligible_net_profit_fen, pool_amount_fen, formula_evidence, status, approved_at, approved_by_user_id)
SELECT
  'inc-2026-q2','per-2026-q2','fpr-q2-network',1000,net_profit_fen,net_profit_fen / 10,
  'max(0, validated network net profit) × 10%; inputs frozen in fpr-q2-network',
  'APPROVED','2026-07-08 18:25:00','usr-local-ops'
FROM financial_period_results WHERE id = 'fpr-q2-network';

INSERT OR IGNORE INTO patient_timeline_events
  (id, patient_id, clinic_id, event_type, occurred_at, title_en, title_zh, description_en, description_zh, reference_type, reference_id, status, amount_fen, metadata_json)
VALUES
  ('pte-fin-001','pat-0006','cln-futian','INVOICE','2026-09-23T10:28:00+08:00','Invoice issued and paid','发票已开具并支付','Two clinical lines reconciled to one paid invoice.','两条临床项目已核对至一张已支付发票。','INVOICE','inv-260923-001','PAID',80000,'{"lineCount":2,"paymentCount":2}'),
  ('pte-fin-002','pat-0007','cln-yuexiu','INVOICE','2026-09-23T11:46:00+08:00','Invoice partially paid','发票部分支付','Payment and authorized refund retained as transaction evidence.','付款及授权退款均保留为交易证据。','INVOICE','inv-260923-002','PARTIALLY_PAID',48000,'{"balanceFen":28000}'),
  ('pte-fin-003','pat-0021','cln-baoan','INVOICE','2026-09-23T10:31:00+08:00','Invoice overdue','发票已逾期','Outstanding balance requires follow-up.','未结余额需要跟进。','INVOICE','inv-260923-003','OVERDUE',28000,'{"balanceFen":28000}');

INSERT OR IGNORE INTO audit_events
  (request_id, actor_user_id, actor_subject, action, entity_type, entity_id, outcome, source, metadata_json)
VALUES
  ('seed-finance-v1', 'usr-local-ops', 'local_seedy', 'FINANCE_DATA_SEEDED', 'ORGANIZATION', 'org-adc', 'SUCCESS', 'SYSTEM', '{"version":"0.6.0","invoices":3,"periods":3,"synthetic":true}');

-- Milestone 7: versioned, advisory expansion scenarios and decision evidence.
INSERT OR IGNORE INTO expansion_scenarios
  (id, scenario_code, version, name_en, name_zh, description_en, description_zh, forecast_horizon_months, status, advisory_disclaimer_en, advisory_disclaimer_zh, created_by_user_id, approved_by_user_id, approved_at)
VALUES
  ('exs-x02-v2','ADC-X02',2,'Capital-efficient corridor','资本效率走廊方案','Two compact clinics prioritising early payback and proven catchments.','新设两家紧凑型诊所，优先考虑较短回收期和成熟客群。',24,'APPROVED','Advisory forecast; management approval and site due diligence remain mandatory.','本结果仅供决策参考；仍需管理层批准及选址尽调。','usr-local-ops','usr-local-ops','2026-09-18 16:30:00'),
  ('exs-x03-v1','ADC-X03',1,'Specialist hub strategy','专科中心方案','Two larger specialist hubs with higher capital and referral capacity.','新设两家较大型专科中心，提高转诊承接能力。',36,'REVIEW','Advisory forecast; qualification recruitment assumptions are not commitments.','本结果仅供决策参考；资质人员招募假设不构成承诺。','usr-local-ops',NULL,NULL),
  ('exs-x04-v3','ADC-X04',3,'Balanced Greater Bay expansion','大湾区均衡扩张方案','Three clinics balancing demand, capital, qualification coverage and travel constraints.','新设三家诊所，综合平衡需求、资本、资质覆盖与跨店出行约束。',24,'RECOMMENDED','Advisory forecast; no scenario automatically changes live operations.','本结果仅供决策参考；任何方案都不会自动更改实际运营。','usr-local-ops','usr-local-ops','2026-09-22 18:10:00');

INSERT OR IGNORE INTO expansion_candidate_clinics
  (id, scenario_id, candidate_code, name_en, name_zh, city_en, city_zh, district_en, district_zh, planned_chair_count, planned_dentist_count, planned_support_staff_count, forecast_quarterly_appointments, initial_capital_fen, quarterly_fixed_cost_fen, required_qualifications_json, qualification_coverage_basis_points, travel_constraint_minutes, readiness_status)
VALUES
  ('exc-x02-01','exs-x02-v2','DG-NC','Dongguan Nancheng Studio','东莞南城诊所','Dongguan','东莞','Nancheng','南城',6,5,8,1820,480000000,68500000,'["GENERAL","ENDODONTICS","PERIODONTICS"]',10000,42,'READY'),
  ('exc-x02-02','exs-x02-v2','HZ-HC','Huizhou Huicheng Studio','惠州惠城诊所','Huizhou','惠州','Huicheng','惠城',5,4,7,1490,390000000,57000000,'["GENERAL","ORTHODONTICS"]',9200,55,'CONDITIONAL'),
  ('exc-x03-01','exs-x03-v1','DG-SL','Dongguan Songshan Lake Specialist Hub','东莞松山湖专科中心','Dongguan','东莞','Songshan Lake','松山湖',10,10,16,2720,920000000,142000000,'["GENERAL","IMPLANTOLOGY","ORTHODONTICS","ENDODONTICS","SEDATION"]',7600,48,'GAP'),
  ('exc-x03-02','exs-x03-v1','ZS-EA','Zhongshan East Area Specialist Hub','中山东区专科中心','Zhongshan','中山','East Area','东区',9,9,14,2410,810000000,127000000,'["GENERAL","IMPLANTOLOGY","PERIODONTICS","PEDIATRIC"]',8100,51,'GAP'),
  ('exc-x04-01','exs-x04-v3','DG-NC','Dongguan Nancheng Clinic','东莞南城诊所','Dongguan','东莞','Nancheng','南城',7,6,10,2060,560000000,79000000,'["GENERAL","ENDODONTICS","PERIODONTICS","ORTHODONTICS"]',10000,42,'READY'),
  ('exc-x04-02','exs-x04-v3','HZ-HC','Huizhou Huicheng Clinic','惠州惠城诊所','Huizhou','惠州','Huicheng','惠城',6,5,8,1710,455000000,65000000,'["GENERAL","ORTHODONTICS","PEDIATRIC"]',10000,55,'READY'),
  ('exc-x04-03','exs-x04-v3','ZS-SQ','Zhongshan Shiqi Clinic','中山石岐诊所','Zhongshan','中山','Shiqi','石岐',6,5,8,1680,445000000,63000000,'["GENERAL","PERIODONTICS","ENDODONTICS"]',10000,38,'READY');

INSERT OR IGNORE INTO expansion_assumptions
  (id, scenario_id, assumption_key, label_en, label_zh, value_text, unit, source_en, source_zh)
VALUES
  ('exa-x02-demand','exs-x02-v2','DEMAND_GROWTH','Annual demand growth','年度需求增长','8.5','PERCENT','Rolling appointment demand model','滚动预约需求模型'),
  ('exa-x02-ramp','exs-x02-v2','RAMP_MONTHS','Clinic ramp-up','诊所爬坡周期','9','MONTHS','Network opening cohort median','网络开业批次中位数'),
  ('exa-x02-price','exs-x02-v2','AVG_REVENUE_VISIT','Average revenue per visit','次均诊疗收入','742','CNY','Validated Q2 treatment mix','已核定第二季度治疗结构'),
  ('exa-x03-demand','exs-x03-v1','DEMAND_GROWTH','Annual demand growth','年度需求增长','11.2','PERCENT','Specialist referral model','专科转诊模型'),
  ('exa-x03-ramp','exs-x03-v1','RAMP_MONTHS','Clinic ramp-up','诊所爬坡周期','15','MONTHS','Specialist hub benchmark','专科中心基准'),
  ('exa-x03-price','exs-x03-v1','AVG_REVENUE_VISIT','Average revenue per visit','次均诊疗收入','1180','CNY','Specialist treatment mix','专科治疗结构'),
  ('exa-x04-demand','exs-x04-v3','DEMAND_GROWTH','Annual demand growth','年度需求增长','9.4','PERCENT','Three-city demand and cancellation model','三城市需求及取消率模型'),
  ('exa-x04-ramp','exs-x04-v3','RAMP_MONTHS','Clinic ramp-up','诊所爬坡周期','10','MONTHS','Network opening cohort median','网络开业批次中位数'),
  ('exa-x04-price','exs-x04-v3','AVG_REVENUE_VISIT','Average revenue per visit','次均诊疗收入','815','CNY','Validated Q2 mix with local adjustment','第二季度核定结构并作本地调整'),
  ('exa-x04-util','exs-x04-v3','TARGET_CHAIR_UTILIZATION','Target chair utilisation','目标牙椅利用率','72','PERCENT','Mature-clinic upper quartile','成熟诊所上四分位数'),
  ('exa-x04-cost','exs-x04-v3','COST_INFLATION','Annual cost inflation','年度成本涨幅','3.8','PERCENT','Finance planning baseline','财务规划基准'),
  ('exa-x04-travel','exs-x04-v3','MAX_SPECIALIST_TRAVEL','Maximum specialist travel','专科医生最长跨店出行','60','MINUTES','Workforce coverage policy','人员覆盖政策');

INSERT OR IGNORE INTO expansion_scenario_results
  (id, scenario_id, projected_quarter_revenue_fen, projected_treatment_cost_fen, projected_operating_expense_fen, projected_net_profit_fen, projected_margin_basis_points, payback_months, demand_coverage_basis_points, qualification_coverage_basis_points, composite_score, risk_level, formula_evidence_json, calculated_at)
VALUES
  ('exr-x02','exs-x02-v2',245641000,65340500,125277000,55023500,2240,22,8460,9600,82,'LOW','{"model":"EXPANSION_V2","weights":{"financial":0.35,"demand":0.25,"qualification":0.25,"execution":0.15},"candidateCount":2}','2026-09-22 15:00:00'),
  ('exr-x03','exs-x03-v1',414150000,115962000,230000000,68188000,1646,31,9300,7850,68,'HIGH','{"model":"EXPANSION_V2","weights":{"financial":0.35,"demand":0.25,"qualification":0.25,"execution":0.15},"candidateCount":2}','2026-09-22 15:05:00'),
  ('exr-x04','exs-x04-v3',444115000,119911000,207995000,116209000,2617,24,9180,10000,91,'LOW','{"model":"EXPANSION_V2","weights":{"financial":0.35,"demand":0.25,"qualification":0.25,"execution":0.15},"candidateCount":3,"advisory":true}','2026-09-22 15:10:00');

INSERT OR IGNORE INTO audit_events
  (request_id, actor_user_id, actor_subject, action, entity_type, entity_id, outcome, source, metadata_json)
VALUES
  ('seed-intelligence-v1', 'usr-local-ops', 'local_seedy', 'EXPANSION_SCENARIOS_SEEDED', 'ORGANIZATION', 'org-adc', 'SUCCESS', 'SYSTEM', '{"version":"0.7.0","scenarios":3,"candidates":7,"synthetic":true}');

PRAGMA optimize;
