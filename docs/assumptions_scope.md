## Assumptions

**Assumption 1**  
All Excel files contain a common key (e.g., `Lot_ID`) that enables relational mapping between datasets, even if column names or key formats differ slightly.

**Assumption 2**  
Excel files serve as the system’s *Source of Truth*, representing exported data from a legacy ERP system rather than a live or continuously updated database.

---

## In Scope

- Identifying whether the same defect type appears across multiple lots over time  
- Distinguishing recurring defect issues from one-off incidents  
- Aggregating inspection data across daily and weekly inspection logs  
- Excluding non-defect inspection records (e.g., `Qty Defects = 0`) from defect occurrence counts  
- Indicating when available data is insufficient to determine defect recurrence  

---

## Out of Scope

- Root cause analysis of defects  
- Predictive or AI-based quality analysis  
- Real-time inspection or production monitoring  
- Enforcement of data correctness at the source (e.g., preventing invalid Excel entries)  
- User authentication, authorization, or role-based access control  
- Pixel-perfect or consumer-grade UI design; the dashboard is expected to be functional and clean only  
