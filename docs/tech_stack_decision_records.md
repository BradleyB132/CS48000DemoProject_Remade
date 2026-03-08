# ADR 001: Selection of Streamlit-Native Modular Monolith (Stack A)

## Status
**Accepted**

## Context
The project requires a Python-based web interface with a PostgreSQL backend. Our architectural goals include maintaining a **Modular Monolith** structure and a **Layered (MVC)** code organization to ensure long-term maintainability and testability using `pytest`.

We evaluated three primary stacks:
1. **Stack A:** Streamlit-Native (Pure Streamlit + SQLAlchemy)
2. **Stack B:** Django-Core (Django + Streamlit UI)
3. **Stack C:** API-First (FastAPI + Streamlit UI)

## Decision
We have decided to proceed with **Stack A (Streamlit-Native)**. 

To meet our architectural dimensions of "Modular Monolith" and "Layered Architecture" within a framework that is traditionally "flat," we will enforce the following engineering standards:

* **Logic Separation:** No SQL queries or heavy business logic will reside in the `app.py` or page files. 
* **Layering:** We will implement a MVC design pattern for seperation of concern. The database used is PostgreSQL.
* **Module Boundaries:** The project will be organized by domain (e.g., `src/module/billing`, `src/module/inventory`) to simulate a modular monolith.
* **State Management:** We will utilize Streamlit's `st.session_state` as the primary mechanism for synchronous state handling across layers.

## Alternatives Considered

### Stack B: Django + Streamlit
* **Pros:** Native modularity and strict MVC.
* **Cons:** High overhead and "double-coding" models/forms that Streamlit handles more simply.

### Stack C: FastAPI + Streamlit
* **Pros:** Excellent performance and clear client-server separation.
* **Cons:** Significant boilerplate for a single-team project; adds complexity to the deployment pipeline.

## Comparison Summary

| Dimension | Metric | Implementation Strategy for Stack A |
| :--- | :--- | :--- |
| **1. Client–Server Architecture** | **Medium** | Streamlit manages the connection; we treat the Python backend as the "Server" logic. |
| **2. Modular Monolith** | **Medium** | Enforced via strict directory structure (`/module`) rather than framework tools. |
| **3. Layered Architecture (MVC)** | **Medium** | Pseudo-MVC: Streamlit (View/Controller) + Service Layer (Model/Logic). |
| **4. Data & State Ownership** | **High** | Centralized PostgreSQL via a shared SQLAlchemy engine instance. |
| **5. Interaction Model** | **High** | Native Streamlit top-down execution (Synchronous). |

## Consequences

### Positive
* **Development Speed:** Unmatched velocity. Changes in the database or logic reflect in the UI immediately without API updates.
* **Reduced Complexity:** A single codebase and single deployment unit. No need to manage CORS or authentication between a separate frontend and backend.
* **Pythonic Workflow:** The entire team stays within the Python ecosystem for both UI and logic.

### Negative
* **Architectural Drift:** High risk of "Spaghetti Code" if developers bypass the service layer and put logic in UI files.
* **Testing Complexity:** Testing the UI requires specialized Streamlit testing tools, though business logic in the `services/` layer remains easily testable via `pytest`.
* **Scalability:** Streamlit has a higher memory overhead per user compared to a traditional React/FastAPI stack; may require vertical scaling sooner.