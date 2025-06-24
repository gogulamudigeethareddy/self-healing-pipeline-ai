# GitHub Copilot Instructions for Self-Healing Data Pipeline AI Workspace

## Purpose
This document provides guidelines and best practices for using GitHub Copilot in the `self-healing-pipeline-ai` workspace. Follow these instructions to ensure code consistency, maintainability, and alignment with the project's architecture.

---

## 1. General Guidelines
- **Follow the Architecture**: Adhere to the modular, agent-based, and API-driven architecture as described in `docs/ARCHITECTURE.md`.
- **Separation of Concerns**: Keep Airflow DAGs, AI agents, backend API, and frontend code in their respective directories.
- **Logging**: Use centralized logging (`logs/pipeline.log`) for all agent and pipeline actions.
- **Configuration**: Use environment variables for secrets and configuration. Do not hardcode sensitive data.

---

## 2. Python (Backend, Agents, Airflow)
- **Python Version**: Use Python 3.8+ features only.
- **Dependencies**: Add new packages to the appropriate `requirements.txt`.
- **Type Hints**: Use type hints for all function signatures.
- **Docstrings**: Document all public functions and classes.
- **Error Handling**: Ensure robust error handling and avoid exposing sensitive information in logs or API responses.
- **AI Agent Design**: Follow the agent workflows (Monitor, Diagnose, Fix) as described in the architecture.

---

## 3. Flask API
- **Endpoints**: Implement endpoints as described in the architecture (`/webhook`, `/api/status`, `/api/logs`, `/api/feedback`, `/api/employees`).
- **Input Validation**: Validate all incoming data.
- **CORS**: Restrict to localhost for development.
- **Rate Limiting**: Apply to all public endpoints.

---

## 4. React Frontend
- **Component Structure**: Place new components in `frontend/src/components/`.
- **TypeScript**: Use TypeScript for all React code.
- **UI Library**: Use Material-UI for UI components.
- **API Calls**: Use Axios for HTTP requests.
- **State Management**: Use React hooks and context as needed.

---

## 5. Airflow DAGs
- **Location**: Place DAGs in `airflow/dags/`.
- **Task Design**: Use modular tasks (fetch, validate, transform, load).
- **Error Handling**: Ensure failures trigger the webhook for agent intervention.

---

## 6. Security & Best Practices
- **No Sensitive Data in Code**: Use `.env` or environment variables for secrets.
- **Sanitize Logs**: Remove sensitive data from logs.
- **Access Control**: Restrict access to local development by default.

---

## 7. Documentation
- **Update Docs**: Update `ARCHITECTURE.md` and `SETUP_AND_RUN.md` when making significant changes.
- **Code Comments**: Use clear comments for complex logic.

---

## 8. Contribution
- **Pull Requests**: Ensure all PRs are reviewed and pass tests.
- **Testing**: Add or update tests for new features and bug fixes.

---

## 9. Naming Conventions
- **Python**: snake_case for variables/functions, PascalCase for classes.
- **React/TypeScript**: PascalCase for components, camelCase for props and variables.

---

## 10. Additional Notes
- **Extensibility**: Design new features to be modular and easily extensible.
- **Human-in-the-Loop**: Where required, provide clear interfaces for manual intervention.

---

For more details, refer to `docs/ARCHITECTURE.md` and other documentation files in the `docs/` directory.
