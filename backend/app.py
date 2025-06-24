import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import copy
import enum

# Import agents (assume these are implemented in ../agents/)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))
from agents.monitor_agent import MonitorAgent
from agents.diagnose_agent import DiagnoseAgent
from agents.fix_agent import FixAgent

app = Flask(__name__)
CORS(app)

# Setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler()
    ]
)

# Instantiate agents
monitor_agent = MonitorAgent()
diagnose_agent = DiagnoseAgent(os.getenv('OPENAI_API_KEY'))
fix_agent = FixAgent()

# In-memory store for logs, status, feedback (for demo)
pipeline_runs = []
feedback_list = []

def safe_dict(obj, _depth=0, _max_depth=10, _visited=None):
    """Helper function to recursively convert non-serializable objects to strings, with depth and cycle protection."""
    if _visited is None:
        _visited = set()
    if _depth > _max_depth:
        return str(obj)
    if id(obj) in _visited:
        return str(obj)
    _visited.add(id(obj))
    if hasattr(obj, '__dict__'):
        return {k: safe_dict(v, _depth+1, _max_depth, _visited) for k, v in obj.__dict__.items()}
    elif isinstance(obj, dict):
        return {k: safe_dict(v, _depth+1, _max_depth, _visited) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [safe_dict(v, _depth+1, _max_depth, _visited) for v in obj]
    elif isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    else:
        return str(obj)

def serialize_obj(obj, _visited=None, _depth=0, _max_depth=10):
    if _visited is None:
        _visited = set()
    if _depth > _max_depth:
        return str(obj)
    obj_id = id(obj)
    if obj_id in _visited:
        return str(obj)
    _visited.add(obj_id)
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        return {k: serialize_obj(v, _visited, _depth+1, _max_depth) for k, v in obj.__dict__.items()}
    elif isinstance(obj, dict):
        return {k: serialize_obj(v, _visited, _depth+1, _max_depth) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_obj(v, _visited, _depth+1, _max_depth) for v in obj]
    elif hasattr(obj, 'value'):
        return obj.value
    elif isinstance(obj, enum.Enum):
        return obj.name
    elif isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    else:
        return str(obj)

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """Mock API endpoint for Airflow DAG to pull data from"""
    # Simulate schema error by removing 'id' field from the first employee
    employees = [
        {"name": "Alice Smith", "email": "alice@example.com", "department": "Engineering", "salary": 120000, "hire_date": "2020-01-15"},
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
        fix_result = fix_agent.apply_fix(
            diagnosis_result.__dict__ if hasattr(diagnosis_result, '__dict__') else diagnosis_result,
            data
        )
    # Log pipeline run with serialization
    pipeline_runs.append({
        'event': data,
        'monitor': serialize_obj(monitor_result),
        'diagnosis': serialize_obj(diagnosis_result) if diagnosis_result else None,
        'fix': serialize_obj(fix_result) if fix_result else None,
        'timestamp': datetime.now().isoformat()
    })
    return jsonify({
        'monitor': serialize_obj(monitor_result),
        'diagnosis': serialize_obj(diagnosis_result) if diagnosis_result else None,
        'fix': serialize_obj(fix_result) if fix_result else None
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
    # Ensure all runs are serializable
    serialized_runs = [serialize_obj(run) for run in pipeline_runs[-20:]]
    return jsonify({'pipeline_runs': serialized_runs})

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

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint for root URL."""
    return jsonify({'status': 'ok', 'message': 'Flask API is running'}), 200

@app.after_request
def after_request(response):
    # Log every request to the log file and console
    logging.info(f"{request.remote_addr} - - [{datetime.now().strftime('%d/%b/%Y %H:%M:%S')}] \"{request.method} {request.path} {request.environ.get('SERVER_PROTOCOL')}\" {response.status_code} -")
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)