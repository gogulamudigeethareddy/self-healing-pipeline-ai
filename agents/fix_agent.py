"""
Fix Agent (CrewAI-powered)

Applies fixes based on diagnosis results using CrewAI agents.
"""

import logging
from datetime import datetime
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

class FixAgent:
    """Applies fixes to pipeline failures using CrewAI agents."""
    def __init__(self, flask_api_url: str = "http://localhost:5000", openai_api_key: str = None):
        self.flask_api_url = flask_api_url
        self.fix_history: List[Dict[str, Any]] = []
        self.openai_api_key = openai_api_key
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1, api_key=openai_api_key) if CREWAI_AVAILABLE and openai_api_key else None

    def apply_fix(self, diagnosis: Dict[str, Any], failure: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a fix based on diagnosis using CrewAI."""
        logger.info(f"Applying fix: {diagnosis}")
        if CREWAI_AVAILABLE and self.llm:
            fix = self._crew_plan_fix(diagnosis, failure)
        else:
            fix = self._choose_fix(diagnosis)
        result = self._execute_fix(fix, failure)
        record = {
            "fix": fix,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.fix_history.append(record)
        return record

    def _crew_plan_fix(self, diagnosis: Dict[str, Any], failure: Dict[str, Any]) -> str:
        try:
            # Define CrewAI agents
            planner_agent = Agent(
                role="Fix Planner",
                goal="Select the safest and most effective fix for the diagnosis",
                backstory="You are a senior engineer specializing in safe remediation.",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
            executor_agent = Agent(
                role="Fix Executor",
                goal="Apply the chosen fix to the pipeline",
                backstory="You are an automation expert for data pipelines.",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
            # Define CrewAI task
            task = Task(
                description=f"""
                Given the following diagnosis:
                - Root cause: {diagnosis.get('root_cause', 'unknown')}
                - Suggested fixes: {diagnosis.get('suggested_fixes', [])}
                - Confidence: {diagnosis.get('confidence', 'unknown')}
                Choose the best fix to apply and explain why. Return a string describing the fix action.
                """,
                agent=planner_agent,
                expected_output="A string describing the chosen fix action."
            )
            crew = Crew(agents=[planner_agent, executor_agent], tasks=[task], verbose=True)
            result = crew.kickoff()
            # Extract the fix string from result
            import re as _re
            match = _re.search(r'"([^"]+)"', str(result))
            if match:
                return match.group(1)
            return str(result)
        except Exception as e:
            logger.error(f"CrewAI fix planning failed: {e}")
            return self._choose_fix(diagnosis)

    def _choose_fix(self, diagnosis: Dict[str, Any]) -> str:
        fixes = diagnosis.get("suggested_fixes", [])
        return fixes[0] if fixes else "Manual intervention required"

    def _execute_fix(self, fix: str, failure: Dict[str, Any]) -> str:
        try:
            if "schema" in fix:
                return self._call_api("update_schema", failure)
            if "type conversion" in fix:
                return self._call_api("add_type_conversion", failure)
            if "missing field" in fix:
                return self._call_api("add_missing_field", failure)
            if "retry" in fix:
                return self._call_api("retry_task", failure)
            return "No automated fix applied"
        except Exception as e:
            logger.error(f"Fix execution failed: {e}")
            return f"Error: {e}"

    def _call_api(self, action: str, failure: Dict[str, Any]) -> str:
        url = f"{self.flask_api_url}/api/{action}"
        resp = requests.post(url, json=failure, timeout=10)
        if resp.status_code == 200:
            return "Success"
        return f"API error: {resp.status_code}"