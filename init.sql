DROP SCHEMA IF EXISTS api CASCADE;
CREATE SCHEMA api;

-- ======================
-- CREATE ROLE FOR API (ต้องมาก่อน GRANT)
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
-- UNIT
-- ======================
CREATE TABLE api.units (
    unit_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    unit_name VARCHAR NOT NULL
);

-- ======================
-- INSPECTION
-- ======================
CREATE TABLE api.inspection (
    inspection_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    unit_id INTEGER NOT NULL
        REFERENCES api.units(unit_id) ON DELETE CASCADE,
    date_time TIMESTAMP DEFAULT now()
);

-- ======================
-- CLASSIFIED
-- ======================
CREATE TABLE api.classified (
    classified_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    inspection_id INTEGER UNIQUE NOT NULL
        REFERENCES api.inspection(inspection_id) ON DELETE CASCADE,

    level0 INTEGER DEFAULT 0,
    level1 INTEGER DEFAULT 0,
    level2 INTEGER DEFAULT 0,
    level3 INTEGER DEFAULT 0,
    level4 INTEGER DEFAULT 0,
    level5 INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0
);

-- ======================
-- RICEGRAIN
-- ======================
CREATE TABLE api.ricegrain (
    rice_grain_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    inspection_id INTEGER NOT NULL
        REFERENCES api.inspection(inspection_id) ON DELETE CASCADE,

    image VARCHAR,
    belly_white_level INTEGER,
    belly_white_ratio DOUBLE PRECISION
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
    status BOOLEAN NOT NULL
);

INSERT INTO api.modelstatus (id, status)
VALUES (1, false)
ON CONFLICT (id) DO NOTHING;

-- ======================
-- PERMISSIONS (หลัง CREATE ROLE)
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
-- SEED ROLES
-- ======================
INSERT INTO api.roles (role_name)
VALUES ('admin'), ('user');
