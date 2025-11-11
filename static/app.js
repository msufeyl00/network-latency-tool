// Initialize Socket.IO
const socket = io();

let latencyChart = null;
let currentData = {};

// Initialize Chart
function initChart() {
    const ctx = document.getElementById('latencyChart').getContext('2d');
    latencyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Latency Measurements',
                    font: { size: 16 }
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Latency (ms)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Ping Number'
                    }
                }
            }
        }
    });
}

// Start measurement
function startMeasurement() {
    const ipAddresses = document.getElementById('ipAddresses').value;
    const numPings = document.getElementById('numPings').value;
    
    if (!ipAddresses.trim()) {
        showAlert('Please enter at least one IP address', 'warning');
        return;
    }
    
    // Show progress bar
    document.getElementById('progressContainer').style.display = 'block';
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressBar').textContent = '0%';
    document.getElementById('progressStatus').textContent = 'Initializing...';
    
    // Disable button
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Measuring...';
    
    // Emit measurement request
    socket.emit('start_measurement', {
        ip_addresses: ipAddresses,
        num_pings: parseInt(numPings)
    });
}

// Socket.IO event handlers
socket.on('progress', function(data) {
    document.getElementById('progressStatus').textContent = data.status;
    const progress = Math.round(data.progress);
    document.getElementById('progressBar').style.width = progress + '%';
    document.getElementById('progressBar').textContent = progress + '%';
});

socket.on('measurement_complete', function(data) {
    currentData = data.data;
    
    // Hide progress bar
    document.getElementById('progressContainer').style.display = 'none';
    
    // Re-enable button
    const btn = document.querySelector('button[onclick="startMeasurement()"]');
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-play-fill"></i> Start Measurement';
    
    if (data.status === 'error') {
        showAlert(data.message || 'Measurement failed', 'danger');
        return;
    }
    
    // Update results table
    updateResultsTable(data.data);
    
    // Update chart
    updateChart(data.data);
    
    // Refresh history
    loadHistoricalData();
    
    // Check if all pings failed (might be permission issue)
    let allFailed = true;
    for (const [ip, stats] of Object.entries(data.data)) {
        if (stats.avg > 0) {
            allFailed = false;
            break;
        }
    }
    
    if (allFailed) {
        showAlert('⚠️ All pings failed! Make sure to run this app as Administrator (Windows) or with sudo (Linux/Mac) for ICMP ping to work.', 'warning');
    } else {
        showAlert('Measurement completed successfully!', 'success');
    }
});

// Update results table
function updateResultsTable(data) {
    const tbody = document.getElementById('resultsTable');
    tbody.innerHTML = '';
    
    for (const [ip, stats] of Object.entries(data)) {
        const row = tbody.insertRow();
        
        // Determine status badge based on packet loss and latency
        let statusBadge, statusText;
        
        if (stats.packet_loss >= 100 || stats.avg === 0) {
            // 100% packet loss or no response
            statusBadge = 'bg-danger';
            statusText = 'Failed';
        } else if (stats.packet_loss > 50) {
            // More than 50% packet loss
            statusBadge = 'bg-danger';
            statusText = 'Poor';
        } else if (stats.packet_loss > 20) {
            // 20-50% packet loss
            statusBadge = 'bg-warning';
            statusText = 'Unstable';
        } else if (stats.avg < 50) {
            // Low latency, low packet loss
            statusBadge = 'bg-success';
            statusText = 'Excellent';
        } else if (stats.avg < 100) {
            // Medium latency, low packet loss
            statusBadge = 'bg-warning';
            statusText = 'Good';
        } else {
            // High latency
            statusBadge = 'bg-danger';
            statusText = 'Poor';
        }
        
        // Network quality indicator for jitter
        const jitter = stats.jitter || 0;
        let jitterBadge = jitter < 10 ? 'bg-success' : jitter < 30 ? 'bg-warning' : 'bg-danger';
        
        row.innerHTML = `
            <td><strong>${ip}</strong></td>
            <td><span class="badge badge-latency ${statusBadge}">${stats.avg.toFixed(2)} ms</span></td>
            <td><small>${stats.min.toFixed(2)} / ${stats.max.toFixed(2)} ms</small></td>
            <td><span class="badge ${jitterBadge}">${jitter.toFixed(2)} ms</span></td>
            <td>${stats.packet_loss.toFixed(1)}%</td>
            <td><span class="badge bg-info">${stats.protocol || 'ICMP'}</span></td>
            <td>${(stats.throughput_estimate || 0).toFixed(2)} Mbps</td>
            <td><span class="badge ${statusBadge}">${statusText}</span></td>
        `;
    }
}

