from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import csv
from io import BytesIO, StringIO
from datetime import datetime
import os
import qrcode
import uuid
import atexit

app = Flask(__name__)

# File paths
STUDENTS_FILE = 'students.txt'
ATTENDANCE_DIR = 'attendance_data'
os.makedirs(ATTENDANCE_DIR, exist_ok=True)

# Global variables
attendance_session = {
    'active': False,
    'module': None,
    'present_students': set(),
    'session_id': None,
    'qr_code_url': None,
    'checkin_url': None
}

def get_attendance_file(module):
    """Get the attendance file path for a module"""
    return os.path.join(ATTENDANCE_DIR, f"{module}_attendance.csv")

def init_attendance_files():
    """Initialize attendance files for all modules"""
    modules = ['SEN152', 'OOP152', 'IDB152', 'ISP152', 'FIT152', 'TAS152']
    for module in modules:
        filepath = get_attendance_file(module)
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                f.write('student_number,name,module,status,date\n')

def load_students():
    """Load student data from text file"""
    students = []
    if os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '-' in line:
                    parts = line.split('-', 1)
                    student_number = parts[0].strip()
                    name = parts[1].strip()
                    students.append({
                        'student_number': student_number,
                        'name': name
                    })
    return students

def load_attendance(module):
    """Load attendance records for a module"""
    filepath = get_attendance_file(module)
    records = []
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            records = list(reader)
    return records

def save_attendance(module, records):
    """Save attendance records for a module"""
    filepath = get_attendance_file(module)
    with open(filepath, 'w', newline='') as f:
        fieldnames = ['student_number', 'name', 'module', 'status', 'date']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def generate_qr_code(url):
    """Generate QR code image"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

@app.route('/static/qrcodes/<path:filename>')
def serve_qrcode(filename):
    """Serve QR code images"""
    return send_from_directory('static/qrcodes', filename)

@app.route('/')
def index():
    modules = ['SEN152', 'OOP152', 'IDB152', 'ISP152', 'FIT152', 'TAS152']
    return render_template('index.html', modules=modules)

@app.route('/start_attendance', methods=['POST'])
def start_attendance():
    module = request.form.get('module')
    if not module:
        return jsonify({'success': False, 'message': 'Please select a module'})
    
    # Generate unique session ID and URLs
    session_id = str(uuid.uuid4())
    checkin_url = f"https://{request.host}/checkin/{session_id}"
    
    # Generate and save QR code
    img = generate_qr_code(checkin_url)
    qr_code_path = f"static/qrcodes/{session_id}.png"
    os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)
    img.save(qr_code_path)
    
    # Update session info
    attendance_session['active'] = True
    attendance_session['module'] = module
    attendance_session['present_students'] = set()
    attendance_session['session_id'] = session_id
    attendance_session['qr_code_url'] = f"/static/qrcodes/{session_id}.png"
    attendance_session['checkin_url'] = checkin_url
    
    return jsonify({
        'success': True, 
        'message': f'Attendance session started for {module}',
        'qr_code_url': attendance_session['qr_code_url'],
        'checkin_url': checkin_url
    })

@app.route('/checkin/<session_id>')
def checkin_page(session_id):
    if not attendance_session['active'] or attendance_session['session_id'] != session_id:
        return render_template('session_expired.html')
    return render_template('checkin.html')

@app.route('/api/check_in', methods=['POST'])
def api_check_in():
    if not attendance_session['active']:
        return jsonify({'success': False, 'message': 'No active attendance session'})
    
    student_number = request.form.get('student_number')
    if not student_number:
        return jsonify({'success': False, 'message': 'Please enter student number'})
    
    students = load_students()
    student = next((s for s in students if s['student_number'] == student_number), None)
    
    if not student:
        return jsonify({'success': False, 'message': 'Invalid student number'})
    
    if student_number in attendance_session['present_students']:
        return jsonify({'success': False, 'message': 'Already checked in'})
    
    attendance_session['present_students'].add(student_number)
    
    # Return updated attendance list
    attendance_list = []
    for s in students:
        attendance_list.append({
            'student_number': s['student_number'],
            'name': s['name'],
            'status': 'present' if s['student_number'] in attendance_session['present_students'] else 'absent'
        })
    
    return jsonify({
        'success': True, 
        'message': f'Checked in successfully: {student["name"]}',
        'name': student['name'],
        'attendance_list': attendance_list
    })

@app.route('/get_attendance_list')
def get_attendance_list():
    if not attendance_session['active']:
        return jsonify({'success': False, 'message': 'No active attendance session'})
    
    students = load_students()
    attendance_list = []
    
    for student in students:
        attendance_list.append({
            'student_number': student['student_number'],
            'name': student['name'],
            'status': 'present' if student['student_number'] in attendance_session['present_students'] else 'absent'
        })
    
    return jsonify({'success': True, 'data': attendance_list})

@app.route('/stop_attendance', methods=['POST'])
def stop_attendance():
    if not attendance_session['active']:
        return jsonify({'success': False, 'message': 'No active attendance session'})
    
    module = attendance_session['module']
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    students = load_students()
    
    # Load existing records
    records = load_attendance(module)
    
    # Add new records
    for student in students:
        status = 'present' if student['student_number'] in attendance_session['present_students'] else 'absent'
        records.append({
            'student_number': student['student_number'],
            'name': student['name'],
            'module': module,
            'status': status,
            'date': date
        })
    
    # Save to file
    save_attendance(module, records)
    
    # Reset session
    attendance_session['active'] = False
    
    return jsonify({'success': True, 'message': f'Attendance session stopped for {module}'})

@app.route('/download_attendance', methods=['POST'])
def download_attendance():
    module = request.form.get('module')
    report_type = request.form.get('report_type')
    
    if not module:
        return jsonify({'success': False, 'message': 'Module not specified'})
    
    records = load_attendance(module)
    
    if not records:
        return jsonify({'success': False, 'message': 'No attendance records found for this module'})
    
    output = StringIO()
    writer = csv.writer(output)
    
    if report_type == 'full':
        writer.writerow(['Student Number', 'Name', 'Status', 'Date'])
        for record in records:
            writer.writerow([
                record['student_number'],
                record['name'],
                record['status'],
                record['date']
            ])
    elif report_type == 'absent':
        writer.writerow(['Student Number', 'Name', 'Date'])
        for record in records:
            if record['status'] == 'absent':
                writer.writerow([
                    record['student_number'],
                    record['name'],
                    record['date']
                ])
    
    output.seek(0)
    filename = f"{module}_{report_type}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static/qrcodes', exist_ok=True)
    os.makedirs(ATTENDANCE_DIR, exist_ok=True)
    
    # Initialize attendance files
    init_attendance_files()
    
    # Ensure directories exist on exit
    atexit.register(lambda: os.makedirs(ATTENDANCE_DIR, exist_ok=True))
    
    app.run(host='0.0.0.0', port=10000, debug=True)
