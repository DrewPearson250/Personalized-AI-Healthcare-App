-- CareBridge NB database schema (PostgreSQL)
-- Every row carries source_url and last_verified so each fact can be traced.
-- Load order: python scripts/load.py (hospitals first: hospital_payers/prices reference it).
-- Eligibility rules live in config/eligibility_rules.yaml (code, not a table).

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

    -- location (Census-geocoded street address; ZIP centroid fallback)
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
    pediatric_source_url   TEXT,                      -- page the pediatric columns came from

    source_url             TEXT NOT NULL,
    last_verified          DATE NOT NULL
);

CREATE INDEX IF NOT EXISTS hospitals_emergency_idx ON hospitals (has_emergency);

-- ---------------------------------------------------------------------------
-- clinics: HRSA health center sites + SAMHSA treatment facilities + hand-built
-- free / student-run clinics. Built by scripts/clean_clinics.py
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clinics (
    clinic_id                 TEXT PRIMARY KEY,        -- hrsa-<BPHC no.> / samhsa-<hash> / manual-<slug>
    source                    TEXT NOT NULL CHECK (source IN ('hrsa', 'samhsa', 'manual')),
    name                      TEXT NOT NULL,
    organization              TEXT,
    clinic_type               TEXT NOT NULL,           -- fqhc, fqhc_look_alike, mental_health, substance_use,
                                                       -- behavioral_health, opioid_treatment, free_clinic, hospital_clinic
    address                   TEXT,                    -- NULL for a few SAMHSA rows with no street listed
    city                      TEXT NOT NULL,
    state                     CHAR(2) NOT NULL,
    zip                       CHAR(5) NOT NULL,
    county                    TEXT NOT NULL,
    phone                     TEXT,
    website                   TEXT,
    lat                       NUMERIC(9,6),
    lng                       NUMERIC(9,6),
    miles_to_nb               NUMERIC(5,1),
    location_type             TEXT,                    -- permanent / mobile
    setting                   TEXT,
    hours_per_week            NUMERIC(5,1),
    care_types                TEXT[],                  -- primary_care, mental_health, substance_use, detox, ...
    service_settings          TEXT[],                  -- Outpatient, Intensive outpatient treatment, ...
    accepts_medicaid          BOOLEAN,
    accepts_medicare          BOOLEAN,
    accepts_private_insurance BOOLEAN,
    accepts_self_pay          BOOLEAN,
    sliding_fee               BOOLEAN,
    free_care                 BOOLEAN,                 -- free / government-funded care or payment assistance
    languages                 TEXT[],                  -- besides English
    serves_children           BOOLEAN,
    serves_adults             BOOLEAN,
    emergency_mh              BOOLEAN,                 -- psychiatric emergency / crisis services
    has_dental                BOOLEAN,                 -- hand-filled
    walk_in                   BOOLEAN,                 -- hand-filled
    notes                     TEXT,
    source_url                TEXT NOT NULL,
    last_verified             DATE NOT NULL
);
CREATE INDEX IF NOT EXISTS clinics_type_idx ON clinics (clinic_type);

-- ---------------------------------------------------------------------------
-- providers: NPPES dentists, pediatrics, OB-GYN; one row per NPI x practice
-- location in scope. Built by scripts/clean_providers.py
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS providers (
    provider_id            TEXT PRIMARY KEY,           -- <npi>-<location_seq>
    npi                    CHAR(10) NOT NULL,
    name                   TEXT NOT NULL,
    credential             TEXT,
    provider_kind          TEXT NOT NULL CHECK (provider_kind IN ('individual', 'organization')),
    sex                    CHAR(1),
    specialty              TEXT NOT NULL CHECK (specialty IN ('dentist', 'pediatrics', 'obgyn')),
    taxonomy               TEXT NOT NULL,
    taxonomy_code          TEXT,
    general_care           BOOLEAN NOT NULL,           -- general practice vs subspecialist
    other_specialties      TEXT[],
    address                TEXT NOT NULL,
    city                   TEXT NOT NULL,
    state                  CHAR(2) NOT NULL,
    zip                    CHAR(5) NOT NULL,
    county                 TEXT NOT NULL,
    phone                  TEXT,
    lat                    NUMERIC(9,6) NOT NULL,
    lng                    NUMERIC(9,6) NOT NULL,
    geo_precision          TEXT CHECK (geo_precision IN ('address', 'zip')),
    miles_to_nb            NUMERIC(5,1),
    is_primary_location    BOOLEAN,
    telehealth             BOOLEAN,                    -- from CMS Doctors & Clinicians; NULL = unknown
    accepts_medicaid       BOOLEAN,                    -- hand-filled
    sliding_fee            BOOLEAN,                    -- hand-filled
    accepting_new_patients BOOLEAN,                    -- hand-filled
    languages              TEXT[],
    nppes_last_updated     DATE,
    source_url             TEXT NOT NULL,
    last_verified          DATE NOT NULL
);
CREATE INDEX IF NOT EXISTS providers_specialty_idx ON providers (specialty, general_care);
CREATE INDEX IF NOT EXISTS providers_npi_idx ON providers (npi);

