"""
Diagnose Agent

This agent is responsible for:
1. Analyzing failure logs and error messages
2. Identifying root causes of pipeline failures
3. Suggesting potential fixes
4. Determining if auto-remediation is safe
"""

import logging
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

# Import CrewAI components
try:
    from crewai import Agent, Task, Crew
    from langchain_openai import ChatOpenAI
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logging.warning("CrewAI not available, using fallback diagnosis")

logger = logging.getLogger(__name__)

class DiagnosisConfidence(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class RemediationSafety(Enum):
    SAFE = "safe"
    RISKY = "risky"
    UNSAFE = "unsafe"

@dataclass
class DiagnosisResult:
    """Result of failure diagnosis"""
    root_cause: str
    confidence: DiagnosisConfidence
    suggested_fixes: List[str]
    remediation_safety: RemediationSafety
    reasoning: str
    timestamp: str
    requires_human_review: bool = False

class DiagnoseAgent:
    """AI-powered diagnosis agent for pipeline failures"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        self.diagnosis_history: List[DiagnosisResult] = []
        self.common_patterns = self._load_common_patterns()
        
        # Initialize AI model if available
        if CREWAI_AVAILABLE and openai_api_key:
            self.llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                api_key=openai_api_key
            )
        else:
            self.llm = None
    
    def diagnose_failure(self, failure_data: Dict[str, Any]) -> DiagnosisResult:
        """
        Diagnose a pipeline failure using AI analysis
        """
        try:
            logger.info(f"Diagnosing failure: {failure_data}")
            
            if self.llm and CREWAI_AVAILABLE:
                # Use AI-powered diagnosis
                result = self._ai_diagnose(failure_data)
            else:
                # Use pattern-based diagnosis
                result = self._pattern_diagnose(failure_data)
            
            # Store diagnosis result
            self.diagnosis_history.append(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error during diagnosis: {str(e)}")
            # Return fallback diagnosis
            return self._fallback_diagnosis(failure_data)
    
    def _ai_diagnose(self, failure_data: Dict[str, Any]) -> DiagnosisResult:
        """
        Use AI to diagnose the failure
        """
        try:
            # Create diagnosis agent
            diagnosis_agent = Agent(
                role='Pipeline Failure Diagnostician',
                goal='Analyze pipeline failures and identify root causes with high accuracy',
                backstory="""You are an expert data engineer with 10+ years of experience 
                diagnosing and fixing data pipeline failures. You have deep knowledge of 
                ETL processes, data validation, and common failure patterns.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
            # Create diagnosis task
            prompt = self._create_diagnosis_prompt(failure_data)
            logger.info(f"[OpenAI] Sending prompt to LLM: {prompt}")
            diagnosis_task = Task(
                description=prompt,
                agent=diagnosis_agent,
                expected_output="""A JSON object with:
                - root_cause: string describing the root cause
                - confidence: \"low\", \"medium\", or \"high\"
                - suggested_fixes: array of fix suggestions
                - remediation_safety: \"safe\", \"risky\", or \"unsafe\"
                - reasoning: detailed explanation
                - requires_human_review: boolean"""
            )
            # Create crew and execute
            crew = Crew(
                agents=[diagnosis_agent],
                tasks=[diagnosis_task],
                verbose=True
            )
            logger.info("[OpenAI] Executing LLM diagnosis via CrewAI...")
            result = crew.kickoff()
            logger.info(f"[OpenAI] LLM raw result: {result}")
            # Parse AI response
            return self._parse_ai_diagnosis(result, failure_data)
        except Exception as e:
            logger.error(f"[OpenAI] AI diagnosis failed: {str(e)}")
            return self._pattern_diagnose(failure_data)
    
    def _pattern_diagnose(self, failure_data: Dict[str, Any]) -> DiagnosisResult:
        """
        Use pattern matching to diagnose the failure
        """
        error_message = failure_data.get('error_message', '').lower()
        error_type = failure_data.get('error_type', '').lower()
        
        # Check for schema validation errors
        if 'schema' in error_message or 'validation' in error_message:
            return self._diagnose_schema_error(error_message, failure_data)
        
        # Check for connection errors
        if 'connection' in error_message or 'timeout' in error_message:
            return self._diagnose_connection_error(error_message, failure_data)
        
        # Check for data type errors
        if 'type' in error_message or 'integer' in error_message or 'string' in error_message:
            return self._diagnose_data_type_error(error_message, failure_data)
        
        # Check for missing field errors
        if 'missing' in error_message or 'required' in error_message:
            return self._diagnose_missing_field_error(error_message, failure_data)
        
        # Default diagnosis
        return DiagnosisResult(
            root_cause="Unknown error pattern",
            confidence=DiagnosisConfidence.LOW,
            suggested_fixes=["Review logs manually", "Check system resources"],
            remediation_safety=RemediationSafety.RISKY,
            reasoning=f"Unable to identify specific pattern in error: {error_message}",
            timestamp=datetime.now().isoformat(),
            requires_human_review=True
        )
    
    def _diagnose_schema_error(self, error_message: str, failure_data: Dict[str, Any]) -> DiagnosisResult:
        """Diagnose schema validation errors"""
        # Extract missing fields from error message
        missing_fields = re.findall(r"Missing required field '([^']+)'", error_message)
        
        if missing_fields:
            root_cause = f"Schema mismatch: Missing required fields: {', '.join(missing_fields)}"
            suggested_fixes = [
                f"Add missing field(s): {', '.join(missing_fields)}",
                "Update schema definition to match actual data",
                "Use data transformation to add default values"
            ]
        else:
            root_cause = "Schema validation failed - unknown field mismatch"
            suggested_fixes = [
                "Review and update schema definition",
                "Check data source for unexpected fields",
                "Implement schema evolution handling"
            ]
        
        return DiagnosisResult(
            root_cause=root_cause,
            confidence=DiagnosisConfidence.HIGH,
            suggested_fixes=suggested_fixes,
            remediation_safety=RemediationSafety.SAFE,
            reasoning=f"Schema validation error detected: {error_message}",
            timestamp=datetime.now().isoformat(),
            requires_human_review=False
        )
    
    def _diagnose_connection_error(self, error_message: str, failure_data: Dict[str, Any]) -> DiagnosisResult:
        """Diagnose connection-related errors"""
        if 'timeout' in error_message:
            root_cause = "API timeout - service may be overloaded or network issues"
            suggested_fixes = [
                "Increase timeout settings",
                "Implement retry logic with exponential backoff",
                "Check API service health"
            ]
        else:
            root_cause = "Connection failure - service unavailable or network issues"
            suggested_fixes = [
                "Check API endpoint availability",
                "Verify network connectivity",
                "Implement circuit breaker pattern"
            ]
        
        return DiagnosisResult(
            root_cause=root_cause,
            confidence=DiagnosisConfidence.MEDIUM,
            suggested_fixes=suggested_fixes,
            remediation_safety=RemediationSafety.RISKY,
            reasoning=f"Connection error detected: {error_message}",
            timestamp=datetime.now().isoformat(),
            requires_human_review=True
        )
    
    def _diagnose_data_type_error(self, error_message: str, failure_data: Dict[str, Any]) -> DiagnosisResult:
        """Diagnose data type validation errors"""
        # Extract field and expected type from error message
        type_match = re.search(r"'([^']+)' must be ([^,]+)", error_message)
        
        if type_match:
            field_name = type_match.group(1)
            expected_type = type_match.group(2)
            root_cause = f"Data type mismatch: Field '{field_name}' should be {expected_type}"
            suggested_fixes = [
                f"Add data type conversion for field '{field_name}'",
                "Update data source to provide correct data types",
                "Implement data validation and transformation"
            ]
        else:
            root_cause = "Data type validation failed"
            suggested_fixes = [
                "Review data type definitions",
                "Implement data type conversion logic",
                "Add data validation checks"
            ]
        
        return DiagnosisResult(
            root_cause=root_cause,
            confidence=DiagnosisConfidence.HIGH,
            suggested_fixes=suggested_fixes,
            remediation_safety=RemediationSafety.SAFE,
            reasoning=f"Data type error detected: {error_message}",
            timestamp=datetime.now().isoformat(),
            requires_human_review=False
        )
    
    def _diagnose_missing_field_error(self, error_message: str, failure_data: Dict[str, Any]) -> DiagnosisResult:
        """Diagnose missing field errors"""
        root_cause = "Required field missing from data source"
        suggested_fixes = [
            "Add missing field to data source",
            "Provide default value for missing field",
            "Update pipeline to handle optional fields"
        ]
        
        return DiagnosisResult(
            root_cause=root_cause,
            confidence=DiagnosisConfidence.HIGH,
            suggested_fixes=suggested_fixes,
            remediation_safety=RemediationSafety.SAFE,
            reasoning=f"Missing field error detected: {error_message}",
            timestamp=datetime.now().isoformat(),
            requires_human_review=False
        )
    
    def _create_diagnosis_prompt(self, failure_data: Dict[str, Any]) -> str:
        """Create a detailed prompt for AI diagnosis"""
        return f"""
        Analyze the following pipeline failure and provide a detailed diagnosis:
        
        Failure Details:
        - DAG ID: {failure_data.get('dag_id', 'unknown')}
        - Task ID: {failure_data.get('task_id', 'unknown')}
        - Error Type: {failure_data.get('error_type', 'unknown')}
        - Error Message: {failure_data.get('error_message', 'unknown')}
        - Execution Date: {failure_data.get('execution_date', 'unknown')}
        
        Recent Failure History:
        {json.dumps(failure_data.get('failure_history', []), indent=2)}
        
        Please provide a comprehensive diagnosis including:
        1. Root cause analysis
        2. Confidence level in the diagnosis
        3. Specific fix suggestions
        4. Safety assessment for auto-remediation
        5. Detailed reasoning
        
        Focus on practical, actionable insights that can help resolve the issue.
        """
    
    def _parse_ai_diagnosis(self, ai_result: str, failure_data: Dict[str, Any]) -> DiagnosisResult:
        """Parse AI diagnosis result"""
        try:
            # Try to extract JSON from AI response
            json_match = re.search(r'\{.*\}', ai_result, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                
                return DiagnosisResult(
                    root_cause=parsed.get('root_cause', 'AI analysis inconclusive'),
                    confidence=DiagnosisConfidence(parsed.get('confidence', 'medium')),
                    suggested_fixes=parsed.get('suggested_fixes', []),
                    remediation_safety=RemediationSafety(parsed.get('remediation_safety', 'risky')),
                    reasoning=parsed.get('reasoning', ai_result),
                    timestamp=datetime.now().isoformat(),
                    requires_human_review=parsed.get('requires_human_review', True)
                )
        except:
            pass
        
        # Fallback parsing
        return DiagnosisResult(
            root_cause="AI analysis completed",
            confidence=DiagnosisConfidence.MEDIUM,
            suggested_fixes=["Review AI analysis manually"],
            remediation_safety=RemediationSafety.RISKY,
            reasoning=ai_result,
            timestamp=datetime.now().isoformat(),
            requires_human_review=True
        )
    
    def _fallback_diagnosis(self, failure_data: Dict[str, Any]) -> DiagnosisResult:
        """Provide a fallback diagnosis when AI is unavailable"""
        return DiagnosisResult(
            root_cause="Diagnosis system unavailable",
            confidence=DiagnosisConfidence.LOW,
            suggested_fixes=["Manual investigation required"],
            remediation_safety=RemediationSafety.UNSAFE,
            reasoning="AI diagnosis system is not available, manual review needed",
            timestamp=datetime.now().isoformat(),
            requires_human_review=True
        )
    
    def _load_common_patterns(self) -> Dict[str, Any]:
        """Load common failure patterns for pattern matching"""
        return {
            'schema_validation': {
                'patterns': ['schema', 'validation', 'missing required field'],
                'confidence': 'high',
                'safety': 'safe'
            },
            'connection_error': {
                'patterns': ['connection', 'timeout', 'network'],
                'confidence': 'medium',
                'safety': 'risky'
            },
            'data_type_error': {
                'patterns': ['type', 'integer', 'string', 'number'],
                'confidence': 'high',
                'safety': 'safe'
            }
        }
    
    def get_diagnosis_summary(self) -> Dict[str, Any]:
        """Get a summary of recent diagnoses"""
        now = datetime.now()
        last_24h = now.timestamp() - (24 * 3600)
        
        recent_diagnoses = []
        for diagnosis in self.diagnosis_history:
            try:
                diagnosis_timestamp = datetime.fromisoformat(diagnosis.timestamp).timestamp()
                if diagnosis_timestamp > last_24h:
                    recent_diagnoses.append(diagnosis)
            except:
                continue
        
        confidence_counts = {}
        safety_counts = {}
        for diagnosis in recent_diagnoses:
            confidence_counts[diagnosis.confidence.value] = confidence_counts.get(diagnosis.confidence.value, 0) + 1
            safety_counts[diagnosis.remediation_safety.value] = safety_counts.get(diagnosis.remediation_safety.value, 0) + 1
        
        return {
            'total_diagnoses_24h': len(recent_diagnoses),
            'confidence_distribution': confidence_counts,
            'safety_distribution': safety_counts,
            'timestamp': now.isoformat()
        }