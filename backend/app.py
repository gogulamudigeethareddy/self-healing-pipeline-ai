import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

# Import agents (assume these are implemented in ../agents/)
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../agents')))
from monitor_agent import MonitorAgent
from diagnose_agent import DiagnoseAgent
from fix_agent import FixAgent

app = Flask(__name__)
CORS(app)

# Setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(filename='logs/pipeline.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Instantiate agents
monitor_agent = MonitorAgent()
diagnose_agent = DiagnoseAgent(os.getenv('OPENAI_API_KEY'))
fix_agent = FixAgent()

# In-memory store for logs, status, feedback (for demo)
pipeline_runs = []
feedback_list = []

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """Mock API endpoint for Airflow DAG to pull data from"""
    # You can simulate schema errors by removing a field here for demo
    employees = [
        {"id": 1, "name": "Alice Smith", "email": "alice@example.com", "department": "Engineering", "salary": 120000, "hire_date": "2020-01-15"},
        {"id": 2, "name": "Bob Jones", "email": "bob@example.com", "department": "Sales", "salary": 95000, "hire_date": "2019-03-22"},
        {"id": 3, "name": "Carol Lee", "email": "carol@example.com", "department": "HR", "salary": 105000, "hire_date": "2021-07-01"}
    ]
    return jsonify(employees)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receives failure events from Airflow and triggers agentic workflow"""
    data = request.json
    logging.info(f"Received webhook: {data}")
    # 1. Monitor agent processes the failure
    monitor_result = monitor_agent.process_webhook(data)
    # 2. If diagnosis triggered, run diagnosis and fix
    diagnosis_result = None
    fix_result = None
    if monitor_result.get('diagnosis_triggered'):
        diagnosis_result = diagnose_agent.diagnose_failure(data)
        # For demo, convert dataclass to dict
        diagnosis_dict = diagnosis_result.__dict__ if hasattr(diagnosis_result, '__dict__') else diagnosis_result
        fix_result = fix_agent.apply_fix(diagnosis_dict, data)
    # Log pipeline run
    pipeline_runs.append({
        'event': data,
        'monitor': monitor_result,
        'diagnosis': diagnosis_result.__dict__ if diagnosis_result else None,
        'fix': fix_result.__dict__ if fix_result else None,
        'timestamp': datetime.now().isoformat()
    })
    return jsonify({
        'monitor': monitor_result,
        'diagnosis': diagnosis_result.__dict__ if diagnosis_result else None,
        'fix': fix_result.__dict__ if fix_result else None
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Return recent pipeline logs"""
    try:
        with open('logs/pipeline.log', 'r') as f:
            lines = f.readlines()[-200:]
        return jsonify({'logs': lines})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Return recent pipeline run status and agent actions"""
    return jsonify({'pipeline_runs': pipeline_runs[-20:]})

@app.route('/api/feedback', methods=['POST'])
def post_feedback():
    """Accept user feedback on fixes"""
    data = request.json
    feedback_list.append({
        'feedback': data.get('feedback'),
        'rating': data.get('rating'),
        'timestamp': datetime.now().isoformat()
    })
    return jsonify({'status': 'received'})

@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    """Return feedback history"""
    return jsonify({'feedback': feedback_list[-20:]})

# --- Endpoints for fix agent simulation (optional, for demo) ---
@app.route('/api/update_schema', methods=['POST'])
def update_schema():
    # Simulate schema update (no-op for demo)
    return jsonify({'status': 'schema updated'})

@app.route('/api/add_transformation', methods=['POST'])
def add_transformation():
    # Simulate adding transformation (no-op for demo)
    return jsonify({'status': 'transformation added'})

@app.route('/api/update_config', methods=['POST'])
def update_config():
    # Simulate config update (no-op for demo)
    return jsonify({'status': 'config updated'})

@app.route('/api/notify', methods=['POST'])
def notify():
    # Simulate manual intervention notification (no-op for demo)
    return jsonify({'status': 'notified'})

@app.route('/api/verify_fix', methods=['POST'])
def verify_fix():
    # Simulate fix verification (always success for demo)
    return jsonify({'status': 'verified'})

@app.route('/api/rollback', methods=['POST'])
def rollback():
    # Simulate rollback (no-op for demo)
    return jsonify({'status': 'rolled back'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('FLASK_PORT', 5000)), debug=True) 