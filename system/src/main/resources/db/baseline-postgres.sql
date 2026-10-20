CREATE TABLE "account_invitations" (
"id" TEXT PRIMARY KEY NOT NULL,
  "phone_e164" TEXT NOT NULL,
  "target_user_id" TEXT,
  "role_id" TEXT,
  "clinic_id" TEXT,
  "status" TEXT NOT NULL DEFAULT 'PENDING',
  "expires_at" TEXT NOT NULL,
  "accepted_at" TEXT,
  "created_by_user_id" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_account_invitations_phone_status" ON "account_invitations" ("phone_e164", "status");

CREATE TABLE "actual_treatment_items" (
"id" TEXT PRIMARY KEY NOT NULL,
  "visit_id" TEXT NOT NULL,
  "requested_treatment_item_id" TEXT,
  "treatment_id" TEXT NOT NULL,
  "provider_dentist_id" TEXT NOT NULL,
  "tooth_code" TEXT,
  "surfaces_json" TEXT NOT NULL DEFAULT '[]',
  "units" BIGINT NOT NULL DEFAULT 1,
  "effective_unit_price_fen" BIGINT NOT NULL,
  "line_amount_fen" BIGINT NOT NULL,
  "price_source" TEXT NOT NULL DEFAULT 'CATALOG',
  "price_override_reason" TEXT,
  "notes_en" TEXT NOT NULL DEFAULT '',
  "notes_zh" TEXT NOT NULL DEFAULT '',
  "performed_at" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'RECORDED',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_actual_treatments_visit_time" ON "actual_treatment_items" ("visit_id", "performed_at");
CREATE INDEX "idx_actual_treatments_requested" ON "actual_treatment_items" ("requested_treatment_item_id");

CREATE TABLE "app_users" (
"id" TEXT PRIMARY KEY NOT NULL,
  "auth_subject" TEXT NOT NULL,
  "email" TEXT NOT NULL,
  "display_name" TEXT NOT NULL,
  "phone_e164" TEXT,
  "username" TEXT,
  "password_hash" TEXT,
  "password_salt" TEXT,
  "password_iterations" BIGINT,
  "password_set_at" TEXT,
  "last_auth_method" TEXT,
  "failed_login_count" BIGINT NOT NULL DEFAULT 0,
  "locked_until" TEXT,
  "preferred_language" TEXT NOT NULL DEFAULT 'zh',
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "last_sign_in_at" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_app_users_auth_subject" ON "app_users" ("auth_subject");
CREATE UNIQUE INDEX "uq_app_users_email" ON "app_users" ("email");
CREATE UNIQUE INDEX "uq_app_users_phone_e164" ON "app_users" ("phone_e164");
CREATE UNIQUE INDEX "uq_app_users_username" ON "app_users" ("username");
CREATE INDEX "idx_app_users_status" ON "app_users" ("status");

CREATE TABLE "appointment_status_history" (
"id" TEXT PRIMARY KEY NOT NULL,
  "appointment_id" TEXT NOT NULL,
  "from_status" TEXT,
  "to_status" TEXT NOT NULL,
  "reason_code" TEXT,
  "reason_text" TEXT,
  "actor_user_id" TEXT,
  "occurred_at" TEXT NOT NULL,
  "metadata_json" TEXT NOT NULL DEFAULT '{}',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_appointment_history_appointment_time" ON "appointment_status_history" ("appointment_id", "occurred_at");

CREATE TABLE "appointments" (
"id" TEXT PRIMARY KEY NOT NULL,
  "appointment_code" TEXT NOT NULL,
  "patient_id" TEXT NOT NULL,
  "clinic_id" TEXT NOT NULL,
  "dentist_id" TEXT NOT NULL,
  "chair_id" TEXT,
  "treatment_id" TEXT NOT NULL,
  "scheduled_start_at" TEXT NOT NULL,
  "scheduled_end_at" TEXT NOT NULL,
  "duration_minutes" BIGINT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'DRAFT',
  "booking_channel" TEXT NOT NULL DEFAULT 'FRONT_DESK',
  "priority" TEXT NOT NULL DEFAULT 'ROUTINE',
  "confirmation_state" TEXT NOT NULL DEFAULT 'PENDING',
  "risk_flag" TEXT NOT NULL DEFAULT 'NONE',
  "notes" TEXT NOT NULL DEFAULT '',
  "cancellation_reason_code" TEXT,
  "appointment_version" BIGINT NOT NULL DEFAULT 1,
  "created_by_user_id" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_appointments_code" ON "appointments" ("appointment_code");
CREATE INDEX "idx_appointments_clinic_time" ON "appointments" ("clinic_id", "scheduled_start_at", "scheduled_end_at");
CREATE INDEX "idx_appointments_dentist_time" ON "appointments" ("dentist_id", "scheduled_start_at", "scheduled_end_at");
CREATE INDEX "idx_appointments_chair_time" ON "appointments" ("chair_id", "scheduled_start_at", "scheduled_end_at");
CREATE INDEX "idx_appointments_patient_time" ON "appointments" ("patient_id", "scheduled_start_at", "scheduled_end_at");
CREATE INDEX "idx_appointments_status_time" ON "appointments" ("status", "scheduled_start_at");

CREATE TABLE "audit_events" (
"id" BIGSERIAL PRIMARY KEY NOT NULL,
  "request_id" TEXT NOT NULL,
  "actor_user_id" TEXT,
  "actor_subject" TEXT,
  "action" TEXT NOT NULL,
  "entity_type" TEXT NOT NULL,
  "entity_id" TEXT NOT NULL,
  "clinic_id" TEXT,
  "outcome" TEXT NOT NULL DEFAULT 'SUCCESS',
  "source" TEXT NOT NULL DEFAULT 'WEB',
  "reason" TEXT,
  "before_json" TEXT,
  "after_json" TEXT,
  "metadata_json" TEXT,
  "occurred_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_audit_events_request_action" ON "audit_events" ("request_id", "action", "entity_type", "entity_id");
CREATE INDEX "idx_audit_events_entity_time" ON "audit_events" ("entity_type", "entity_id", "occurred_at");
CREATE INDEX "idx_audit_events_actor_time" ON "audit_events" ("actor_user_id", "occurred_at");
CREATE INDEX "idx_audit_events_clinic_time" ON "audit_events" ("clinic_id", "occurred_at");

CREATE TABLE "auth_identities" (
"id" TEXT PRIMARY KEY NOT NULL,
  "user_id" TEXT NOT NULL,
  "provider" TEXT NOT NULL,
  "provider_subject" TEXT NOT NULL,
  "profile_json" TEXT NOT NULL DEFAULT '{}',
  "last_used_at" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_auth_identities_provider_subject" ON "auth_identities" ("provider", "provider_subject");
CREATE INDEX "idx_auth_identities_user" ON "auth_identities" ("user_id");

CREATE TABLE "auth_oauth_states" (
"id" TEXT PRIMARY KEY NOT NULL,
  "provider" TEXT NOT NULL,
  "state_hash" TEXT NOT NULL,
  "return_to" TEXT NOT NULL DEFAULT '/',
  "expires_at" TEXT NOT NULL,
  "consumed_at" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_auth_oauth_states_state_hash" ON "auth_oauth_states" ("state_hash");
CREATE INDEX "idx_auth_oauth_states_expiry" ON "auth_oauth_states" ("expires_at");

CREATE TABLE "auth_otp_challenges" (
"id" TEXT PRIMARY KEY NOT NULL,
  "phone_e164" TEXT NOT NULL,
  "purpose" TEXT NOT NULL,
  "code_hash" TEXT NOT NULL,
  "code_salt" TEXT NOT NULL,
  "expires_at" TEXT NOT NULL,
  "consumed_at" TEXT,
  "attempt_count" BIGINT NOT NULL DEFAULT 0,
  "max_attempts" BIGINT NOT NULL DEFAULT 5,
  "request_ip_hash" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_auth_otp_phone_purpose_created" ON "auth_otp_challenges" ("phone_e164", "purpose", "created_at");
CREATE INDEX "idx_auth_otp_expiry" ON "auth_otp_challenges" ("expires_at");

CREATE TABLE "auth_sessions" (
"id" TEXT PRIMARY KEY NOT NULL,
  "user_id" TEXT NOT NULL,
  "token_hash" TEXT NOT NULL,
  "auth_method" TEXT NOT NULL,
  "expires_at" TEXT NOT NULL,
  "revoked_at" TEXT,
  "last_seen_at" TEXT,
  "ip_hash" TEXT,
  "user_agent_hash" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_auth_sessions_token_hash" ON "auth_sessions" ("token_hash");
CREATE INDEX "idx_auth_sessions_user_expiry" ON "auth_sessions" ("user_id", "expires_at");

CREATE TABLE "clinic_chairs" (
"id" TEXT PRIMARY KEY NOT NULL,
  "clinic_id" TEXT NOT NULL,
  "code" TEXT NOT NULL,
  "name_en" TEXT NOT NULL,
  "name_zh" TEXT NOT NULL,
  "room_name_en" TEXT NOT NULL,
  "room_name_zh" TEXT NOT NULL,
  "equipment_json" TEXT NOT NULL DEFAULT '[]',
  "is_accessible" BIGINT NOT NULL DEFAULT 0,
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_clinic_chairs_clinic_code" ON "clinic_chairs" ("clinic_id", "code");
CREATE INDEX "idx_clinic_chairs_clinic_status" ON "clinic_chairs" ("clinic_id", "status");

CREATE TABLE "clinic_closures" (
"id" TEXT PRIMARY KEY NOT NULL,
  "clinic_id" TEXT NOT NULL,
  "starts_at" TEXT NOT NULL,
  "ends_at" TEXT NOT NULL,
  "reason_code" TEXT NOT NULL,
  "reason_en" TEXT NOT NULL,
  "reason_zh" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_clinic_closures_clinic_time" ON "clinic_closures" ("clinic_id", "starts_at", "ends_at");

CREATE TABLE "clinic_operating_hours" (
"clinic_id" TEXT NOT NULL,
  "day_of_week" BIGINT NOT NULL,
  "opens_at" TEXT NOT NULL,
  "closes_at" TEXT NOT NULL,
  "slot_minutes" BIGINT NOT NULL DEFAULT 10,
  "is_closed" BIGINT NOT NULL DEFAULT 0,
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  PRIMARY KEY ("clinic_id", "day_of_week")
);
CREATE INDEX "idx_clinic_hours_day" ON "clinic_operating_hours" ("day_of_week", "is_closed");

CREATE TABLE "clinical_attachments" (
"id" TEXT PRIMARY KEY NOT NULL,
  "visit_id" TEXT NOT NULL,
  "category" TEXT NOT NULL,
  "file_name" TEXT NOT NULL,
  "mime_type" TEXT NOT NULL,
  "storage_key" TEXT NOT NULL,
  "size_bytes" BIGINT NOT NULL,
  "description_en" TEXT NOT NULL DEFAULT '',
  "description_zh" TEXT NOT NULL DEFAULT '',
  "content_checksum" TEXT NOT NULL,
  "captured_at" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'AVAILABLE',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_clinical_attachment_storage" ON "clinical_attachments" ("storage_key");
CREATE INDEX "idx_clinical_attachments_visit" ON "clinical_attachments" ("visit_id", "category");

CREATE TABLE "clinical_note_versions" (
"id" TEXT PRIMARY KEY NOT NULL,
  "clinical_note_id" TEXT NOT NULL,
  "version_number" BIGINT NOT NULL,
  "content_en" TEXT NOT NULL,
  "content_zh" TEXT NOT NULL,
  "amendment_reason" TEXT,
  "author_user_id" TEXT,
  "content_checksum" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_clinical_note_version" ON "clinical_note_versions" ("clinical_note_id", "version_number");

CREATE TABLE "clinical_notes" (
"id" TEXT PRIMARY KEY NOT NULL,
  "visit_id" TEXT NOT NULL,
  "note_type" TEXT NOT NULL DEFAULT 'SOAP',
  "current_version" BIGINT NOT NULL DEFAULT 1,
  "status" TEXT NOT NULL DEFAULT 'DRAFT',
  "signed_by_dentist_id" TEXT,
  "signed_at" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_clinical_notes_visit_type" ON "clinical_notes" ("visit_id", "note_type");

CREATE TABLE "clinical_visits" (
"id" TEXT PRIMARY KEY NOT NULL,
  "visit_code" TEXT NOT NULL,
  "appointment_id" TEXT NOT NULL,
  "patient_id" TEXT NOT NULL,
  "clinic_id" TEXT NOT NULL,
  "dentist_id" TEXT NOT NULL,
  "chair_id" TEXT,
  "status" TEXT NOT NULL DEFAULT 'OPEN',
  "chief_complaint_en" TEXT NOT NULL DEFAULT '',
  "chief_complaint_zh" TEXT NOT NULL DEFAULT '',
  "safety_gate_status" TEXT NOT NULL DEFAULT 'PENDING',
  "started_at" TEXT NOT NULL,
  "completed_at" TEXT,
  "visit_version" BIGINT NOT NULL DEFAULT 1,
  "created_by_user_id" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_clinical_visits_code" ON "clinical_visits" ("visit_code");
CREATE UNIQUE INDEX "uq_clinical_visits_appointment" ON "clinical_visits" ("appointment_id");
CREATE INDEX "idx_clinical_visits_patient_time" ON "clinical_visits" ("patient_id", "started_at");
CREATE INDEX "idx_clinical_visits_clinic_status" ON "clinical_visits" ("clinic_id", "status");

CREATE TABLE "clinics" (
"id" TEXT PRIMARY KEY NOT NULL,
  "organization_id" TEXT NOT NULL,
  "code" TEXT NOT NULL,
  "name_en" TEXT NOT NULL,
  "name_zh" TEXT NOT NULL,
  "city_en" TEXT NOT NULL,
  "city_zh" TEXT NOT NULL,
  "address_en" TEXT NOT NULL DEFAULT '',
  "address_zh" TEXT NOT NULL DEFAULT '',
  "phone" TEXT,
  "email" TEXT,
  "chair_capacity" BIGINT NOT NULL DEFAULT 1,
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "opened_on" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_clinics_code" ON "clinics" ("code");
CREATE INDEX "idx_clinics_organization_status" ON "clinics" ("organization_id", "status");

CREATE TABLE "dentist_availability_rules" (
"id" TEXT PRIMARY KEY NOT NULL,
  "dentist_id" TEXT NOT NULL,
  "clinic_id" TEXT NOT NULL,
  "day_of_week" BIGINT NOT NULL,
  "starts_at" TEXT NOT NULL,
  "ends_at" TEXT NOT NULL,
  "effective_from" TEXT NOT NULL,
  "effective_to" TEXT,
  "recurrence_rule" TEXT NOT NULL DEFAULT 'WEEKLY',
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_dentist_availability_lookup" ON "dentist_availability_rules" ("dentist_id", "clinic_id", "day_of_week", "status");

CREATE TABLE "dentist_clinic_assignments" (
"id" TEXT PRIMARY KEY NOT NULL,
  "dentist_id" TEXT NOT NULL,
  "clinic_id" TEXT NOT NULL,
  "is_primary" BIGINT NOT NULL DEFAULT 0,
  "effective_from" TEXT NOT NULL,
  "effective_to" TEXT,
  "weekly_hours" BIGINT NOT NULL DEFAULT 40,
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_dentist_assignments_dentist_status" ON "dentist_clinic_assignments" ("dentist_id", "status");
CREATE INDEX "idx_dentist_assignments_clinic_status" ON "dentist_clinic_assignments" ("clinic_id", "status");

CREATE TABLE "dentist_qualifications" (
"id" TEXT PRIMARY KEY NOT NULL,
  "dentist_id" TEXT NOT NULL,
  "qualification_type_id" TEXT NOT NULL,
  "issuing_body" TEXT NOT NULL,
  "reference_number" TEXT NOT NULL,
  "issued_on" TEXT NOT NULL,
  "expires_on" TEXT,
  "verification_status" TEXT NOT NULL DEFAULT 'VERIFIED',
  "verified_at" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_dentist_qualification_reference" ON "dentist_qualifications" ("reference_number");
CREATE INDEX "idx_dentist_qualifications_dentist" ON "dentist_qualifications" ("dentist_id");
CREATE INDEX "idx_dentist_qualifications_expiry" ON "dentist_qualifications" ("expires_on");

CREATE TABLE "dentist_schedule_exceptions" (
"id" TEXT PRIMARY KEY NOT NULL,
  "dentist_id" TEXT NOT NULL,
  "clinic_id" TEXT,
  "starts_at" TEXT NOT NULL,
  "ends_at" TEXT NOT NULL,
  "exception_type" TEXT NOT NULL,
  "reason_en" TEXT NOT NULL DEFAULT '',
  "reason_zh" TEXT NOT NULL DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_dentist_exceptions_time" ON "dentist_schedule_exceptions" ("dentist_id", "starts_at", "ends_at");

CREATE TABLE "dentists" (
"id" TEXT PRIMARY KEY NOT NULL,
  "employee_code" TEXT NOT NULL,
  "name_en" TEXT NOT NULL,
  "name_zh" TEXT NOT NULL,
  "title_en" TEXT NOT NULL,
  "title_zh" TEXT NOT NULL,
  "email" TEXT NOT NULL,
  "phone" TEXT,
  "hire_date" TEXT NOT NULL,
  "employment_status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "languages_json" TEXT NOT NULL DEFAULT '["zh"]',
  "biography_en" TEXT NOT NULL DEFAULT '',
  "biography_zh" TEXT NOT NULL DEFAULT '',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_dentists_employee_code" ON "dentists" ("employee_code");
CREATE UNIQUE INDEX "uq_dentists_email" ON "dentists" ("email");
CREATE INDEX "idx_dentists_employment_status" ON "dentists" ("employment_status");

CREATE TABLE "emergency_contacts" (
"id" TEXT PRIMARY KEY NOT NULL,
  "patient_id" TEXT NOT NULL,
  "contact_name" TEXT NOT NULL,
  "relationship_en" TEXT NOT NULL,
  "relationship_zh" TEXT NOT NULL,
  "phone" TEXT NOT NULL,
  "priority" BIGINT NOT NULL DEFAULT 1,
  "is_authorized_contact" BIGINT NOT NULL DEFAULT 1,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_emergency_contact_patient_priority" ON "emergency_contacts" ("patient_id", "priority");
CREATE INDEX "idx_emergency_contacts_patient" ON "emergency_contacts" ("patient_id");

CREATE TABLE "expansion_assumptions" (
"id" TEXT PRIMARY KEY NOT NULL,
  "scenario_id" TEXT NOT NULL,
  "assumption_key" TEXT NOT NULL,
  "label_en" TEXT NOT NULL,
  "label_zh" TEXT NOT NULL,
  "value_text" TEXT NOT NULL,
  "unit" TEXT NOT NULL,
  "source_en" TEXT NOT NULL,
  "source_zh" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_expansion_assumption_key" ON "expansion_assumptions" ("scenario_id", "assumption_key");

CREATE TABLE "expansion_candidate_clinics" (
"id" TEXT PRIMARY KEY NOT NULL,
  "scenario_id" TEXT NOT NULL,
  "candidate_code" TEXT NOT NULL,
  "name_en" TEXT NOT NULL,
  "name_zh" TEXT NOT NULL,
  "city_en" TEXT NOT NULL,
  "city_zh" TEXT NOT NULL,
  "district_en" TEXT NOT NULL,
  "district_zh" TEXT NOT NULL,
  "planned_chair_count" BIGINT NOT NULL,
  "planned_dentist_count" BIGINT NOT NULL,
  "planned_support_staff_count" BIGINT NOT NULL,
  "forecast_quarterly_appointments" BIGINT NOT NULL,
  "initial_capital_fen" BIGINT NOT NULL,
  "quarterly_fixed_cost_fen" BIGINT NOT NULL,
  "required_qualifications_json" TEXT NOT NULL DEFAULT '[]',
  "qualification_coverage_basis_points" BIGINT NOT NULL,
  "travel_constraint_minutes" BIGINT NOT NULL,
  "readiness_status" TEXT NOT NULL DEFAULT 'REVIEW',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_expansion_candidate_code" ON "expansion_candidate_clinics" ("scenario_id", "candidate_code");
CREATE INDEX "idx_expansion_candidates_scenario_readiness" ON "expansion_candidate_clinics" ("scenario_id", "readiness_status");

CREATE TABLE "expansion_scenario_results" (
"id" TEXT PRIMARY KEY NOT NULL,
  "scenario_id" TEXT NOT NULL,
  "projected_quarter_revenue_fen" BIGINT NOT NULL,
  "projected_treatment_cost_fen" BIGINT NOT NULL,
  "projected_operating_expense_fen" BIGINT NOT NULL,
  "projected_net_profit_fen" BIGINT NOT NULL,
  "projected_margin_basis_points" BIGINT NOT NULL,
  "payback_months" BIGINT NOT NULL,
  "demand_coverage_basis_points" BIGINT NOT NULL,
  "qualification_coverage_basis_points" BIGINT NOT NULL,
  "composite_score" BIGINT NOT NULL,
  "risk_level" TEXT NOT NULL,
  "formula_evidence_json" TEXT NOT NULL,
  "calculated_at" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_expansion_result_scenario" ON "expansion_scenario_results" ("scenario_id");
CREATE INDEX "idx_expansion_result_score" ON "expansion_scenario_results" ("composite_score", "risk_level");

CREATE TABLE "expansion_scenarios" (
"id" TEXT PRIMARY KEY NOT NULL,
  "scenario_code" TEXT NOT NULL,
  "version" BIGINT NOT NULL DEFAULT 1,
  "name_en" TEXT NOT NULL,
  "name_zh" TEXT NOT NULL,
  "description_en" TEXT NOT NULL,
  "description_zh" TEXT NOT NULL,
  "forecast_horizon_months" BIGINT NOT NULL DEFAULT 24,
  "status" TEXT NOT NULL DEFAULT 'DRAFT',
  "advisory_disclaimer_en" TEXT NOT NULL,
  "advisory_disclaimer_zh" TEXT NOT NULL,
  "created_by_user_id" TEXT,
  "approved_by_user_id" TEXT,
  "approved_at" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_expansion_scenario_code_version" ON "expansion_scenarios" ("scenario_code", "version");
CREATE INDEX "idx_expansion_scenario_status" ON "expansion_scenarios" ("status", "updated_at");

CREATE TABLE "financial_close_exceptions" (
"id" TEXT PRIMARY KEY NOT NULL,
  "reporting_period_id" TEXT NOT NULL,
  "clinic_id" TEXT,
  "exception_type" TEXT NOT NULL,
  "severity" TEXT NOT NULL,
  "entity_type" TEXT NOT NULL,
  "entity_id" TEXT NOT NULL,
  "description_en" TEXT NOT NULL,
  "description_zh" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'OPEN',
  "resolved_at" TEXT,
  "resolution_note" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_financial_exceptions_period_status" ON "financial_close_exceptions" ("reporting_period_id", "status", "severity");

CREATE TABLE "financial_period_results" (
"id" TEXT PRIMARY KEY NOT NULL,
  "reporting_period_id" TEXT NOT NULL,
  "clinic_id" TEXT,
  "scope_key" TEXT NOT NULL,
  "recognized_revenue_fen" BIGINT NOT NULL,
  "treatment_cost_fen" BIGINT NOT NULL,
  "operating_expense_fen" BIGINT NOT NULL,
  "net_profit_fen" BIGINT NOT NULL,
  "net_margin_basis_points" BIGINT NOT NULL,
  "invoice_count" BIGINT NOT NULL DEFAULT 0,
  "open_exception_count" BIGINT NOT NULL DEFAULT 0,
  "calculation_inputs_json" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'DRAFT',
  "calculated_at" TEXT NOT NULL,
  "approved_at" TEXT,
  "approved_by_user_id" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_financial_result_period_scope" ON "financial_period_results" ("reporting_period_id", "scope_key");
CREATE INDEX "idx_financial_results_period_profit" ON "financial_period_results" ("reporting_period_id", "net_profit_fen");

CREATE TABLE "financial_reporting_periods" (
"id" TEXT PRIMARY KEY NOT NULL,
  "period_code" TEXT NOT NULL,
  "name_en" TEXT NOT NULL,
  "name_zh" TEXT NOT NULL,
  "starts_on" TEXT NOT NULL,
  "ends_on" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'OPEN',
  "close_checklist_json" TEXT NOT NULL DEFAULT '[]',
  "locked_at" TEXT,
  "locked_by_user_id" TEXT,
  "reopened_at" TEXT,
  "reopened_by_user_id" TEXT,
  "reopen_reason" TEXT,
  "period_version" BIGINT NOT NULL DEFAULT 1,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_financial_period_code" ON "financial_reporting_periods" ("period_code");
CREATE INDEX "idx_financial_period_dates" ON "financial_reporting_periods" ("starts_on", "ends_on");

CREATE TABLE "incentive_pools" (
"id" TEXT PRIMARY KEY NOT NULL,
  "reporting_period_id" TEXT NOT NULL,
  "network_result_id" TEXT NOT NULL,
  "rate_basis_points" BIGINT NOT NULL DEFAULT 1000,
  "eligible_net_profit_fen" BIGINT NOT NULL,
  "pool_amount_fen" BIGINT NOT NULL,
  "formula_evidence" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'DRAFT',
  "approved_at" TEXT,
  "approved_by_user_id" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_incentive_pool_period" ON "incentive_pools" ("reporting_period_id");

CREATE TABLE "invoice_adjustments" (
"id" TEXT PRIMARY KEY NOT NULL,
  "invoice_id" TEXT NOT NULL,
  "adjustment_type" TEXT NOT NULL,
  "amount_fen" BIGINT NOT NULL,
  "reason_code" TEXT NOT NULL,
  "reason_text" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "authored_by_user_id" TEXT,
  "approved_by_user_id" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_invoice_adjustments_invoice" ON "invoice_adjustments" ("invoice_id", "status");

CREATE TABLE "invoice_lines" (
"id" TEXT PRIMARY KEY NOT NULL,
  "invoice_id" TEXT NOT NULL,
  "actual_treatment_item_id" TEXT NOT NULL,
  "line_number" BIGINT NOT NULL,
  "treatment_code_snapshot" TEXT NOT NULL,
  "description_en_snapshot" TEXT NOT NULL,
  "description_zh_snapshot" TEXT NOT NULL,
  "tooth_code_snapshot" TEXT,
  "surfaces_json_snapshot" TEXT NOT NULL DEFAULT '[]',
  "units_snapshot" BIGINT NOT NULL,
  "unit_price_fen_snapshot" BIGINT NOT NULL,
  "amount_fen_snapshot" BIGINT NOT NULL,
  "cost_fen_snapshot" BIGINT NOT NULL DEFAULT 0,
  "performed_at_snapshot" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_invoice_line_number" ON "invoice_lines" ("invoice_id", "line_number");
CREATE UNIQUE INDEX "uq_invoice_line_actual_treatment" ON "invoice_lines" ("actual_treatment_item_id");
CREATE INDEX "idx_invoice_lines_invoice" ON "invoice_lines" ("invoice_id");

CREATE TABLE "invoices" (
"id" TEXT PRIMARY KEY NOT NULL,
  "invoice_code" TEXT NOT NULL,
  "visit_id" TEXT NOT NULL,
  "patient_id" TEXT NOT NULL,
  "clinic_id" TEXT NOT NULL,
  "reporting_period_id" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'DRAFT',
  "currency" TEXT NOT NULL DEFAULT 'CNY',
  "subtotal_fen" BIGINT NOT NULL DEFAULT 0,
  "adjustment_total_fen" BIGINT NOT NULL DEFAULT 0,
  "tax_total_fen" BIGINT NOT NULL DEFAULT 0,
  "total_fen" BIGINT NOT NULL DEFAULT 0,
  "paid_fen" BIGINT NOT NULL DEFAULT 0,
  "refunded_fen" BIGINT NOT NULL DEFAULT 0,
  "balance_fen" BIGINT NOT NULL DEFAULT 0,
  "issued_at" TEXT,
  "due_at" TEXT,
  "voided_at" TEXT,
  "void_reason" TEXT,
  "invoice_version" BIGINT NOT NULL DEFAULT 1,
  "created_by_user_id" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_invoices_code" ON "invoices" ("invoice_code");
CREATE UNIQUE INDEX "uq_invoices_visit" ON "invoices" ("visit_id");
CREATE INDEX "idx_invoices_clinic_status" ON "invoices" ("clinic_id", "status");
CREATE INDEX "idx_invoices_period_status" ON "invoices" ("reporting_period_id", "status");
CREATE INDEX "idx_invoices_due_balance" ON "invoices" ("due_at", "balance_fen");

CREATE TABLE "notification_events" (
"id" TEXT PRIMARY KEY NOT NULL,
  "appointment_id" TEXT,
  "channel" TEXT NOT NULL,
  "template_code" TEXT NOT NULL,
  "recipient_masked" TEXT NOT NULL,
  "locale" TEXT NOT NULL DEFAULT 'zh',
  "status" TEXT NOT NULL DEFAULT 'QUEUED',
  "idempotency_key" TEXT NOT NULL,
  "queued_at" TEXT NOT NULL,
  "sent_at" TEXT,
  "delivered_at" TEXT,
  "failure_code" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_notification_idempotency" ON "notification_events" ("idempotency_key");
CREATE INDEX "idx_notifications_appointment_time" ON "notification_events" ("appointment_id", "queued_at");

CREATE TABLE "odontogram_observations" (
"id" TEXT PRIMARY KEY NOT NULL,
  "visit_id" TEXT NOT NULL,
  "patient_id" TEXT NOT NULL,
  "tooth_code" TEXT NOT NULL,
  "dentition" TEXT NOT NULL DEFAULT 'PERMANENT',
  "surfaces_json" TEXT NOT NULL DEFAULT '[]',
  "observation_type" TEXT NOT NULL,
  "severity" TEXT NOT NULL DEFAULT 'ROUTINE',
  "finding_en" TEXT NOT NULL,
  "finding_zh" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "observed_by_dentist_id" TEXT NOT NULL,
  "observed_at" TEXT NOT NULL,
  "supersedes_observation_id" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_odontogram_patient_tooth" ON "odontogram_observations" ("patient_id", "tooth_code");
CREATE INDEX "idx_odontogram_visit_tooth" ON "odontogram_observations" ("visit_id", "tooth_code");

CREATE TABLE "operating_expenses" (
"id" TEXT PRIMARY KEY NOT NULL,
  "clinic_id" TEXT NOT NULL,
  "reporting_period_id" TEXT NOT NULL,
  "category" TEXT NOT NULL,
  "vendor_name" TEXT NOT NULL DEFAULT '',
  "amount_fen" BIGINT NOT NULL,
  "incurred_on" TEXT NOT NULL,
  "description_en" TEXT NOT NULL,
  "description_zh" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'APPROVED',
  "entered_by_user_id" TEXT,
  "approved_by_user_id" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_operating_expense_period_clinic" ON "operating_expenses" ("reporting_period_id", "clinic_id");
CREATE INDEX "idx_operating_expense_category" ON "operating_expenses" ("category", "incurred_on");

CREATE TABLE "organizations" (
"id" TEXT PRIMARY KEY NOT NULL,
  "code" TEXT NOT NULL,
  "name_en" TEXT NOT NULL,
  "name_zh" TEXT NOT NULL,
  "timezone" TEXT NOT NULL DEFAULT 'Asia/Shanghai',
  "currency" TEXT NOT NULL DEFAULT 'CNY',
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_organizations_code" ON "organizations" ("code");

CREATE TABLE "patient_account_links" (
"id" TEXT PRIMARY KEY NOT NULL,
  "user_id" TEXT NOT NULL,
  "patient_id" TEXT NOT NULL,
  "verification_method" TEXT NOT NULL,
  "verified_at" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_patient_account_links_user" ON "patient_account_links" ("user_id");
CREATE UNIQUE INDEX "uq_patient_account_links_patient" ON "patient_account_links" ("patient_id");

CREATE TABLE "patient_allergies" (
"id" TEXT PRIMARY KEY NOT NULL,
  "patient_id" TEXT NOT NULL,
  "substance_en" TEXT NOT NULL,
  "substance_zh" TEXT NOT NULL,
  "reaction_en" TEXT NOT NULL,
  "reaction_zh" TEXT NOT NULL,
  "severity" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "verified_at" TEXT,
  "verified_by_dentist_id" TEXT,
  "notes_en" TEXT NOT NULL DEFAULT '',
  "notes_zh" TEXT NOT NULL DEFAULT '',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_patient_allergies_patient_status" ON "patient_allergies" ("patient_id", "status");
CREATE INDEX "idx_patient_allergies_severity" ON "patient_allergies" ("severity");

CREATE TABLE "patient_consents" (
"id" TEXT PRIMARY KEY NOT NULL,
  "patient_id" TEXT NOT NULL,
  "consent_type" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "policy_version" TEXT NOT NULL,
  "captured_at" TEXT NOT NULL,
  "expires_at" TEXT,
  "source" TEXT NOT NULL DEFAULT 'FRONT_DESK',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_patient_consents_type_version" ON "patient_consents" ("patient_id", "consent_type", "policy_version");
CREATE INDEX "idx_patient_consents_patient_status" ON "patient_consents" ("patient_id", "status");

CREATE TABLE "patient_duplicate_reviews" (
"id" TEXT PRIMARY KEY NOT NULL,
  "source_patient_id" TEXT NOT NULL,
  "candidate_patient_id" TEXT NOT NULL,
  "match_score" BIGINT NOT NULL,
  "match_reasons_json" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'OPEN',
  "reviewed_by_user_id" TEXT,
  "reviewed_at" TEXT,
  "resolution_notes" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_patient_duplicate_pair" ON "patient_duplicate_reviews" ("source_patient_id", "candidate_patient_id");
CREATE INDEX "idx_patient_duplicate_status_score" ON "patient_duplicate_reviews" ("status", "match_score");

CREATE TABLE "patient_timeline_events" (
"id" TEXT PRIMARY KEY NOT NULL,
  "patient_id" TEXT NOT NULL,
  "clinic_id" TEXT,
  "event_type" TEXT NOT NULL,
  "occurred_at" TEXT NOT NULL,
  "title_en" TEXT NOT NULL,
  "title_zh" TEXT NOT NULL,
  "description_en" TEXT NOT NULL DEFAULT '',
  "description_zh" TEXT NOT NULL DEFAULT '',
  "reference_type" TEXT,
  "reference_id" TEXT,
  "status" TEXT NOT NULL,
  "amount_fen" BIGINT,
  "metadata_json" TEXT NOT NULL DEFAULT '{}',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_patient_timeline_patient_time" ON "patient_timeline_events" ("patient_id", "occurred_at");
CREATE INDEX "idx_patient_timeline_reference" ON "patient_timeline_events" ("reference_type", "reference_id");

CREATE TABLE "patients" (
"id" TEXT PRIMARY KEY NOT NULL,
  "patient_code" TEXT NOT NULL,
  "name_en" TEXT NOT NULL,
  "name_zh" TEXT NOT NULL,
  "date_of_birth" TEXT NOT NULL,
  "gender" TEXT NOT NULL,
  "phone" TEXT NOT NULL,
  "email" TEXT,
  "government_id_last4" TEXT,
  "preferred_language" TEXT NOT NULL DEFAULT 'zh',
  "communication_channel" TEXT NOT NULL DEFAULT 'WECHAT',
  "primary_clinic_id" TEXT,
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "last_visit_at" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_patients_patient_code" ON "patients" ("patient_code");
CREATE INDEX "idx_patients_name_zh" ON "patients" ("name_zh");
CREATE INDEX "idx_patients_name_en" ON "patients" ("name_en");
CREATE INDEX "idx_patients_phone" ON "patients" ("phone");
CREATE INDEX "idx_patients_primary_clinic" ON "patients" ("primary_clinic_id");

CREATE TABLE "payment_refunds" (
"id" TEXT PRIMARY KEY NOT NULL,
  "refund_code" TEXT NOT NULL,
  "payment_id" TEXT NOT NULL,
  "amount_fen" BIGINT NOT NULL,
  "reason_code" TEXT NOT NULL,
  "reason_text" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'COMPLETED',
  "authorized_by_user_id" TEXT,
  "refunded_at" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_payment_refunds_code" ON "payment_refunds" ("refund_code");
CREATE INDEX "idx_payment_refunds_payment" ON "payment_refunds" ("payment_id", "status");

CREATE TABLE "payments" (
"id" TEXT PRIMARY KEY NOT NULL,
  "payment_code" TEXT NOT NULL,
  "invoice_id" TEXT NOT NULL,
  "amount_fen" BIGINT NOT NULL,
  "method" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'CAPTURED',
  "simulated_gateway_reference" TEXT NOT NULL,
  "received_at" TEXT NOT NULL,
  "recorded_by_user_id" TEXT,
  "notes" TEXT NOT NULL DEFAULT '',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_payments_code" ON "payments" ("payment_code");
CREATE UNIQUE INDEX "uq_payments_gateway_reference" ON "payments" ("simulated_gateway_reference");
CREATE INDEX "idx_payments_invoice_time" ON "payments" ("invoice_id", "received_at");

CREATE TABLE "permissions" (
"id" TEXT PRIMARY KEY NOT NULL,
  "code" TEXT NOT NULL,
  "domain" TEXT NOT NULL,
  "description_en" TEXT NOT NULL,
  "description_zh" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_permissions_code" ON "permissions" ("code");
CREATE INDEX "idx_permissions_domain" ON "permissions" ("domain");

CREATE TABLE "qualification_types" (
"id" TEXT PRIMARY KEY NOT NULL,
  "code" TEXT NOT NULL,
  "name_en" TEXT NOT NULL,
  "name_zh" TEXT NOT NULL,
  "category" TEXT NOT NULL,
  "description_en" TEXT NOT NULL DEFAULT '',
  "description_zh" TEXT NOT NULL DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_qualification_types_code" ON "qualification_types" ("code");

CREATE TABLE "requested_treatment_items" (
"id" TEXT PRIMARY KEY NOT NULL,
  "plan_id" TEXT NOT NULL,
  "visit_id" TEXT NOT NULL,
  "treatment_id" TEXT NOT NULL,
  "sequence" BIGINT NOT NULL,
  "tooth_code" TEXT,
  "surfaces_json" TEXT NOT NULL DEFAULT '[]',
  "units" BIGINT NOT NULL DEFAULT 1,
  "priority" TEXT NOT NULL DEFAULT 'ROUTINE',
  "rationale_en" TEXT NOT NULL DEFAULT '',
  "rationale_zh" TEXT NOT NULL DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'PLANNED',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_requested_treatment_sequence" ON "requested_treatment_items" ("plan_id", "sequence");
CREATE INDEX "idx_requested_treatments_visit" ON "requested_treatment_items" ("visit_id", "status");

CREATE TABLE "role_permissions" (
"role_id" TEXT NOT NULL,
  "permission_id" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  PRIMARY KEY ("role_id", "permission_id")
);
CREATE INDEX "idx_role_permissions_permission" ON "role_permissions" ("permission_id");

CREATE TABLE "roles" (
"id" TEXT PRIMARY KEY NOT NULL,
  "code" TEXT NOT NULL,
  "name_en" TEXT NOT NULL,
  "name_zh" TEXT NOT NULL,
  "description_en" TEXT NOT NULL DEFAULT '',
  "description_zh" TEXT NOT NULL DEFAULT '',
  "is_system" BIGINT NOT NULL DEFAULT 1,
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_roles_code" ON "roles" ("code");

CREATE TABLE "system_settings" (
"organization_id" TEXT NOT NULL,
  "setting_key" TEXT NOT NULL,
  "value_json" TEXT NOT NULL,
  "updated_by_user_id" TEXT,
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  PRIMARY KEY ("organization_id", "setting_key")
);

CREATE TABLE "treatment_catalog" (
"id" TEXT PRIMARY KEY NOT NULL,
  "code" TEXT NOT NULL,
  "name_en" TEXT NOT NULL,
  "name_zh" TEXT NOT NULL,
  "category" TEXT NOT NULL,
  "description_en" TEXT NOT NULL DEFAULT '',
  "description_zh" TEXT NOT NULL DEFAULT '',
  "duration_minutes" BIGINT NOT NULL,
  "standard_price_fen" BIGINT NOT NULL,
  "estimated_cost_fen" BIGINT NOT NULL,
  "version" BIGINT NOT NULL DEFAULT 1,
  "effective_from" TEXT NOT NULL,
  "effective_to" TEXT,
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_treatment_catalog_code_version" ON "treatment_catalog" ("code", "version");
CREATE INDEX "idx_treatment_catalog_category_status" ON "treatment_catalog" ("category", "status");

CREATE TABLE "treatment_cost_entries" (
"id" TEXT PRIMARY KEY NOT NULL,
  "actual_treatment_item_id" TEXT NOT NULL,
  "visit_id" TEXT NOT NULL,
  "clinic_id" TEXT NOT NULL,
  "reporting_period_id" TEXT NOT NULL,
  "catalog_estimated_cost_fen" BIGINT NOT NULL,
  "materials_cost_fen" BIGINT NOT NULL DEFAULT 0,
  "laboratory_cost_fen" BIGINT NOT NULL DEFAULT 0,
  "provider_cost_fen" BIGINT NOT NULL DEFAULT 0,
  "total_cost_fen" BIGINT NOT NULL,
  "cost_date" TEXT NOT NULL,
  "source" TEXT NOT NULL DEFAULT 'CATALOG_SNAPSHOT',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_treatment_cost_actual_item" ON "treatment_cost_entries" ("actual_treatment_item_id");
CREATE INDEX "idx_treatment_cost_period_clinic" ON "treatment_cost_entries" ("reporting_period_id", "clinic_id");

CREATE TABLE "treatment_plans" (
"id" TEXT PRIMARY KEY NOT NULL,
  "visit_id" TEXT NOT NULL,
  "plan_code" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'DRAFT',
  "clinical_priority" TEXT NOT NULL DEFAULT 'ROUTINE',
  "estimated_total_fen" BIGINT NOT NULL DEFAULT 0,
  "acceptance_status" TEXT NOT NULL DEFAULT 'PENDING',
  "accepted_at" TEXT,
  "accepted_by" TEXT,
  "valid_until" TEXT,
  "notes_en" TEXT NOT NULL DEFAULT '',
  "notes_zh" TEXT NOT NULL DEFAULT '',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_treatment_plans_code" ON "treatment_plans" ("plan_code");
CREATE INDEX "idx_treatment_plans_visit_status" ON "treatment_plans" ("visit_id", "status");

CREATE TABLE "treatment_qualification_requirements" (
"treatment_id" TEXT NOT NULL,
  "qualification_type_id" TEXT NOT NULL,
  "requirement_level" TEXT NOT NULL DEFAULT 'REQUIRED',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  PRIMARY KEY ("treatment_id", "qualification_type_id")
);
CREATE INDEX "idx_treatment_qualification_type" ON "treatment_qualification_requirements" ("qualification_type_id");

CREATE TABLE "user_role_assignments" (
"id" TEXT PRIMARY KEY NOT NULL,
  "user_id" TEXT NOT NULL,
  "role_id" TEXT NOT NULL,
  "clinic_id" TEXT,
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "effective_from" TEXT NOT NULL,
  "effective_to" TEXT,
  "granted_by_user_id" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_user_role_assignments_user_status" ON "user_role_assignments" ("user_id", "status");
CREATE INDEX "idx_user_role_assignments_clinic_status" ON "user_role_assignments" ("clinic_id", "status");

CREATE TABLE "visit_allergy_acknowledgements" (
"id" TEXT PRIMARY KEY NOT NULL,
  "visit_id" TEXT NOT NULL,
  "allergy_id" TEXT NOT NULL,
  "acknowledged_by_user_id" TEXT,
  "acknowledged_at" TEXT NOT NULL,
  "precaution_en" TEXT NOT NULL,
  "precaution_zh" TEXT NOT NULL,
  "outcome" TEXT NOT NULL DEFAULT 'ACKNOWLEDGED',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_visit_allergy_ack" ON "visit_allergy_acknowledgements" ("visit_id", "allergy_id");
CREATE INDEX "idx_visit_allergy_ack_visit" ON "visit_allergy_acknowledgements" ("visit_id", "acknowledged_at");

CREATE TABLE "waitlist_entries" (
"id" TEXT PRIMARY KEY NOT NULL,
  "patient_id" TEXT NOT NULL,
  "treatment_id" TEXT NOT NULL,
  "preferred_clinic_id" TEXT,
  "earliest_date" TEXT NOT NULL,
  "latest_date" TEXT NOT NULL,
  "preferred_periods_json" TEXT NOT NULL DEFAULT '[]',
  "acceptable_clinic_ids_json" TEXT NOT NULL DEFAULT '[]',
  "notice_hours" BIGINT NOT NULL DEFAULT 24,
  "priority_score" BIGINT NOT NULL DEFAULT 50,
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
  "updated_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE INDEX "idx_waitlist_status_dates" ON "waitlist_entries" ("status", "earliest_date", "latest_date");
CREATE INDEX "idx_waitlist_treatment_clinic" ON "waitlist_entries" ("treatment_id", "preferred_clinic_id");

CREATE TABLE "waitlist_offers" (
"id" TEXT PRIMARY KEY NOT NULL,
  "waitlist_entry_id" TEXT NOT NULL,
  "released_appointment_id" TEXT NOT NULL,
  "clinic_id" TEXT NOT NULL,
  "dentist_id" TEXT NOT NULL,
  "chair_id" TEXT,
  "offered_start_at" TEXT NOT NULL,
  "offered_end_at" TEXT NOT NULL,
  "compatibility_score" BIGINT NOT NULL,
  "reasons_json" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'PENDING',
  "expires_at" TEXT NOT NULL,
  "responded_at" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);
CREATE UNIQUE INDEX "uq_waitlist_offer_slot_entry" ON "waitlist_offers" ("waitlist_entry_id", "released_appointment_id");
CREATE INDEX "idx_waitlist_offers_status_expiry" ON "waitlist_offers" ("status", "expires_at");

ALTER TABLE "account_invitations" ADD FOREIGN KEY ("target_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "account_invitations" ADD FOREIGN KEY ("created_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "actual_treatment_items" ADD FOREIGN KEY ("visit_id") REFERENCES "clinical_visits" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "actual_treatment_items" ADD FOREIGN KEY ("requested_treatment_item_id") REFERENCES "requested_treatment_items" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "actual_treatment_items" ADD FOREIGN KEY ("treatment_id") REFERENCES "treatment_catalog" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "actual_treatment_items" ADD FOREIGN KEY ("provider_dentist_id") REFERENCES "dentists" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "appointment_status_history" ADD FOREIGN KEY ("appointment_id") REFERENCES "appointments" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "appointment_status_history" ADD FOREIGN KEY ("actor_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "appointments" ADD FOREIGN KEY ("patient_id") REFERENCES "patients" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "appointments" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "appointments" ADD FOREIGN KEY ("dentist_id") REFERENCES "dentists" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "appointments" ADD FOREIGN KEY ("chair_id") REFERENCES "clinic_chairs" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "appointments" ADD FOREIGN KEY ("treatment_id") REFERENCES "treatment_catalog" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "appointments" ADD FOREIGN KEY ("created_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "audit_events" ADD FOREIGN KEY ("actor_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "audit_events" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "auth_identities" ADD FOREIGN KEY ("user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "auth_sessions" ADD FOREIGN KEY ("user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "clinic_chairs" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "clinic_closures" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "clinic_operating_hours" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "clinical_attachments" ADD FOREIGN KEY ("visit_id") REFERENCES "clinical_visits" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "clinical_note_versions" ADD FOREIGN KEY ("clinical_note_id") REFERENCES "clinical_notes" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "clinical_note_versions" ADD FOREIGN KEY ("author_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "clinical_notes" ADD FOREIGN KEY ("visit_id") REFERENCES "clinical_visits" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "clinical_notes" ADD FOREIGN KEY ("signed_by_dentist_id") REFERENCES "dentists" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "clinical_visits" ADD FOREIGN KEY ("appointment_id") REFERENCES "appointments" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "clinical_visits" ADD FOREIGN KEY ("patient_id") REFERENCES "patients" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "clinical_visits" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "clinical_visits" ADD FOREIGN KEY ("dentist_id") REFERENCES "dentists" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "clinical_visits" ADD FOREIGN KEY ("chair_id") REFERENCES "clinic_chairs" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "clinical_visits" ADD FOREIGN KEY ("created_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "clinics" ADD FOREIGN KEY ("organization_id") REFERENCES "organizations" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "dentist_availability_rules" ADD FOREIGN KEY ("dentist_id") REFERENCES "dentists" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "dentist_availability_rules" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "dentist_clinic_assignments" ADD FOREIGN KEY ("dentist_id") REFERENCES "dentists" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "dentist_clinic_assignments" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "dentist_qualifications" ADD FOREIGN KEY ("dentist_id") REFERENCES "dentists" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "dentist_qualifications" ADD FOREIGN KEY ("qualification_type_id") REFERENCES "qualification_types" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "dentist_schedule_exceptions" ADD FOREIGN KEY ("dentist_id") REFERENCES "dentists" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "dentist_schedule_exceptions" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "emergency_contacts" ADD FOREIGN KEY ("patient_id") REFERENCES "patients" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "expansion_assumptions" ADD FOREIGN KEY ("scenario_id") REFERENCES "expansion_scenarios" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "expansion_candidate_clinics" ADD FOREIGN KEY ("scenario_id") REFERENCES "expansion_scenarios" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "expansion_scenario_results" ADD FOREIGN KEY ("scenario_id") REFERENCES "expansion_scenarios" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "expansion_scenarios" ADD FOREIGN KEY ("created_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "expansion_scenarios" ADD FOREIGN KEY ("approved_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "financial_close_exceptions" ADD FOREIGN KEY ("reporting_period_id") REFERENCES "financial_reporting_periods" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "financial_close_exceptions" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "financial_period_results" ADD FOREIGN KEY ("reporting_period_id") REFERENCES "financial_reporting_periods" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "financial_period_results" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "financial_period_results" ADD FOREIGN KEY ("approved_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "financial_reporting_periods" ADD FOREIGN KEY ("locked_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "financial_reporting_periods" ADD FOREIGN KEY ("reopened_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "incentive_pools" ADD FOREIGN KEY ("reporting_period_id") REFERENCES "financial_reporting_periods" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "incentive_pools" ADD FOREIGN KEY ("network_result_id") REFERENCES "financial_period_results" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "incentive_pools" ADD FOREIGN KEY ("approved_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "invoice_adjustments" ADD FOREIGN KEY ("invoice_id") REFERENCES "invoices" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "invoice_adjustments" ADD FOREIGN KEY ("authored_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "invoice_adjustments" ADD FOREIGN KEY ("approved_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "invoice_lines" ADD FOREIGN KEY ("invoice_id") REFERENCES "invoices" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "invoice_lines" ADD FOREIGN KEY ("actual_treatment_item_id") REFERENCES "actual_treatment_items" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "invoices" ADD FOREIGN KEY ("visit_id") REFERENCES "clinical_visits" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "invoices" ADD FOREIGN KEY ("patient_id") REFERENCES "patients" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "invoices" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "invoices" ADD FOREIGN KEY ("reporting_period_id") REFERENCES "financial_reporting_periods" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "invoices" ADD FOREIGN KEY ("created_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "notification_events" ADD FOREIGN KEY ("appointment_id") REFERENCES "appointments" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "odontogram_observations" ADD FOREIGN KEY ("visit_id") REFERENCES "clinical_visits" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "odontogram_observations" ADD FOREIGN KEY ("patient_id") REFERENCES "patients" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "odontogram_observations" ADD FOREIGN KEY ("observed_by_dentist_id") REFERENCES "dentists" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "operating_expenses" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "operating_expenses" ADD FOREIGN KEY ("reporting_period_id") REFERENCES "financial_reporting_periods" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "operating_expenses" ADD FOREIGN KEY ("entered_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "operating_expenses" ADD FOREIGN KEY ("approved_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "patient_account_links" ADD FOREIGN KEY ("user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "patient_account_links" ADD FOREIGN KEY ("patient_id") REFERENCES "patients" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "patient_allergies" ADD FOREIGN KEY ("patient_id") REFERENCES "patients" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "patient_allergies" ADD FOREIGN KEY ("verified_by_dentist_id") REFERENCES "dentists" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "patient_consents" ADD FOREIGN KEY ("patient_id") REFERENCES "patients" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "patient_duplicate_reviews" ADD FOREIGN KEY ("source_patient_id") REFERENCES "patients" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "patient_duplicate_reviews" ADD FOREIGN KEY ("candidate_patient_id") REFERENCES "patients" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "patient_duplicate_reviews" ADD FOREIGN KEY ("reviewed_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "patient_timeline_events" ADD FOREIGN KEY ("patient_id") REFERENCES "patients" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "patient_timeline_events" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "patients" ADD FOREIGN KEY ("primary_clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "payment_refunds" ADD FOREIGN KEY ("payment_id") REFERENCES "payments" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "payment_refunds" ADD FOREIGN KEY ("authorized_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "payments" ADD FOREIGN KEY ("invoice_id") REFERENCES "invoices" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "payments" ADD FOREIGN KEY ("recorded_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "requested_treatment_items" ADD FOREIGN KEY ("plan_id") REFERENCES "treatment_plans" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "requested_treatment_items" ADD FOREIGN KEY ("visit_id") REFERENCES "clinical_visits" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "requested_treatment_items" ADD FOREIGN KEY ("treatment_id") REFERENCES "treatment_catalog" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "roles" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "permissions" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "system_settings" ADD FOREIGN KEY ("organization_id") REFERENCES "organizations" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "system_settings" ADD FOREIGN KEY ("updated_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "treatment_cost_entries" ADD FOREIGN KEY ("actual_treatment_item_id") REFERENCES "actual_treatment_items" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "treatment_cost_entries" ADD FOREIGN KEY ("visit_id") REFERENCES "clinical_visits" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "treatment_cost_entries" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "treatment_cost_entries" ADD FOREIGN KEY ("reporting_period_id") REFERENCES "financial_reporting_periods" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "treatment_plans" ADD FOREIGN KEY ("visit_id") REFERENCES "clinical_visits" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "treatment_qualification_requirements" ADD FOREIGN KEY ("treatment_id") REFERENCES "treatment_catalog" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "treatment_qualification_requirements" ADD FOREIGN KEY ("qualification_type_id") REFERENCES "qualification_types" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "user_role_assignments" ADD FOREIGN KEY ("user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "user_role_assignments" ADD FOREIGN KEY ("role_id") REFERENCES "roles" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "user_role_assignments" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "user_role_assignments" ADD FOREIGN KEY ("granted_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "visit_allergy_acknowledgements" ADD FOREIGN KEY ("visit_id") REFERENCES "clinical_visits" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "visit_allergy_acknowledgements" ADD FOREIGN KEY ("allergy_id") REFERENCES "patient_allergies" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "visit_allergy_acknowledgements" ADD FOREIGN KEY ("acknowledged_by_user_id") REFERENCES "app_users" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "waitlist_entries" ADD FOREIGN KEY ("patient_id") REFERENCES "patients" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "waitlist_entries" ADD FOREIGN KEY ("treatment_id") REFERENCES "treatment_catalog" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "waitlist_entries" ADD FOREIGN KEY ("preferred_clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE "waitlist_offers" ADD FOREIGN KEY ("waitlist_entry_id") REFERENCES "waitlist_entries" ("id") ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE "waitlist_offers" ADD FOREIGN KEY ("released_appointment_id") REFERENCES "appointments" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "waitlist_offers" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "waitlist_offers" ADD FOREIGN KEY ("dentist_id") REFERENCES "dentists" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE "waitlist_offers" ADD FOREIGN KEY ("chair_id") REFERENCES "clinic_chairs" ("id") ON UPDATE NO ACTION ON DELETE RESTRICT;
