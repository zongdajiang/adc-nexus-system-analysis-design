-- SQLite 3.53+ can enforce these constraints without replacing the tables.
ALTER TABLE schema_migrations ALTER COLUMN version SET NOT NULL;
ALTER TABLE treatment_item_consents ALTER COLUMN id SET NOT NULL;
ALTER TABLE dentist_expense_allocations ALTER COLUMN id SET NOT NULL;
ALTER TABLE patient_history_versions ALTER COLUMN id SET NOT NULL;
ALTER TABLE request_receipts ALTER COLUMN id SET NOT NULL;
ALTER TABLE clinical_note_signatures ALTER COLUMN id SET NOT NULL;
ALTER TABLE patient_followups ALTER COLUMN id SET NOT NULL;
ALTER TABLE followup_contact_events ALTER COLUMN id SET NOT NULL;
