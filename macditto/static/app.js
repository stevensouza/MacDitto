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
    // Start scan
    fetch('/scan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show progress modal
            document.getElementById('scanProgressModal').classList.add('show');
            // Connect to SSE for progress updates
            connectToScanProgress();
        } else {
            showToast('Scan failed: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Error starting scan', 'error');
        console.error('Error:', error);
    });
}

// Connect to scan progress SSE stream
function connectToScanProgress() {
    const eventSource = new EventSource('/scan_progress');

    eventSource.onmessage = function(event) {
        const progress = JSON.parse(event.data);

        // Update progress bar
        const progressBar = document.getElementById('progressBar');
        const progressPercentage = document.getElementById('progressPercentage');
        progressBar.style.width = progress.percentage + '%';
        progressPercentage.textContent = progress.percentage + '%';

        // Update step info
        document.getElementById('progressStep').textContent = progress.current_step;
        document.getElementById('progressCounter').textContent =
            `Step ${progress.step_number} of ${progress.total_steps}`;

        // Update item counts
        const itemCountsDiv = document.getElementById('progressItemCounts');
        if (Object.keys(progress.item_counts).length > 0) {
            let countsHTML = '<div style="margin-top: 1rem; padding: 1rem; background: var(--bg-tertiary); border-radius: 8px;">';
            countsHTML += '<h4 style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.5rem;">Items Found:</h4>';
            countsHTML += '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; font-size: 0.85rem;">';
            for (const [key, value] of Object.entries(progress.item_counts)) {
                countsHTML += `<div><span style="color: var(--text-secondary);">${formatLabel(key)}:</span> <span style="color: var(--cyan-bright); font-weight: 600;">${value}</span></div>`;
            }
            countsHTML += '</div></div>';
            itemCountsDiv.innerHTML = countsHTML;
        }

        // Check if completed
        if (progress.completed) {
            eventSource.close();

            if (progress.error) {
                // Show error
                document.getElementById('progressError').style.display = 'block';
                document.getElementById('progressError').textContent = 'Error: ' + progress.error;
                showToast('Scan failed: ' + progress.error, 'error');
            } else {
                // Success
                showToast('Scan completed and saved!', 'success');
                setTimeout(() => {
                    document.getElementById('scanProgressModal').classList.remove('show');
                    window.location.reload();
                }, 1500);
            }
        }
    };

    eventSource.onerror = function(error) {
        console.error('SSE Error:', error);
        eventSource.close();
        showToast('Connection error during scan', 'error');
    };
}

