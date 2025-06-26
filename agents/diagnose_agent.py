"""
Diagnose Agent (CrewAI-powered)

Analyzes failure logs and suggests fixes using CrewAI agents.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
import re

# CrewAI imports
try:
    from crewai import Agent, Task, Crew
    from langchain_openai import ChatOpenAI
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class DiagnoseAgent:
    """Diagnoses pipeline failures and suggests fixes using CrewAI agents."""
    def __init__(self, openai_api_key: str = None):
        self.diagnosis_history: List[Dict[str, Any]] = []
        self.openai_api_key = openai_api_key
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1, api_key=openai_api_key) if CREWAI_AVAILABLE and openai_api_key else None

    def diagnose_failure(self, failure: Dict[str, Any]) -> Dict[str, Any]:
        """Diagnose a pipeline failure and suggest fixes using CrewAI."""
        logger.info(f"Diagnosing failure: {failure}")
        if CREWAI_AVAILABLE and self.llm:
            result = self._crew_diagnose(failure)
        else:
            result = self._pattern_diagnose(failure)
        result["timestamp"] = datetime.now().isoformat()
        self.diagnosis_history.append(result)
        return result

    def _crew_diagnose(self, failure: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Define CrewAI agents
            root_cause_agent = Agent(
                role="Root Cause Analyst",
                goal="Analyze failure logs and identify the root cause",
                backstory="You are an expert in root cause analysis for data pipelines.",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
            fix_suggester_agent = Agent(
                role="Fix Suggester",
                goal="Suggest actionable fixes for pipeline failures",
                backstory="You are a senior data engineer specializing in remediation.",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
            # Define CrewAI task
            task = Task(
                description=f"""
                Analyze the following pipeline failure:
                - DAG ID: {failure.get('dag_id', 'unknown')}
                - Task ID: {failure.get('task_id', 'unknown')}
                - Error: {failure.get('error_message', 'unknown')}
                - Type: {failure.get('error_type', 'unknown')}
                - Execution Date: {failure.get('execution_date', 'unknown')}
                Provide a JSON object with: root_cause (str), suggested_fixes (list of str), and confidence (low/medium/high).
                """,
                agent=root_cause_agent,
                expected_output="A JSON object with: root_cause, suggested_fixes, confidence"
            )
            crew = Crew(agents=[root_cause_agent, fix_suggester_agent], tasks=[task], verbose=True)
            result = crew.kickoff()
            # Try to parse JSON from result
            import json
            import re as _re
            match = _re.search(r'\{.*\}', str(result), _re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"root_cause": "CrewAI output parsing failed", "suggested_fixes": ["Manual review required"], "confidence": "low"}
        except Exception as e:
            logger.error(f"CrewAI diagnosis failed: {e}")
            return {"root_cause": f"CrewAI error: {e}", "suggested_fixes": ["Manual review required"], "confidence": "low"}

    def _pattern_diagnose(self, failure: Dict[str, Any]) -> Dict[str, Any]:
        error = failure.get("error_message", "").lower()
        if "schema" in error or "validation" in error:
            return self._diagnose_schema_error(error)
        elif "connection" in error or "timeout" in error:
            return self._diagnose_connection_error(error)
        elif "type" in error or "integer" in error or "string" in error:
            return self._diagnose_type_error(error)
        elif "missing" in error or "required" in error:
            return self._diagnose_missing_field_error(error)
        else:
            return {"root_cause": "Unknown error", "suggested_fixes": ["Manual review required"], "confidence": "low"}

    def _diagnose_schema_error(self, error: str) -> Dict[str, Any]:
        import re
        missing = re.findall(r"missing required field '([^']+)'", error)
        if missing:
            return {
                "root_cause": f"Missing fields: {', '.join(missing)}",
                "suggested_fixes": [f"Add missing field(s): {', '.join(missing)}", "Update schema"],
                "confidence": "high"
            }
        return {"root_cause": "Schema validation failed", "suggested_fixes": ["Review schema"], "confidence": "medium"}

    def _diagnose_connection_error(self, error: str) -> Dict[str, Any]:
        return {
            "root_cause": "Connection error",
            "suggested_fixes": ["Check API/network", "Retry with backoff"],
            "confidence": "medium"
        }

    def _diagnose_type_error(self, error: str) -> Dict[str, Any]:
        return {
            "root_cause": "Data type mismatch",
            "suggested_fixes": ["Add type conversion", "Check data source"],
            "confidence": "high"
        }

    def _diagnose_missing_field_error(self, error: str) -> Dict[str, Any]:
        return {
            "root_cause": "Missing required field",
            "suggested_fixes": ["Add missing field", "Provide default value"],
            "confidence": "high"
        }