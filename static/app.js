// WebSocket and Chart globals
let ws;
let charts = {};
const maxDataPoints = 100;
let isConnected = false;

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

// ========== PARTICLES ANIMATION ==========
function initParticles() {
    const canvas = document.getElementById('particles');
    if (!canvas) {
        console.warn('Particles canvas not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 0.5;
            this.vy = (Math.random() - 0.5) * 0.5;
            this.radius = Math.random() * 2;
        }
        
        update() {
            this.x += this.vx;
            this.y += this.vy;
            if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
            if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
        }
        
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(0, 243, 255, 0.5)';
            ctx.fill();
        }
    }
    
    const particles = [];
    for (let i = 0; i < 100; i++) {
        particles.push(new Particle());
    }
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            p.update();
            p.draw();
        });
        
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                if (dist < 100) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(0, 243, 255, ${0.2 * (1 - dist / 100)})`;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animate);
    }
    
    animate();
    
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

// ========== WEBSOCKET CONNECTION ==========
function connectWebSocket() {
    const wsUrl = `ws://${window.location.host}/ws`;
    console.log('🔌 Connecting to:', wsUrl);
    
    try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log('✅ WebSocket Connected');
            isConnected = true;
            updateConnectionStatus(true);
            showNotification('Connected to server', 'success');
        };
        
        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                if (message.type === 'update') {
                    updateDashboard(message.data);
                }
            } catch (error) {
                console.error('❌ Message parse error:', error);
            }
        };
        
        ws.onerror = (error) => {
            console.error('❌ WebSocket Error:', error);
            isConnected = false;
            updateConnectionStatus(false);
        };
        
        ws.onclose = () => {
            console.log('⚠️ WebSocket Disconnected');
            isConnected = false;
            updateConnectionStatus(false);
            showNotification('Disconnected. Reconnecting...', 'warning');
            setTimeout(connectWebSocket, 3000);
        };
    } catch (error) {
        console.error('❌ Connection failed:', error);
        setTimeout(connectWebSocket, 3000);
    }
}

function updateConnectionStatus(connected) {
    const statusPill = document.getElementById('systemStatus');
    if (!statusPill) return;
    
    if (connected) {
        statusPill.style.borderColor = '#00ff88';
        statusPill.style.boxShadow = '0 0 20px rgba(0, 255, 136, 0.5)';
        const dot = statusPill.querySelector('.status-dot');
        if (dot) dot.style.background = '#00ff88';
    } else {
        statusPill.style.borderColor = '#ff3366';
        statusPill.style.boxShadow = '0 0 20px rgba(255, 51, 102, 0.5)';
        const dot = statusPill.querySelector('.status-dot');
        if (dot) dot.style.background = '#ff3366';
    }
}

// ========== CHARTS INITIALIZATION ==========
function initCharts() {
    console.log('📊 Initializing charts...');
    
    const chartConfig = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 0 },
        plugins: {
            legend: {
                labels: {
                    color: '#ffffff',
                    font: { size: 11, family: 'Rajdhani' }
                }
            }
        },
        scales: {
            x: { display: false },
            y: {
                grid: { color: 'rgba(0, 243, 255, 0.1)' },
                ticks: { 
                    color: '#a8a8b8',
                    font: { family: 'Orbitron' }
                }
            }
        }
    };
    
    try {
        const systemCanvas = document.getElementById('systemChart');
        const faultCanvas = document.getElementById('faultChart');
        const attackCanvas = document.getElementById('attackChart');
        
        if (!systemCanvas || !faultCanvas || !attackCanvas) {
            console.error('❌ Chart canvases not found!');
            return;
        }
        
        charts.system = new Chart(systemCanvas, {
            type: 'line',
            data: {
                labels: systemData.time,
                datasets: [
                    {
                        label: 'Output',
                        data: systemData.output,
                        borderColor: '#00f3ff',
                        backgroundColor: 'rgba(0, 243, 255, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        pointRadius: 0
                    },
                    {
                        label: 'Control U₁',
                        data: systemData.control1,
                        borderColor: '#bf00ff',
                        backgroundColor: 'rgba(191, 0, 255, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        pointRadius: 0
                    }
                ]
            },
            options: chartConfig
        });
        
        charts.fault = new Chart(faultCanvas, {
            type: 'line',
            data: {
                labels: detectionData.time,
                datasets: [
                    {
                        label: 'Statistic',
                        data: detectionData.faultStatistic,
                        borderColor: '#00f3ff',
                        backgroundColor: 'rgba(0, 243, 255, 0.2)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Threshold',
                        data: detectionData.faultThreshold,
                        borderColor: '#ff3366',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        tension: 0
                    }
                ]
            },
            options: { ...chartConfig, plugins: { legend: { display: false } } }
        });
        
        charts.attack = new Chart(attackCanvas, {
            type: 'line',
            data: {
                labels: detectionData.time,
                datasets: [
                    {
                        label: 'Statistic',
                        data: detectionData.attackStatistic,
                        borderColor: '#bf00ff',
                        backgroundColor: 'rgba(191, 0, 255, 0.2)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Threshold',
                        data: detectionData.attackThreshold,
                        borderColor: '#ff3366',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        tension: 0
                    }
                ]
            },
            options: { ...chartConfig, plugins: { legend: { display: false } } }
        });
        
        console.log('✅ Charts initialized');
    } catch (error) {
        console.error('❌ Chart initialization error:', error);
    }
}

