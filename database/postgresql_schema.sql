-- PostgreSQL Schema for Grime Guardians Operations
-- This schema supports the migration from Notion to PostgreSQL

-- Create database (run as superuser)
-- CREATE DATABASE grime_guardians_ops;

-- Connect to the database and create tables
\c grime_guardians_ops;

-- Enable UUID extension for primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Attendance tracking table (replaces Notion Attendance DB)
CREATE TABLE attendance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cleaner_name VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('check-in', 'check-out')),
    job_id VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Strikes and violations table (replaces Notion Strikes DB)
CREATE TABLE strikes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cleaner_name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('punctuality', 'quality', 'compliance')),
    timestamp TIMESTAMPTZ NOT NULL,
    notes TEXT,
    severity VARCHAR(20) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high')),
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cleaner profiles table (replaces Notion Cleaner Profiles DB)
CREATE TABLE cleaner_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'probation', 'terminated')),
    performance_score DECIMAL(5,2) DEFAULT 0.00,
    hire_date DATE,
    phone VARCHAR(20),
    email VARCHAR(255),
    notes TEXT,
    total_jobs INTEGER DEFAULT 0,
    total_strikes INTEGER DEFAULT 0,
    last_strike_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance metrics aggregation table
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cleaner_name VARCHAR(100) NOT NULL,
    metric_date DATE NOT NULL,
    punctuality_score DECIMAL(5,2),
    quality_score DECIMAL(5,2),
    jobs_completed INTEGER DEFAULT 0,
    strikes_received INTEGER DEFAULT 0,
    bonus_earned DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(cleaner_name, metric_date)
);

-- Job assignments table (for tracking job-specific data)
CREATE TABLE job_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(50) NOT NULL,
    cleaner_name VARCHAR(100) NOT NULL,
    scheduled_start TIMESTAMPTZ,
    actual_start TIMESTAMPTZ,
    actual_end TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'in-progress', 'completed', 'cancelled')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Escalation log table (for tracking all escalations)
CREATE TABLE escalations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cleaner_name VARCHAR(100) NOT NULL,
    escalation_type VARCHAR(30) NOT NULL, -- 'punctuality', 'quality', 'no-show', etc.
    severity VARCHAR(20) DEFAULT 'medium',
    description TEXT,
    action_taken TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    escalated_to VARCHAR(100), -- ops person who handled it
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- Indexes for performance optimization
CREATE INDEX idx_attendance_cleaner_timestamp ON attendance(cleaner_name, timestamp);
CREATE INDEX idx_attendance_timestamp ON attendance(timestamp);
CREATE INDEX idx_strikes_cleaner_timestamp ON strikes(cleaner_name, timestamp);
CREATE INDEX idx_strikes_timestamp ON strikes(timestamp);
CREATE INDEX idx_cleaner_profiles_name ON cleaner_profiles(name);
CREATE INDEX idx_cleaner_profiles_status ON cleaner_profiles(status);
CREATE INDEX idx_performance_metrics_cleaner_date ON performance_metrics(cleaner_name, metric_date);
CREATE INDEX idx_job_assignments_cleaner ON job_assignments(cleaner_name);
CREATE INDEX idx_job_assignments_job_id ON job_assignments(job_id);
CREATE INDEX idx_escalations_cleaner ON escalations(cleaner_name);

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_attendance_updated_at BEFORE UPDATE ON attendance
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cleaner_profiles_updated_at BEFORE UPDATE ON cleaner_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_assignments_updated_at BEFORE UPDATE ON job_assignments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE VIEW active_cleaners AS
SELECT * FROM cleaner_profiles WHERE status = 'active';

CREATE VIEW recent_strikes AS
SELECT s.*, cp.status as cleaner_status 
FROM strikes s
JOIN cleaner_profiles cp ON s.cleaner_name = cp.name
WHERE s.timestamp >= NOW() - INTERVAL '30 days';

CREATE VIEW punctuality_summary AS
SELECT 
    cp.name,
    cp.status,
    COUNT(s.id) as total_strikes,
    COUNT(CASE WHEN s.timestamp >= NOW() - INTERVAL '30 days' THEN 1 END) as recent_strikes
FROM cleaner_profiles cp
LEFT JOIN strikes s ON cp.name = s.cleaner_name AND s.type = 'punctuality'
GROUP BY cp.name, cp.status;

-- Function to calculate performance scores
CREATE OR REPLACE FUNCTION calculate_performance_score(cleaner_name_param VARCHAR)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    total_jobs INTEGER;
    recent_strikes INTEGER;
    base_score DECIMAL(5,2) := 100.00;
    penalty_per_strike DECIMAL(5,2) := 5.00;
BEGIN
    -- Count total jobs in last 30 days
    SELECT COUNT(*) INTO total_jobs
    FROM job_assignments 
    WHERE cleaner_name = cleaner_name_param 
    AND created_at >= NOW() - INTERVAL '30 days';
    
    -- Count strikes in last 30 days
    SELECT COUNT(*) INTO recent_strikes
    FROM strikes 
    WHERE cleaner_name = cleaner_name_param 
    AND timestamp >= NOW() - INTERVAL '30 days';
    
    -- Calculate score (base score minus penalties)
    RETURN GREATEST(0, base_score - (recent_strikes * penalty_per_strike));
END;
$$ LANGUAGE plpgsql;

-- Stored procedure to update all performance scores
CREATE OR REPLACE FUNCTION update_all_performance_scores()
RETURNS VOID AS $$
DECLARE
    cleaner_record RECORD;
    new_score DECIMAL(5,2);
BEGIN
    FOR cleaner_record IN SELECT name FROM cleaner_profiles WHERE status = 'active' LOOP
        new_score := calculate_performance_score(cleaner_record.name);
        
        UPDATE cleaner_profiles 
        SET performance_score = new_score,
            updated_at = NOW()
        WHERE name = cleaner_record.name;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Sample data for testing (remove in production)
INSERT INTO cleaner_profiles (name, status, hire_date, performance_score) VALUES
('Sarah Johnson', 'active', '2024-01-15', 95.50),
('Mike Rodriguez', 'active', '2024-02-01', 88.75),
('Lisa Chen', 'probation', '2024-03-10', 72.25);

-- Grant permissions (adjust role name as needed)
-- CREATE ROLE grime_guardians_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO grime_guardians_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO grime_guardians_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO grime_guardians_app;

COMMIT;
