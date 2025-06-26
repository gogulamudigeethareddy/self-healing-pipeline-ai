# API Endpoints Documentation: Self-Healing Pipeline

This document describes each backend API endpoint, its purpose, method, sample request, and sample response or payload.

---

## 1. Health Check
**Endpoint:** `/`
**Method:** `GET`
**Description:** Returns API health status.
**Sample Request:**
```
GET http://localhost:5000/
```
**Sample Response:**
```json
{
  "status": "ok",
  "message": "Flask API is running"
}
```

---

## 2. Get Employees
**Endpoint:** `/api/employees`
**Method:** `GET`
**Description:** Returns the current list of employee records (from `data/sample_employees.json`).
**Sample Request:**
```
GET http://localhost:5000/api/employees
```
**Sample Response:**
```json
[
  {
    "id": 1,
    "name": "Alice Smith",
    "email": "alice@example.com",
    "department": "Engineering",
    "salary": 120000,
    "hire_date": "2020-01-15"
  },
  ...
]
```

---

## 3. Trigger Webhook
**Endpoint:** `/webhook`
**Method:** `POST`
**Description:** Receives failure events from Airflow and triggers the agentic workflow.
**Sample Request:**
```
POST http://localhost:5000/webhook
Content-Type: application/json

{
  "dag_id": "self_healing_pipeline",
  "task_id": "validate_schema",
  "execution_date": "2025-06-24T22:02:10.072360+00:00",
  "error_message": "Schema validation failed: Record 0: Missing required field 'id'",
  "error_type": "schema_validation",
  "timestamp": "2025-06-24T22:02:13.999934"
}
```
**Sample Response:**
```json
{
  "monitor": { ... },
  "diagnosis": { ... },
  "fix": { ... },
  "timings": { ... },
  "errors": { ... }
}
```

---

## 4. Get Logs
**Endpoint:** `/api/logs`
**Method:** `GET`
**Description:** Returns the last 200 lines of the pipeline log file.
**Sample Request:**
```
GET http://localhost:5000/api/logs
```
**Sample Response:**
```json
{
  "logs": [
    "2025-06-24 22:02:14,010 INFO ...",
    ...
  ]
}
```

---

## 5. Get Pipeline Status
**Endpoint:** `/api/status`
**Method:** `GET`
**Description:** Returns recent pipeline run status and agent actions.
**Sample Request:**
```
GET http://localhost:5000/api/status
```
**Sample Response:**
```json
{
  "pipeline_runs": [
    {
      "event": { ... },
      "monitor": { ... },
      "diagnosis": { ... },
      "fix": { ... },
      "timestamp": "..."
    },
    ...
  ]
}
```

---

## 6. Trigger Diagnosis
**Endpoint:** `/api/diagnose`
**Method:** `POST`
**Description:** Triggers the diagnosis agent from external services.
**Sample Request:**
```
POST http://localhost:5000/api/diagnose
Content-Type: application/json

{
  "failure_event": {
    "dag_id": "self_healing_pipeline",
    "task_id": "validate_schema",
    "error_message": "Schema validation failed: Record 0: Missing required field 'id'"
  }
}
```
**Sample Response:**
```json
{
  "root_cause": "Missing required field 'id' in record 0",
  "confidence": "high",
  "suggested_fixes": [ ... ],
  ...
}
```

---

## 7. Feedback Endpoints
**Endpoint:** `/api/feedback`
**Method:** `GET`, `POST`
**Description:**
- `GET`: Returns feedback history.
- `POST`: Accepts user feedback on fixes.

**Sample POST Request:**
```
POST http://localhost:5000/api/feedback
Content-Type: application/json

{
  "feedback": "The fix worked!",
  "rating": 5
}
```
**Sample GET Response:**
```json
{
  "feedback": [
    { "feedback": "The fix worked!", "rating": 5, "timestamp": "..." },
    ...
  ]
}
```

---

## 8. Fix Simulation Endpoints (Demo Only)
- `/api/update_schema` (POST)
- `/api/add_transformation` (POST)
- `/api/update_config` (POST)
- `/api/notify` (POST)
- `/api/verify_fix` (POST)
- `/api/rollback` (POST)

**All accept a JSON payload and return a status message.**

**Sample Request:**
```
POST http://localhost:5000/api/update_schema
Content-Type: application/json

{
  "dag_id": "self_healing_pipeline",
  "task_id": "validate_schema",
  "action": "update_schema",
  "timestamp": "2025-06-24T22:02:49.902098"
}
```
**Sample Response:**
```json
{
  "status": "schema updated"
}
```

---

For more, see the Postman collection in `docs/postman_collection.json`.
