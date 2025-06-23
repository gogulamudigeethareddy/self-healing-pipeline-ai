#!/usr/bin/env python3
"""
Demo Script for AI-Powered Self-Healing Data Pipeline

This script simulates different failure scenarios to demonstrate
the self-healing capabilities of the pipeline.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
FLASK_API_URL = "http://localhost:5000"
AIRFLOW_API_URL = "http://localhost:8080"

def print_step(step, description):
    """Print a formatted step description"""
    print(f"\n{'='*60}")
    print(f"STEP {step}: {description}")
    print(f"{'='*60}")

def check_service(url, service_name):
    """Check if a service is running"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {service_name} is running at {url}")
            return True
        else:
            print(f"❌ {service_name} returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {service_name} is not accessible: {e}")
        return False

def simulate_schema_error():
    """Simulate a schema validation error by modifying the API response"""
    print_step(1, "Simulating Schema Validation Error")
    
    # First, get the normal response
    try:
        response = requests.get(f"{FLASK_API_URL}/api/employees")
        if response.status_code == 200:
            employees = response.json()
            print(f"✅ Retrieved {len(employees)} employee records")
            
            # Create a modified version with missing email field
            modified_employees = []
            for emp in employees:
                modified_emp = emp.copy()
                if 'email' in modified_emp:
                    del modified_emp['email']  # Remove email field to cause schema error
                modified_employees.append(modified_emp)
            
            print(f"⚠️  Modified data: Removed 'email' field from all records")
            print(f"📊 Modified data sample: {json.dumps(modified_employees[0], indent=2)}")
            
            return modified_employees
        else:
            print(f"❌ Failed to get employee data: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error simulating schema error: {e}")
        return None

def trigger_pipeline_failure():
    """Trigger a pipeline failure by sending a webhook"""
    print_step(2, "Triggering Pipeline Failure via Webhook")
    
    # Simulate the webhook payload that Airflow would send
    webhook_payload = {
        "dag_id": "self_healing_pipeline",
        "task_id": "validate_schema",
        "execution_date": datetime.now().isoformat(),
        "error_message": "Schema validation failed: Record 0: Missing required field 'email'",
        "error_type": "schema_validation",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(f"{FLASK_API_URL}/webhook", json=webhook_payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Webhook triggered successfully")
            print(f"📊 Monitor result: {result.get('monitor', {}).get('status', 'unknown')}")
            if result.get('diagnosis'):
                print(f"🔍 Diagnosis: {result['diagnosis'].get('root_cause', 'unknown')}")
            if result.get('fix'):
                print(f"🔧 Fix status: {result['fix'].get('status', 'unknown')}")
            return result
        else:
            print(f"❌ Failed to trigger webhook: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error triggering webhook: {e}")
        return None

def check_agent_workflow():
    """Check the status of the agent workflow"""
    print_step(3, "Checking Agent Workflow Status")
    
    try:
        response = requests.get(f"{FLASK_API_URL}/api/status")
        if response.status_code == 200:
            status = response.json()
            runs = status.get('pipeline_runs', [])
            print(f"📊 Total pipeline runs: {len(runs)}")
            
            if runs:
                latest_run = runs[-1]
                print(f"🕒 Latest run: {latest_run.get('timestamp', 'unknown')}")
                print(f"📋 Monitor status: {latest_run.get('monitor', {}).get('status', 'unknown')}")
                
                if latest_run.get('diagnosis'):
                    diagnosis = latest_run['diagnosis']
                    print(f"🔍 Root cause: {diagnosis.get('root_cause', 'unknown')}")
                    print(f"🎯 Confidence: {diagnosis.get('confidence', 'unknown')}")
                    print(f"🛡️  Safety: {diagnosis.get('remediation_safety', 'unknown')}")
                
                if latest_run.get('fix'):
                    fix = latest_run['fix']
                    print(f"🔧 Fix status: {fix.get('status', 'unknown')}")
                    print(f"✅ Success: {fix.get('success', 'unknown')}")
            
            return status
        else:
            print(f"❌ Failed to get status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return None

def view_agent_logs():
    """View recent agent logs"""
    print_step(4, "Viewing Agent Logs")
    
    try:
        response = requests.get(f"{FLASK_API_URL}/api/logs")
        if response.status_code == 200:
            logs_data = response.json()
            logs = logs_data.get('logs', [])
            print(f"📋 Total log entries: {len(logs)}")
            
            # Show last 5 log entries
            recent_logs = logs[-5:] if len(logs) > 5 else logs
            for log in recent_logs:
                print(f"📝 {log.strip()}")
            
            return logs
        else:
            print(f"❌ Failed to get logs: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting logs: {e}")
        return None

def submit_feedback():
    """Submit feedback on the fix"""
    print_step(5, "Submitting Feedback")
    
    feedback_payload = {
        "rating": 5,
        "feedback": "Great job! The AI agents successfully identified and fixed the schema validation issue."
    }
    
    try:
        response = requests.post(f"{FLASK_API_URL}/api/feedback", json=feedback_payload)
        if response.status_code == 200:
            print(f"✅ Feedback submitted successfully")
            print(f"📝 Rating: {feedback_payload['rating']}/5")
            print(f"💬 Comment: {feedback_payload['feedback']}")
            return True
        else:
            print(f"❌ Failed to submit feedback: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error submitting feedback: {e}")
        return False

def main():
    """Main demo function"""
    print("🚀 AI-Powered Self-Healing Data Pipeline Demo")
    print("=" * 60)
    
    # Check if services are running
    print("\n🔍 Checking Services...")
    flask_ok = check_service(FLASK_API_URL, "Flask API")
    
    if not flask_ok:
        print("\n❌ Flask API is not running. Please start it first:")
        print("   cd backend && python app.py")
        sys.exit(1)
    
    # Run demo steps
    simulate_schema_error()
    trigger_pipeline_failure()
    check_agent_workflow()
    view_agent_logs()
    submit_feedback()
    
    print("\n" + "="*60)
    print("🎉 Demo completed!")
    print("\nNext steps:")
    print("1. Check the React dashboard at http://localhost:3000")
    print("2. View Airflow UI at http://localhost:8080")
    print("3. Review logs in the backend/logs directory")
    print("="*60)

if __name__ == "__main__":
    main() 