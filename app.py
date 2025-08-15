from flask import Flask, render_template, request, jsonify, send_file
from flask import send_from_directory
import csv
from io import BytesIO, StringIO
from datetime import datetime
import os
import qrcode
import uuid

app = Flask(__name__)

# Global variables
attendance_session = {
    'active': False,
    'module': None,
    'present_students': set(),
    'session_id': None,
    'qr_code_url': None
}

attendance_records = []

def load_students():
    """Load student data from text file"""
    students = []
    if os.path.exists('students.txt'):
        with open('students.txt', 'r') as f:
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

# Add this route before the main application routes
@app.route('/static/qrcodes/<path:filename>')
def serve_qrcode(filename):
    return send_from_directory('static/qrcodes', filename)
    
@app.route('/')
def index():
    modules = ['SEN152', 'OOP152', 'IDB152', 'ISP152', 'FIT152', 'TAS152']
    return render_template('index.html', modules=modules)

# Update the start_attendance route to use absolute URL
@app.route('/start_attendance', methods=['POST'])
def start_attendance():
    module = request.form.get('module')
    if not module:
        return jsonify({'success': False, 'message': 'Please select a module'})
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    qr_code_url = f"https://{request.host}/checkin/{session_id}"  # Use absolute URL
    
    # Generate QR code
    img = generate_qr_code(qr_code_url)
    img_buffer = BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    
    # Save QR code image
    qr_code_path = f"static/qrcodes/{session_id}.png"
    os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)
    with open(qr_code_path, 'wb') as f:
        f.write(img_buffer.getbuffer())
    
    attendance_session['active'] = True
    attendance_session['module'] = module
    attendance_session['present_students'] = set()
    attendance_session['session_id'] = session_id
    attendance_session['qr_code_url'] = f"/static/qrcodes/{session_id}.png"  # Use web path
    
    return jsonify({
        'success': True, 
        'message': f'Attendance session started for {module}',
        'qr_code_url': attendance_session['qr_code_url'],
        'checkin_url': qr_code_url  # Also return the direct URL
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
    return jsonify({
        'success': True, 
        'message': f'Checked in successfully: {student["name"]}',
        'name': student['name']
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

@app.route('/download_attendance', methods=['POST'])
def download_attendance():
    module = request.form.get('module')
    report_type = request.form.get('report_type')
    
    if not module:
        return jsonify({'success': False, 'message': 'Module not specified'})
    
    relevant_records = [r for r in attendance_records if r['module'] == module]
    
    if not relevant_records:
        return jsonify({'success': False, 'message': 'No attendance records found'})
    
    output = StringIO()
    writer = csv.writer(output)
    
    if report_type == 'full':
        writer.writerow(['Student Number', 'Name', 'Status', 'Date'])
        for record in relevant_records:
            writer.writerow([
                record['student_number'],
                record.get('name', ''),
                record['status'],
                record['date']
            ])
    elif report_type == 'absent':
        writer.writerow(['Student Number', 'Name', 'Date'])
        for record in relevant_records:
            if record['status'] == 'absent':
                writer.writerow([
                    record['student_number'],
                    record.get('name', ''),
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
    app.run(host='0.0.0.0', port=10000, debug=True)