-- ---------------------------------------------------------------------------
-- insurers_local: DOBI Q2 2026 enrollment, Middlesex column. scripts/clean_plans.py
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS insurers_local (
    insurer_id             TEXT PRIMARY KEY,           -- NAIC code
    insurer_name           TEXT NOT NULL,              -- legal entity as DOBI lists it
    naic                   TEXT NOT NULL,
    brand                  TEXT NOT NULL,              -- Horizon, UnitedHealthcare, Aetna, ...
    marketplace_issuer_id  TEXT,                       -- joins plans.issuer_id
    total_enrollment       INTEGER NOT NULL,
    commercial_enrollment  INTEGER NOT NULL,
    commercial_network     INTEGER NOT NULL,
    commercial_non_network INTEGER NOT NULL,
    medicaid_enrollment    INTEGER NOT NULL,
    is_medicaid_plan       BOOLEAN NOT NULL,           -- an NJ FamilyCare plan in Middlesex
    share_of_county_pct    NUMERIC(4,1),
    rank                   SMALLINT,
    brand_rank             SMALLINT,
    quarter                TEXT NOT NULL,
    source_url             TEXT NOT NULL,
    last_verified          DATE NOT NULL
);

-- ---------------------------------------------------------------------------
-- plans / plan_rates / plan_benefits: CMS SBE QHP PUF, NJ 2026, plans sold in
-- Middlesex. scripts/clean_plans.py
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plans (
    plan_id                 TEXT PRIMARY KEY,          -- variant, e.g. 17970NJ0010003-04
    standard_component_id   TEXT NOT NULL,             -- joins plan_rates
    issuer_id               TEXT NOT NULL,
    issuer_name             TEXT,
    plan_name               TEXT NOT NULL,
    variant_name            TEXT,
    dental_only             BOOLEAN NOT NULL,
    plan_type               TEXT,                      -- EPO, PPO, HMO
    metal_level             TEXT NOT NULL,
    csr_variant             TEXT NOT NULL CHECK (csr_variant IN ('standard', 'csr_73', 'csr_87', 'csr_94')),
    actuarial_value_pct     NUMERIC(5,2),
    deductible_individual   NUMERIC(10,2),
    deductible_family       NUMERIC(10,2),
    coinsurance_pct         NUMERIC(5,2),
    moop_individual         NUMERIC(10,2),
    moop_family             NUMERIC(10,2),
    hsa_eligible            BOOLEAN,
    referral_required       BOOLEAN,
    out_of_network_coverage BOOLEAN,
    child_only_offering     TEXT,
    cost_having_baby        NUMERIC(10,2),             -- SBC coverage example totals
    cost_diabetes           NUMERIC(10,2),
    cost_simple_fracture    NUMERIC(10,2),
    plan_year               SMALLINT NOT NULL,
    enroll_url              TEXT,
    source_url              TEXT NOT NULL,
    last_verified           DATE NOT NULL
);
CREATE INDEX IF NOT EXISTS plans_component_idx ON plans (standard_component_id);

CREATE TABLE IF NOT EXISTS plan_rates (
    rate_id               TEXT PRIMARY KEY,            -- <component>-<rating_area>-<age>
    standard_component_id TEXT NOT NULL,
    issuer_id             TEXT NOT NULL,
    rating_area           SMALLINT NOT NULL,
    age                   SMALLINT NOT NULL,           -- 0 = ages 0-14, 64 = 64 and over
    age_label             TEXT NOT NULL,
    monthly_premium       NUMERIC(10,2),               -- full price before subsidy; NULL = not sold at that age
    tobacco_premium       NUMERIC(10,2),
    rate_effective        DATE,
    rate_expiration       DATE,
    source_url            TEXT NOT NULL,
    last_verified         DATE NOT NULL
);
CREATE INDEX IF NOT EXISTS plan_rates_lookup_idx ON plan_rates (standard_component_id, rating_area, age);

