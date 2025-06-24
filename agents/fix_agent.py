"""
Fix Agent

This agent is responsible for:
1. Implementing safe auto-remediation strategies
2. Applying fixes based on diagnosis results
3. Monitoring fix effectiveness
4. Rolling back changes if needed
"""

import logging
import json
import requests
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class FixStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class FixType(Enum):
    SCHEMA_UPDATE = "schema_update"
    DATA_TRANSFORMATION = "data_transformation"
    RETRY_TASK = "retry_task"
    CONFIG_UPDATE = "config_update"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class FixAction:
    """Represents a fix action to be applied"""
    fix_type: FixType
    description: str
    parameters: Dict[str, Any]
    safety_level: str
    estimated_duration: int  # seconds
    rollback_plan: str

@dataclass
class FixResult:
    """Result of applying a fix"""
    fix_id: str
    status: FixStatus
    applied_fix: FixAction
    start_time: str
    end_time: Optional[str]
    success: bool
    error_message: Optional[str]
    rollback_applied: bool = False
    verification_result: Optional[Dict[str, Any]] = None

class FixAgent:
    """AI-powered fix agent for pipeline failures"""
    
    def __init__(self, airflow_api_url: str = "http://localhost:8080", flask_api_url: str = "http://localhost:5000"):
        self.airflow_api_url = airflow_api_url
        self.flask_api_url = flask_api_url
        self.fix_history: List[FixResult] = []
        self.active_fixes: Dict[str, FixResult] = {}
        
        # Fix strategies for different error types
        self.fix_strategies = {
            'schema_validation': self._get_schema_fix_strategies,
            'connection_error': self._get_connection_fix_strategies,
            'data_type_error': self._get_data_type_fix_strategies,
            'missing_field': self._get_missing_field_fix_strategies
        }
    
    def apply_fix(self, diagnosis_result: Dict[str, Any], failure_data: Dict[str, Any]) -> FixResult:
        """
        Apply a fix based on diagnosis results
        """
        try:
            logger.info(f"Applying fix for diagnosis: {diagnosis_result}")
            
            # Generate fix ID
            fix_id = f"fix_{int(time.time())}_{failure_data.get('task_id', 'unknown')}"
            
            # Determine appropriate fix strategy
            fix_action = self._determine_fix_strategy(diagnosis_result, failure_data)
            
            # Create fix result
            fix_result = FixResult(
                fix_id=fix_id,
                status=FixStatus.IN_PROGRESS,
                applied_fix=fix_action,
                start_time=datetime.now().isoformat(),
                end_time=None,
                success=False,
                error_message=None
            )
            
            # Store active fix
            self.active_fixes[fix_id] = fix_result
            
            # Apply the fix
            success = self._execute_fix(fix_action, failure_data)
            
            # Update fix result
            fix_result.end_time = datetime.now().isoformat()
            fix_result.success = success
            
            if success:
                fix_result.status = FixStatus.SUCCESS
                # Verify the fix
                verification_result = self._verify_fix(fix_action, failure_data)
                fix_result.verification_result = verification_result
            else:
                fix_result.status = FixStatus.FAILED
                fix_result.error_message = "Fix execution failed"
            
            # Store in history
            self.fix_history.append(fix_result)
            
            # Remove from active fixes
            if fix_id in self.active_fixes:
                del self.active_fixes[fix_id]
            
            return fix_result
            
        except Exception as e:
            logger.error(f"Error applying fix: {str(e)}")
            # Create failed fix result
            fix_result = FixResult(
                fix_id=f"fix_{int(time.time())}",
                status=FixStatus.FAILED,
                applied_fix=FixAction(
                    fix_type=FixType.MANUAL_INTERVENTION,
                    description="Fix application failed",
                    parameters={},
                    safety_level="unsafe",
                    estimated_duration=0,
                    rollback_plan="Manual intervention required"
                ),
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat(),
                success=False,
                error_message=str(e)
            )
            
            self.fix_history.append(fix_result)
            return fix_result
    
    def _determine_fix_strategy(self, diagnosis_result: Dict[str, Any], failure_data: Dict[str, Any]) -> FixAction:
        """
        Determine the best fix strategy based on diagnosis
        """
        error_type = failure_data.get('error_type', 'unknown')
        suggested_fixes = diagnosis_result.get('suggested_fixes', [])
        safety_level = diagnosis_result.get('remediation_safety', 'risky')
        
        # Get available strategies for this error type
        if error_type in self.fix_strategies:
            strategies = self.fix_strategies[error_type](failure_data, suggested_fixes)
        else:
            strategies = [self._create_manual_intervention_fix()]
        
        # Select the safest strategy that matches suggestions
        for strategy in strategies:
            if strategy.safety_level == 'safe' or safety_level == 'safe':
                return strategy
        
        # Fallback to manual intervention
        return self._create_manual_intervention_fix()
    
    def _get_schema_fix_strategies(self, failure_data: Dict[str, Any], suggested_fixes: List[str]) -> List[FixAction]:
        """Get fix strategies for schema validation errors"""
        strategies = []
        
        # Strategy 1: Update schema to match actual data
        strategies.append(FixAction(
            fix_type=FixType.SCHEMA_UPDATE,
            description="Update schema definition to match actual data structure",
            parameters={
                'action': 'update_schema',
                'dag_id': failure_data.get('dag_id'),
                'task_id': failure_data.get('task_id')
            },
            safety_level='safe',
            estimated_duration=60,
            rollback_plan="Restore original schema definition"
        ))
        
        # Strategy 2: Add data transformation
        strategies.append(FixAction(
            fix_type=FixType.DATA_TRANSFORMATION,
            description="Add data transformation to handle schema mismatches",
            parameters={
                'action': 'add_transformation',
                'transform_type': 'schema_adaptation'
            },
            safety_level='safe',
            estimated_duration=120,
            rollback_plan="Remove added transformation step"
        ))
        
        return strategies
    
    def _get_connection_fix_strategies(self, failure_data: Dict[str, Any], suggested_fixes: List[str]) -> List[FixAction]:
        """Get fix strategies for connection errors"""
        strategies = []
        
        # Strategy 1: Retry with exponential backoff
        strategies.append(FixAction(
            fix_type=FixType.RETRY_TASK,
            description="Retry failed task with exponential backoff",
            parameters={
                'action': 'retry_task',
                'max_retries': 3,
                'backoff_factor': 2
            },
            safety_level='safe',
            estimated_duration=300,
            rollback_plan="Stop retry attempts"
        ))
        
        # Strategy 2: Update timeout configuration
        strategies.append(FixAction(
            fix_type=FixType.CONFIG_UPDATE,
            description="Increase timeout settings for API calls",
            parameters={
                'action': 'update_timeout',
                'timeout_seconds': 60
            },
            safety_level='risky',
            estimated_duration=30,
            rollback_plan="Restore original timeout settings"
        ))
        
        return strategies
    
    def _get_data_type_fix_strategies(self, failure_data: Dict[str, Any], suggested_fixes: List[str]) -> List[FixAction]:
        """Get fix strategies for data type errors"""
        strategies = []
        
        # Strategy 1: Add data type conversion
        strategies.append(FixAction(
            fix_type=FixType.DATA_TRANSFORMATION,
            description="Add data type conversion logic",
            parameters={
                'action': 'add_type_conversion',
                'conversion_rules': 'auto_detect'
            },
            safety_level='safe',
            estimated_duration=90,
            rollback_plan="Remove type conversion logic"
        ))
        
        return strategies
    
    def _get_missing_field_fix_strategies(self, failure_data: Dict[str, Any], suggested_fixes: List[str]) -> List[FixAction]:
        """Get fix strategies for missing field errors"""
        strategies = []
        
        # Strategy 1: Add default values
        strategies.append(FixAction(
            fix_type=FixType.DATA_TRANSFORMATION,
            description="Add default values for missing fields",
            parameters={
                'action': 'add_default_values',
                'default_strategy': 'null_safe'
            },
            safety_level='safe',
            estimated_duration=60,
            rollback_plan="Remove default value logic"
        ))
        
        return strategies
    
    def _create_manual_intervention_fix(self) -> FixAction:
        """Create a manual intervention fix action"""
        return FixAction(
            fix_type=FixType.MANUAL_INTERVENTION,
            description="Manual intervention required - AI cannot safely apply fix",
            parameters={
                'action': 'notify_human',
                'priority': 'high'
            },
            safety_level='unsafe',
            estimated_duration=0,
            rollback_plan="Manual intervention required"
        )
    
    def _execute_fix(self, fix_action: FixAction, failure_data: Dict[str, Any]) -> bool:
        """
        Execute the fix action
        """
        try:
            logger.info(f"Executing fix: {fix_action.description}")
            
            if fix_action.fix_type == FixType.SCHEMA_UPDATE:
                return self._execute_schema_update(fix_action, failure_data)
            
            elif fix_action.fix_type == FixType.DATA_TRANSFORMATION:
                return self._execute_data_transformation(fix_action, failure_data)
            
            elif fix_action.fix_type == FixType.RETRY_TASK:
                return self._execute_retry_task(fix_action, failure_data)
            
            elif fix_action.fix_type == FixType.CONFIG_UPDATE:
                return self._execute_config_update(fix_action, failure_data)
            
            elif fix_action.fix_type == FixType.MANUAL_INTERVENTION:
                return self._execute_manual_intervention(fix_action, failure_data)
            
            else:
                logger.error(f"Unknown fix type: {fix_action.fix_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing fix: {str(e)}")
            return False
    
    def _execute_schema_update(self, fix_action: FixAction, failure_data: Dict[str, Any]) -> bool:
        """Execute schema update fix"""
        try:
            dag_id = fix_action.parameters.get('dag_id')
            task_id = fix_action.parameters.get('task_id')
            logger.info(f"[FixAgent] Preparing to update schema for DAG {dag_id}, task {task_id}")
            update_url = f"{self.flask_api_url}/api/update_schema"
            payload = {
                'dag_id': dag_id,
                'task_id': task_id,
                'action': 'update_schema',
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"[FixAgent] Sending schema update request to {update_url} with payload: {payload}")
            response = requests.post(update_url, json=payload, timeout=30)
            logger.info(f"[FixAgent] Schema update response: {response.status_code} {response.text}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"[FixAgent] Schema update failed: {str(e)}")
            return False
    
    def _execute_data_transformation(self, fix_action: FixAction, failure_data: Dict[str, Any]) -> bool:
        """Execute data transformation fix"""
        try:
            transform_type = fix_action.parameters.get('transform_type', 'unknown')
            logger.info(f"[FixAgent] Adding data transformation: {transform_type}")
            transform_url = f"{self.flask_api_url}/api/add_transformation"
            payload = {
                'transform_type': transform_type,
                'parameters': fix_action.parameters,
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"[FixAgent] Sending data transformation request to {transform_url} with payload: {payload}")
            response = requests.post(transform_url, json=payload, timeout=30)
            logger.info(f"[FixAgent] Data transformation response: {response.status_code} {response.text}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"[FixAgent] Data transformation failed: {str(e)}")
            return False
    
    def _execute_retry_task(self, fix_action: FixAction, failure_data: Dict[str, Any]) -> bool:
        """Execute task retry fix"""
        try:
            logger.info(f"[FixAgent] Retrying task with action: {fix_action.parameters}")
            retry_url = f"{self.flask_api_url}/api/retry_task"
            payload = {
                'parameters': fix_action.parameters,
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"[FixAgent] Sending retry task request to {retry_url} with payload: {payload}")
            response = requests.post(retry_url, json=payload, timeout=30)
            logger.info(f"[FixAgent] Retry task response: {response.status_code} {response.text}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"[FixAgent] Retry task failed: {str(e)}")
            return False

    def _execute_config_update(self, fix_action: FixAction, failure_data: Dict[str, Any]) -> bool:
        """Execute config update fix"""
        try:
            logger.info(f"[FixAgent] Updating config with action: {fix_action.parameters}")
            config_url = f"{self.flask_api_url}/api/update_config"
            payload = {
                'parameters': fix_action.parameters,
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"[FixAgent] Sending config update request to {config_url} with payload: {payload}")
            response = requests.post(config_url, json=payload, timeout=30)
            logger.info(f"[FixAgent] Config update response: {response.status_code} {response.text}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"[FixAgent] Config update failed: {str(e)}")
            return False

    def _execute_manual_intervention(self, fix_action: FixAction, failure_data: Dict[str, Any]) -> bool:
        """Notify for manual intervention"""
        try:
            logger.info(f"[FixAgent] Notifying for manual intervention: {fix_action.parameters}")
            notify_url = f"{self.flask_api_url}/api/notify"
            payload = {
                'parameters': fix_action.parameters,
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"[FixAgent] Sending manual intervention notification to {notify_url} with payload: {payload}")
            response = requests.post(notify_url, json=payload, timeout=30)
            logger.info(f"[FixAgent] Manual intervention response: {response.status_code} {response.text}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"[FixAgent] Manual intervention notification failed: {str(e)}")
            return False
    
    def _verify_fix(self, fix_action: FixAction, failure_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify that the fix was successful
        """
        try:
            # Wait a bit for the fix to take effect
            time.sleep(5)
            
            # Check if the pipeline can run successfully now
            dag_id = failure_data.get('dag_id')
            task_id = failure_data.get('task_id')
            
            # Simulate verification by checking pipeline status
            verify_url = f"{self.flask_api_url}/api/verify_fix"
            payload = {
                'dag_id': dag_id,
                'task_id': task_id,
                'fix_type': fix_action.fix_type.value,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(verify_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'verified': True,
                    'verification_method': 'api_check',
                    'details': result
                }
            else:
                return {
                    'verified': False,
                    'verification_method': 'api_check',
                    'error': f"Verification failed with status {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Fix verification failed: {str(e)}")
            return {
                'verified': False,
                'verification_method': 'error',
                'error': str(e)
            }
    
    def rollback_fix(self, fix_id: str) -> bool:
        """
        Rollback a previously applied fix
        """
        try:
            # Find the fix in history
            fix_result = None
            for fix in self.fix_history:
                if fix.fix_id == fix_id:
                    fix_result = fix
                    break
            
            if not fix_result:
                logger.error(f"Fix {fix_id} not found")
                return False
            
            logger.info(f"Rolling back fix: {fix_result.applied_fix.description}")
            
            # Execute rollback based on fix type
            rollback_success = self._execute_rollback(fix_result.applied_fix)
            
            if rollback_success:
                fix_result.status = FixStatus.ROLLED_BACK
                fix_result.rollback_applied = True
                logger.info(f"Successfully rolled back fix {fix_id}")
            else:
                logger.error(f"Failed to rollback fix {fix_id}")
            
            return rollback_success
            
        except Exception as e:
            logger.error(f"Error during rollback: {str(e)}")
            return False
    
    def _execute_rollback(self, fix_action: FixAction) -> bool:
        """
        Execute rollback for a specific fix action
        """
        try:
            rollback_url = f"{self.flask_api_url}/api/rollback"
            payload = {
                'fix_type': fix_action.fix_type.value,
                'rollback_plan': fix_action.rollback_plan,
                'parameters': fix_action.parameters,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(rollback_url, json=payload, timeout=30)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Rollback execution failed: {str(e)}")
            return False
    
    def get_fix_summary(self) -> Dict[str, Any]:
        """Get a summary of recent fixes"""
        now = datetime.now()
        last_24h = now.timestamp() - (24 * 3600)
        
        recent_fixes = []
        for fix in self.fix_history:
            try:
                fix_timestamp = datetime.fromisoformat(fix.start_time).timestamp()
                if fix_timestamp > last_24h:
                    recent_fixes.append(fix)
            except:
                continue
        
        status_counts = {}
        type_counts = {}
        for fix in recent_fixes:
            status_counts[fix.status.value] = status_counts.get(fix.status.value, 0) + 1
            type_counts[fix.applied_fix.fix_type.value] = type_counts.get(fix.applied_fix.fix_type.value, 0) + 1
        
        return {
            'total_fixes_24h': len(recent_fixes),
            'status_distribution': status_counts,
            'type_distribution': type_counts,
            'success_rate': len([f for f in recent_fixes if f.success]) / len(recent_fixes) if recent_fixes else 0,
            'timestamp': now.isoformat()
        }