-- The "Weekly Issue" Report (AC5)
-- Which production lines had the most issues this week and what is trending?
SELECT 
    p.line_number,
    q.defect_type,
    COUNT(q.quality_inspection_id) AS total_defects
FROM production_logs p
JOIN quality_inspections q ON p.production_log_id = q.production_log_id
WHERE p.production_date >= CURRENT_DATE - INTERVAL '7 days'
  AND q.is_defective = TRUE
GROUP BY p.line_number, q.defect_type
ORDER BY total_defects DESC;

-- The "Risk" Check (Q1)
-- Has a problematic batch (High/Critical defect) already shipped?
SELECT 
    p.lot_number,
    q.defect_severity,
    s.is_shipped,
    s.ship_date,
    s.destination
FROM production_logs p
JOIN quality_inspections q ON p.production_log_id = q.production_log_id
JOIN shipping_manifests s ON p.production_log_id = s.production_log_id
WHERE q.defect_severity IN ('High', 'Critical')
  AND s.is_shipped = TRUE;
