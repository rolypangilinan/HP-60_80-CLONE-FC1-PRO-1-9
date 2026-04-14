# Import tools needed to build a website
# Flask: The main tool that creates our website
# request: Helps handle user clicks and form submissions
# render_template: Shows our HTML pages to visitors
# jsonify: For returning JSON responses to AJAX calls
from flask import Flask, request, render_template, jsonify
from database_manager import DatabaseManager
import threading
import time
import json
import os

# Initialize database manager
db_manager = DatabaseManager()

# Create our website using Flask
# This line starts up our web application
app = Flask(__name__)

@app.after_request
def add_no_cache_headers(response):
    """Prevent browser from caching HTML pages so users always get the latest code"""
    if 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# Arduino signal queue: stores pending signals from the Arduino bridge
# Format: { process_no: {"action": "start"/"stop", "timestamp": time.time()} }
arduino_signals = {}
arduino_signals_lock = threading.Lock()

# ==================== SERVER-SIDE TIMER TRACKING ====================
# Tracks active timers server-side so Arduino START works even when browser page is closed
# Format: { process_no: {"start_time": time.time(), "kitting_no": N} }
server_timers = {}
server_timers_lock = threading.Lock()

# Server-side counter tracking per process
# Format: { process_no: counter_value }
server_counters = {}
server_counters_lock = threading.Lock()

# Tracks when data was last updated (for auto-refresh on graph pages)
last_data_update = {"timestamp": time.time()}
last_data_update_lock = threading.Lock()

# File to persist timer state across Flask restarts
TIMER_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server_timer_state.json')

