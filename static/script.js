document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const checkInBtn = document.getElementById('checkInBtn');
    const studentNumberInput = document.getElementById('studentNumber');
    const moduleSelect = document.getElementById('moduleSelect');
    const attendanceControls = document.getElementById('attendanceControls');
    const checkInMessage = document.getElementById('checkInMessage');
    const attendanceTableBody = document.getElementById('attendanceTableBody');
    const reportModule = document.getElementById('reportModule');
    const downloadFullBtn = document.getElementById('downloadFullBtn');
    const downloadAbsentBtn = document.getElementById('downloadAbsentBtn');
    
    let currentModule = null;
    let attendanceInterval = null;
    
    // Start attendance session
    startBtn.addEventListener('click', function() {
        const module = moduleSelect.value;
        if (!module) {
            alert('Please select a module');
            return;
        }
        
        fetch('/start_attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `module=${module}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentModule = module;
                startBtn.disabled = true;
                stopBtn.disabled = false;
                moduleSelect.disabled = true;
                attendanceControls.classList.remove('d-none');
                checkInMessage.classList.add('d-none');
                
                // Start polling for attendance updates
                updateAttendanceList();
                attendanceInterval = setInterval(updateAttendanceList, 5000);
                
                alert(data.message);
            } else {
                alert(data.message);
            }
        });
    });
    
    // Stop attendance session
    stopBtn.addEventListener('click', function() {
        fetch('/stop_attendance', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                clearInterval(attendanceInterval);
                startBtn.disabled = false;
                stopBtn.disabled = true;
                moduleSelect.disabled = false;
                alert(data.message);
                
                // Enable download buttons for this module
                reportModule.value = currentModule;
                downloadFullBtn.disabled = false;
                downloadAbsentBtn.disabled = false;
            } else {
                alert(data.message);
            }
        });
    });
    
    // Student check-in
    checkInBtn.addEventListener('click', function() {
        const studentNumber = studentNumberInput.value.trim();
        if (!studentNumber) {
            alert('Please enter student number');
            return;
        }
        
        fetch('/check_in', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `student_number=${studentNumber}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                checkInMessage.textContent = `Checked in: ${data.name} (${studentNumber})`;
                checkInMessage.classList.remove('d-none', 'alert-danger');
                checkInMessage.classList.add('alert-success');
                studentNumberInput.value = '';
                updateAttendanceList();
            } else {
                checkInMessage.textContent = data.message;
                checkInMessage.classList.remove('d-none', 'alert-success');
                checkInMessage.classList.add('alert-danger');
            }
        });
    });
    
    // Update attendance list
    function updateAttendanceList() {
        fetch('/get_attendance_list')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                attendanceTableBody.innerHTML = '';
                data.data.forEach(student => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${student.student_number}</td>
                        <td>${student.name}</td>
                        <td>${student.status === 'present' ? '✔️ Present' : '❌ Absent'}</td>
                    `;
                    attendanceTableBody.appendChild(row);
                });
            }
        });
    }
    
    // Download reports
    downloadFullBtn.addEventListener('click', function() {
        const module = reportModule.value;
        if (!module) {
            alert('Please select a module');
            return;
        }
        
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/download_attendance';
        
        const moduleInput = document.createElement('input');
        moduleInput.type = 'hidden';
        moduleInput.name = 'module';
        moduleInput.value = module;
        form.appendChild(moduleInput);
        
        const typeInput = document.createElement('input');
        typeInput.type = 'hidden';
        typeInput.name = 'report_type';
        typeInput.value = 'full';
        form.appendChild(typeInput);
        
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
    });
    
    downloadAbsentBtn.addEventListener('click', function() {
        const module = reportModule.value;
        if (!module) {
            alert('Please select a module');
            return;
        }
        
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/download_attendance';
        
        const moduleInput = document.createElement('input');
        moduleInput.type = 'hidden';
        moduleInput.name = 'module';
        moduleInput.value = module;
        form.appendChild(moduleInput);
        
        const typeInput = document.createElement('input');
        typeInput.type = 'hidden';
        typeInput.name = 'report_type';
        typeInput.value = 'absent';
        form.appendChild(typeInput);
        
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
    });
    
    // Enable/disable download buttons based on module selection
    reportModule.addEventListener('change', function() {
        const module = this.value;
        downloadFullBtn.disabled = !module;
        downloadAbsentBtn.disabled = !module;
    });
});