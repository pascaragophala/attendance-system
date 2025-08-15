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
		// Update the start attendance success handler
		.then(data => {
			if (data.success) {
				startBtn.disabled = true;
				stopBtn.disabled = false;
				moduleSelect.disabled = true;
				attendanceControls.classList.remove('d-none');
				checkInMessage.classList.add('d-none');
				
				// Show QR code
				document.getElementById('qrCodeSection').classList.remove('d-none');
				document.getElementById('qrCodeImage').src = data.qr_code_url;
				
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
                reportModule.value = moduleSelect.value;
                downloadFullBtn.disabled = false;
                downloadAbsentBtn.disabled = false;
                alert(data.message);
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
                checkInMessage.textContent = data.message;
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
    
	// Update the row creation in updateAttendanceList()
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
