DROP SCHEMA IF EXISTS api CASCADE;
CREATE SCHEMA api;

-- ======================
-- CREATE ROLE FOR API
-- ======================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_roles WHERE rolname = 'api_user'
    ) THEN
        CREATE ROLE api_user LOGIN PASSWORD 'api_password';
    END IF;
END$$;

-- ======================
-- UNIT (เปลี่ยนชื่อกลับเป็น units ตามของเก่า)
-- ======================
CREATE TABLE api.units (
    unit_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    unit_name VARCHAR NOT NULL
    create_date TIMESTAMP DEFAULT now(),
);

-- ======================
-- INSPECTION
-- ======================
CREATE TABLE api.inspection (
    inspection_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    unit_id INTEGER REFERENCES api.units(unit_id) ON DELETE CASCADE,
    date_time TIMESTAMP DEFAULT now()
);

-- ======================
-- CLASSIFIED
-- ======================
CREATE TABLE api.classified (
    classified_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    inspection_id INTEGER REFERENCES api.inspection(inspection_id) ON DELETE CASCADE,
    level0 INTEGER DEFAULT 0,
    level1 INTEGER DEFAULT 0,
    level2 INTEGER DEFAULT 0,
    level3 INTEGER DEFAULT 0,
    level4 INTEGER DEFAULT 0,
    level5 INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    round_number INTEGER,
    date_time TIMESTAMP DEFAULT now()
);

-- ======================
-- RICEGRAIN
-- ======================
CREATE TABLE api.ricegrain (
    rice_grain_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    classified_id INTEGER REFERENCES api.classified(classified_id) ON DELETE CASCADE,
    image VARCHAR,
    belly_white_level INTEGER,
    belly_white_ratio DOUBLE PRECISION
);

-- ======================
-- ACCURACY (ตารางเก็บความแม่นยำ)
-- ======================
CREATE TABLE api.accuracy (
    accuracy_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    classified_id INTEGER REFERENCES api.classified(classified_id) ON DELETE CASCADE,
    level0 DECIMAL(5,2) DEFAULT 0.00,
    level1 DECIMAL(5,2) DEFAULT 0.00,
    level2 DECIMAL(5,2) DEFAULT 0.00,
    level3 DECIMAL(5,2) DEFAULT 0.00,
    level4 DECIMAL(5,2) DEFAULT 0.00,
    level5 DECIMAL(5,2) DEFAULT 0.00,
    overall DECIMAL(5,2) DEFAULT 0.00
);

-- ======================
-- ROLES TABLE
-- ======================
CREATE TABLE api.roles (
    role_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_name VARCHAR NOT NULL
);

-- ======================
-- USERS TABLE
-- ======================
CREATE TABLE api.users (
    user_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL,
    full_name VARCHAR,
    email VARCHAR,
    role_id INTEGER REFERENCES api.roles(role_id),
    status BOOLEAN DEFAULT true,
    create_date TIMESTAMP DEFAULT now()
);

-- ======================
-- MODEL STATUS
-- ======================
CREATE TABLE api.modelstatus (
    id INTEGER PRIMARY KEY,
    status BOOLEAN NOT NULL,
    unit_id INTEGER
);

INSERT INTO api.modelstatus (id, status)
VALUES (1, false)
ON CONFLICT (id) DO NOTHING;

-- ======================
-- PERMISSIONS 
-- ======================
GRANT USAGE ON SCHEMA api TO api_user;

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA api
TO api_user;

GRANT USAGE, SELECT
ON ALL SEQUENCES IN SCHEMA api
TO api_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA api
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO api_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA api
GRANT USAGE, SELECT ON SEQUENCES TO api_user;

-- ======================
-- INSERT DATA (ข้อมูลเริ่มต้น)
-- ======================
-- 1. ข้อมูล Roles
INSERT INTO api.roles (role_name) 
VALUES ('admin'), ('user');

-- 2. ข้อมูล Users
INSERT INTO api.users (username, password, full_name, email, role_id)
VALUES ('admin', '1234', 'System Administrator', 'admin@example.com', 1);

-- 3. ข้อมูล Model Status
INSERT INTO api.modelstatus (id, status)
VALUES (1, false)
ON CONFLICT (id) DO NOTHING;

-- 4. ข้อมูล Unit
INSERT INTO api.units (unit_name) 
VALUES ('Default Machine');