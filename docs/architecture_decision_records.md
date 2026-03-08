# Architecture Decision

## Status
Proposed

## Context
This system supports internal university event management, allowing student organization leaders to submit events, staff administrators to review and publish them, and students to browse approved events.

Key constraints and drivers include:
- Low to moderate concurrent usage
- A small development and maintenance team (2–4 engineers)
- Limited budget and operational overhead
- No real-time or high-availability requirements
- A strong need for maintainability and ease of extension across semesters

The architecture must support event submission, review workflows, browsing and filtering, and future feature additions (e.g., reminders) without major refactoring.

---

## Decision

The system will use the following architectural choices:

1. **System Roles & Communication:** Client–Server Architecture  
2. **Deployment & Evolution:** Modular Monolith  
3. **Code Organization & Dependency Direction:** Layered Architecture  
4. **Data & State Ownership:** Single Shared Database  
5. **Interaction Model:** Synchronous Request–Response

---

## Alternatives Considered

### 1. System Roles & Communication
- **Chosen:** Client–Server  
- **Alternative:** Event-Driven Architecture  

Event-driven architecture was not chosen because the system does not require real-time updates, background processing, or complex inter-service communication. A client–server model is simpler and sufficient for form submissions, reviews, and browsing.

---

### 2. Deployment & Evolution
- **Chosen:** Modular Monolith  
- **Alternative:** Microservices  

Microservices were not chosen due to the operational complexity, deployment overhead, and coordination burden they introduce. Given the small team and modest scale, a modular monolith provides better maintainability while still allowing future refactoring if the system grows.

---

### 3. Code Organization & Dependency Direction
- **Chosen:** Layered Architecture  
- **Alternative:** Feature-Based Architecture  

A feature-based architecture was considered but rejected due to the team’s junior experience level. A layered approach (presentation, business logic, data access) provides clearer separation of concerns and is easier to understand, test, and maintain.

---

### 4. Data & State Ownership
- **Chosen:** Single Shared Database  
- **Alternative:** Database per Service  

A database-per-service approach was not selected because the system is not using microservices. A single database simplifies data consistency, reporting, and administration while meeting performance requirements.

---

### 5. Interaction Model
- **Chosen:** Synchronous Request–Response  
- **Alternative:** Asynchronous Messaging  

Asynchronous interactions were not chosen because user actions (submission, approval, browsing) require immediate feedback. Synchronous interactions better align with user expectations and acceptance criteria such as confirmation messages and fast search results.

---

## Consequences

### Positive
- Simple and understandable architecture suitable for a junior team
- Low operational and infrastructure overhead
- Clear separation of concerns improves maintainability
- Easy to extend with new features without major refactoring
- Meets performance needs for hundreds of users

### Negative
- Limited scalability compared to event-driven or microservice-based systems
- Tighter coupling than distributed architectures
- Future migration to microservices would require deliberate refactoring
