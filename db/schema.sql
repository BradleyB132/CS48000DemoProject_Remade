-- 1. PRODUCTION LOGS
-- Core table representing the manufacturing event
CREATE TABLE production_logs (
    production_log_id SERIAL PRIMARY KEY,
    lot_number VARCHAR(50) NOT NULL UNIQUE, -- Business ID kept unique but not as PK
    line_number INTEGER NOT NULL CHECK (line_number > 0),
    production_date DATE NOT NULL DEFAULT CURRENT_DATE,
    shift_leader VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. QUALITY INSPECTIONS
-- One production_log can have many inspections
CREATE TABLE quality_inspections (
    quality_inspection_id SERIAL PRIMARY KEY,
    production_log_id INTEGER NOT NULL, -- FK following [singular_table]_id convention
    defect_type VARCHAR(100),
    defect_severity VARCHAR(20) CHECK (defect_severity IN ('Low', 'Medium', 'High', 'Critical')),
    is_defective BOOLEAN NOT NULL DEFAULT FALSE,
    inspection_count INTEGER NOT NULL CHECK (inspection_count >= 0),
    inspected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_production_log 
        FOREIGN KEY (production_log_id) 
        REFERENCES production_logs(production_log_id) 
        ON DELETE CASCADE
);

-- 3. SHIPPING MANIFESTS
-- One production_log has one shipping entry
CREATE TABLE shipping_manifests (
    shipping_manifest_id SERIAL PRIMARY KEY,
    production_log_id INTEGER NOT NULL UNIQUE, -- UNIQUE ensures 1:1 relationship
    ship_date DATE,
    destination VARCHAR(255) NOT NULL,
    is_shipped BOOLEAN NOT NULL DEFAULT FALSE,
    is_cancelled BOOLEAN NOT NULL DEFAULT FALSE,
    
    CONSTRAINT fk_production_log 
        FOREIGN KEY (production_log_id) 
        REFERENCES production_logs(production_log_id) 
        ON DELETE CASCADE
);

---
-- INDEXES FOR PERFORMANCE (AC7, AC12)
---

-- Index on production_date for weekly/monthly reporting
CREATE INDEX idx_production_logs_date ON production_logs(production_date);

-- Index on line_number to answer "Which lines have issues?"
CREATE INDEX idx_production_logs_line ON production_logs(line_number);

-- Index on Foreign Keys to speed up joins
CREATE INDEX idx_quality_inspections_log_id ON quality_inspections(production_log_id);
