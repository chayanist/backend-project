DROP SCHEMA IF EXISTS api CASCADE;
CREATE SCHEMA api;

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
-- 1 inspection : 1 classified
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
-- many ricegrain : 1 inspection
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
-- ROLES
-- ======================
CREATE TABLE api.roles (
    role_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_name VARCHAR
);

-- ======================
-- USERS
-- ======================
CREATE TABLE api.users (
    user_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR,
    password VARCHAR,
    full_name VARCHAR,
    email VARCHAR,
    role_id INTEGER REFERENCES api.roles(role_id),
    status BOOLEAN,
    create_date TIMESTAMP
);
-- ======================
-- PERMISSIONS
-- ======================
GRANT USAGE ON SCHEMA api TO api_user;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA api TO api_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA api TO api_user;


INSERT INTO api.roles (role_name)
VALUES 
('admin'),
('user')