CREATE TABLE IF NOT EXISTS plan_benefits (
    benefit_id            TEXT PRIMARY KEY,            -- <plan_id>|<benefit_name>
    plan_id               TEXT NOT NULL REFERENCES plans (plan_id),
    benefit_name          TEXT NOT NULL,
    is_covered            BOOLEAN,
    is_ehb                BOOLEAN,
    quantity_limit        BOOLEAN,
    limit_quantity        NUMERIC,
    limit_unit            TEXT,
    exclusions            TEXT,
    explanation           TEXT,
    subject_to_deductible BOOLEAN,
    source_url            TEXT NOT NULL,
    last_verified         DATE NOT NULL
);

-- ---------------------------------------------------------------------------
-- hospital_payers / hospital_prices: hospital price transparency files,
-- prefiltered. scripts/clean_price_transparency.py
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hospital_payers (
    payer_id          TEXT PRIMARY KEY,                -- <facility_id>|<payer>|<plan>
    facility_id       TEXT NOT NULL REFERENCES hospitals (facility_id),
    payer_name        TEXT NOT NULL,
    plan_name         TEXT,
    brand             TEXT,                            -- normalized insurer brand
    product           TEXT,                            -- commercial / medicaid / medicare / medicare_medicaid (keyword guess)
    charge_rows       INTEGER,
    file_last_updated DATE,
    source_url        TEXT NOT NULL,
    last_verified     DATE NOT NULL
);
CREATE INDEX IF NOT EXISTS hospital_payers_brand_idx ON hospital_payers (brand, product);

CREATE TABLE IF NOT EXISTS hospital_prices (
    price_id              TEXT PRIMARY KEY,
    facility_id           TEXT NOT NULL REFERENCES hospitals (facility_id),
    code                  TEXT NOT NULL,               -- CPT / HCPCS
    service               TEXT NOT NULL,               -- plain-language label
    service_group         TEXT NOT NULL,               -- emergency, office, maternity, imaging, lab, other
    description_raw       TEXT,
    setting               TEXT,                        -- inpatient / outpatient / both
    billing_class         TEXT,                        -- facility / professional
    modifiers             TEXT,
    gross_charge          NUMERIC(12,2),
    discounted_cash       NUMERIC(12,2),               -- self-pay price
    min_negotiated        NUMERIC(12,2),
    max_negotiated        NUMERIC(12,2),
    payer_name            TEXT,                        -- NULL = row without a payer (cash/gross only)
    plan_name             TEXT,
    brand                 TEXT,
    negotiated_dollar     NUMERIC(12,2),
    negotiated_percentage NUMERIC(8,4),
    methodology           TEXT,
    file_last_updated     DATE,
    source_url            TEXT NOT NULL,
    last_verified         DATE NOT NULL
);
CREATE INDEX IF NOT EXISTS hospital_prices_code_idx ON hospital_prices (code, facility_id);

-- ---------------------------------------------------------------------------
-- services: hand-built non-medical help (food, housing, benefits, legal, ...).
-- The service matcher embeds embed_text. scripts/clean_services.py
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS services (
    service_id        TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    organization      TEXT,
    category          TEXT NOT NULL CHECK (category IN ('food', 'housing', 'transportation',
                          'prescriptions', 'benefits', 'legal', 'domestic_violence', 'immigrant',
                          'utilities', 'mental_health', 'other')),
    description       TEXT NOT NULL,
    eligibility       TEXT,
    address           TEXT,
    city              TEXT,
    zip               CHAR(5),
    phone             TEXT,
    hours             TEXT,
    languages         TEXT[],
    cost              TEXT,
    documents_needed  TEXT,
    nearest_bus_stop  TEXT,
    lat               NUMERIC(9,6),
    lng               NUMERIC(9,6),
    miles_to_nb       NUMERIC(5,1),
    scope             TEXT NOT NULL CHECK (scope IN ('local', 'statewide')),
    embed_text        TEXT NOT NULL,                   -- what the service matcher embeds
    -- embedding      vector(384),                     -- add with pgvector when the matcher is built
    verified          BOOLEAN NOT NULL DEFAULT FALSE,  -- a person checked it against source_url
    notes             TEXT,
    source_url        TEXT NOT NULL,
    source_date       DATE,                            -- date of the source document, if older
    last_verified     DATE NOT NULL
);
CREATE INDEX IF NOT EXISTS services_category_idx ON services (category);
