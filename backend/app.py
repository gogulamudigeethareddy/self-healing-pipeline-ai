import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import copy
import enum
import json

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

approval_state_path = os.path.join(os.path.dirname(__file__), 'approval_state.json')

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
    """API endpoint for Airflow DAG to pull data from. Reads from data/sample_employees.json."""
    import os
    import json
    data_path = os.path.join(os.path.dirname(__file__), '../data/sample_employees.json')
    try:
        with open(data_path, 'r') as f:
            employees = json.load(f)
    except Exception as e:
        logging.error(f"Failed to read employee data: {e}")
        employees = []
    return jsonify(employees)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receives failure events from Airflow and triggers agentic workflow"""
    import time
    data = request.json
    logging.info(f"Received webhook: {data}")
    step_timings = {}
    error_info = {}
    start_time = time.time()
    # 1. Monitor agent processes the failure
    try:
        t0 = time.time()
        monitor_result = monitor_agent.process_webhook(data)
        t1 = time.time()
        step_timings['monitor_agent'] = t1 - t0
        logging.info(f"MonitorAgent completed in {step_timings['monitor_agent']:.2f}s: {serialize_obj(monitor_result)}")
    except Exception as e:
        error_info['monitor_agent'] = str(e)
        logging.error(f"MonitorAgent error: {e}")
        monitor_result = {'error': str(e)}
    # 2. If intervention triggered, run diagnosis and fix
    diagnosis_result = None
    fix_result = None
    if monitor_result.get('status') == 'intervention_triggered':
        try:
            t0 = time.time()
            diagnosis_result = diagnose_agent.diagnose_failure(data)
            t1 = time.time()
            step_timings['diagnose_agent'] = t1 - t0
            logging.info(f"DiagnoseAgent completed in {step_timings['diagnose_agent']:.2f}s: {serialize_obj(diagnosis_result)}")
        except Exception as e:
            error_info['diagnose_agent'] = str(e)
            logging.error(f"DiagnoseAgent error: {e}")
            diagnosis_result = {'error': str(e)}
        try:
            t0 = time.time()
            fix_result = fix_agent.apply_fix(
                diagnosis_result.__dict__ if hasattr(diagnosis_result, '__dict__') else diagnosis_result,
                data
            )
            t1 = time.time()
            step_timings['fix_agent'] = t1 - t0
            logging.info(f"FixAgent completed in {step_timings['fix_agent']:.2f}s: {serialize_obj(fix_result)}")
        except Exception as e:
            error_info['fix_agent'] = str(e)
            logging.error(f"FixAgent error: {e}")
            fix_result = {'error': str(e)}
    total_time = time.time() - start_time
    logging.info(f"/webhook total execution time: {total_time:.2f}s | Step timings: {step_timings} | Errors: {error_info}")
    # Log pipeline run with serialization
    pipeline_runs.append({
        'event': data,
        'monitor': serialize_obj(monitor_result),
        'diagnosis': serialize_obj(diagnosis_result) if diagnosis_result else None,
        'fix': serialize_obj(fix_result) if fix_result else None,
        'timings': step_timings,
        'errors': error_info,
        'timestamp': datetime.now().isoformat()
    })
    return jsonify({
        'monitor': serialize_obj(monitor_result),
        'diagnosis': serialize_obj(diagnosis_result) if diagnosis_result else None,
        'fix': serialize_obj(fix_result) if fix_result else None,
        'timings': step_timings,
        'errors': error_info
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

@app.route('/api/diagnose', methods=['POST'])
def api_diagnose():
    """API endpoint to trigger diagnosis agent from external services (e.g., MonitorAgent)."""
    data = request.json
    logging.info(f"[API] Received diagnosis request: {data}")
    result = diagnose_agent.diagnose_failure(data.get('failure_event', data))
    return jsonify(serialize_obj(result)), 200

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

@app.route('/api/pending_fix', methods=['GET'])
def api_pending_fix():
    """Get the pending fix details, if any."""
    return jsonify(get_pending_fix())

@app.route('/api/approve_fix', methods=['POST'])
def api_approve_fix():
    """Approve the pending fix for application."""
    state = approve_pending_fix()
    # Here you could trigger the actual fix logic if needed
    return jsonify(state)

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint for root URL."""
    return jsonify({'status': 'ok', 'message': 'Flask API is running'}), 200

@app.after_request
def after_request(response):
    # Log every request to the log file and console
    logging.info(f"{request.remote_addr} - - [{datetime.now().strftime('%d/%b/%Y %H:%M:%S')}] \"{request.method} {request.path} {request.environ.get('SERVER_PROTOCOL')}\" {response.status_code} -")
    return response

def set_pending_fix(fix_desc, failure):
    with open(approval_state_path, 'w') as f:
        json.dump({"pending_fix": fix_desc, "failure": failure, "approved": False}, f)

def get_pending_fix():
    try:
        with open(approval_state_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {"pending_fix": None, "approved": False}

def approve_pending_fix():
    state = get_pending_fix()
    state["approved"] = True
    with open(approval_state_path, 'w') as f:
        json.dump(state, f)
    return state

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)