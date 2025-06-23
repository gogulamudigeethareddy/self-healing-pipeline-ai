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
├── airflow/                 # Airflow DAGs and configurations
├── backend/                 # Flask API server
├── frontend/               # React dashboard
├── agents/                 # AI agent implementations
├── scripts/                # Demo and utility scripts
├── data/                   # Sample data and schemas
├── docs/                   # Documentation and presentations
└── docker-compose.yml      # Service orchestration
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

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details