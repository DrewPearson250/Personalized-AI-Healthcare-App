-- CareBridge NB database schema (PostgreSQL)
-- Every row carries source_url and last_verified so each fact can be traced.
-- Tables are added batch by batch; see dataset_catalog.pdf for the full plan.

-- ---------------------------------------------------------------------------
-- hospitals: CMS General Info + HCAHPS (pivoted) + Timely & Effective Care (ER)
-- Scope: Middlesex County, within 15 miles of New Brunswick.
-- Built by scripts/clean_hospitals.py -> data/clean/hospitals.csv
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hospitals (
    facility_id            TEXT PRIMARY KEY,          -- CMS certification number
    name                   TEXT NOT NULL,
    address                TEXT NOT NULL,
    city                   TEXT NOT NULL,
    state                  CHAR(2) NOT NULL,
    zip                    CHAR(5) NOT NULL,
    county                 TEXT NOT NULL,
    phone                  TEXT,
    hospital_type          TEXT NOT NULL,             -- e.g. Acute Care Hospitals, Childrens, Psychiatric
    ownership              TEXT,
    has_emergency          BOOLEAN NOT NULL,          -- first filter for urgent needs
    birthing_friendly      BOOLEAN NOT NULL,
    overall_rating         SMALLINT CHECK (overall_rating BETWEEN 1 AND 5),  -- NULL = not rated

    -- location (ZIP centroid, approximate; NULL when the ZIP has no Census centroid)
    lat                    NUMERIC(9,6),
    lng                    NUMERIC(9,6),
    miles_to_nb            NUMERIC(5,1),

    -- patient survey (HCAHPS); NULL = not reported
    survey_star            SMALLINT CHECK (survey_star BETWEEN 1 AND 5),
    nurse_comm_star        SMALLINT CHECK (nurse_comm_star BETWEEN 1 AND 5),
    doctor_comm_star       SMALLINT CHECK (doctor_comm_star BETWEEN 1 AND 5),
    recommend_pct          SMALLINT CHECK (recommend_pct BETWEEN 0 AND 100),   -- "definitely recommend"
    rating_9_10_pct        SMALLINT CHECK (rating_9_10_pct BETWEEN 0 AND 100),
    survey_count           INTEGER,
    survey_period_end      DATE,

    -- emergency department (Timely & Effective Care); NULL = not reported
    er_median_minutes      INTEGER,                   -- OP_18b
    er_left_unseen_pct     SMALLINT,                  -- OP_22
    er_volume              TEXT,                      -- EDV: low / medium / high / very high
    er_period_end          DATE,

    -- added by hand from hospital websites (no dataset has these)
    has_pediatric_er       BOOLEAN,
    has_childrens_hospital BOOLEAN,
    pediatric_specialties  TEXT[],

    source_url             TEXT NOT NULL,
    last_verified          DATE NOT NULL
);

CREATE INDEX IF NOT EXISTS hospitals_emergency_idx ON hospitals (has_emergency);
