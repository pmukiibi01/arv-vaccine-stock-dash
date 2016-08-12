-- Initialize the database schema for ARV and Vaccine Stock-Out Prediction System

CREATE TABLE IF NOT EXISTS facilities (
    id SERIAL PRIMARY KEY,
    facility_code VARCHAR(50) UNIQUE NOT NULL,
    facility_name VARCHAR(255) NOT NULL,
    district VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    facility_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS commodities (
    id SERIAL PRIMARY KEY,
    commodity_code VARCHAR(50) UNIQUE NOT NULL,
    commodity_name VARCHAR(255) NOT NULL,
    commodity_type VARCHAR(50) NOT NULL, -- ARV, Vaccine, etc.
    unit_of_measure VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stock_movements (
    id SERIAL PRIMARY KEY,
    facility_id INTEGER REFERENCES facilities(id),
    commodity_id INTEGER REFERENCES commodities(id),
    movement_type VARCHAR(20) NOT NULL, -- ISSUE, RECEIPT, ADJUSTMENT
    quantity DECIMAL(10,2) NOT NULL,
    unit_cost DECIMAL(10,2),
    movement_date DATE NOT NULL,
    reference_number VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stock_balances (
    id SERIAL PRIMARY KEY,
    facility_id INTEGER REFERENCES facilities(id),
    commodity_id INTEGER REFERENCES commodities(id),
    current_stock DECIMAL(10,2) NOT NULL DEFAULT 0,
    reorder_level DECIMAL(10,2) NOT NULL DEFAULT 0,
    maximum_stock DECIMAL(10,2) NOT NULL DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(facility_id, commodity_id)
);

CREATE TABLE IF NOT EXISTS service_volumes (
    id SERIAL PRIMARY KEY,
    facility_id INTEGER REFERENCES facilities(id),
    service_type VARCHAR(50) NOT NULL, -- HIV, Immunization, etc.
    volume_count INTEGER NOT NULL,
    reporting_period DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lead_times (
    id SERIAL PRIMARY KEY,
    facility_id INTEGER REFERENCES facilities(id),
    commodity_id INTEGER REFERENCES commodities(id),
    supplier VARCHAR(100) NOT NULL,
    average_lead_time_days INTEGER NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    facility_id INTEGER REFERENCES facilities(id),
    commodity_id INTEGER REFERENCES commodities(id),
    prediction_date DATE NOT NULL,
    predicted_stock_out_date DATE,
    confidence_score DECIMAL(5,2),
    risk_level VARCHAR(20), -- LOW, MEDIUM, HIGH, CRITICAL
    model_used VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    facility_id INTEGER REFERENCES facilities(id),
    commodity_id INTEGER REFERENCES commodities(id),
    alert_type VARCHAR(50) NOT NULL, -- STOCK_OUT, LOW_STOCK, REORDER
    alert_level VARCHAR(20) NOT NULL, -- INFO, WARNING, CRITICAL
    message TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_stock_movements_facility_commodity ON stock_movements(facility_id, commodity_id);
CREATE INDEX idx_stock_movements_date ON stock_movements(movement_date);
CREATE INDEX idx_predictions_facility_commodity ON predictions(facility_id, commodity_id);
CREATE INDEX idx_predictions_date ON predictions(prediction_date);
CREATE INDEX idx_alerts_facility_commodity ON alerts(facility_id, commodity_id);
CREATE INDEX idx_alerts_resolved ON alerts(is_resolved);

-- Insert sample data
INSERT INTO facilities (facility_code, facility_name, district, region, facility_type) VALUES
('HC001', 'Kampala Central Health Center', 'Kampala', 'Central', 'Health Center'),
('HC002', 'Jinja Regional Hospital', 'Jinja', 'Eastern', 'Hospital'),
('HC003', 'Mbarara Referral Hospital', 'Mbarara', 'Western', 'Referral Hospital'),
('HC004', 'Gulu Health Center IV', 'Gulu', 'Northern', 'Health Center'),
('HC005', 'Mbale Health Center III', 'Mbale', 'Eastern', 'Health Center');

INSERT INTO commodities (commodity_code, commodity_name, commodity_type, unit_of_measure) VALUES
('ARV001', 'Tenofovir/Lamivudine/Dolutegravir (TLD)', 'ARV', 'Tablets'),
('ARV002', 'Efavirenz 600mg', 'ARV', 'Tablets'),
('VAC001', 'BCG Vaccine', 'Vaccine', 'Vials'),
('VAC002', 'DPT-HepB-Hib', 'Vaccine', 'Vials'),
('VAC003', 'Measles Vaccine', 'Vaccine', 'Vials'),
('VAC004', 'Polio Vaccine (OPV)', 'Vaccine', 'Vials');

INSERT INTO stock_balances (facility_id, commodity_id, current_stock, reorder_level, maximum_stock) VALUES
(1, 1, 5000, 1000, 10000),
(1, 2, 3000, 800, 6000),
(1, 3, 200, 50, 500),
(2, 1, 8000, 1500, 15000),
(2, 2, 4000, 1000, 8000),
(3, 1, 12000, 2000, 20000),
(3, 2, 6000, 1500, 12000),
(4, 1, 2000, 500, 4000),
(5, 1, 1500, 400, 3000);

