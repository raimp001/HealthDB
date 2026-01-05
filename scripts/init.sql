-- HealthDB Database Initialization Script
-- This runs automatically when the PostgreSQL container first starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    user_type VARCHAR(50) NOT NULL DEFAULT 'researcher',
    organization VARCHAR(255),
    institution_id UUID,
    role VARCHAR(50) DEFAULT 'user',
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Institutions table
CREATE TABLE IF NOT EXISTS institutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    emr_system VARCHAR(100),
    fhir_endpoint VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Patient profiles (for patient portal)
CREATE TABLE IF NOT EXISTS patient_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    hashed_mrn VARCHAR(255) UNIQUE,
    points_balance INTEGER DEFAULT 0,
    total_points_earned INTEGER DEFAULT 0,
    engagement_level VARCHAR(50) DEFAULT 'new',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Consents table
CREATE TABLE IF NOT EXISTS consents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patient_profiles(id) ON DELETE CASCADE,
    consent_type VARCHAR(100) NOT NULL,
    consent_version VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    consent_options JSONB,
    signed_date TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    signature TEXT,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Cancer diagnoses
CREATE TABLE IF NOT EXISTS cancer_diagnoses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hashed_patient_id VARCHAR(255) NOT NULL,
    institution_id UUID REFERENCES institutions(id),
    cancer_type VARCHAR(255) NOT NULL,
    icd10_code VARCHAR(20),
    diagnosis_date DATE,
    stage VARCHAR(50),
    substage VARCHAR(50),
    grade VARCHAR(50),
    histology VARCHAR(255),
    primary_site VARCHAR(255),
    laterality VARCHAR(50),
    risk_group VARCHAR(100),
    performance_status INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Treatments
CREATE TABLE IF NOT EXISTS treatments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    diagnosis_id UUID REFERENCES cancer_diagnoses(id) ON DELETE CASCADE,
    treatment_type VARCHAR(100) NOT NULL,
    regimen_name VARCHAR(255),
    line_of_therapy INTEGER DEFAULT 1,
    start_date DATE,
    end_date DATE,
    cycles_planned INTEGER,
    cycles_completed INTEGER,
    dose_modifications JSONB,
    intent VARCHAR(100),
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Treatment responses
CREATE TABLE IF NOT EXISTS treatment_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    treatment_id UUID REFERENCES treatments(id) ON DELETE CASCADE,
    assessment_date DATE,
    response_criteria VARCHAR(100),
    response_type VARCHAR(100),
    mrd_status VARCHAR(50),
    mrd_method VARCHAR(100),
    imaging_result TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Molecular data
CREATE TABLE IF NOT EXISTS molecular_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    diagnosis_id UUID REFERENCES cancer_diagnoses(id) ON DELETE CASCADE,
    test_type VARCHAR(100),
    test_date DATE,
    gene VARCHAR(100),
    mutation VARCHAR(255),
    variant_allele_frequency DECIMAL(5,4),
    interpretation VARCHAR(100),
    clinical_significance VARCHAR(100),
    raw_results JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Outcomes
CREATE TABLE IF NOT EXISTS outcomes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    diagnosis_id UUID REFERENCES cancer_diagnoses(id) ON DELETE CASCADE,
    outcome_type VARCHAR(100),
    outcome_date DATE,
    status VARCHAR(100),
    cause VARCHAR(255),
    survival_months DECIMAL(6,2),
    pfs_months DECIMAL(6,2),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Data products (marketplace)
CREATE TABLE IF NOT EXISTS data_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    cancer_types JSONB,
    data_categories JSONB,
    patient_count INTEGER,
    record_count INTEGER,
    completeness_score DECIMAL(5,2),
    date_range_start DATE,
    date_range_end DATE,
    pricing_tiers JSONB,
    is_featured BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Data access logs
CREATE TABLE IF NOT EXISTS data_access_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    patient_id UUID REFERENCES patient_profiles(id),
    data_product_id UUID REFERENCES data_products(id),
    access_type VARCHAR(100),
    data_type VARCHAR(100),
    purpose TEXT,
    query_hash VARCHAR(255),
    record_count INTEGER,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Rewards transactions
CREATE TABLE IF NOT EXISTS rewards_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patient_profiles(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50),
    points INTEGER NOT NULL,
    description TEXT,
    reference_type VARCHAR(100),
    reference_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Research cohorts
CREATE TABLE IF NOT EXISTS research_cohorts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    criteria JSONB,
    patient_count INTEGER,
    is_saved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_user_type ON users(user_type);
CREATE INDEX IF NOT EXISTS idx_cancer_diagnoses_patient ON cancer_diagnoses(hashed_patient_id);
CREATE INDEX IF NOT EXISTS idx_cancer_diagnoses_type ON cancer_diagnoses(cancer_type);
CREATE INDEX IF NOT EXISTS idx_treatments_diagnosis ON treatments(diagnosis_id);
CREATE INDEX IF NOT EXISTS idx_molecular_data_gene ON molecular_data(gene);
CREATE INDEX IF NOT EXISTS idx_data_access_logs_user ON data_access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_data_access_logs_patient ON data_access_logs(patient_id);
CREATE INDEX IF NOT EXISTS idx_consents_patient ON consents(patient_id);
CREATE INDEX IF NOT EXISTS idx_rewards_patient ON rewards_transactions(patient_id);

-- Insert sample data products
INSERT INTO data_products (id, name, description, category, cancer_types, data_categories, patient_count, record_count, completeness_score, date_range_start, date_range_end, pricing_tiers, is_featured) VALUES
(uuid_generate_v4(), 'Comprehensive DLBCL Outcomes Registry', 'Largest de-identified DLBCL dataset with 5-year outcomes, molecular data, and treatment details including CAR-T and novel therapies.', 'Hematologic', '["Diffuse Large B-Cell Lymphoma"]'::jsonb, '["Demographics", "Diagnoses", "Treatments", "Outcomes", "Molecular"]'::jsonb, 4250, 125000, 94.0, '2015-01-01', '2025-12-31', '{"academic": 15000, "startup": 35000, "enterprise": 75000, "pharma": 150000}'::jsonb, true),
(uuid_generate_v4(), 'AML Treatment Response Database', 'Acute myeloid leukemia patients with FLT3/NPM1 status, treatment responses, and MRD data from multiple centers.', 'Hematologic', '["Acute Myeloid Leukemia"]'::jsonb, '["Demographics", "Diagnoses", "Treatments", "Molecular", "MRD"]'::jsonb, 2800, 84000, 91.0, '2016-01-01', '2025-12-31', '{"academic": 12000, "startup": 28000, "enterprise": 60000, "pharma": 120000}'::jsonb, true),
(uuid_generate_v4(), 'CAR-T Real-World Outcomes', 'Multi-center CAR-T therapy outcomes across lymphoma and leukemia with CRS/ICANS data and long-term follow-up.', 'Cell Therapy', '["DLBCL", "ALL", "MCL", "FL"]'::jsonb, '["Demographics", "Treatments", "Toxicity", "Response", "Outcomes"]'::jsonb, 890, 35600, 97.0, '2018-01-01', '2025-12-31', '{"academic": 25000, "startup": 55000, "enterprise": 125000, "pharma": 250000}'::jsonb, true)
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO healthdb;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO healthdb;

