-- =========================
-- 1. CREATE SCHEMA
-- =========================
CREATE SCHEMA IF NOT EXISTS api;

-- =========================
-- 2. TABLES
-- =========================

CREATE TABLE api.roles (
  role_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  role_name VARCHAR
);

CREATE TABLE api.users (
  user_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  username VARCHAR,
  password VARCHAR,
  full_name VARCHAR,
  email VARCHAR,
  role_id INTEGER
);

CREATE TABLE api.units (
  unit_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  unit_name VARCHAR
);

CREATE TABLE api.ricegrain (
  rice_grain_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  image_path VARCHAR,
  belly_white_level INTEGER,
  belly_white_ratio FLOAT
);

CREATE TABLE api.classified (
  classified_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  unit_id INTEGER,
  level0 INTEGER,
  level1 INTEGER,
  level2 INTEGER,
  level3 INTEGER,
  level4 INTEGER,
  level5 INTEGER,
  total INTEGER,
  date_time TIMESTAMP
);

CREATE TABLE api.inspection (
  inspection_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  classified_id INTEGER,
  date_time TIMESTAMP
);

CREATE TABLE api.inspection_detail (
  inspection_id INTEGER,
  rice_grain_id INTEGER,
  PRIMARY KEY (inspection_id, rice_grain_id)
);

-- =========================
-- 3. CONSTRAINTS
-- =========================

ALTER TABLE api.users
ADD CONSTRAINT user_role
FOREIGN KEY (role_id) REFERENCES api.roles (role_id);

ALTER TABLE api.classified
ADD CONSTRAINT classified_unit
FOREIGN KEY (unit_id) REFERENCES api.units (unit_id);

ALTER TABLE api.inspection
ADD CONSTRAINT inspection_classified
FOREIGN KEY (classified_id) REFERENCES api.classified (classified_id);

ALTER TABLE api.inspection_detail
ADD CONSTRAINT inspectiondetail_inspection
FOREIGN KEY (inspection_id) REFERENCES api.inspection (inspection_id);

ALTER TABLE api.inspection_detail
ADD CONSTRAINT inspectiondetail_ricegrain
FOREIGN KEY (rice_grain_id) REFERENCES api.ricegrain (rice_grain_id);

COMMENT ON COLUMN api.users.password IS 'hashed password';

-- =========================
-- 4. CREATE API USER
-- =========================
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'api_user') THEN
    CREATE ROLE api_user WITH LOGIN PASSWORD 'password';
  END IF;
END $$;

-- =========================
-- 5. PERMISSIONS
-- =========================
GRANT CONNECT ON DATABASE postgres TO api_user;
GRANT USAGE ON SCHEMA api TO api_user;

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA api
TO api_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA api
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO api_user;