// Update chart
function updateChart(data) {
    const colors = [
        'rgba(255, 99, 132, 1)',
        'rgba(54, 162, 235, 1)',
        'rgba(255, 206, 86, 1)',
        'rgba(75, 192, 192, 1)',
        'rgba(153, 102, 255, 1)',
        'rgba(255, 159, 64, 1)'
    ];
    
    const datasets = [];
    let maxLength = 0;
    
    let colorIndex = 0;
    for (const [ip, stats] of Object.entries(data)) {
        const validLatencies = stats.latencies.map(l => l !== null ? l : 0);
        maxLength = Math.max(maxLength, validLatencies.length);
        
        datasets.push({
            label: ip,
            data: validLatencies,
            borderColor: colors[colorIndex % colors.length],
            backgroundColor: colors[colorIndex % colors.length].replace('1)', '0.1)'),
            tension: 0.1,
            borderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
        });
        colorIndex++;
    }
    
    latencyChart.data.labels = Array.from({length: maxLength}, (_, i) => i + 1);
    latencyChart.data.datasets = datasets;
    latencyChart.update();
}

// Clear data
function clearData() {
    if (confirm('Are you sure you want to clear all current data?')) {
        fetch('/clear_data', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                document.getElementById('resultsTable').innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-muted">
                            No data available. Run a measurement to see results.
                        </td>
                    </tr>
                `;
                
                latencyChart.data.labels = [];
                latencyChart.data.datasets = [];
                latencyChart.update();
                
                showAlert(data.message, 'success');
            });
    }
}

// Export data
function exportData(format) {
    window.location.href = `/export_data/${format}`;
}

// Load historical data
function loadHistoricalData() {
    fetch('/get_historical_data')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('historyTable');
            tbody.innerHTML = '';
            
            if (data.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center text-muted">
                            No historical data available.
                        </td>
                    </tr>
                `;
                return;
            }
            
            data.forEach((entry, index) => {
                const row = tbody.insertRow();
                const ips = Object.keys(entry.data).join(', ');
                
                const avgLatencies = Object.values(entry.data).map(d => d.avg);
                const overallAvg = avgLatencies.reduce((a, b) => a + b, 0) / avgLatencies.length;
                
                const packetLosses = Object.values(entry.data).map(d => d.packet_loss);
                const overallLoss = packetLosses.reduce((a, b) => a + b, 0) / packetLosses.length;
                
                row.innerHTML = `
                    <td>${entry.timestamp}</td>
                    <td><small>${ips}</small></td>
                    <td>${overallAvg.toFixed(2)} ms</td>
                    <td>${overallLoss.toFixed(1)}%</td>
                    <td>
                        <button class="btn btn-sm btn-info" onclick="viewHistoricalDetails(${index})">
                            <i class="bi bi-eye"></i> View
                        </button>
                    </td>
                `;
            });
        });
}

// View historical details
function viewHistoricalDetails(index) {
    fetch('/get_historical_data')
        .then(response => response.json())
        .then(data => {
            const entry = data[index];
            let details = `<h5>Details for ${entry.timestamp}</h5>`;
            details += '<table class="table table-sm"><thead><tr><th>IP</th><th>Avg</th><th>Min</th><th>Max</th><th>Loss</th></tr></thead><tbody>';
            
            for (const [ip, stats] of Object.entries(entry.data)) {
                details += `
                    <tr>
                        <td>${ip}</td>
                        <td>${stats.avg.toFixed(2)} ms</td>
                        <td>${stats.min.toFixed(2)} ms</td>
                        <td>${stats.max.toFixed(2)} ms</td>
                        <td>${stats.packet_loss.toFixed(1)}%</td>
                    </tr>
                `;
            }
            
            details += '</tbody></table>';
            showModal('Historical Details', details);
        });
}

// Clear history
function clearHistory() {
    if (confirm('Are you sure you want to clear all historical data?')) {
        fetch('/clear_history', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                loadHistoricalData();
                showAlert(data.message, 'success');
            });
    }
}

// Export history
function exportHistory(format) {
    window.location.href = `/export_history/${format}`;
}

// Generate map
function generateMap() {
    fetch('/generate_map')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('mapContainer').innerHTML = 
                    `<iframe src="${data.map_url}" class="w-100 h-100" frameborder="0"></iframe>`;
                showAlert(data.message, 'success');
            } else {
                showAlert(data.message, 'warning');
            }
        })
        .catch(error => {
            showAlert('Error generating map: ' + error, 'danger');
        });
}

// Load and save settings
function loadSettings() {
    fetch('/get_settings')
        .then(response => response.json())
        .then(data => {
            document.getElementById('settingsDefaultPings').value = data.default_pings;
            document.getElementById('settingsPingTimeout').value = data.ping_timeout;
            document.getElementById('settingsStoragePath').value = data.storage_path;
        });
}

function saveSettings() {
    const settings = {
        default_pings: parseInt(document.getElementById('settingsDefaultPings').value),
        ping_timeout: parseInt(document.getElementById('settingsPingTimeout').value),
        storage_path: document.getElementById('settingsStoragePath').value
    };
    
    fetch('/save_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        showAlert(data.message, 'success');
    });
}

// Show alert
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Show modal
function showModal(title, content) {
    const modalDiv = document.createElement('div');
    modalDiv.className = 'modal fade';
    modalDiv.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modalDiv);
    
    const modal = new bootstrap.Modal(modalDiv);
    modal.show();
    
    modalDiv.addEventListener('hidden.bs.modal', function () {
        modalDiv.remove();
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initChart();
    loadSettings();
    loadHistoricalData();
});
