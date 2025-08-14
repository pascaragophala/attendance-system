from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
import csv
from io import StringIO
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(8), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<Student {self.student_number}>'

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(8), nullable=False)
    module = db.Column(db.String(10), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(10), nullable=False)  # 'present' or 'absent'
    
    def __repr__(self):
        return f'<Attendance {self.student_number} {self.module} {self.status}>'

# Initialize database
with app.app_context():
    db.create_all()
    # Populate with sample student data if empty
    if Student.query.count() == 0:
        sample_students = [
            {'student_number': '25302223', 'name': 'John Smith'},
            {'student_number': '25302091', 'name': 'Emma Johnson'},
            # Add all other students from the file
        ]
        for student in sample_students:
            db.session.add(Student(student_number=student['student_number'], name=student['name']))
        db.session.commit()

# Global variables for attendance session
attendance_session = {
    'active': False,
    'module': None,
    'present_students': set()
}

@app.route('/')
def index():
    modules = ['SEN152', 'OOP152', 'IDB152', 'ISP152', 'FIT152', 'TAS152']
    return render_template('index.html', modules=modules)

@app.route('/start_attendance', methods=['POST'])
def start_attendance():
    module = request.form.get('module')
    if not module:
        return jsonify({'success': False, 'message': 'Please select a module'})
    
    attendance_session['active'] = True
    attendance_session['module'] = module
    attendance_session['present_students'] = set()
    
    return jsonify({'success': True, 'message': f'Attendance session started for {module}'})

@app.route('/stop_attendance', methods=['POST'])
def stop_attendance():
    if not attendance_session['active']:
        return jsonify({'success': False, 'message': 'No active attendance session'})
    
    module = attendance_session['module']
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Mark all students not present as absent
    all_students = Student.query.all()
    for student in all_students:
        if student.student_number not in attendance_session['present_students']:
            record = Attendance(
                student_number=student.student_number,
                module=module,
                date=date,
                status='absent'
            )
            db.session.add(record)
    
    # Mark present students
    for student_number in attendance_session['present_students']:
        record = Attendance(
            student_number=student_number,
            module=module,
            date=date,
            status='present'
        )
        db.session.add(record)
    
    db.session.commit()
    attendance_session['active'] = False
    
    return jsonify({'success': True, 'message': f'Attendance session stopped for {module}'})

@app.route('/check_in', methods=['POST'])
def check_in():
    if not attendance_session['active']:
        return jsonify({'success': False, 'message': 'No active attendance session'})
    
    student_number = request.form.get('student_number')
    if not student_number:
        return jsonify({'success': False, 'message': 'Please enter student number'})
    
    student = Student.query.filter_by(student_number=student_number).first()
    if not student:
        return jsonify({'success': False, 'message': 'Invalid student number'})
    
    if student_number in attendance_session['present_students']:
        return jsonify({'success': False, 'message': 'Already checked in'})
    
    attendance_session['present_students'].add(student_number)
    return jsonify({'success': True, 'message': 'Checked in successfully', 'name': student.name})

@app.route('/get_attendance_list')
def get_attendance_list():
    if not attendance_session['active']:
        return jsonify({'success': False, 'message': 'No active attendance session'})
    
    all_students = Student.query.all()
    attendance_list = []
    
    for student in all_students:
        attendance_list.append({
            'student_number': student.student_number,
            'name': student.name,
            'status': 'present' if student.student_number in attendance_session['present_students'] else 'absent'
        })
    
    return jsonify({'success': True, 'data': attendance_list})

@app.route('/download_attendance', methods=['POST'])
def download_attendance():
    module = request.form.get('module')
    report_type = request.form.get('report_type')
    
    if not module:
        return jsonify({'success': False, 'message': 'Module not specified'})
    
    records = Attendance.query.filter_by(module=module).order_by(Attendance.date.desc(), Attendance.student_number).all()
    
    if not records:
        return jsonify({'success': False, 'message': 'No attendance records found'})
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    if report_type == 'full':
        writer.writerow(['Student Number', 'Name', 'Status', 'Date'])
        for record in records:
            student = Student.query.filter_by(student_number=record.student_number).first()
            writer.writerow([
                record.student_number,
                student.name if student else 'Unknown',
                record.status,
                record.date
            ])
    elif report_type == 'absent':
        writer.writerow(['Student Number', 'Name', 'Date'])
        for record in records:
            if record.status == 'absent':
                student = Student.query.filter_by(student_number=record.student_number).first()
                writer.writerow([
                    record.student_number,
                    student.name if student else 'Unknown',
                    record.date
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
    app.run(debug=True)