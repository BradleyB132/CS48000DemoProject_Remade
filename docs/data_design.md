## Production_Log
- Lot_ID
- Line_No
- Production_Date
- Shift_Leader

## Quality_Inspection
- Inspection_ID
- Lot_ID
- Defect_Type
- Defect_Severity
- Inspection_Status

## Shipping_Manifest
- Shipment_ID
- Lot_ID
- Ship_Date
- Destination
- Ship_Status

## Relationships
- One Production_Log (Lot) can have many Quality_Inspections.
- One Production_Log (Lot) has one Shipping_Manifest entry.
---
```mermaid
erDiagram
    ProductionLog ||--o{ QualityInspection : has
    ProductionLog ||--|| ShippingManifest : ships

    ProductionLog {
        LotID string
        Line string
        Date string
        ShiftLeader string
    }

    QualityInspection {
        Inspection string
        LotID string
        DefectType string
        Severity string
        Status string
    }

    ShippingManifest {
        Shipment string
        LotID string
        ShipDate string
        Destination string
        Status string
    }
