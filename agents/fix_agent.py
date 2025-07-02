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
            import os, json
            approval_state_path = os.path.join(os.path.dirname(__file__), '../backend/approval_state.json')
            approval_dir = os.path.dirname(approval_state_path)
            if not os.path.exists(approval_dir):
                os.makedirs(approval_dir, exist_ok=True)
            # Always check for any approved pending fix and apply it, regardless of current failure
            try:
                with open(approval_state_path, 'r') as f:
                    approval_state = json.load(f)
                if approval_state.get("approved") and approval_state.get("pending_fix"):
                    # Patch the data file if possible
                    data_path = os.path.join(os.path.dirname(__file__), '../data/sample_employees.json')
                    with open(data_path, 'r') as f:
                        employees = json.load(f)
                    import re
                    # Try to extract missing field from the last failure in approval_state
                    failure_obj = approval_state.get("failure") or failure
                    match = re.search(r"Missing required field '([a-zA-Z0-9_]+)'", failure_obj.get("error_message", ""))
                    if match:
                        missing_field = match.group(1)
                        for emp in employees:
                            if missing_field not in emp:
                                emp[missing_field] = f"autofix_{missing_field}@example.com" if missing_field == "email" else f"autofix_{missing_field}"
                        with open(data_path, 'w') as f:
                            json.dump(employees, f, indent=2)
                        logger.info(f"Patched missing field '{missing_field}' in sample_employees.json via FixAgent after approval.")
                    # Reset approval state
                    with open(approval_state_path, 'w') as f:
                        json.dump({"pending_fix": None, "failure": None, "approved": False}, f)
                    return f"Patched missing field after approval and reset approval state."
            except Exception as e:
                logger.error(f"Error applying approved fix: {e}")
            # Existing logic for schema/type fixes
            if "schema" in fix:
                return self._call_api("update_schema", failure)
            if "type conversion" in fix:
                return self._call_api("add_type_conversion", failure)
            if "missing field" in fix:
                return self._call_api("add_missing_field", failure)
            if "retry" in fix:
                return self._call_api("retry_task", failure)
            # If not handled above, always set a pending fix for human approval
            try:
                with open(approval_state_path, 'w') as f:
                    json.dump({"pending_fix": fix, "failure": failure, "approved": False}, f)
                logger.info(f"Stored pending fix for human approval: {fix}")
                return f"Pending human approval: {fix}"
            except Exception as e:
                logger.error(f"Failed to store pending fix: {e}")
                return f"Failed to store pending fix: {e}"
        except Exception as e:
            logger.error(f"Fix execution failed: {e}")
            return f"Error: {e}"

    def _notify_manual_intervention(self, fix: str, failure: Dict[str, Any]) -> None:
        try:
            url = f"{self.flask_api_url}/api/notify"
            payload = {"fix": fix, "failure": failure}
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Failed to notify for manual intervention: {e}")

    def _call_api(self, action: str, failure: Dict[str, Any]) -> str:
        """
        Call the backend Flask API to perform a fix action.
        """
        import requests
        import os
        import json
        try:
            url = f"{self.flask_api_url}/api/fix_action"
            payload = {"action": action, "failure": failure}
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Called backend API for action '{action}': {response.text}")
            return f"API call '{action}' successful: {response.text}"
        except Exception as e:
            logger.error(f"API call '{action}' failed: {e}")
            return f"API call '{action}' failed: {e}"