def save_timer_state_to_file():
    """Persist server timer and counter state to file"""
    try:
        with server_timers_lock:
            timers_copy = {str(k): v for k, v in server_timers.items()}
        with server_counters_lock:
            counters_copy = {str(k): v for k, v in server_counters.items()}
        state = {'timers': timers_copy, 'counters': counters_copy}
        with open(TIMER_STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        print(f"Error saving timer state to file: {e}")

def load_timer_state_from_file():
    """Load server timer and counter state from file on startup"""
    try:
        if os.path.exists(TIMER_STATE_FILE):
            with open(TIMER_STATE_FILE, 'r') as f:
                state = json.load(f)
            now = time.time()
            max_age = 7200  # Discard timers older than 2 hours (stale from previous session)
            loaded_timers = 0
            with server_timers_lock:
                for k, v in state.get('timers', {}).items():
                    age = now - v.get('start_time', 0)
                    if age <= max_age:
                        server_timers[int(k)] = v
                        loaded_timers += 1
                    else:
                        print(f"Discarding stale timer for Process {k} (age: {int(age)}s)")
            with server_counters_lock:
                for k, v in state.get('counters', {}).items():
                    server_counters[int(k)] = int(v)
            print(f"Loaded timer state from file: {loaded_timers} active timers, {len(server_counters)} counters")
    except Exception as e:
        print(f"Error loading timer state from file: {e}")

def update_last_data_timestamp():
    """Update the last data change timestamp"""
    with last_data_update_lock:
        last_data_update["timestamp"] = time.time()

def clear_all_server_state():
    """Clear all server-side timers, counters, and the state file"""
    with server_timers_lock:
        server_timers.clear()
    with server_counters_lock:
        server_counters.clear()
    with arduino_signals_lock:
        arduino_signals.clear()
    try:
        if os.path.exists(TIMER_STATE_FILE):
            os.remove(TIMER_STATE_FILE)
            print("Deleted server_timer_state.json")
    except Exception as e:
        print(f"Error deleting timer state file: {e}")
    save_timer_state_to_file()
    print("All server timers, counters, and Arduino signals cleared")

def check_and_auto_reset():
    """Check if all 9 processes have the same completed count (>0).
    If so, auto-reset records and counters but keep manpower."""
    try:
        counts = []
        for i in range(1, 10):
            counts.append(db_manager.get_completed_count(i))
        # All must be > 0 and all must be equal
        if all(c > 0 for c in counts) and len(set(counts)) == 1:
            print(f"AUTO-RESET TRIGGERED: All 9 processes have {counts[0]} completed records")
            # Reset database records (keeps manpower)
            db_manager.reset_records_only()
            # Clear server-side timers and counters
            with server_timers_lock:
                server_timers.clear()
            with server_counters_lock:
                server_counters.clear()
            with arduino_signals_lock:
                arduino_signals.clear()
            try:
                if os.path.exists(TIMER_STATE_FILE):
                    os.remove(TIMER_STATE_FILE)
            except:
                pass
            save_timer_state_to_file()
            update_last_data_timestamp()
            return True
        return False
    except Exception as e:
        print(f"Error in check_and_auto_reset: {e}")
        return False

@app.route("/api/auto_reset_check", methods=["GET"])
def auto_reset_check():
    """API endpoint to check if all processes have the same completed count"""
    try:
        if check_and_auto_reset():
            return jsonify({"success": True, "message": "Auto-reset triggered"})
        else:
            return jsonify({"success": False, "message": "No auto-reset needed"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# This is the homepage route
# When someone visits our website's main address, this code runs
@app.route("/")
def home():
    # Show the homepage to the visitor
    # This is like opening the front door of our website
    return render_template('home.html')

# Page for Process 1
# When someone goes to website.com/process1 or process1.html, they see this page
@app.route("/process1")
@app.route("/process1.html")
@app.route("/process1.HTML")
def process1():
    # Show the Process 1 monitoring page
    return render_template('process1.html')

# Page for Process 2
# When someone goes to website.com/process2 or process2.html, they see this page
@app.route("/process2")
@app.route("/process2.html")
@app.route("/process2.HTML")
def process2():
    # Show the Process 2 monitoring page
    return render_template('process2.html')

# Page for Process 3
# When someone goes to website.com/process3 or process3.html, they see this page
@app.route("/process3")
@app.route("/process3.html")
@app.route("/process3.HTML")
def process3():
    # Show the Process 3 monitoring page
    return render_template('process3.html')

# Page for Process 4
# When someone goes to website.com/process4 or process4.html, they see this page
@app.route("/process4")
@app.route("/process4.html")
@app.route("/process4.HTML")
def process4():
    # Show the Process 4 monitoring page
    return render_template('process4.html')

# Page for Process 5
# When someone goes to website.com/process5 or process5.html, they see this page
@app.route("/process5")
@app.route("/process5.html")
@app.route("/process5.HTML")
def process5():
    # Show the Process 5 monitoring page
    return render_template('process5.html')

# Page for Process 6
# When someone goes to website.com/process6 or process6.html, they see this page
@app.route("/process6")
@app.route("/process6.html")
@app.route("/process6.HTML")
def process6():
    # Show the Process 6 monitoring page
    return render_template('process6.html')

# Page for Process 7
# When someone goes to website.com/process7 or process7.html, they see this page
@app.route("/process7")
@app.route("/process7.html")
@app.route("/process7.HTML")
def process7():
    # Show the Process 7 monitoring page
    return render_template('process7.html')

# Page for Process 8
# When someone goes to website.com/process8 or process8.html, they see this page
@app.route("/process8")
@app.route("/process8.html")
@app.route("/process8.HTML")
def process8():
    # Show the Process 8 monitoring page
    return render_template('process8.html')

# Page for Process 9
# When someone goes to website.com/process9 or process9.html, they see this page
@app.route("/process9")
@app.route("/process9.html")
@app.route("/process9.HTML")
def process9():
    # Show the Process 9 monitoring page
    return render_template('process9.html')

# Settings page
@app.route("/settings")
def settings():
    # Show the settings page
    return render_template('settings.html')

# Standard time configuration page
@app.route("/standard_time")
def standard_time():
    # Show the standard time configuration page
    return render_template('standard_time.html')

# Manpower configuration page
@app.route("/manpower")
def manpower():
    # Show the manpower configuration page
    return render_template('manpower.html')

# Cycle Time Graph Monitoring page
@app.route("/cycle_graph")
def cycle_graph():
    # Show the cycle time graph monitoring page
    return render_template('cycle_graph.html')

# Line Trend Graph Monitoring page
@app.route("/line_trend")
def line_trend():
    # Show the line trend graph monitoring page
    return render_template('line_trend.html')

@app.route("/api/reset_all", methods=["POST"])
def reset_all():
    """Clear all server-side timers, counters, and signals"""
    try:
        clear_all_server_state()
        return jsonify({"success": True, "message": "All server state cleared"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API Routes for data insertion
@app.route("/api/start_process", methods=["POST"])
def start_process():
    """Handle START button click - no database insertion, just acknowledge"""
    try:
        data = request.json
        kitting_no = data.get('kitting_no', '')
        process_no = data.get('process_no', 1)
        
        print(f"START: kitting_no={kitting_no}, process_no={process_no}")
        
        # Don't insert record here - only insert on STOP/NG/LINEOUT
        # This prevents duplicate records for the same process
        
        return jsonify({"success": True, "message": "Process started successfully"})
    except Exception as e:
        print(f"Error in start_process: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/stop_process", methods=["POST"])
def stop_process():
    """Handle STOP button click - update elapsed time"""
    try:
        # Check if request has JSON data
        if not request.is_json:
            print("ERROR: Request is not JSON")
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
            
        data = request.get_json()
        if not data:
            print("ERROR: No JSON data received")
            return jsonify({"success": False, "error": "No data received"}), 400
            
        print(f"Received data: {data}")
        
        kitting_no = data.get('kitting_no', '')
        elapsed_time = data.get('elapsed_time', '00:00')
        process_no = data.get('process_no', 1)
        
        print(f"STOP: kitting_no={kitting_no}, elapsed_time={elapsed_time}, process_no={process_no}, pass_ng=0")
        
        # SERVER-SIDE VALIDATION: Block if upstream process hasn't completed this kitting
        process_no_int = int(process_no) if process_no else 1
        if process_no_int > 1 and kitting_no:
            prev_completed = db_manager.get_completed_count(process_no_int - 1)
            kitting_no_int = int(kitting_no) if str(kitting_no).isdigit() else 0
            if kitting_no_int > prev_completed:
                print(f"STOP BLOCKED: Process {process_no_int} Kitting {kitting_no_int} - Process {process_no_int-1} only completed {prev_completed}")
                return jsonify({"success": False, "error": f"Process {process_no_int-1} has only completed {prev_completed} kittings"})
        
        # Validate elapsed_time format
        if elapsed_time and ':' not in str(elapsed_time):
            print(f"WARNING: Invalid elapsed_time format: {elapsed_time}")
            elapsed_time = '00:00'
        
        # Insert record with elapsed time and pass_ng=0 (PASS)
        record_id = db_manager.insert_record(
            kitting_no=str(kitting_no) if kitting_no else '',
            lineout_reason=None,
            elapsed_time=str(elapsed_time),
            pass_ng=0,
            process_no=int(process_no) if process_no else 1
        )
        
        # Clear server-side timer for this process
        with server_timers_lock:
            server_timers.pop(int(process_no) if process_no else 1, None)
        
        # Update last data timestamp for auto-refresh
        update_last_data_timestamp()
        save_timer_state_to_file()
        
        # Check if auto-reset should trigger
        did_reset = check_and_auto_reset()
        
        if record_id:
            return jsonify({"success": True, "record_id": record_id, "auto_reset": did_reset})
        else:
            return jsonify({"success": False, "error": "Failed to insert record"}), 500
    except Exception as e:
        print(f"Error in stop_process: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/ng_process", methods=["POST"])
def ng_process():
    """Handle NG button click"""
    try:
        # Check if request has JSON data
        if not request.is_json:
            print("ERROR: Request is not JSON")
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
            
        data = request.get_json()
        if not data:
            print("ERROR: No JSON data received")
            return jsonify({"success": False, "error": "No data received"}), 400
            
        print(f"Received data: {data}")
        
        kitting_no = data.get('kitting_no', '')
        elapsed_time = data.get('elapsed_time', '00:00')
        process_no = data.get('process_no', 1)
        
        print(f"NG: kitting_no={kitting_no}, elapsed_time={elapsed_time}, process_no={process_no}, pass_ng=1")
        
        # SERVER-SIDE VALIDATION: Block if upstream process hasn't completed this kitting
        process_no_int = int(process_no) if process_no else 1
        if process_no_int > 1 and kitting_no:
            prev_completed = db_manager.get_completed_count(process_no_int - 1)
            kitting_no_int = int(kitting_no) if str(kitting_no).isdigit() else 0
            if kitting_no_int > prev_completed:
                print(f"NG BLOCKED: Process {process_no_int} Kitting {kitting_no_int} - Process {process_no_int-1} only completed {prev_completed}")
                return jsonify({"success": False, "error": f"Process {process_no_int-1} has only completed {prev_completed} kittings"})
        
        # Validate elapsed_time format
        if elapsed_time and ':' not in str(elapsed_time):
            print(f"WARNING: Invalid elapsed_time format: {elapsed_time}")
            elapsed_time = '00:00'
        
        # Insert record with pass_ng=1 (NG)
        record_id = db_manager.insert_record(
            kitting_no=str(kitting_no) if kitting_no else '',
            lineout_reason=None,
            elapsed_time=str(elapsed_time),
            pass_ng=1,
            process_no=int(process_no) if process_no else 1
        )
        
        # Clear server-side timer for this process
        with server_timers_lock:
            server_timers.pop(int(process_no) if process_no else 1, None)
        
        # Update last data timestamp for auto-refresh
        update_last_data_timestamp()
        save_timer_state_to_file()
        
        # Check if auto-reset should trigger
        did_reset = check_and_auto_reset()
        
        if record_id:
            return jsonify({"success": True, "record_id": record_id, "auto_reset": did_reset})
        else:
            return jsonify({"success": False, "error": "Failed to insert record"}), 500
    except Exception as e:
        print(f"Error in ng_process: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/ng_lineout_process", methods=["POST"])
def ng_lineout_process():
    """Handle NG LINEOUT button click with reason"""
    try:
        data = request.json
        kitting_no = data.get('kitting_no', '')
        lineout_reason = data.get('lineout_reason', '')
        elapsed_time = data.get('elapsed_time', '00:00')
        process_no = data.get('process_no', 1)
        
        print(f"NG LINEOUT: kitting_no={kitting_no}, lineout_reason={lineout_reason}, elapsed_time={elapsed_time}, process_no={process_no}, pass_ng=1")
        
        # SERVER-SIDE VALIDATION: Block if upstream process hasn't completed this kitting
        process_no_int = int(process_no) if process_no else 1
        if process_no_int > 1 and kitting_no:
            prev_completed = db_manager.get_completed_count(process_no_int - 1)
            kitting_no_int = int(kitting_no) if str(kitting_no).isdigit() else 0
            if kitting_no_int > prev_completed:
                print(f"NG LINEOUT BLOCKED: Process {process_no_int} Kitting {kitting_no_int} - Process {process_no_int-1} only completed {prev_completed}")
                return jsonify({"success": False, "error": f"Process {process_no_int-1} has only completed {prev_completed} kittings"})
        
        # Insert record with lineout reason and pass_ng=1 (NG)
        record_id = db_manager.insert_record(
            kitting_no=kitting_no,
            lineout_reason=lineout_reason,
            elapsed_time=elapsed_time,
            pass_ng=1,
            process_no=process_no
        )
        
        # Clear server-side timer for this process
        with server_timers_lock:
            server_timers.pop(int(process_no) if process_no else 1, None)
        
        # Update last data timestamp for auto-refresh
        update_last_data_timestamp()
        save_timer_state_to_file()
        
        # Check if auto-reset should trigger
        did_reset = check_and_auto_reset()
        
        if record_id:
            return jsonify({"success": True, "record_id": record_id, "auto_reset": did_reset})
        else:
            return jsonify({"success": False, "error": "Failed to insert record"}), 500
    except Exception as e:
        print(f"Error in ng_lineout_process: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/lineout_process", methods=["POST"])
def lineout_process():
    """Handle LINEOUT button click with reason"""
    try:
        data = request.json
        kitting_no = data.get('kitting_no', '')
        lineout_reason = data.get('lineout_reason', '')
        elapsed_time = data.get('elapsed_time', '00:00')
        process_no = data.get('process_no', 1)
        
        print(f"LINEOUT: kitting_no={kitting_no}, lineout_reason={lineout_reason}, elapsed_time={elapsed_time}, process_no={process_no}, pass_ng=0")
        
        # SERVER-SIDE VALIDATION: Block if upstream process hasn't completed this kitting
        process_no_int = int(process_no) if process_no else 1
        if process_no_int > 1 and kitting_no:
            prev_completed = db_manager.get_completed_count(process_no_int - 1)
            kitting_no_int = int(kitting_no) if str(kitting_no).isdigit() else 0
            if kitting_no_int > prev_completed:
                print(f"LINEOUT BLOCKED: Process {process_no_int} Kitting {kitting_no_int} - Process {process_no_int-1} only completed {prev_completed}")
                return jsonify({"success": False, "error": f"Process {process_no_int-1} has only completed {prev_completed} kittings"})
        
        # Insert record with lineout reason and pass_ng=0 (NG was NOT clicked)
        record_id = db_manager.insert_record(
            kitting_no=kitting_no,
            lineout_reason=lineout_reason,
            elapsed_time=elapsed_time,
            pass_ng=0,
            process_no=process_no
        )
        
        # Clear server-side timer for this process
        with server_timers_lock:
            server_timers.pop(int(process_no) if process_no else 1, None)
        
        # Update last data timestamp for auto-refresh
        update_last_data_timestamp()
        save_timer_state_to_file()
        
        # Check if auto-reset should trigger
        did_reset = check_and_auto_reset()
        
        if record_id:
            return jsonify({"success": True, "record_id": record_id, "auto_reset": did_reset})
        else:
            return jsonify({"success": False, "error": "Failed to insert record"}), 500
    except Exception as e:
        print(f"Error in lineout_process: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/get_process_records/<int:process_no>", methods=["GET"])
def get_process_records(process_no):
    """Get records for a specific process"""
    try:
        records = db_manager.get_records_by_process(process_no)
        return jsonify({"success": True, "records": records})
    except Exception as e:
        print(f"Error in get_process_records: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/get_standard_times", methods=["GET"])
def get_standard_times():
    """Get all standard times"""
    try:
        standard_times = db_manager.get_all_standard_times()
        # Convert Decimal to float for JSON serialization
        for st in standard_times:
            st['standard_time'] = float(st['standard_time'])
            st['title'] = st.get('title', '')
        return jsonify({"success": True, "standard_times": standard_times})
    except Exception as e:
        print(f"Error in get_standard_times: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/get_standard_time/<int:process_no>", methods=["GET"])
def get_standard_time(process_no):
    """Get standard time for a specific process"""
    try:
        standard_times = db_manager.get_all_standard_times()
        for st in standard_times:
            if st['process_no'] == process_no:
                return jsonify({"success": True, "standard_time": float(st['standard_time']), "title": st.get('title', '')})
        return jsonify({"success": False, "error": "Process not found"}), 404
    except Exception as e:
        print(f"Error in get_standard_time: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/update_standard_time", methods=["POST"])
def update_standard_time():
    """Update standard time for a process"""
    try:
        data = request.json
        process_no = data.get('process_no')
        standard_time = data.get('standard_time')
        title = data.get('title', None)
        
        if not process_no or not standard_time:
            return jsonify({"success": False, "error": "Missing process_no or standard_time"}), 400
        
        success = db_manager.update_standard_time(process_no, standard_time, title)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to update standard time"}), 500
    except Exception as e:
        print(f"Error in update_standard_time: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/add_process", methods=["POST"])
def add_process():
    """Add a new process"""
    try:
        data = request.json
        standard_time = data.get('standard_time', '50')
        
        new_process_no = db_manager.add_new_process(standard_time)
        if new_process_no:
            return jsonify({"success": True, "process_no": new_process_no})
        else:
            return jsonify({"success": False, "error": "Failed to add process"}), 500
    except Exception as e:
        print(f"Error in add_process: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/delete_process", methods=["POST"])
def delete_process():
    """Delete a process"""
    try:
        data = request.json
        process_no = data.get('process_no')
        
        if not process_no:
            return jsonify({"success": False, "error": "Missing process_no"}), 400
        
        # Don't allow deletion of processes 1-9 (default processes)
        if process_no <= 9:
            return jsonify({"success": False, "error": "Cannot delete default processes 1-9"}), 400
        
        success = db_manager.delete_process(process_no)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to delete process"}), 500
    except Exception as e:
        print(f"Error in delete_process: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/check_manpower_complete", methods=["GET"])
def check_manpower_complete():
    """Check if all processes 1-9 have manpower assigned"""
    try:
        manpower = db_manager.get_all_manpower()
        missing = []
        for i in range(1, 10):
            found = False
            for mp in manpower:
                if mp['process_no'] == i:
                    # Check if operator_scan OR operator_manual is filled
                    has_scan = mp.get('operator_scan', '').strip() != ''
                    has_manual = mp.get('operator_manual', '').strip() != ''
                    if has_scan or has_manual:
                        found = True
                    break
            if not found:
                missing.append(i)
        
        is_complete = len(missing) == 0
        return jsonify({"success": True, "is_complete": is_complete, "missing_processes": missing})
    except Exception as e:
        print(f"Error in check_manpower_complete: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/get_manpower", methods=["GET"])
def get_manpower():
    """Get all manpower records"""
    try:
        manpower = db_manager.get_all_manpower()
        return jsonify({"success": True, "manpower": manpower})
    except Exception as e:
        print(f"Error in get_manpower: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/get_manpower/<int:process_no>", methods=["GET"])
def get_manpower_by_process(process_no):
    """Get manpower for a specific process"""
    try:
        manpower = db_manager.get_manpower_by_process(process_no)
        if manpower:
            return jsonify({"success": True, "manpower": manpower})
        return jsonify({"success": False, "error": "Process not found"}), 404
    except Exception as e:
        print(f"Error in get_manpower_by_process: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/get_cycle_graph_data", methods=["GET"])
def get_cycle_graph_data():
    """Get all data needed for cycle time graph monitoring"""
    try:
        # Get average elapsed times per process
        cycle_data = db_manager.get_cycle_graph_data()
        
        # Get all standard times
        standard_times = db_manager.get_all_standard_times()
        st_map = {}
        for st in standard_times:
            st_map[st['process_no']] = float(st['standard_time'])
        
        # Get all manpower (operator names)
        manpower = db_manager.get_all_manpower()
        operator_map = {}
        for mp in manpower:
            # Use operator_manual or operator_scan, whichever is set
            name = mp.get('operator_manual', '') or mp.get('operator_scan', '') or ''
            operator_map[mp['process_no']] = name
        
        # Build combined data for all 9 processes
        graph_data = []
        for i in range(1, 10):
            avg_mss = 0
            avg_seconds = 0
            record_count = 0
            for cd in cycle_data:
                if cd['process_no'] == i:
                    avg_mss = cd['avg_mss']
                    avg_seconds = cd['avg_seconds']
                    record_count = cd['record_count']
                    break
            
            graph_data.append({
                'process_no': i,
                'avg_mss': avg_mss,
                'avg_seconds': avg_seconds,
                'record_count': record_count,
                'standard_time': st_map.get(i, 1.50),
                'operator': operator_map.get(i, '')
            })
        
        return jsonify({"success": True, "graph_data": graph_data})
    except Exception as e:
        print(f"Error in get_cycle_graph_data: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/get_line_trend_data", methods=["GET"])
def get_line_trend_data():
    """Get all data needed for line trend graph monitoring"""
    try:
        # Get all standard times
        standard_times = db_manager.get_all_standard_times()
        st_map = {}
        for st in standard_times:
            st_map[st['process_no']] = float(st['standard_time'])
        
        # Get all manpower (operator names)
        manpower = db_manager.get_all_manpower()
        operator_map = {}
        for mp in manpower:
            name = mp.get('operator_manual', '') or mp.get('operator_scan', '') or ''
            operator_map[mp['process_no']] = name
        
        # Build data for all 9 processes
        # Fixed values for all processes: TACT TIME = 1.50, (+) TOL = 1.65, (-) TOL = 1.35
        trend_data = []
        for i in range(1, 10):
            records = db_manager.get_line_trend_data(i, limit=10)
            completed_count = db_manager.get_completed_count(i)
            trend_data.append({
                'process_no': i,
                'tol_plus': 1.65,
                'tol_minus': 1.35,
                'tact_time': 1.50,
                'operator': operator_map.get(i, ''),
                'records': records,
                'completed_count': completed_count
            })
        
        return jsonify({"success": True, "trend_data": trend_data})
    except Exception as e:
        print(f"Error in get_line_trend_data: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/update_manpower", methods=["POST"])
def update_manpower():
    """Update manpower for a process"""
    try:
        data = request.json
        process_no = data.get('process_no')
        operator_manual = data.get('operator_manual', '')
        operator_scan = data.get('operator_scan', '')
        
        if not process_no:
            return jsonify({"success": False, "error": "Missing process_no"}), 400
        
        success = db_manager.update_manpower(process_no, operator_manual, operator_scan)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to update manpower"}), 500
    except Exception as e:
        print(f"Error in update_manpower: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/operator_out", methods=["POST"])
def operator_out():
    """Clear operator for a process (operator OUT)"""
    try:
        data = request.json
        process_no = data.get('process_no')
        reason = data.get('reason', '')
        
        if not process_no:
            return jsonify({"success": False, "error": "Missing process_no"}), 400
        
        success = db_manager.clear_manpower(process_no)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to clear operator"}), 500
    except Exception as e:
        print(f"Error in operator_out: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/get_out_reasons", methods=["GET"])
def get_out_reasons():
    """Get all OUT reasons for dropdown"""
    try:
        reasons = db_manager.get_out_reasons()
        return jsonify({"success": True, "reasons": reasons})
    except Exception as e:
        print(f"Error in get_out_reasons: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/add_out_reason", methods=["POST"])
def add_out_reason():
    """Add a custom OUT reason (shared across all processes)"""
    try:
        data = request.json
        reason = data.get('reason', '').strip().upper()
        
        if not reason:
            return jsonify({"success": False, "error": "Missing reason"}), 400
        
        success = db_manager.add_out_reason(reason)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Reason already exists or failed to add"}), 500
    except Exception as e:
        print(f"Error in add_out_reason: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== ARDUINO SIGNAL API ====================

@app.route("/api/arduino_signal", methods=["POST"])
def receive_arduino_signal():
    """Receive signal from Arduino bridge (arduino_bridge.py)
    Also handles server-side timer start/stop so timers work even when browser page is closed."""
    try:
        data = request.json
        process_no = int(data.get('process_no', 0))
        action = data.get('action', '').lower()  # "start" or "stop"
        
        if process_no < 1 or process_no > 9:
            return jsonify({"success": False, "error": "Invalid process_no"}), 400
        if action not in ('start', 'stop'):
            return jsonify({"success": False, "error": "Invalid action"}), 400
        
        # SERVER-SIDE TIMER HANDLING (works even when browser page is closed)
        if action == 'start':
            # Check if timer is already running for this process
            with server_timers_lock:
                if process_no in server_timers:
                    print(f"ARDUINO: Process {process_no} timer already running, ignoring START")
                    return jsonify({"success": True, "info": "Timer already running"})
            
            # Get current counter and compute next kitting number
            with server_counters_lock:
                current_counter = server_counters.get(process_no, 0)
                new_counter = current_counter + 1
            
            # VALIDATE: Check if previous process has completed enough kittings
            if process_no > 1:
                prev_completed = db_manager.get_completed_count(process_no - 1)
                if new_counter > prev_completed:
                    print(f"ARDUINO: BLOCKED Process {process_no} Kitting {new_counter} - Process {process_no-1} only completed {prev_completed}")
                    return jsonify({"success": False, "error": f"Process {process_no-1} has only completed {prev_completed} kittings"})
            
            # Validation passed - start the timer
            with server_counters_lock:
                server_counters[process_no] = new_counter
            with server_timers_lock:
                server_timers[process_no] = {
                    "start_time": time.time(),
                    "kitting_no": new_counter
                }
            save_timer_state_to_file()
            print(f"ARDUINO: Server-side timer STARTED for Process {process_no}, Kitting {new_counter}")
        
        elif action == 'stop':
            with server_timers_lock:
                timer_data = server_timers.pop(process_no, None)
            
            if timer_data:
                elapsed_seconds = int(time.time() - timer_data["start_time"])
                mins = elapsed_seconds // 60
                secs = elapsed_seconds % 60
                elapsed_time_str = f"{mins:02d}:{secs:02d}"
                kitting_no = timer_data["kitting_no"]
                
                record_id = db_manager.insert_record(
                    kitting_no=str(kitting_no),
                    lineout_reason=None,
                    elapsed_time=elapsed_time_str,
                    pass_ng=0,
                    process_no=process_no
                )
                
                update_last_data_timestamp()
                save_timer_state_to_file()
                
                # Check if auto-reset should trigger
                check_and_auto_reset()
                
                print(f"ARDUINO: Server-side timer STOPPED for Process {process_no}, Kitting {kitting_no}, Elapsed {elapsed_time_str}, Record ID: {record_id}")
            else:
                print(f"ARDUINO: No active timer for Process {process_no} to stop")
        
        # Store the signal for browser polling (only reached if validation passed)
        with arduino_signals_lock:
            arduino_signals[process_no] = {
                "action": action,
                "timestamp": time.time()
            }
        
        print(f"ARDUINO SIGNAL: Process {process_no} -> {action.upper()}")
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error in receive_arduino_signal: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/arduino_signal/<int:process_no>", methods=["GET"])
def get_arduino_signal(process_no):
    """Browser polls this endpoint to check for pending Arduino signals"""
    try:
        with arduino_signals_lock:
            signal = arduino_signals.pop(process_no, None)
        
        if signal:
            # Only return signals that are less than 10 seconds old
            if time.time() - signal["timestamp"] < 10:
                return jsonify({"success": True, "action": signal["action"]})
        
        return jsonify({"success": True, "action": None})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/get_server_timer/<int:process_no>", methods=["GET"])
def get_server_timer(process_no):
    """Get server-side timer state for a process.
    Used by browser pages to pick up timers started by Arduino when page was closed."""
    try:
        with server_timers_lock:
            timer_data = server_timers.get(process_no, None)
        
        if timer_data:
            elapsed_seconds = int(time.time() - timer_data["start_time"])
            return jsonify({
                "success": True,
                "active": True,
                "start_time": timer_data["start_time"],
                "kitting_no": timer_data["kitting_no"],
                "elapsed_seconds": elapsed_seconds
            })
        else:
            return jsonify({"success": True, "active": False})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/sync_counter/<int:process_no>", methods=["POST"])
def sync_counter(process_no):
    """Sync browser counter with server-side counter.
    Browser sends its counter value, server updates if browser value is higher."""
    try:
        data = request.json
        browser_counter = int(data.get('counter', 0))
        
        with server_counters_lock:
            server_val = server_counters.get(process_no, 0)
            # Use the higher value (browser or server)
            final_val = max(browser_counter, server_val)
            server_counters[process_no] = final_val
        
        return jsonify({"success": True, "counter": final_val})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/clear_server_timer/<int:process_no>", methods=["POST"])
def clear_server_timer(process_no):
    """Clear server-side timer (called when browser takes over the timer)."""
    try:
        with server_timers_lock:
            server_timers.pop(process_no, None)
        save_timer_state_to_file()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/start_server_timer/<int:process_no>", methods=["POST"])
def start_server_timer(process_no):
    """Start server-side timer tracking (called when browser START button is clicked)."""
    try:
        data = request.json
        kitting_no = int(data.get('kitting_no', 0))
        
        # VALIDATE: Check if previous process has completed enough kittings
        if process_no > 1:
            prev_completed = db_manager.get_completed_count(process_no - 1)
            if kitting_no > prev_completed:
                print(f"START_SERVER_TIMER: BLOCKED Process {process_no} Kitting {kitting_no} - Process {process_no-1} only completed {prev_completed}")
                return jsonify({"success": False, "error": f"Process {process_no-1} has only completed {prev_completed} kittings"})
        
        with server_timers_lock:
            server_timers[process_no] = {
                "start_time": time.time(),
                "kitting_no": kitting_no
            }
        
        # Also update server counter
        with server_counters_lock:
            server_counters[process_no] = max(server_counters.get(process_no, 0), kitting_no)
        
        save_timer_state_to_file()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/get_completed_count/<int:process_no>", methods=["GET"])
def get_completed_count(process_no):
    """Get the number of completed records for a process from the database.
    Used by downstream processes to verify upstream completion."""
    try:
        count = db_manager.get_completed_count(process_no)
        # Also check if there's an active server timer (started but not yet stopped)
        with server_timers_lock:
            has_active = process_no in server_timers
        return jsonify({"success": True, "count": count, "has_active_timer": has_active})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/can_start_kitting/<int:process_no>/<int:kitting_no>", methods=["GET"])
def can_start_kitting(process_no, kitting_no):
    """Check if a process can start a specific kitting number.
    Verifies that the previous process (process_no - 1) has completed at least kitting_no records."""
    try:
        if process_no <= 1:
            return jsonify({"success": True, "allowed": True})
        
        prev_process = process_no - 1
        prev_completed = db_manager.get_completed_count(prev_process)
        
        allowed = kitting_no <= prev_completed
        print(f"CAN_START_KITTING: Process {process_no} wants Kitting {kitting_no}, Process {prev_process} completed {prev_completed}, Allowed: {allowed}")
        return jsonify({
            "success": True,
            "allowed": allowed,
            "prev_process": prev_process,
            "prev_completed": prev_completed,
            "requested_kitting": kitting_no
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/get_all_active_timers", methods=["GET"])
def get_all_active_timers():
    """Get active timer status for all processes (used by graph pages for blinking indicators)"""
    try:
        import time as _time
        with server_timers_lock:
            active = {}
            for k, v in server_timers.items():
                elapsed_sec = int(_time.time() - v.get("start_time", _time.time()))
                active[str(k)] = {"active": True, "elapsed_seconds": elapsed_sec}
        return jsonify({"success": True, "active_timers": active})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/get_last_update", methods=["GET"])
def get_last_update():
    """Get timestamp of last data update. Used by graph pages for auto-refresh."""
    try:
        with last_data_update_lock:
            ts = last_data_update["timestamp"]
        return jsonify({"success": True, "timestamp": ts})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Start the website when this file is run
# This code only runs when you click "Run" on this file
if __name__ == "__main__":
    # Initialize database connection and create tables
    try:
        db_manager.connect()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        print("Please ensure XAMPP MySQL/MariaDB is running")
    
    # Load persisted timer state from file (survives Flask restarts)
    load_timer_state_from_file()
    
    # Turn on the web server so people can visit the site
    # host="0.0.0.0": Anyone on the network can visit (not just you)
    # port=5000: The website "door number" - like apartment 5000
    # debug=True: Shows helpful error messages if something breaks
    app.run(host="0.0.0.0", port=5000, debug=True)  #host="0.0.0.0", port=5000 for porthost