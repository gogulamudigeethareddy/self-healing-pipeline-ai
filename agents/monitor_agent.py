"""
Monitor Agent (CrewAI-powered)

Detects pipeline failures, analyzes severity, and triggers diagnosis using CrewAI agents.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import requests

# CrewAI imports
try:
    from crewai import Agent, Task, Crew
    from langchain_openai import ChatOpenAI
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class MonitorAgent:
    """Monitors pipeline failures and triggers diagnosis using CrewAI agents."""
    def __init__(self, api_base_url: str = "http://localhost:5000", openai_api_key: str = None):
        self.api_base_url = api_base_url
        self.failure_history: List[Dict[str, Any]] = []
        self.alert_threshold = 3  # consecutive failures
        self.time_window = timedelta(hours=24)
        self.openai_api_key = openai_api_key
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1, api_key=openai_api_key) if CREWAI_AVAILABLE and openai_api_key else None

    def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming webhook data from failed pipeline tasks using CrewAI."""
        logger.info(f"Processing webhook: {webhook_data}")
        event = self._create_failure_event(webhook_data)
        self.failure_history.append(event)
        if self._should_intervene(event):
            diagnosis = self._crew_trigger_diagnosis(event)
            return {"status": "intervention_triggered", "diagnosis": diagnosis}
        return {"status": "monitored"}

    def _create_failure_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "dag_id": data.get("dag_id", "unknown"),
            "task_id": data.get("task_id", "unknown"),
            "execution_date": data.get("execution_date", ""),
            "error_message": data.get("error_message", ""),
            "error_type": data.get("error_type", "unknown"),
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "resolved": False,
        }

    def _should_intervene(self, event: Dict[str, Any]) -> bool:
        recent = [f for f in self.failure_history if f["task_id"] == event["task_id"] and not f["resolved"]
                  and datetime.fromisoformat(f["timestamp"]) > datetime.now() - self.time_window]
        return len(recent) >= self.alert_threshold or event["error_type"] in ("schema_validation", "connection_error")

    def _crew_trigger_diagnosis(self, event: Dict[str, Any]) -> Any:
        if not (CREWAI_AVAILABLE and self.llm):
            return self._fallback_trigger_diagnosis(event)
        try:
            # Define CrewAI agents
            monitor_agent = Agent(
                role="Failure Monitor",
                goal="Detect and summarize pipeline failures",
                backstory="You monitor data pipelines and escalate issues for diagnosis.",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
            diagnosis_agent = Agent(
                role="Diagnosis Specialist",
                goal="Analyze failure events and recommend next steps",
                backstory="You are an expert in diagnosing pipeline failures.",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
            # Define CrewAI task
            task = Task(
                description=f"""
                A pipeline failure occurred:
                - DAG ID: {event['dag_id']}
                - Task ID: {event['task_id']}
                - Error: {event['error_message']}
                - Type: {event['error_type']}
                - Time: {event['timestamp']}
                Recent history: {self.failure_history[-5:]}
                Please summarize the failure and recommend if diagnosis should be triggered, and what info to send.
                """,
                agent=monitor_agent,
                expected_output="A JSON object with: summary, should_diagnose (bool), and recommended_info (dict)"
            )
            crew = Crew(agents=[monitor_agent, diagnosis_agent], tasks=[task], verbose=True)
            result = crew.kickoff()
            return result
        except Exception as e:
            logger.error(f"CrewAI diagnosis trigger failed: {e}")
            return {"error": str(e)}

    def _fallback_trigger_diagnosis(self, event: Dict[str, Any]) -> Any:
        # Fallback to API call if CrewAI is not available
        try:
            url = f"{self.api_base_url}/api/diagnose"
            payload = {"failure_event": event, "history": self.failure_history[-10:]}
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Diagnosis trigger failed: {e}")
            return {"error": str(e)}

    def mark_failure_resolved(self, dag_id: str, task_id: str) -> bool:
        for f in self.failure_history:
            if f["dag_id"] == dag_id and f["task_id"] == task_id:
                f["resolved"] = True
                return True
        return False