// ========== UPDATE DASHBOARD ==========
function updateDashboard(data) {
    if (!data) {
        console.warn('⚠️ No data received');
        return;
    }
    
    console.log('📊 Updating dashboard:', data.time);
    
    try {
        // Update metric values with smooth animation
        updateMetricValue('outputValue', data.output, 3);
        updateMetricValue('control1Value', data.control[0], 3);
        updateMetricValue('control2Value', data.control[1], 3);
        updateMetricValue('referenceValue', data.reference, 2);
        
        // Update detection statistics
        updateMetricValue('faultStatistic', data.fault_detector.statistic, 2);
        updateMetricValue('attackStatistic', data.attack_detector.statistic, 2);
        updateMetricValue('faultThreshold', data.fault_detector.threshold, 2);
        updateMetricValue('attackThreshold', data.attack_detector.threshold, 2);
        
        // Update detector status
        updateDetectorStatus('faultDetectorCard', 'faultDetectorStatus', data.fault_detector.detected);
        updateDetectorStatus('attackDetectorCard', 'attackDetectorStatus', data.attack_detector.detected);
        
        // Update classification
        updateClassification(data.anomaly_type);
        
        // Update network stats
        updateMetricValue('packetsSent', data.network.packets_sent, 0);
        updateMetricValue('packetsEncrypted', data.network.packets_encrypted, 0);
        updateMetricValue('packetsAttacked', data.network.packets_attacked, 0);
        
        // Update charts
        addDataPoint(data);
        updateCharts();
        
        // Pulse metric cards
        pulseMetricCards();
        
    } catch (error) {
        console.error('❌ Dashboard update error:', error);
    }
}

function updateMetricValue(id, value, decimals) {
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`⚠️ Element not found: ${id}`);
        return;
    }
    
    const displayValue = typeof value === 'number' ? value.toFixed(decimals) : String(value);
    
    if (element.textContent !== displayValue) {
        element.textContent = displayValue;
        element.style.transform = 'scale(1.1)';
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 200);
    }
}

function updateDetectorStatus(cardId, statusId, detected) {
    const card = document.getElementById(cardId);
    const status = document.getElementById(statusId);
    
    if (!card || !status) return;
    
    if (detected) {
        card.style.borderColor = '#ff3366';
        card.style.boxShadow = '0 0 40px rgba(255, 51, 102, 0.6)';
        card.classList.add('alert');
        status.classList.add('alert');
        
        const span = status.querySelector('span');
        if (span) span.textContent = 'ALERT';
        
        // Shake animation
        card.style.animation = 'shake 0.5s';
        setTimeout(() => {
            card.style.animation = '';
        }, 500);
    } else {
        card.style.borderColor = '';
        card.style.boxShadow = '';
        card.classList.remove('alert');
        status.classList.remove('alert');
        
        const span = status.querySelector('span');
        if (span) span.textContent = 'NORMAL';
    }
}

function updateClassification(type) {
    const badge = document.getElementById('anomalyResult');
    const desc = document.getElementById('anomalyDescription');
    const panel = document.getElementById('classificationPanel');
    
    if (!badge || !desc || !panel) return;
    
    const configs = {
        'Normal': {
            text: 'NORMAL',
            desc: 'System operating normally',
            color: '#00ff88',
            border: '#00ff88'
        },
        'System Fault': {
            text: 'FAULT',
            desc: 'Controller-side fault detected',
            color: '#ffee00',
            border: '#ffee00'
        },
        'Kernel Attack': {
            text: 'ATTACK',
            desc: 'Plant-side attack detected',
            color: '#ff0080',
            border: '#ff0080'
        },
        'Fault and Attack': {
            text: 'CRITICAL',
            desc: 'Multiple anomalies detected',
            color: '#ff3366',
            border: '#ff3366'
        }
    };
    
    const config = configs[type] || configs['Normal'];
    
    badge.textContent = config.text;
    badge.style.background = `linear-gradient(135deg, ${config.color}, ${config.color}dd)`;
    badge.style.boxShadow = `0 0 30px ${config.color}`;
    desc.textContent = config.desc;
    panel.style.borderColor = config.border;
    
    // Pulse animation
    panel.style.transform = 'scale(1.05)';
    setTimeout(() => {
        panel.style.transform = 'scale(1)';
    }, 300);
}

