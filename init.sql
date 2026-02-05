CREATE TABLE "roles" (
  "role_id" integer PRIMARY KEY,
  "role_name" varchar
);

CREATE TABLE "users" (
  "user_id" integer PRIMARY KEY,
  "username" varchar,
  "password" varchar,
  "full_name" varchar,
  "email" varchar,
  "role_id" integer
);

CREATE TABLE "units" (
  "unit_id" integer PRIMARY KEY,
  "unit_name" varchar
);

CREATE TABLE "ricegrain" (
  "rice_grain_id" integer PRIMARY KEY,
  "image_path" varchar,
  "belly_white_level" integer,
  "belly_white_ratio" float
);

CREATE TABLE "classified" (
  "classified_id" integer PRIMARY KEY,
  "unit_id" integer,
  "level0" integer,
  "level1" integer,
  "level2" integer,
  "level3" integer,
  "level4" integer,
  "level5" integer,
  "total" integer,
  "date_time" timestamp
);

CREATE TABLE "inspection" (
  "inspection_id" integer PRIMARY KEY,
  "classified_id" integer,
  "date_time" timestamp
);

CREATE TABLE "inspection_detail" (
  "inspection_id" integer,
  "rice_grain_id" integer,
  PRIMARY KEY ("inspection_id", "rice_grain_id")
);

COMMENT ON COLUMN "users"."password" IS 'hashed password';

ALTER TABLE "users" ADD CONSTRAINT "user_role" FOREIGN KEY ("role_id") REFERENCES "roles" ("role_id");

ALTER TABLE "classified" ADD CONSTRAINT "classified_unit" FOREIGN KEY ("unit_id") REFERENCES "units" ("unit_id");

ALTER TABLE "inspection" ADD CONSTRAINT "inspection_classified" FOREIGN KEY ("classified_id") REFERENCES "classified" ("classified_id");

ALTER TABLE "inspection_detail" ADD CONSTRAINT "inspectiondetail_inspection" FOREIGN KEY ("inspection_id") REFERENCES "inspection" ("inspection_id");

ALTER TABLE "inspection_detail" ADD CONSTRAINT "inspectiondetail_ricegrain" FOREIGN KEY ("rice_grain_id") REFERENCES "ricegrain" ("rice_grain_id");
