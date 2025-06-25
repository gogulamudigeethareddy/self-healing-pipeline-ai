# AI-Powered Self-Healing Data Pipeline — Local Setup & Run Guide

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Project Structure](#project-structure)
4. [Quick Start](#quick-start)
5. [Detailed Setup](#detailed-setup)
6. [Running the Demo](#running-the-demo)
7. [Simulating Failures](#simulating-failures)
8. [Agentic Workflow](#agentic-workflow)
9. [Frontend Dashboard](#frontend-dashboard)
10. [Troubleshooting](#troubleshooting)
11. [Resetting the Demo](#resetting-the-demo)
12. [Further Reading](#further-reading)

---

## 1. Overview
This guide walks you through setting up, running, and demoing the AI-Powered Self-Healing Data Pipeline on your local machine. The system uses Apache Airflow, Flask, React, and AI agents (CrewAI/LangChain + OpenAI GPT-4) to automatically detect, diagnose, and fix data pipeline failures.

> **Note:** If you use GitHub Copilot, please review `.github/copilot-instructions.md` for workspace-specific best practices and coding standards.

### Key Features
- **Real-time Monitoring**: Continuous pipeline health checks
- **Intelligent Diagnosis**: AI-powered root cause analysis
- **Safe Auto-remediation**: Configurable fix strategies with human oversight
- **Visual Dashboard**: Real-time pipeline status and agent reasoning
- **Audit Trail**: Complete history of failures and fixes

---

## 2. Prerequisites
- **Python 3.8+**
- **Node.js 16+**
- **Docker & Docker Compose**
- **OpenAI API Key** (for agentic reasoning)
- **Git**

### System Requirements
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: 2GB free space
- **Network**: Internet connection for Docker images and API calls

---

## 3. Project Structure
```
self-healing-pipeline-ai/
├── 📁 airflow/                  # Airflow DAGs and configurations
│   └── dags/
│       └── self_healing_pipeline.py
├── 📁 agents/                   # AI agent implementations
│   ├── monitor_agent.py      # Failure detection agent
│   ├── diagnose_agent.py     # Root cause analysis agent
│   └── fix_agent.py          # Auto-remediation agent
├── 📁 backend/                  # Flask API server
│   ├── app.py                # Main API endpoints
│   ├── requirements.txt      # Backend dependencies
│   └── logs/                 # Backend logs
├── 📁 frontend/                 # React dashboard
│   └── src/
│       ├── App.tsx
│       ├── index.tsx
│       ├── setupProxy.js
│       └── components/
│           ├── StatusView.tsx
│           ├── AgentLogs.tsx
│           ├── TimelineView.tsx
│           └── FeedbackForm.tsx
├── 📁 scripts/                  # Utility scripts
│   ├── demo.py               # Demo runner
│   ├── start_services.sh     # Start all services
│   └── stop_services.sh      # Stop all services
├── 📁 data/                     # Sample data and schema
│   ├── expected_schema.json
│   └── sample_employees.json
├── 📁 logs/                     # Pipeline logs
│   └── pipeline.log
├── .github/                     # GitHub-specific files
│   └── copilot-instructions.md # Copilot and automation guidelines
```

---

## 4. Quick Start

### Option A: Automated Setup (Recommended)
```bash
# 1. Clone the repository
git clone <your-repo-url>
cd self-healing-pipeline-ai

# 2. Configure environment
cp env.example .env
# Edit .env with your OpenAI API key

# 3. Start all services
./scripts/start_services.sh

# 4. Run the demo
python scripts/demo.py
```

### Option B: Manual Setup
Follow the detailed setup instructions below.

---

## 5. Detailed Setup

### 5.1. Clone and Prepare
```bash
git clone <your-repo-url>
cd self-healing-pipeline-ai
```

### 5.2. Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
```bash
# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_PORT=5000

# Airflow Configuration
AIRFLOW_HOME=./airflow
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__SQL_ALCHEMY_CONN=sqlite:///./airflow/airflow.db
AIRFLOW__CORE__LOAD_EXAMPLES=False

# Agent Configuration
AGENT_TIMEOUT=300
MAX_RETRIES=3
AUTO_FIX_ENABLED=True
REQUIRE_HUMAN_APPROVAL=False
```

### 5.3. Python Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 5.4. Node.js Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## 6. Running with Docker Compose (Recommended)

1. **Start all services:**
   ```sh
   docker-compose up --build
   ```
   This will start Airflow, backend, frontend, and supporting services.

2. **Access services:**
   - Airflow UI: [http://localhost:8080](http://localhost:8080)
   - Backend API: [http://localhost:5000](http://localhost:5000)
   - Frontend: [http://localhost:3000](http://localhost:3000)

---

## 7. Testing the Self-Healing Pipeline
1. **Trigger the DAG in Airflow UI** (`self_healing_pipeline`).
2. The pipeline will fetch data, validate schema, and (if a failure is detected) trigger the self-healing loop via the backend webhook.
3. The FixAgent will patch `data/sample_employees.json` if needed.
4. On the next run, the pipeline should succeed end-to-end.

---

## 8. Debugging & API Testing
- See `docs/DEBUGGING.md` for troubleshooting steps, common issues, and Postman examples.
- Logs are available in `backend/logs/pipeline.log` and via the API (`/api/logs`).
- Use the Postman collection in `docs/postman_collection.json` to test endpoints.
- Full API documentation with sample payloads: `docs/API_ENDPOINTS.md`

---

## 9. Stopping and Cleaning Up
- To stop all services:
  ```sh
  docker-compose down
  ```
- To remove all containers, networks, and volumes:
  ```sh
  docker-compose down -v
  ```

---

## 10. Updating Agents or Code
- After editing code in `backend/`, `agents/`, or `airflow/dags/`, restart the affected containers:
  ```sh
  docker-compose restart backend airflow-webserver airflow-scheduler
  ```

---

## 11. Documentation Reference
- **API Reference:** `docs/API_ENDPOINTS.md`
- **Debugging Guide:** `docs/DEBUGGING.md`
- **Postman Collection:** `docs/postman_collection.json`
- **Architecture:** `docs/ARCHITECTURE.md`

---

For questions, see the documentation in the `docs/` folder or contact the project maintainers.