// Format label for display
function formatLabel(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// Format duration in seconds to human-readable string
function formatDuration(seconds) {
    if (seconds < 60) {
        return seconds.toFixed(1) + 's';
    } else if (seconds < 3600) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}m ${secs}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${mins}m`;
    }
}

// File button helper
function createFileButton(name, path) {
    const iconMap = {
        'install_script': '⚡',
        'brewfile': '🍺',
        'manual_steps': '📋',
        'setup_notes': '📝',
        'software_catalog': '📚'
    };

    const nameMap = {
        'brewfile': 'Brew',
        'install_script': 'install.sh',
        'manual_steps': 'Manual',
        'setup_notes': 'Notes',
        'software_catalog': 'Catalog'
    };

    const fullNameMap = {
        'brewfile': 'Brewfile',
        'install_script': 'install.sh',
        'manual_steps': 'MANUAL_STEPS.md',
        'setup_notes': 'SETUP_NOTES.md',
        'software_catalog': 'SOFTWARE_CATALOG.md'
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

// Show saved scans modal
function showSavedScans() {
    fetch('/saved_scans')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displaySavedScans(data.scans);
                document.getElementById('savedScansModal').classList.add('show');
            } else {
                showToast('Error loading saved scans', 'error');
            }
        })
        .catch(error => {
            showToast('Error loading saved scans', 'error');
            console.error('Error:', error);
        });
}

function displaySavedScans(scans) {
    const list = document.getElementById('savedScansList');

    if (scans.length === 0) {
        list.innerHTML = '<p style="color: var(--text-tertiary); text-align: center; padding: 2rem;">No saved scans yet. Click "Run Scan" to create one.</p>';
        return;
    }

    let tableHTML = `
        <table style="width: 100%; border-collapse: collapse; background: var(--bg-secondary); border: 1px solid var(--border-subtle); border-radius: 10px;">
            <thead>
                <tr>
                    <th style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border-subtle);">#</th>
                    <th style="padding: 0.75rem; border-bottom: 1px solid var(--border-subtle);">Date</th>
                    <th style="padding: 0.75rem; border-bottom: 1px solid var(--border-subtle);">Machine</th>
                    <th style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border-subtle);">Duration</th>
                    <th style="padding: 0.75rem; border-bottom: 1px solid var(--border-subtle);">Items</th>
                    <th style="padding: 0.75rem; border-bottom: 1px solid var(--border-subtle);">Installation Files</th>
                </tr>
            </thead>
            <tbody>
    `;

    scans.forEach((scan, index) => {
        const rowNumber = scans.length - index;
        const date = new Date(scan.scan_date);
        const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const duration = formatDuration(scan.duration_seconds);
        const dirname = scan.scan_dirname;

        // Format item counts
        let itemsHTML = '';
        if (scan.item_counts && Object.keys(scan.item_counts).length > 0) {
            const totalItems = Object.values(scan.item_counts).reduce((a, b) => a + b, 0);
            itemsHTML = `<div style="font-size: 0.85rem;">`;
            itemsHTML += `<div style="font-weight: 600; color: var(--cyan-bright); margin-bottom: 0.25rem;">Total: ${totalItems}</div>`;
            for (const [key, value] of Object.entries(scan.item_counts)) {
                if (value > 0) {
                    itemsHTML += `<div style="color: var(--text-secondary); font-size: 0.75rem;">${formatLabel(key)}: ${value}</div>`;
                }
            }
            itemsHTML += `</div>`;
        } else {
            itemsHTML = '<span style="color: var(--text-tertiary);">N/A</span>';
        }

        tableHTML += `
            <tr class="scan-row-clickable" onclick="loadSavedScan('${dirname}')" title="Click to load this scan into the dashboard" style="cursor: pointer;">
                <td style="padding: 0.75rem; text-align: center; font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--cyan-bright);">${rowNumber}</td>
                <td style="padding: 0.75rem; font-size: 0.8rem; color: var(--text-secondary);">${formattedDate}</td>
                <td style="padding: 0.75rem; font-size: 0.85rem;">${scan.machine_name}</td>
                <td style="padding: 0.75rem; text-align: center; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--text-secondary);">${duration}</td>
                <td style="padding: 0.75rem;">${itemsHTML}</td>
                <td style="padding: 0.75rem;" id="files-${rowNumber}" onclick="event.stopPropagation()"></td>
            </tr>
        `;
    });

    tableHTML += `
            </tbody>
        </table>
    `;

    list.innerHTML = tableHTML;

    // Add file buttons using DOM manipulation
    scans.forEach((scan, index) => {
        const rowNumber = scans.length - index;
        const filesCell = document.getElementById(`files-${rowNumber}`);
        if (filesCell && scan.files) {
            const buttonContainer = document.createElement('div');
            buttonContainer.style.cssText = 'display: flex; gap: 0.4rem; flex-wrap: wrap;';
            Object.entries(scan.files).forEach(([name, path]) => {
                buttonContainer.appendChild(createFileButton(name, path));
            });
            filesCell.appendChild(buttonContainer);
        }
    });
}

function closeSavedScansModal() {
    document.getElementById('savedScansModal').classList.remove('show');
}

function loadSavedScan(dirname) {
    window.location.href = `/load_scan/${dirname}`;
}

// Regenerate installation files
function regenerateFiles() {
    showToast('Regenerating installation files...', 'info');

    fetch('/regenerate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Installation files regenerated!', 'success');
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Error regenerating files', 'error');
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
    const savedScansModal = document.getElementById('savedScansModal');

    if (event.target === savedScansModal) {
        closeSavedScansModal();
    }
}

// Enable smooth scrolling
document.documentElement.style.scrollBehavior = 'smooth';

// Add keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Escape key closes modals
    if (event.key === 'Escape') {
        closeSavedScansModal();
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