function pulseMetricCards() {
    const cards = document.querySelectorAll('.metric-card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.style.transform = 'scale(1.02)';
            setTimeout(() => {
                card.style.transform = 'scale(1)';
            }, 100);
        }, index * 50);
    });
}

function addDataPoint(data) {
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

function updateCharts() {
    try {
        if (charts.system) charts.system.update('none');
        if (charts.fault) charts.fault.update('none');
        if (charts.attack) charts.attack.update('none');
    } catch (error) {
        console.error('❌ Chart update error:', error);
    }
}

// ========== SLIDERS ==========
function setupSliders() {
    const sliders = document.querySelectorAll('.cyber-slider');
    console.log(`🎚️ Setting up ${sliders.length} sliders`);
    
    sliders.forEach(slider => {
        const wrapper = slider.closest('.slider-wrapper');
        if (!wrapper) return;
        
        const fill = wrapper.querySelector('.slider-fill');
        const valueDisplay = wrapper.querySelector('.slider-value');
        
        const updateSlider = (e) => {
            const value = parseFloat(e.target.value);
            const min = parseFloat(e.target.min);
            const max = parseFloat(e.target.max);
            const percent = ((value - min) / (max - min)) * 100;
            
            if (fill) fill.style.width = percent + '%';
            if (valueDisplay) valueDisplay.textContent = value.toFixed(1);
        };
        
        slider.addEventListener('input', updateSlider);
        slider.addEventListener('change', updateSlider);
        
        // Initialize
        updateSlider({ target: slider });
    });
}

// ========== CONTROL FUNCTIONS ==========
function setReference() {
    const value = parseFloat(document.getElementById('referenceSlider').value);
    console.log('🎯 Setting reference:', value);
    sendCommand('set_reference', { value });
    showNotification(`Reference set to ${value.toFixed(1)}`, 'success');
}

function injectFault() {
    const type = document.getElementById('faultType').value;
    const magnitude = parseFloat(document.getElementById('faultMagnitude').value);
    console.log('⚠️ Injecting fault:', type, magnitude);
    sendCommand('inject_fault', { fault_type: type, magnitude });
    showNotification(`${type} fault injected`, 'warning');
}

function injectAttack() {
    const type = document.getElementById('attackType').value;
    const magnitude = parseFloat(document.getElementById('attackMagnitude').value);
    console.log('🎭 Injecting attack:', type, magnitude);
    sendCommand('inject_attack', { attack_type: type, magnitude });
    showNotification(`${type} injected`, 'danger');
}

function clearAnomalies() {
    console.log('🔄 Clearing anomalies');
    sendCommand('clear_anomalies', {});
    showNotification('All anomalies cleared', 'success');
}

function sendCommand(command, params) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const message = { command, ...params };
        console.log('📤 Sending command:', message);
        ws.send(JSON.stringify(message));
    } else {
        console.error('❌ WebSocket not connected');
        showNotification('Not connected to server', 'danger');
    }
}

function showNotification(message, type = 'info') {
    const colors = {
        success: '#00ff88',
        warning: '#ffee00',
        danger: '#ff3366',
        info: '#00f3ff'
    };
    
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, ${colors[type]}, ${colors[type]}dd);
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        font-weight: 700;
        box-shadow: 0 0 30px ${colors[type]};
        z-index: 9999;
        animation: slideIn 0.3s ease;
        font-family: 'Orbitron', sans-serif;
        font-size: 14px;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ========== ANIMATIONS ==========
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        50% { transform: translateX(10px); }
        75% { transform: translateX(-10px); }
    }
    .metric-value {
        transition: transform 0.2s ease;
    }
    .classification-panel {
        transition: all 0.3s ease;
    }
`;
document.head.appendChild(style);

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Dual Detection Framework...');
    console.log('🌐 Host:', window.location.host);
    
    // Initialize components
    initParticles();
    initCharts();
    setupSliders();
    
    // Connect WebSocket
    connectWebSocket();
    
    // Show connection attempt
    showNotification('Connecting to server...', 'info');
    
    console.log('✅ Initialization complete');
});

// Expose functions to global scope for button onclick
window.setReference = setReference;
window.injectFault = injectFault;
window.injectAttack = injectAttack;
window.clearAnomalies = clearAnomalies;