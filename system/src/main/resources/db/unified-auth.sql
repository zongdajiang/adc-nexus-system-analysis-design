-- Additive migration 005. The approved 61-table baseline remains unchanged.
CREATE TABLE staff_directory (
  id TEXT PRIMARY KEY NOT NULL,
  employee_code TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  role_id TEXT NOT NULL REFERENCES roles(id),
  clinic_id TEXT REFERENCES clinics(id),
  dentist_id TEXT REFERENCES dentists(id),
  phone_e164 TEXT NOT NULL,
  email TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','INACTIVE')),
  claimed_user_id TEXT UNIQUE REFERENCES app_users(id),
  created_by_user_id TEXT NOT NULL REFERENCES app_users(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
ALTER TABLE account_invitations ADD COLUMN staff_directory_id TEXT REFERENCES staff_directory(id);
ALTER TABLE account_invitations ADD COLUMN token_hash TEXT;
CREATE UNIQUE INDEX uq_invitation_token_hash ON account_invitations(token_hash);
CREATE INDEX idx_staff_directory_role ON staff_directory(role_id,clinic_id);
CREATE TABLE verification_challenges (
  id TEXT PRIMARY KEY NOT NULL,
  channel TEXT NOT NULL CHECK(channel IN ('EMAIL','PHONE')),
  destination TEXT NOT NULL,
  purpose TEXT NOT NULL CHECK(purpose IN ('REGISTER','LOGIN','RECOVER')),
  user_id TEXT REFERENCES app_users(id),
  code_hash TEXT NOT NULL,
  code_salt TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('PENDING','SENT','FAILED')),
  request_ip_hash TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  consumed_at TEXT,
  attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count>=0),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_verification_destination ON verification_challenges(channel,destination,created_at);
CREATE INDEX idx_verification_ip ON verification_challenges(request_ip_hash,created_at);
CREATE INDEX idx_verification_expiry ON verification_challenges(expires_at);
