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

## 6. Service Startup

### 6.1. Start Airflow (Docker)
```bash
# Start Airflow services
docker-compose up -d airflow-webserver airflow-scheduler postgres redis airflow-init

# Wait for initialization (30-60 seconds)
sleep 30

# Verify Airflow is running
curl http://localhost:8080/health
```

**Airflow Access:**
- **URL**: http://localhost:8080
- **Username**: admin
- **Password**: admin

### 6.2. Start Flask Backend
```bash
cd backend
python app.py
```

**Flask API Access:**
- **URL**: http://localhost:5000
- **Health Check**: http://localhost:5000/api/employees

### 6.3. Start React Frontend
```bash
cd frontend
npm start
```

**React Dashboard Access:**
- **URL**: http://localhost:3000

---

## 7. Running the Demo

### 7.1. Automated Demo
```bash
# Run the complete demo script
python scripts/demo.py
```

This script will:
1. Check if services are running
2. Simulate a schema validation error
3. Trigger the agentic workflow
4. Display results and logs
5. Submit feedback

### 7.2. Manual Demo Steps

#### Step 1: Verify Pipeline Success
1. Open Airflow UI: http://localhost:8080
2. Navigate to DAGs → self_healing_pipeline
3. Trigger the DAG manually
4. Verify all tasks complete successfully

#### Step 2: Inject Failure
1. Modify the API response in `backend/app.py`:
   ```python
   # Remove email field to simulate schema error
   employees = [
       {"id": 1, "name": "Alice Smith", "department": "Engineering", "salary": 120000, "hire_date": "2020-01-15"},
       # ... remove email field from all records
   ]
   ```

#### Step 3: Trigger Failure
1. Restart Flask backend: `Ctrl+C` then `python app.py`
2. Trigger the Airflow DAG again
3. Observe the failure at schema validation step

#### Step 4: Observe Self-Healing
1. Check the webhook was triggered
2. Monitor agent workflow in Flask logs
3. View results in React dashboard
4. Check if pipeline was fixed automatically

---

## 8. Simulating Failures

### 8.1. Schema Validation Error
```python
# In backend/app.py, modify the employees data:
employees = [
    {"id": 1, "name": "Alice Smith", "department": "Engineering", "salary": 120000, "hire_date": "2020-01-15"}
    # Missing email field
]
```

### 8.2. Data Type Error
```python
# Change salary to string instead of number:
employees = [
    {"id": 1, "name": "Alice Smith", "email": "alice@example.com", "department": "Engineering", "salary": "120000", "hire_date": "2020-01-15"}
]
```

### 8.3. Connection Error
```bash
# Stop Flask backend to simulate API downtime
# Then trigger Airflow DAG
```

### 8.4. Manual Approval Required
```bash
# Set in .env file:
REQUIRE_HUMAN_APPROVAL=True
```

---

## 9. Agentic Workflow

### 9.1. Monitor Agent
- **Purpose**: Detects failures and determines severity
- **Triggers**: Webhook from Airflow on task failure
- **Actions**: 
  - Analyzes failure patterns
  - Determines if intervention is needed
  - Triggers diagnosis agent

### 9.2. Diagnose Agent
- **Purpose**: Analyzes root cause using AI
- **Input**: Failure logs and error messages
- **Output**: 
  - Root cause analysis
  - Suggested fixes
  - Safety assessment

### 9.3. Fix Agent
- **Purpose**: Applies safe remediation strategies
- **Strategies**:
  - Retry failed task
  - Update schema definition
  - Add data transformation
  - Request manual intervention

### 9.4. Feedback Loop
- Users can rate fix effectiveness
- Feedback improves agent decision-making
- Audit trail maintained for all actions

---

## 10. Frontend Dashboard

### 10.1. Status View
- Current pipeline run status
- Recent execution history
- Success/failure metrics

### 10.2. Timeline View
- Chronological view of failures and fixes
- Agent action timeline
- Resolution tracking

### 10.3. Agent Logs
- Real-time agent reasoning
- Decision-making process
- Error analysis details

### 10.4. Feedback Form
- Rate fix effectiveness (1-5 stars)
- Submit comments
- Track user satisfaction

---

## 11. Troubleshooting

### 11.1. Common Issues

#### Airflow Not Starting
```bash
# Check Docker logs
docker-compose logs airflow-webserver

# Ensure ports are free
lsof -i :8080
lsof -i :5432
lsof -i :6379

# Reset Airflow
docker-compose down -v
docker-compose up -d airflow-init
```

#### Flask API Errors
```bash
# Check Python environment
python --version
pip list | grep flask

# Check logs
tail -f logs/pipeline.log

# Verify .env configuration
cat .env
```

#### React Dashboard Issues
```bash
# Check Node.js version
node --version
npm --version

# Clear npm cache
npm cache clean --force

# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### Agent Not Responding
```bash
# Check OpenAI API key
echo $OPENAI_API_KEY

# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Check agent logs
tail -f logs/pipeline.log | grep -i agent
```

### 11.2. Port Conflicts
```bash
# Check what's using the ports
lsof -i :5000  # Flask
lsof -i :3000  # React
lsof -i :8080  # Airflow

# Kill processes if needed
kill -9 <PID>
```

### 11.3. Docker Issues
```bash
# Clean up Docker
docker system prune -a
docker volume prune

# Restart Docker Desktop
# Then restart services
```

---

## 12. Resetting the Demo

### 12.1. Complete Reset
```bash
# Stop all services
./scripts/stop_services.sh

# Clean up data
docker-compose down -v
rm -rf airflow/logs airflow/dags/__pycache__ data/processed_*
rm -f .flask_pid .react_pid

# Restart from scratch
./scripts/start_services.sh
```

### 12.2. Partial Reset
```bash
# Reset only pipeline state
rm -rf airflow/logs/*

# Reset agent history
rm -f backend/pipeline_runs.json

# Restart specific service
cd backend && python app.py
```

---

## 13. Further Reading

### 13.1. Documentation
- [README.md](../README.md) — Project overview and architecture
- [agents/](../agents/) — AI agent source code and documentation
- [airflow/dags/](../airflow/dags/) — Airflow pipeline definition
- [backend/](../backend/) — Flask API implementation
- [frontend/](../frontend/) — React dashboard implementation

### 13.2. External Resources
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [React Documentation](https://reactjs.org/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)

### 13.3. API Endpoints
- **Health Check**: `GET /api/employees`
- **Webhook**: `POST /webhook`
- **Status**: `GET /api/status`
- **Logs**: `GET /api/logs`
- **Feedback**: `POST /api/feedback`

---

## 14. Support

### 14.1. Getting Help
- Check the troubleshooting section above
- Review logs in `logs/pipeline.log`
- Check service status at respective URLs
- Open an issue on GitHub

### 14.2. Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

**For questions or issues, open an issue on GitHub or contact the project maintainer.**