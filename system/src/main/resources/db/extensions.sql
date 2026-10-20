CREATE TABLE treatment_item_consents (
 id TEXT PRIMARY KEY, requested_treatment_item_id TEXT NOT NULL REFERENCES requested_treatment_items(id),
 decision TEXT NOT NULL CHECK(decision IN ('ACCEPTED','DECLINED','DEFERRED')), policy_version TEXT NOT NULL,
 evidence TEXT NOT NULL, witnessed_by_user_id TEXT NOT NULL REFERENCES app_users(id), captured_at TEXT NOT NULL
);
CREATE INDEX idx_item_consent_item ON treatment_item_consents(requested_treatment_item_id,captured_at);
CREATE TABLE dentist_expense_allocations (
 id TEXT PRIMARY KEY, expense_id TEXT NOT NULL REFERENCES operating_expenses(id),
 dentist_id TEXT NOT NULL REFERENCES dentists(id), amount_fen BIGINT NOT NULL CHECK(amount_fen>0),
 basis TEXT NOT NULL, approved_by_user_id TEXT NOT NULL REFERENCES app_users(id), created_at TEXT NOT NULL,
 UNIQUE(expense_id,dentist_id)
);
CREATE TABLE patient_history_versions (
 id TEXT PRIMARY KEY, patient_id TEXT NOT NULL REFERENCES patients(id), version_number BIGINT NOT NULL,
 history_text TEXT NOT NULL, history_status TEXT NOT NULL CHECK(history_status IN ('UNKNOWN','DECLARED_NONE','DECLARED')),
 author_user_id TEXT NOT NULL REFERENCES app_users(id), reason TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(patient_id,version_number)
);
CREATE TABLE request_receipts (
 id TEXT PRIMARY KEY, actor_user_id TEXT NOT NULL REFERENCES app_users(id), operation TEXT NOT NULL,
 request_hash TEXT NOT NULL, response_json TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(actor_user_id,operation,id)
);
CREATE TABLE IF NOT EXISTS clinical_note_signatures (
 id TEXT PRIMARY KEY, note_version_id TEXT NOT NULL UNIQUE REFERENCES clinical_note_versions(id),
 dentist_id TEXT NOT NULL REFERENCES dentists(id), signer_user_id TEXT NOT NULL REFERENCES app_users(id),
 content_checksum TEXT NOT NULL, signed_at TEXT NOT NULL
);
