# AI-Powered Self-Healing Data Pipeline

## 🎯 Project Overview

This project demonstrates an intelligent data pipeline that automatically monitors, diagnoses, and fixes failures using AI agents. The system uses Apache Airflow for orchestration, AI agents for problem-solving, and a React dashboard for visualization.

### Business Value
- **Reduced Downtime**: Automatic detection and remediation of pipeline failures
- **Lower Maintenance**: AI agents handle common issues without human intervention
- **Improved Reliability**: Self-healing capabilities ensure data quality and pipeline stability

### Realistic Failure Scenario
The demo simulates a JSON API data pull failure due to a schema mismatch (missing column). This is a common real-world issue that can cause entire pipelines to fail.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React         │    │   Flask API     │    │   Airflow       │
│   Dashboard     │◄──►│   (Backend)     │◄──►│   (Orchestrator)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   AI Agents     │
                       │   (CrewAI)      │
                       │  • Monitor      │
                       │  • Diagnose     │
                       │  • Fix          │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Docker & Docker Compose
- OpenAI API Key

### Using Python 3.11 with pyenv and Virtual Environment

Python 3.11 is recommended for this project. You can manage Python versions with [pyenv](https://github.com/pyenv/pyenv):

```bash
# Ensure Python 3.11 is installed via pyenv
pyenv install 3.11.12

# Set the local Python version for this project
pyenv local 3.11.12

# Create a virtual environment using Python 3.11
/Users/geethareddy/.pyenv/versions/3.11.12/bin/python -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

Once activated, install dependencies as usual:

```bash
pip install -r requirements.txt
```

### Installation

1. **Clone and setup environment:**
```bash
git clone <repository-url>
cd self-healing-pipeline-ai
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your OpenAI API key and other settings
```

3. **Start the services:**
```bash
# Start Airflow
docker-compose up -d airflow

# Start Flask API
python backend/app.py

# Start React dashboard
cd frontend && npm install && npm start
```

4. **Run the demo:**
```bash
python scripts/demo.py
```

## 📁 Project Structure

```
self-healing-pipeline-ai/
├── airflow/                  # Airflow DAGs and configurations
│   └── dags/
│       └── self_healing_pipeline.py
├── agents/                   # AI agent implementations
│   ├── monitor_agent.py      # Failure detection agent
│   ├── diagnose_agent.py     # Root cause analysis agent
│   └── fix_agent.py          # Auto-remediation agent
├── backend/                  # Flask API server
│   ├── app.py                # Main API endpoints
│   ├── requirements.txt      # Backend dependencies
│   └── logs/                 # Backend logs
├── frontend/                 # React dashboard
│   └── src/
│       ├── App.tsx
│       ├── index.tsx
│       ├── setupProxy.js
│       └── components/
│           ├── StatusView.tsx
│           ├── AgentLogs.tsx
│           ├── TimelineView.tsx
│           └── FeedbackForm.tsx
├── scripts/                  # Utility scripts
│   ├── demo.py               # Demo runner
│   ├── start_services.sh     # Start all services
│   └── stop_services.sh      # Stop all services
├── data/                     # Sample data and schema
│   ├── expected_schema.json
│   └── sample_employees.json
├── logs/                     # Pipeline logs
│   └── pipeline.log
└── .github/                  # Project automation and Copilot instructions
    └── copilot-instructions.md
```

## 🎭 Demo Script

1. **Initial Success**: Pipeline runs successfully with correct schema
2. **Inject Failure**: Schema mismatch introduced (missing column)
3. **Automatic Detection**: Monitor agent detects the failure
4. **Root Cause Analysis**: Diagnose agent analyzes logs and identifies issue
5. **Self-Healing**: Fix agent applies remediation strategy
6. **Recovery**: Pipeline reruns successfully
7. **Visualization**: Dashboard shows the complete resolution timeline

## 🛠️ Technology Stack

- **Orchestration**: Apache Airflow
- **AI Framework**: CrewAI with OpenAI GPT-4
- **Backend**: Flask (Python)
- **Frontend**: React with TypeScript
- **Database**: SQLite (development) / PostgreSQL (production)
- **Containerization**: Docker & Docker Compose

## 📊 Key Features

- **Real-time Monitoring**: Continuous pipeline health checks
- **Intelligent Diagnosis**: AI-powered root cause analysis
- **Safe Auto-remediation**: Configurable fix strategies with human oversight
- **Visual Dashboard**: Real-time pipeline status and agent reasoning
- **Audit Trail**: Complete history of failures and fixes
- **Extensible Design**: Easy to add new failure scenarios and agents

## 🤝 Contributing

Welcome to the contributions! To get started:

1. Fork this repository to your own GitHub account.
2. Create a new branch for your feature or bugfix.
3. Make your changes and ensure they follow the project's coding standards.
4. Add or update tests as needed.
5. Commit and push your changes to your fork.
6. Open a pull request with a clear description of your changes.

Please review existing issues and pull requests to avoid duplication. For major changes, open an issue first to discuss your proposal.

- **Copilot Users**: Please review `.github/copilot-instructions.md` for workspace-specific Copilot usage guidelines before submitting code.
