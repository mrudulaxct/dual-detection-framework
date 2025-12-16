// WebSocket Connection
let ws;
let charts = {};
const maxDataPoints = 100;

// Data buffers
const systemData = {
    time: [],
    output: [],
    control1: [],
    control2: []
};

const detectionData = {
    time: [],
    faultStatistic: [],
    faultThreshold: [],
    attackStatistic: [],
    attackThreshold: []
};

// Initialize WebSocket connection
function connectWebSocket() {
    ws = new WebSocket(`ws://${window.location.host}/ws`);
    
    ws.onopen = () => {
        console.log('Connected to server');
        updateSystemStatus('CONNECTED', 'success');
    };
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'update') {
            updateDashboard(message.data);
        } else if (message.type === 'history') {
            loadHistory(message.data);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateSystemStatus('ERROR', 'danger');
    };
    
    ws.onclose = () => {
        console.log('Disconnected from server');
        updateSystemStatus('DISCONNECTED', 'warning');
        setTimeout(connectWebSocket, 3000);
    };
}

// Initialize charts
function initCharts() {
    // System chart
    const systemCtx = document.getElementById('systemChart').getContext('2d');
    charts.system = new Chart(systemCtx, {
        type: 'line',
        data: {
            labels: systemData.time,
            datasets: [
                {
                    label: 'Output (y)',
                    data: systemData.output,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Control (u₁)',
                    data: systemData.control1,
                    borderColor: '#764ba2',
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                x: {
                    display: false
                },
                y: {
                    beginAtZero: false
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
    
    // Fault detector chart
    const faultCtx = document.getElementById('faultChart').getContext('2d');
    charts.fault = new Chart(faultCtx, {
        type: 'line',
        data: {
            labels: detectionData.time,
            datasets: [
                {
                    label: 'Statistic (J)',
                    data: detectionData.faultStatistic,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Threshold',
                    data: detectionData.faultThreshold,
                    borderColor: '#dc3545',
                    borderDash: [5, 5],
                    pointRadius: 0,
                    tension: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                x: {
                    display: false
                },
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
    
    // Attack detector chart
    const attackCtx = document.getElementById('attackChart').getContext('2d');
    charts.attack = new Chart(attackCtx, {
        type: 'line',
        data: {
            labels: detectionData.time,
            datasets: [
                {
                    label: 'Statistic (Jᵤ)',
                    data: detectionData.attackStatistic,
                    borderColor: '#764ba2',
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Threshold',
                    data: detectionData.attackThreshold,
                    borderColor: '#dc3545',
                    borderDash: [5, 5],
                    pointRadius: 0,
                    tension: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                x: {
                    display: false
                },
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Update dashboard with new data
function updateDashboard(data) {
    // Update state values
    document.getElementById('outputValue').textContent = data.output.toFixed(3);
    document.getElementById('control1Value').textContent = data.control[0].toFixed(3);
    document.getElementById('control2Value').textContent = data.control[1].toFixed(3);
    document.getElementById('referenceValue').textContent = data.reference.toFixed(2);
    
    // Update detection metrics
    document.getElementById('faultStatistic').textContent = data.fault_detector.statistic.toFixed(2);
    document.getElementById('faultThreshold').textContent = data.fault_detector.threshold.toFixed(2);
    document.getElementById('attackStatistic').textContent = data.attack_detector.statistic.toFixed(2);
    document.getElementById('attackThreshold').textContent = data.attack_detector.threshold.toFixed(2);
    
    // Update detector status
    updateDetectorStatus('faultDetectorStatus', data.fault_detector.detected);
    updateDetectorStatus('attackDetectorStatus', data.attack_detector.detected);
    
    // Update anomaly classification
    updateAnomalyClassification(data.anomaly_type, data.active_fault, data.active_attack);
    
    // Update network statistics
    document.getElementById('packetsSent').textContent = data.network.packets_sent;
    document.getElementById('packetsEncrypted').textContent = data.network.packets_encrypted;
    document.getElementById('packetsAttacked').textContent = data.network.packets_attacked;
    
    // Update chart data
    addDataPoint(data);
    updateCharts();
}

// Add data point to buffers
function addDataPoint(data) {
    // Keep only last N points
    if (systemData.time.length >= maxDataPoints) {
        systemData.time.shift();
        systemData.output.shift();
        systemData.control1.shift();
        systemData.control2.shift();
        detectionData.time.shift();
        detectionData.faultStatistic.shift();
        detectionData.faultThreshold.shift();
        detectionData.attackStatistic.shift();
        detectionData.attackThreshold.shift();
    }
    
    systemData.time.push(data.time.toFixed(1));
    systemData.output.push(data.output);
    systemData.control1.push(data.control[0]);
    systemData.control2.push(data.control[1]);
    
    detectionData.time.push(data.time.toFixed(1));
    detectionData.faultStatistic.push(data.fault_detector.statistic);
    detectionData.faultThreshold.push(data.fault_detector.threshold);
    detectionData.attackStatistic.push(data.attack_detector.statistic);
    detectionData.attackThreshold.push(data.attack_detector.threshold);
}

// Update charts
function updateCharts() {
    charts.system.update();
    charts.fault.update();
    charts.attack.update();
}

// Update detector status indicator
function updateDetectorStatus(elementId, detected) {
    const element = document.getElementById(elementId);
    const indicator = element.querySelector('.status-indicator');
    const text = element.querySelector('span');
    
    if (detected) {
        indicator.className = 'status-indicator danger';
        text.textContent = 'DETECTED';
        element.style.color = '#dc3545';
    } else {
        indicator.className = 'status-indicator normal';
        text.textContent = 'NORMAL';
        element.style.color = '#28a745';
    }
}

// Update anomaly classification
function updateAnomalyClassification(anomalyType, activeFault, activeAttack) {
    const resultDiv = document.getElementById('anomalyResult');
    const typeDiv = resultDiv.querySelector('.anomaly-type');
    const descDiv = document.getElementById('anomalyDescription');
    
    typeDiv.textContent = anomalyType.toUpperCase();
    
    const descriptions = {
        'Normal': 'System operating normally. No faults or attacks detected.',
        'System Fault': 'Fault detected on controller side. Plant malfunction or sensor failure likely.',
        'Kernel Attack': 'Stealthy attack detected on plant side. Attack bypasses controller detector.',
        'Fault and Attack': 'Both fault and attack detected. Multiple anomalies present.'
    };
    
    descDiv.textContent = descriptions[anomalyType] || descriptions['Normal'];
    
    // Update system status badge
    if (anomalyType !== 'Normal') {
        updateSystemStatus(anomalyType.toUpperCase(), 'danger');
    } else {
        updateSystemStatus('NORMAL', 'success');
    }
}

// Update system status badge
function updateSystemStatus(status, level) {
    const badge = document.getElementById('systemStatus');
    const valueSpan = badge.querySelector('.badge-value');
    valueSpan.textContent = status;
    
    badge.className = 'badge';
    if (level === 'danger') {
        badge.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
    } else if (level === 'warning') {
        badge.style.background = 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)';
    } else {
        badge.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    }
}

// Control functions
function setReference() {
    const value = parseFloat(document.getElementById('referenceSlider').value);
    sendCommand('set_reference', { value });
}

function injectFault() {
    const faultType = document.getElementById('faultType').value;
    const magnitude = parseFloat(document.getElementById('faultMagnitude').value);
    sendCommand('inject_fault', { fault_type: faultType, magnitude });
}

function injectAttack() {
    const attackType = document.getElementById('attackType').value;
    const magnitude = parseFloat(document.getElementById('attackMagnitude').value);
    sendCommand('inject_attack', { attack_type: attackType, magnitude });
}

function clearAnomalies() {
    sendCommand('clear_anomalies', {});
}

function sendCommand(command, params) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ command, ...params }));
    }
}

// Slider updates
document.getElementById('referenceSlider').addEventListener('input', (e) => {
    document.getElementById('referenceLabel').textContent = parseFloat(e.target.value).toFixed(1);
});

document.getElementById('faultMagnitude').addEventListener('input', (e) => {
    document.getElementById('faultMagLabel').textContent = parseFloat(e.target.value).toFixed(1);
});

document.getElementById('attackMagnitude').addEventListener('input', (e) => {
    document.getElementById('attackMagLabel').textContent = parseFloat(e.target.value).toFixed(1);
});

// Initialize on page load
window.addEventListener('load', () => {
    initCharts();
    connectWebSocket();
});