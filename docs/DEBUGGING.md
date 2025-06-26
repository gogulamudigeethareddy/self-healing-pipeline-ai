# Debugging Guide: Self-Healing Data Pipeline AI

This guide provides step-by-step instructions for debugging the self-healing pipeline, including Airflow, Flask backend, agents, and Docker Compose setup.

---

## 1. General Debugging Steps
- **Check Service Health:**
  - Use `docker-compose ps` to ensure all containers are running.
  - Use `docker-compose logs <service>` to view logs for a specific service (e.g., `backend`, `airflow-webserver`).
- **Check Flask Backend:**
  - Access the health endpoint: `GET http://localhost:5000/` (should return status OK).
  - Check `backend/logs/pipeline.log` for agent and API logs.
- **Check Airflow:**
  - Access the Airflow UI at `http://localhost:8080`.
  - Inspect DAG/task logs for errors and tracebacks.
- **Check Data Volume:**
  - Ensure `data/sample_employees.json` is mounted in the backend container.
  - Changes to this file should persist and be visible both inside and outside the container.

---

## 2. Common Issues & Fixes
- **Backend cannot find data file:**
  - Ensure `./data:/app/../data` is in the backend's `volumes` in `docker-compose.yml`.
  - Rebuild containers after changing volumes: `docker-compose down && docker-compose up --build`.
- **Webhook timeouts:**
  - Increase the timeout in Airflow DAG's `requests.post(..., timeout=60)`.
- **Agents not healing data:**
  - Confirm `/api/employees` reads from `data/sample_employees.json`.
  - Check FixAgent logs for patching actions.
- **Airflow DAG stuck or failing:**
  - Check Airflow logs for the failing task.
  - Ensure the backend is reachable from Airflow (use service name, not localhost).

---

## 3. Useful Docker Commands
- View all logs: `docker-compose logs`
- View logs for backend: `docker-compose logs backend`
- Exec into backend: `docker-compose exec backend /bin/bash`
- Exec into Airflow webserver: `docker-compose exec airflow-webserver /bin/bash`

---

## 4. Postman Collection

### Example Requests

#### 1. Health Check
```
GET http://localhost:5000/
```

#### 2. Get Employees
```
GET http://localhost:5000/api/employees
```

#### 3. Trigger Webhook (simulate Airflow failure)
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

#### 4. Get Logs
```
GET http://localhost:5000/api/logs
```

#### 5. Get Pipeline Status
```
GET http://localhost:5000/api/status
```

#### 6. Trigger Diagnosis
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

---

## 5. Tips
- Always check logs for the most recent errors.
- Use Postman or curl to test endpoints independently.
- If changes to data or code are not reflected, restart the affected containers.

---

For more details, see `docs/ARCHITECTURE.md` and `docs/SETUP_AND_RUN.md`.
