// MacDitto Web Interface JavaScript

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 5000);
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
            const message = `${data.message}\n📁 Saved to: ${data.filepath}`;
            showToast(message, 'success');
            // Also log the full path to console for easy copying
            console.log('Profile saved to:', data.filepath);
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
                showToast('Export completed! View in Export History.', 'success');
                console.log('Export location:', data.export_dir);
                console.log('Files:', data.files);

                // Auto-open export history modal after 1 second
                setTimeout(() => {
                    showExportHistory();
                }, 1000);
            } else {
                showToast('Export failed: ' + data.error, 'error');
            }
        })
        .catch(error => {
            showToast('Error exporting profile', 'error');
            console.error('Error:', error);
        });
}

// Show export history modal
function showExportHistory() {
    fetch('/export_history')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayExportHistory(data.exports);
                document.getElementById('exportHistoryModal').classList.add('show');
            } else {
                showToast('Error loading export history', 'error');
            }
        })
        .catch(error => {
            showToast('Error loading export history', 'error');
            console.error('Error:', error);
        });
}

function createFileButton(name, path) {
    const iconMap = {
        'install_script': '⚡',
        'brewfile': '🍺',
        'manual_steps': '📋',
        'config': '⚙️'
    };

    const nameMap = {
        'brewfile': 'Brew',
        'install_script': 'install.sh',
        'manual_steps': 'Manual',
        'config': 'Config'
    };

    const fullNameMap = {
        'brewfile': 'Brewfile',
        'install_script': 'install.sh',
        'manual_steps': 'MANUAL_STEPS.md',
        'config': 'macditto_config.json'
    };

    const icon = iconMap[name] || '📄';
    const shortName = nameMap[name] || name;
    const fullName = fullNameMap[name] || name;

    const btn = document.createElement('a');
    btn.href = '/open_file?path=' + encodeURIComponent(path);
    btn.target = '_blank';
    btn.title = fullName;
    btn.style.cssText = 'display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem 0.5rem; background: var(--bg-tertiary); border: 1px solid var(--border-subtle); border-radius: 4px; text-decoration: none; color: var(--text-primary); font-size: 0.75rem; transition: all 0.2s;';
    btn.onmouseover = function() {
        this.style.borderColor = 'var(--cyan-bright)';
        this.style.background = 'var(--bg-elevated)';
    };
    btn.onmouseout = function() {
        this.style.borderColor = 'var(--border-subtle)';
        this.style.background = 'var(--bg-tertiary)';
    };

    const iconSpan = document.createElement('span');
    iconSpan.style.fontSize = '0.9rem';
    iconSpan.textContent = icon;

    const nameSpan = document.createElement('span');
    nameSpan.style.fontFamily = "'JetBrains Mono', monospace";
    nameSpan.style.fontSize = '0.7rem';
    nameSpan.textContent = shortName;

    btn.appendChild(iconSpan);
    btn.appendChild(nameSpan);

    return btn;
}

function displayExportHistory(exports) {
    const historyList = document.getElementById('exportHistoryList');

    if (exports.length === 0) {
        historyList.innerHTML = '<p style="color: var(--text-tertiary); text-align: center; padding: 2rem;">No exports yet. Click "Export" to create one.</p>';
        return;
    }

    // Build table using innerHTML for clean rendering
    let tableHTML = `
        <table style="width: 100%; border-collapse: collapse; background: var(--bg-secondary); border: 1px solid var(--border-subtle); border-radius: 10px;">
            <thead>
                <tr>
                    <th style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border-subtle);">#</th>
                    <th style="padding: 0.75rem; border-bottom: 1px solid var(--border-subtle);">Export Name</th>
                    <th style="padding: 0.75rem; border-bottom: 1px solid var(--border-subtle);">Date</th>
                    <th style="padding: 0.75rem; border-bottom: 1px solid var(--border-subtle);">Machine</th>
                    <th style="padding: 0.75rem; border-bottom: 1px solid var(--border-subtle);">Location</th>
                    <th style="padding: 0.75rem; border-bottom: 1px solid var(--border-subtle);">Files</th>
                </tr>
            </thead>
            <tbody>
    `;

    exports.forEach((exp, index) => {
        const rowNumber = exports.length - index;
        const date = new Date(exp.export_date);
        const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

        tableHTML += `
            <tr>
                <td style="padding: 0.75rem; text-align: center; font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--cyan-bright);">${rowNumber}</td>
                <td style="padding: 0.75rem; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">${exp.export_dirname}</td>
                <td style="padding: 0.75rem; font-size: 0.8rem; color: var(--text-secondary);">${formattedDate}</td>
                <td style="padding: 0.75rem; font-size: 0.85rem;">${exp.machine_name}</td>
                <td style="padding: 0.75rem; max-width: 400px; overflow: hidden; text-overflow: ellipsis;"><code style="font-size: 0.7rem;">${exp.export_dir}</code></td>
                <td style="padding: 0.75rem;" id="files-${rowNumber}"></td>
            </tr>
        `;
    });

    tableHTML += `
            </tbody>
        </table>
    `;

    historyList.innerHTML = tableHTML;

    // Now add buttons using DOM manipulation
    exports.forEach((exp, index) => {
        const rowNumber = exports.length - index;
        const filesCell = document.getElementById(`files-${rowNumber}`);
        if (filesCell && exp.files) {
            const buttonContainer = document.createElement('div');
            buttonContainer.style.cssText = 'display: flex; gap: 0.4rem; flex-wrap: wrap;';
            Object.entries(exp.files).forEach(([name, path]) => {
                buttonContainer.appendChild(createFileButton(name, path));
            });
            filesCell.appendChild(buttonContainer);
        }
    });
}

function closeExportHistoryModal() {
    document.getElementById('exportHistoryModal').classList.remove('show');
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
    const exportHistoryModal = document.getElementById('exportHistoryModal');

    if (event.target === profileModal) {
        closeProfileModal();
    }
    if (event.target === saveModal) {
        closeSaveModal();
    }
    if (event.target === exportHistoryModal) {
        closeExportHistoryModal();
    }
}

// Enable smooth scrolling
document.documentElement.style.scrollBehavior = 'smooth';

// Add keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Escape key closes modals
    if (event.key === 'Escape') {
        closeProfileModal();
        closeSaveModal();
        closeExportHistoryModal();
    }

    // Ctrl/Cmd + K for search (if search box exists)
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        const searchBox = document.getElementById('searchBox');
        if (searchBox) {
            searchBox.focus();
        }
    }
});
