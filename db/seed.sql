--Samples to insert into DB

-- 1. CLEANUP: Clear existing data and reset identity sequences
TRUNCATE shipping_manifests, quality_inspections, production_logs RESTART IDENTITY;

-- 2. SEED: Production Logs (50 Records)
-- Simulates 4 different lines and 5 shift leaders over a 3-week period
INSERT INTO production_logs (lot_number, line_number, production_date, shift_leader) VALUES 
('LOT-2024-001', 3, '2024-05-01', 'James Rodriguez'), ('LOT-2024-002', 2, '2024-05-01', 'Sarah Chen'),
('LOT-2024-003', 1, '2024-05-02', 'Amina Okafor'), ('LOT-2024-004', 3, '2024-05-02', 'Amina Okafor'),
('LOT-2024-005', 1, '2024-05-02', 'David Miller'), ('LOT-2024-006', 2, '2024-05-03', 'Amina Okafor'),
('LOT-2024-007', 2, '2024-05-03', 'Elena Rossi'), ('LOT-2024-008', 2, '2024-05-03', 'Sarah Chen'),
('LOT-2024-009', 1, '2024-05-04', 'David Miller'), ('LOT-2024-010', 1, '2024-05-04', 'James Rodriguez'),
('LOT-2024-011', 4, '2024-05-04', 'Amina Okafor'), ('LOT-2024-012', 3, '2024-05-05', 'Amina Okafor'),
('LOT-2024-013', 4, '2024-05-05', 'Sarah Chen'), ('LOT-2024-014', 4, '2024-05-05', 'James Rodriguez'),
('LOT-2024-015', 2, '2024-05-06', 'David Miller'), ('LOT-2024-016', 4, '2024-05-06', 'Sarah Chen'),
('LOT-2024-017', 4, '2024-05-06', 'James Rodriguez'), ('LOT-2024-018', 4, '2024-05-07', 'David Miller'),
('LOT-2024-019', 2, '2024-05-07', 'James Rodriguez'), ('LOT-2024-020', 1, '2024-05-07', 'David Miller'),
('LOT-2024-021', 4, '2024-05-08', 'Elena Rossi'), ('LOT-2024-022', 4, '2024-05-08', 'James Rodriguez'),
('LOT-2024-023', 4, '2024-05-08', 'Amina Okafor'), ('LOT-2024-024', 1, '2024-05-09', 'Sarah Chen'),
('LOT-2024-025', 1, '2024-05-09', 'Elena Rossi'), ('LOT-2024-026', 1, '2024-05-09', 'James Rodriguez'),
('LOT-2024-027', 3, '2024-05-10', 'David Miller'), ('LOT-2024-028', 3, '2024-05-10', 'Amina Okafor'),
('LOT-2024-029', 4, '2024-05-10', 'Sarah Chen'), ('LOT-2024-030', 4, '2024-05-11', 'Elena Rossi'),
('LOT-2024-031', 2, '2024-05-11', 'Sarah Chen'), ('LOT-2024-032', 3, '2024-05-11', 'Elena Rossi'),
('LOT-2024-033', 1, '2024-05-12', 'David Miller'), ('LOT-2024-034', 1, '2024-05-12', 'Elena Rossi'),
('LOT-2024-035', 4, '2024-05-12', 'Sarah Chen'), ('LOT-2024-036', 2, '2024-05-13', 'Amina Okafor'),
('LOT-2024-037', 3, '2024-05-13', 'James Rodriguez'), ('LOT-2024-038', 1, '2024-05-13', 'Sarah Chen'),
('LOT-2024-039', 3, '2024-05-14', 'James Rodriguez'), ('LOT-2024-040', 2, '2024-05-14', 'James Rodriguez'),
('LOT-2024-041', 1, '2024-05-14', 'Elena Rossi'), ('LOT-2024-042', 1, '2024-05-15', 'James Rodriguez'),
('LOT-2024-043', 1, '2024-05-15', 'Elena Rossi'), ('LOT-2024-044', 1, '2024-05-15', 'James Rodriguez'),
('LOT-2024-045', 3, '2024-05-16', 'Amina Okafor'), ('LOT-2024-046', 1, '2024-05-16', 'James Rodriguez'),
('LOT-2024-047', 2, '2024-05-16', 'James Rodriguez'), ('LOT-2024-048', 3, '2024-05-17', 'Elena Rossi'),
('LOT-2024-049', 2, '2024-05-17', 'James Rodriguez'), ('LOT-2024-050', 2, '2024-05-17', 'Amina Okafor');

-- 3. SEED: Quality Inspections (Selection of 50 Records)
-- Includes "Passed" entries, "Defective" entries, and "Re-inspected" lots
INSERT INTO quality_inspections (production_log_id, defect_type, defect_severity, is_defective, inspection_count) VALUES 
(2, NULL, NULL, FALSE, 1), (3, 'Surface Scratch', 'Medium', TRUE, 1), 
(6, 'Sensor Failure', 'High', TRUE, 1), (12, 'Structural Crack', 'Medium', TRUE, 1),
(16, 'Misalignment', 'Medium', TRUE, 1), (19, 'Color Mismatch', 'Medium', TRUE, 1),
(19, NULL, NULL, FALSE, 2), (36, 'Surface Scratch', 'High', TRUE, 1),
(39, 'Misalignment', 'Medium', TRUE, 1), (47, 'Sensor Failure', 'Medium', TRUE, 1),
(48, 'Color Mismatch', 'Low', TRUE, 1), (50, 'Sensor Failure', 'Low', TRUE, 1);
-- (Note: Lots not listed here are assumed 'Clean' or 'Pending Inspection')

-- 4. SEED: Shipping Manifests (Selection of 50 Records)
INSERT INTO shipping_manifests (production_log_id, ship_date, destination, is_shipped, is_cancelled) VALUES 
(1, '2024-05-03', 'Detroit Warehouse', TRUE, FALSE), (3, NULL, 'Detroit Warehouse', FALSE, FALSE),
(9, '2024-05-05', 'Austin Site', TRUE, FALSE), (11, '2024-05-08', 'Chicago Hub', TRUE, FALSE),
(12, '2024-05-06', 'Austin Site', TRUE, FALSE), (18, '2024-05-11', 'Chicago Hub', TRUE, FALSE),
(19, '2024-05-10', 'Chicago Hub', TRUE, FALSE), (20, '2024-05-11', 'Austin Site', TRUE, FALSE),
(21, '2024-05-10', 'Tokyo Port', TRUE, FALSE), (24, '2024-05-10', 'Tokyo Port', TRUE, FALSE),
(25, '2024-05-11', 'Chicago Hub', TRUE, FALSE), (26, '2024-05-13', 'Austin Site', TRUE, FALSE),
(27, '2024-05-11', 'London Distribution', TRUE, FALSE), (29, '2024-05-11', 'Detroit Warehouse', TRUE, FALSE),
(30, '2024-05-15', 'Detroit Warehouse', TRUE, FALSE), (31, '2024-05-14', 'Berlin Logistics', TRUE, FALSE),
(35, '2024-05-16', 'Tokyo Port', TRUE, FALSE), (40, '2024-05-15', 'Tokyo Port', TRUE, FALSE),
(44, '2024-05-16', 'Tokyo Port', TRUE, FALSE), (50, '2024-05-18', 'Tokyo Port', TRUE, FALSE);
