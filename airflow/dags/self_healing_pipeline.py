"""
Self-Healing Data Pipeline DAG

This DAG demonstrates an AI-powered self-healing data pipeline that:
1. Ingests JSON data from an API
2. Validates the schema
3. Transforms the data
4. Loads to target
5. Automatically detects and fixes failures using AI agents
"""

import json
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.models import Variable
from airflow.utils.trigger_rule import TriggerRule

# Configure logging
logger = logging.getLogger(__name__)

# Default arguments
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Expected schema for validation
EXPECTED_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "email": {"type": "string"},
        "department": {"type": "string"},
        "salary": {"type": "number"},
        "hire_date": {"type": "string"}
    },
    "required": ["id", "name", "email", "department", "salary", "hire_date"]
}

def fetch_api_data(**context) -> Dict[str, Any]:
    """
    Fetch data from mock API endpoint
    """
    try:
        # Simulate API call to get employee data
        api_url = "http://localhost:5000/api/employees"
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Successfully fetched {len(data)} records from API")
        
        # Store data in XCom for next task
        context['task_instance'].xcom_push(key='raw_data', value=data)
        
        return {
            'status': 'success',
            'record_count': len(data),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch API data: {str(e)}")
        raise

def validate_schema(**context) -> Dict[str, Any]:
    """
    Validate the schema of incoming data
    """
    try:
        # Get data from previous task
        raw_data = context['task_instance'].xcom_pull(task_ids='fetch_api_data', key='raw_data')
        
        if not raw_data:
            raise ValueError("No data received from previous task")
        
        validation_errors = []
        
        for i, record in enumerate(raw_data):
            # Check if all required fields are present
            for field in EXPECTED_SCHEMA['required']:
                if field not in record:
                    validation_errors.append(f"Record {i}: Missing required field '{field}'")
            
            # Check data types
            if 'id' in record and not isinstance(record['id'], int):
                validation_errors.append(f"Record {i}: 'id' must be integer, got {type(record['id'])}")
            
            if 'salary' in record and not isinstance(record['salary'], (int, float)):
                validation_errors.append(f"Record {i}: 'salary' must be number, got {type(record['salary'])}")
        
        if validation_errors:
            error_msg = f"Schema validation failed: {'; '.join(validation_errors)}"
            logger.error(error_msg)
            
            # Trigger webhook for AI agent intervention
            trigger_ai_webhook(error_msg, context)
            
            raise ValueError(error_msg)
        
        logger.info(f"Schema validation passed for {len(raw_data)} records")
        
        return {
            'status': 'success',
            'validated_records': len(raw_data),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Schema validation failed: {str(e)}")
        raise

def transform_data(**context) -> Dict[str, Any]:
    """
    Transform the validated data
    """
    try:
        raw_data = context['task_instance'].xcom_pull(task_ids='fetch_api_data', key='raw_data')
        
        # Convert to DataFrame for easier transformation
        df = pd.DataFrame(raw_data)
        
        # Apply transformations
        df['full_name'] = df['name'].str.upper()
        df['department_upper'] = df['department'].str.upper()
        df['salary_formatted'] = df['salary'].apply(lambda x: f"${x:,.2f}")
        df['processed_at'] = datetime.now().isoformat()
        
        # Convert back to list of dicts
        transformed_data = df.to_dict('records')
        
        # Store transformed data
        context['task_instance'].xcom_push(key='transformed_data', value=transformed_data)
        
        logger.info(f"Successfully transformed {len(transformed_data)} records")
        
        return {
            'status': 'success',
            'transformed_records': len(transformed_data),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Data transformation failed: {str(e)}")
        raise

def load_data(**context) -> Dict[str, Any]:
    """
    Load transformed data to target system
    """
    try:
        transformed_data = context['task_instance'].xcom_pull(task_ids='transform_data', key='transformed_data')
        
        # Simulate loading to database/file system
        # In real implementation, this would connect to actual target system
        
        # Save to JSON file for demo purposes
        output_file = f"/tmp/processed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(transformed_data, f, indent=2)
        
        logger.info(f"Successfully loaded {len(transformed_data)} records to {output_file}")
        
        return {
            'status': 'success',
            'loaded_records': len(transformed_data),
            'output_file': output_file,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Data loading failed: {str(e)}")
        raise

def trigger_ai_webhook(error_message: str, context: Dict[str, Any]) -> None:
    """
    Trigger webhook to notify AI agents of failure
    """
    try:
        webhook_url = Variable.get("ai_webhook_url", default_var="http://localhost:5000/webhook")
        
        payload = {
            'dag_id': context['dag'].dag_id,
            'task_id': context['task_instance'].task_id,
            'execution_date': context['execution_date'].isoformat(),
            'error_message': error_message,
            'error_type': 'schema_validation',
            'timestamp': datetime.now().isoformat()
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Successfully triggered AI webhook: {response.status_code}")
        
    except Exception as e:
        logger.error(f"Failed to trigger AI webhook: {str(e)}")

def on_failure_callback(context: Dict[str, Any]) -> None:
    """
    Callback function when any task fails
    """
    task_instance = context['task_instance']
    dag_id = context['dag'].dag_id
    task_id = task_instance.task_id
    execution_date = context['execution_date']
    
    logger.error(f"Task {task_id} in DAG {dag_id} failed at {execution_date}")
    
    # Trigger AI webhook for failure analysis
    trigger_ai_webhook(f"Task {task_id} failed", context)

# Create DAG
dag = DAG(
    'self_healing_pipeline',
    default_args=default_args,
    description='AI-Powered Self-Healing Data Pipeline',
    schedule_interval=timedelta(hours=1),
    catchup=False,
    tags=['ai', 'self-healing', 'data-pipeline'],
    on_failure_callback=on_failure_callback
)

# Define tasks
fetch_task = PythonOperator(
    task_id='fetch_api_data',
    python_callable=fetch_api_data,
    dag=dag
)

validate_task = PythonOperator(
    task_id='validate_schema',
    python_callable=validate_schema,
    dag=dag
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag
)

load_task = PythonOperator(
    task_id='load_data',
    python_callable=load_data,
    dag=dag
)

# Define task dependencies
fetch_task >> validate_task >> transform_task >> load_task 