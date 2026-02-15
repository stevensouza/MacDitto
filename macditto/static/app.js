// MacDitto Web Interface JavaScript

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Run scan
function runScan() {
    showToast('Starting scan...', 'info');

    fetch('/scan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Scan completed successfully!', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showToast('Scan failed: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Error running scan', 'error');
        console.error('Error:', error);
    });
}

// Save profile modal
function saveProfile() {
    document.getElementById('saveModal').classList.add('show');
}

function closeSaveModal() {
    document.getElementById('saveModal').classList.remove('show');
}

function confirmSave() {
    const profileName = document.getElementById('profileName').value;

    fetch('/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            name: profileName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            closeSaveModal();
            document.getElementById('profileName').value = '';
        } else {
            showToast('Save failed: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Error saving profile', 'error');
        console.error('Error:', error);
    });
}

// Show profiles modal
function showProfiles() {
    fetch('/profiles')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayProfiles(data.profiles);
                document.getElementById('profileModal').classList.add('show');
            } else {
                showToast('Error loading profiles', 'error');
            }
        })
        .catch(error => {
            showToast('Error loading profiles', 'error');
            console.error('Error:', error);
        });
}

function displayProfiles(profiles) {
    const profileList = document.getElementById('profileList');

    if (profiles.length === 0) {
        profileList.innerHTML = '<p>No saved profiles found.</p>';
        return;
    }

    profileList.innerHTML = profiles.map(profile => `
        <div class="profile-item" onclick="loadProfile('${profile.name}')">
            <h4>${profile.name}</h4>
            <small>Modified: ${new Date(profile.modified).toLocaleString()}</small>
            <small> | Size: ${formatBytes(profile.size)}</small>
        </div>
    `).join('');
}

function closeProfileModal() {
    document.getElementById('profileModal').classList.remove('show');
}

function loadProfile(profileName) {
    window.location.href = `/load/${profileName}`;
}

// Export profile
function exportProfile() {
    showToast('Generating export files...', 'info');

    fetch('/export')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(data.message, 'success');
            } else {
                showToast('Export failed: ' + data.error, 'error');
            }
        })
        .catch(error => {
            showToast('Error exporting profile', 'error');
            console.error('Error:', error);
        });
}

// Utility functions
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Close modals on outside click
window.onclick = function(event) {
    const profileModal = document.getElementById('profileModal');
    const saveModal = document.getElementById('saveModal');

    if (event.target === profileModal) {
        closeProfileModal();
    }
    if (event.target === saveModal) {
        closeSaveModal();
    }
}
