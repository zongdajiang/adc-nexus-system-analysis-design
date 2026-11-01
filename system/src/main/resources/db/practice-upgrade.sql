CREATE TABLE IF NOT EXISTS patient_followups (
  id TEXT PRIMARY KEY,
  patient_id TEXT NOT NULL REFERENCES patients(id),
  clinic_id TEXT NOT NULL REFERENCES clinics(id),
  source_visit_id TEXT NOT NULL REFERENCES clinical_visits(id),
  dentist_id TEXT NOT NULL REFERENCES dentists(id),
  due_on TEXT NOT NULL,
  reason TEXT NOT NULL,
  priority TEXT NOT NULL DEFAULT 'ROUTINE',
  contact_allowed INTEGER NOT NULL DEFAULT 0,
  next_contact_on TEXT,
  status TEXT NOT NULL DEFAULT 'PENDING',
  appointment_id TEXT REFERENCES appointments(id),
  revision INTEGER NOT NULL DEFAULT 1,
  created_by_user_id TEXT NOT NULL REFERENCES app_users(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_followups_clinic_due ON patient_followups(clinic_id,status,due_on);
CREATE INDEX IF NOT EXISTS idx_followups_patient ON patient_followups(patient_id,created_at);
CREATE TABLE IF NOT EXISTS followup_contact_events (
  id TEXT PRIMARY KEY,
  followup_id TEXT NOT NULL REFERENCES patient_followups(id),
  actor_user_id TEXT NOT NULL REFERENCES app_users(id),
  event_type TEXT NOT NULL,
  channel TEXT NOT NULL,
  outcome TEXT NOT NULL,
  note TEXT NOT NULL,
  appointment_id TEXT REFERENCES appointments(id),
  next_contact_on TEXT,
  occurred_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_followup_events ON followup_contact_events(followup_id,occurred_at);
