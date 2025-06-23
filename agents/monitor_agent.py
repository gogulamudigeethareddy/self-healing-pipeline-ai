"""
Monitor Agent

This agent is responsible for:
1. Detecting pipeline failures from webhooks
2. Analyzing failure patterns
3. Triggering the diagnosis agent when needed
"""

import logging
import json
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class FailureSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class FailureEvent:
    """Represents a pipeline failure event"""
    dag_id: str
    task_id: str
    execution_date: str
    error_message: str
    error_type: str
    severity: FailureSeverity
    timestamp: str
    retry_count: int = 0
    resolved: bool = False

class MonitorAgent:
    """AI-powered monitoring agent for pipeline failures"""
    
    def __init__(self, api_base_url: str = "http://localhost:5000"):
        self.api_base_url = api_base_url
        self.failure_history: List[FailureEvent] = []
        self.alert_thresholds = {
            'consecutive_failures': 3,
            'failure_rate': 0.2,  # 20%
            'time_window_hours': 24
        }
    
    def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming webhook data from failed pipeline tasks
        """
        try:
            logger.info(f"Processing webhook data: {webhook_data}")
            
            # Create failure event
            failure_event = self._create_failure_event(webhook_data)
            
            # Analyze failure severity
            severity = self._analyze_failure_severity(failure_event)
            failure_event.severity = severity
            
            # Store failure event
            self.failure_history.append(failure_event)
            
            # Check if intervention is needed
            should_intervene = self._should_intervene(failure_event)
            
            if should_intervene:
                # Trigger diagnosis agent
                diagnosis_result = self._trigger_diagnosis(failure_event)
                
                return {
                    'status': 'intervention_triggered',
                    'failure_event': failure_event.__dict__,
                    'diagnosis_triggered': True,
                    'diagnosis_result': diagnosis_result,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'monitored',
                    'failure_event': failure_event.__dict__,
                    'intervention_triggered': False,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            raise
    
    def _create_failure_event(self, webhook_data: Dict[str, Any]) -> FailureEvent:
        """Create a failure event from webhook data"""
        return FailureEvent(
            dag_id=webhook_data.get('dag_id', 'unknown'),
            task_id=webhook_data.get('task_id', 'unknown'),
            execution_date=webhook_data.get('execution_date', ''),
            error_message=webhook_data.get('error_message', ''),
            error_type=webhook_data.get('error_type', 'unknown'),
            severity=FailureSeverity.MEDIUM,  # Default severity
            timestamp=webhook_data.get('timestamp', datetime.now().isoformat())
        )
    
    def _analyze_failure_severity(self, failure_event: FailureEvent) -> FailureSeverity:
        """
        Analyze the severity of a failure based on multiple factors
        """
        # Check error type
        if failure_event.error_type == 'schema_validation':
            # Schema validation failures are usually medium severity
            base_severity = FailureSeverity.MEDIUM
        elif failure_event.error_type == 'connection_error':
            # Connection errors might be high severity
            base_severity = FailureSeverity.HIGH
        else:
            base_severity = FailureSeverity.MEDIUM
        
        # Check retry count
        if failure_event.retry_count >= 3:
            base_severity = FailureSeverity.HIGH
        
        # Check if this is a recurring failure
        recent_failures = self._get_recent_failures(
            task_id=failure_event.task_id,
            hours=self.alert_thresholds['time_window_hours']
        )
        
        if len(recent_failures) >= self.alert_thresholds['consecutive_failures']:
            base_severity = FailureSeverity.CRITICAL
        
        return base_severity
    
    def _should_intervene(self, failure_event: FailureEvent) -> bool:
        """
        Determine if AI intervention is needed
        """
        # Always intervene for critical failures
        if failure_event.severity == FailureSeverity.CRITICAL:
            return True
        
        # Intervene for high severity failures
        if failure_event.severity == FailureSeverity.HIGH:
            return True
        
        # Check failure patterns
        recent_failures = self._get_recent_failures(
            task_id=failure_event.task_id,
            hours=self.alert_thresholds['time_window_hours']
        )
        
        # Intervene if we have multiple recent failures
        if len(recent_failures) >= 2:
            return True
        
        # Intervene for schema validation failures (common and fixable)
        if failure_event.error_type == 'schema_validation':
            return True
        
        return False
    
    def _get_recent_failures(self, task_id: str, hours: int) -> List[FailureEvent]:
        """Get recent failures for a specific task"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        recent_failures = []
        for failure in self.failure_history:
            try:
                failure_timestamp = datetime.fromisoformat(failure.timestamp).timestamp()
                if (failure_timestamp > cutoff_time and 
                    failure.task_id == task_id and 
                    not failure.resolved):
                    recent_failures.append(failure)
            except:
                continue
        
        return recent_failures
    
    def _trigger_diagnosis(self, failure_event: FailureEvent) -> Dict[str, Any]:
        """
        Trigger the diagnosis agent to analyze the failure
        """
        try:
            diagnosis_url = f"{self.api_base_url}/api/diagnose"
            
            payload = {
                'failure_event': failure_event.__dict__,
                'failure_history': [f.__dict__ for f in self.failure_history[-10:]],  # Last 10 failures
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(diagnosis_url, json=payload, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to trigger diagnosis: {str(e)}")
            return {
                'status': 'error',
                'message': f"Failed to trigger diagnosis: {str(e)}"
            }
    
    def get_failure_summary(self) -> Dict[str, Any]:
        """Get a summary of recent failures"""
        now = datetime.now()
        last_24h = now.timestamp() - (24 * 3600)
        
        recent_failures = []
        for failure in self.failure_history:
            try:
                failure_timestamp = datetime.fromisoformat(failure.timestamp).timestamp()
                if failure_timestamp > last_24h:
                    recent_failures.append(failure)
            except:
                continue
        
        severity_counts = {}
        for failure in recent_failures:
            severity = failure.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_failures_24h': len(recent_failures),
            'severity_distribution': severity_counts,
            'unresolved_failures': len([f for f in recent_failures if not f.resolved]),
            'timestamp': now.isoformat()
        }
    
    def mark_failure_resolved(self, failure_id: str) -> bool:
        """Mark a failure as resolved"""
        for failure in self.failure_history:
            if (failure.dag_id == failure_id or 
                f"{failure.dag_id}_{failure.task_id}_{failure.execution_date}" == failure_id):
                failure.resolved = True
                return True
        return False 