document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const checkinLink = document.getElementById('checkinLink');
    const moduleSelect = document.getElementById('moduleSelect');
    const attendanceControls = document.getElementById('attendanceControls');
    const attendanceTableBody = document.getElementById('attendanceTableBody');
    const reportModule = document.getElementById('reportModule');
    const downloadFullBtn = document.getElementById('downloadFullBtn');
    const downloadAbsentBtn = document.getElementById('downloadAbsentBtn');
    
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
                startBtn.disabled = true;
                stopBtn.disabled = false;
                moduleSelect.disabled = true;
                attendanceControls.classList.remove('d-none');
                checkinLink.style.display = 'block';
                
                // Show QR code and link
                document.getElementById('qrCodeImage').src = data.qr_code_url;
                document.getElementById('checkinUrl').value = data.checkin_url;
                
                updateAttendanceList();
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
                startBtn.disabled = false;
                stopBtn.disabled = true;
                moduleSelect.disabled = false;
                checkinLink.style.display = 'none';
                reportModule.value = moduleSelect.value;
                downloadFullBtn.disabled = false;
                downloadAbsentBtn.disabled = false;
                alert(data.message);
            } else {
                alert(data.message);
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
    
    // Enable/disable download buttons
    reportModule.addEventListener('change', function() {
        const module = this.value;
        downloadFullBtn.disabled = !module;
        downloadAbsentBtn.disabled = !module;
    });
});
