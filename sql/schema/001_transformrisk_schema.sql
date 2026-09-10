-- ============================================================
-- TransformRisk
-- PostgreSQL Raw Data Schema
-- ============================================================

-- ============================================================
-- 1. Schemas
-- ============================================================

CREATE SCHEMA IF NOT EXISTS raw;

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE SCHEMA IF NOT EXISTS reporting;


-- ============================================================
-- 2. Transformation Initiatives
-- ============================================================

CREATE TABLE IF NOT EXISTS raw.transformation_initiatives (
    initiative_id VARCHAR(30) PRIMARY KEY,

    initiative_name VARCHAR(250) NOT NULL,

    transformation_type VARCHAR(100) NOT NULL,

    business_unit VARCHAR(100) NOT NULL,

    owner VARCHAR(100) NOT NULL,

    current_state TEXT,

    target_state TEXT,

    strategic_priority VARCHAR(30),

    criticality VARCHAR(30),

    budget NUMERIC(18,2),

    target_completion_date DATE,

    status VARCHAR(30)
);


-- ============================================================
-- 3. Transformation Risks
-- ============================================================

CREATE TABLE IF NOT EXISTS raw.transformation_risks (
    risk_id VARCHAR(30) PRIMARY KEY,

    initiative_id VARCHAR(30) NOT NULL,

    risk_name VARCHAR(250) NOT NULL,

    risk_domain VARCHAR(100) NOT NULL,

    description TEXT,

    likelihood INTEGER NOT NULL
        CHECK (likelihood BETWEEN 1 AND 5),

    impact INTEGER NOT NULL
        CHECK (impact BETWEEN 1 AND 5),

    control_effectiveness NUMERIC(5,2)
        CHECK (
            control_effectiveness BETWEEN 0 AND 100
        ),

    status VARCHAR(30),

    CONSTRAINT fk_risk_initiative
        FOREIGN KEY (initiative_id)
        REFERENCES raw.transformation_initiatives(
            initiative_id
        )
        ON DELETE CASCADE
);


-- ============================================================
-- 4. Risk Controls
-- ============================================================

CREATE TABLE IF NOT EXISTS raw.risk_controls (
    control_id VARCHAR(30) PRIMARY KEY,

    risk_id VARCHAR(30) NOT NULL,

    control_name VARCHAR(250) NOT NULL,

    control_type VARCHAR(50),

    control_owner VARCHAR(100),

    control_frequency VARCHAR(50),

    effectiveness_score NUMERIC(5,2)
        CHECK (
            effectiveness_score BETWEEN 0 AND 100
        ),

    control_status VARCHAR(50),

    description TEXT,

    CONSTRAINT fk_control_risk
        FOREIGN KEY (risk_id)
        REFERENCES raw.transformation_risks(
            risk_id
        )
        ON DELETE CASCADE
);


-- ============================================================
-- 5. Mitigation Actions
-- ============================================================

CREATE TABLE IF NOT EXISTS raw.mitigation_actions (
    action_id VARCHAR(30) PRIMARY KEY,

    risk_id VARCHAR(30) NOT NULL,

    action_name VARCHAR(250) NOT NULL,

    action_owner VARCHAR(100) NOT NULL,

    priority VARCHAR(30),

    status VARCHAR(30),

    due_date DATE,

    completion_percentage INTEGER
        CHECK (
            completion_percentage BETWEEN 0 AND 100
        ),

    expected_risk_reduction NUMERIC(6,2),

    CONSTRAINT fk_action_risk
        FOREIGN KEY (risk_id)
        REFERENCES raw.transformation_risks(
            risk_id
        )
        ON DELETE CASCADE
);


-- ============================================================
-- 6. Readiness Assessments
-- ============================================================

CREATE TABLE IF NOT EXISTS raw.readiness_assessments (
    readiness_id VARCHAR(30) PRIMARY KEY,

    initiative_id VARCHAR(30) NOT NULL,

    readiness_dimension VARCHAR(50) NOT NULL,

    readiness_score INTEGER
        CHECK (
            readiness_score BETWEEN 0 AND 100
        ),

    assessment_status VARCHAR(50),

    assessment_note TEXT,

    CONSTRAINT fk_readiness_initiative
        FOREIGN KEY (initiative_id)
        REFERENCES raw.transformation_initiatives(
            initiative_id
        )
        ON DELETE CASCADE
);


-- ============================================================
-- 7. Indexes
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_risk_initiative
ON raw.transformation_risks(
    initiative_id
);


CREATE INDEX IF NOT EXISTS idx_risk_domain
ON raw.transformation_risks(
    risk_domain
);


CREATE INDEX IF NOT EXISTS idx_risk_status
ON raw.transformation_risks(
    status
);


CREATE INDEX IF NOT EXISTS idx_control_risk
ON raw.risk_controls(
    risk_id
);


CREATE INDEX IF NOT EXISTS idx_control_status
ON raw.risk_controls(
    control_status
);


CREATE INDEX IF NOT EXISTS idx_action_risk
ON raw.mitigation_actions(
    risk_id
);


CREATE INDEX IF NOT EXISTS idx_action_status
ON raw.mitigation_actions(
    status
);


CREATE INDEX IF NOT EXISTS idx_action_due_date
ON raw.mitigation_actions(
    due_date
);


CREATE INDEX IF NOT EXISTS idx_readiness_initiative
ON raw.readiness_assessments(
    initiative_id
);


CREATE INDEX IF NOT EXISTS idx_readiness_dimension
ON raw.readiness_assessments(
    readiness_dimension
);


-- ============================================================
-- 8. Schema validation comments
-- ============================================================

COMMENT ON TABLE raw.transformation_initiatives
IS 'Transformation initiatives evaluated by TransformRisk.';


COMMENT ON TABLE raw.transformation_risks
IS 'Risks associated with transformation initiatives.';


COMMENT ON TABLE raw.risk_controls
IS 'Controls designed to reduce transformation risk.';


COMMENT ON TABLE raw.mitigation_actions
IS 'Management actions created to mitigate transformation risks.';


COMMENT ON TABLE raw.readiness_assessments
IS 'Readiness assessments across technology, data, process, people and governance dimensions.';