# Import tools needed to build a website
# Flask: The main tool that creates our website
# request: Helps handle user clicks and form submissions
# render_template: Shows our HTML pages to visitors
# jsonify: For returning JSON responses to AJAX calls
from flask import Flask, request, render_template, jsonify
from database_manager import DatabaseManager

# Initialize database manager
db_manager = DatabaseManager()

# Create our website using Flask
# This line starts up our web application
app = Flask(__name__)

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
        
        if record_id:
            return jsonify({"success": True, "record_id": record_id})
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
        
        if record_id:
            return jsonify({"success": True, "record_id": record_id})
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
        
        # Insert record with lineout reason and pass_ng=1 (NG)
        record_id = db_manager.insert_record(
            kitting_no=kitting_no,
            lineout_reason=lineout_reason,
            elapsed_time=elapsed_time,
            pass_ng=1,
            process_no=process_no
        )
        
        if record_id:
            return jsonify({"success": True, "record_id": record_id})
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
        
        # Insert record with lineout reason and pass_ng=0 (NG was NOT clicked)
        record_id = db_manager.insert_record(
            kitting_no=kitting_no,
            lineout_reason=lineout_reason,
            elapsed_time=elapsed_time,
            pass_ng=0,
            process_no=process_no
        )
        
        if record_id:
            return jsonify({"success": True, "record_id": record_id})
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
            trend_data.append({
                'process_no': i,
                'tol_plus': 1.65,
                'tol_minus': 1.35,
                'tact_time': 1.50,
                'operator': operator_map.get(i, ''),
                'records': records
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
    
    # Turn on the web server so people can visit the site
    # host="0.0.0.0": Anyone on the network can visit (not just you)
    # port=5000: The website "door number" - like apartment 5000
    # debug=True: Shows helpful error messages if something breaks
    app.run(host="0.0.0.0", port=5000 ,debug=True)  #host="0.0.0.0", port=5000 for porthost