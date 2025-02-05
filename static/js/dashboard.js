// File: static/js/dashboard.js

class IoTDashboard {
    constructor() {
        // Initialize socket connection
        this.socket = io('http://127.0.0.1:5002', {
            transports: ['websocket'],
            autoConnect: true
        });
        
        // State management
        this.charts = {};
        this.devices = new Map();
        this.selectedDevice = null;
        this.isRealtime = true;
        
        // Initialize components
        this.initializeSocket();
        this.initializeCharts();
        this.loadDevices();
        this.setupEventListeners();
    }

    initializeSocket() {
        this.socket.on('connect', () => {
            console.log('Connected to monitoring service');
            this.updateConnectionStatus(true);
        });

        this.socket.on('connect_error', (error) => {
            console.error('Socket connection error:', error);
            this.updateConnectionStatus(false);
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from monitoring service');
            this.updateConnectionStatus(false);
        });

        this.socket.on('device_data', (data) => {
            console.log('Received device data:', data);
            this.handleDeviceData(data);
        });

        this.socket.on('devices_list', (devices) => {
            console.log('Received devices list:', devices);
            this.updateDevicesList(devices);
        });
    }

    initializeCharts() {
        const ctx = document.getElementById('realTimeChart').getContext('2d');
        
        this.charts.realTime = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Temperature (°C)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Humidity (%)',
                        data: [],
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'CPU Usage (%)',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.3,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 750,
                    easing: 'easeInOutQuart'
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 15
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                        titleColor: '#333',
                        bodyColor: '#666',
                        borderColor: '#ddd',
                        borderWidth: 1
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'nearest'
                }
            }
        });
    }

    async loadDevices() {
        try {
            // Try monitoring service first
            let response = await fetch('http://127.0.0.1:5002/api/devices');
            if (!response.ok) {
                // Fallback to device management service
                response = await fetch('http://127.0.0.1:5001/api/devices');
            }
            
            const data = await response.json();
            
            if (data.success && data.devices) {
                console.log('Loaded devices:', data.devices);
                this.updateDevicesList(data.devices);
            } else {
                throw new Error('Failed to load devices');
            }
        } catch (error) {
            console.error('Error loading devices:', error);
            this.showNotification('Error loading devices. Please try again.', 'error');
        }
    }

    updateDevicesList(devices) {
        const container = document.getElementById('devices-container');
        container.innerHTML = '';
        
        devices.forEach(device => {
            this.devices.set(device.device_id, device);
            this.createDeviceElement(device);
        });

        document.querySelector('.device-count').textContent = 
            `${devices.length} devices`;

        // Select first device by default if none selected
        if (!this.selectedDevice && devices.length > 0) {
            this.selectDevice(devices[0].device_id);
        }
    }

    createDeviceElement(device) {
        const div = document.createElement('div');
        div.className = 'device-item';
        div.setAttribute('data-device-id', device.device_id);
        
        div.innerHTML = `
            <div class="device-header">
                <h3>${device.name}</h3>
                <span class="device-status ${device.status || 'unknown'}"></span>
            </div>
            <div class="device-metrics">
                <div class="metric">
                    <span class="metric-label">Temperature</span>
                    <span class="metric-value" id="temp-${device.device_id}">--°C</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Humidity</span>
                    <span class="metric-value" id="humid-${device.device_id}">--%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">CPU</span>
                    <span class="metric-value" id="cpu-${device.device_id}">--%</span>
                </div>
            </div>
            <div class="device-footer">
                <span class="last-updated" id="update-${device.device_id}">Never</span>
            </div>
        `;
        
        div.addEventListener('click', () => this.selectDevice(device.device_id));
        document.getElementById('devices-container').appendChild(div);
    }

    handleDeviceData(data) {
        const deviceId = data.device_id;
        
        // Update device metrics
        document.getElementById(`temp-${deviceId}`).textContent = 
            `${data.temperature.toFixed(1)}°C`;
        document.getElementById(`humid-${deviceId}`).textContent = 
            `${data.humidity.toFixed(1)}%`;
        document.getElementById(`cpu-${deviceId}`).textContent = 
            `${data.cpu_usage.toFixed(1)}%`;
        document.getElementById(`update-${deviceId}`).textContent = 
            new Date().toLocaleTimeString();

        // Update charts if this is the selected device
        if (deviceId === this.selectedDevice) {
            this.updateCharts(data);
        }

        // Add to event log
        this.addEvent(`Received data from ${deviceId}`);
    }

    selectDevice(deviceId) {
        this.selectedDevice = deviceId;
        
        // Update UI selection
        document.querySelectorAll('.device-item').forEach(el => {
            el.classList.remove('selected');
        });
        document.querySelector(`[data-device-id="${deviceId}"]`)
            .classList.add('selected');

        // Reset chart data
        const chart = this.charts.realTime;
        chart.data.labels = [];
        chart.data.datasets.forEach(dataset => {
            dataset.data = [];
        });
        chart.update();

        // Subscribe to device updates
        this.socket.emit('subscribe_device', deviceId);

        // Load historical data
        this.loadDeviceHistory(deviceId);
    }

    async loadDeviceHistory(deviceId) {
        try {
            const response = await fetch(
                `http://127.0.0.1:5002/api/monitoring/data/${deviceId}?hours=1`
            );
            const data = await response.json();
            
            if (data.success && data.data) {
                data.data.reverse().forEach(point => {
                    this.updateCharts(point, false);
                });
                this.charts.realTime.update();
            }
        } catch (error) {
            console.error('Error loading device history:', error);
        }
    }

    updateCharts(data, updateChart = true) {
        const chart = this.charts.realTime;
        const timestamp = new Date(data.timestamp).toLocaleTimeString();

        chart.data.labels.push(timestamp);
        chart.data.datasets[0].data.push(data.temperature);
        chart.data.datasets[1].data.push(data.humidity);
        chart.data.datasets[2].data.push(data.cpu_usage);

        // Keep last 30 data points
        if (chart.data.labels.length > 30) {
            chart.data.labels.shift();
            chart.data.datasets.forEach(dataset => dataset.data.shift());
        }

        if (updateChart) {
            chart.update('none');
        }
    }

    addEvent(message) {
        const container = document.getElementById('eventsList');
        const event = document.createElement('div');
        event.className = 'event-item';
        
        event.innerHTML = `
            <span class="event-time">${new Date().toLocaleTimeString()}</span>
            <span class="event-message">${message}</span>
        `;
        
        container.insertBefore(event, container.firstChild);
        
        // Keep only last 50 events
        while (container.children.length > 50) {
            container.removeChild(container.lastChild);
        }
    }

    updateConnectionStatus(connected) {
        const status = document.getElementById('connection-status');
        if (status) {
            status.className = `connection-status ${connected ? 'connected' : 'disconnected'}`;
            status.textContent = connected ? 'Connected' : 'Disconnected';
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    setupEventListeners() {
        // Handle window resize for chart responsiveness
        window.addEventListener('resize', () => {
            if (this.charts.realTime) {
                this.charts.realTime.resize();
            }
        });

        // Handle real-time/historical toggle
        const viewToggle = document.getElementById('view-toggle');
        if (viewToggle) {
            viewToggle.addEventListener('change', (e) => {
                this.isRealtime = e.target.checked;
                this.updateViewMode();
            });
        }

        // Handle time range selection
        const timeRange = document.getElementById('time-range');
        if (timeRange) {
            timeRange.addEventListener('change', (e) => {
                const hours = parseInt(e.target.value);
                if (this.selectedDevice) {
                    this.loadDeviceHistory(this.selectedDevice, hours);
                }
            });
        }

        // Handle manual refresh
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                if (this.selectedDevice) {
                    this.loadDeviceHistory(this.selectedDevice);
                }
            });
        }
    }

    updateViewMode() {
        const chart = this.charts.realTime;
        if (!chart) return;

        if (this.isRealtime) {
            // Enable animations for real-time updates
            chart.options.animation = {
                duration: 750,
                easing: 'easeInOutQuart'
            };
        } else {
            // Disable animations for historical data
            chart.options.animation = false;
        }
        chart.update();
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString();
    }

    formatMetric(value, unit = '', precision = 1) {
        if (typeof value !== 'number') return '--';
        return `${value.toFixed(precision)}${unit}`;
    }

    async fetchDeviceStats(deviceId) {
        try {
            const response = await fetch(
                `http://127.0.0.1:5002/api/monitoring/stats/${deviceId}`
            );
            const data = await response.json();
            
            if (data.success) {
                this.updateDeviceStats(data.stats);
            }
        } catch (error) {
            console.error('Error fetching device stats:', error);
        }
    }

    updateDeviceStats(stats) {
        const container = document.getElementById('deviceStats');
        if (!container) return;

        container.innerHTML = `
            <div class="stat-card">
                <h4>Average Temperature</h4>
                <div class="stat-value">${this.formatMetric(stats.avg_temperature, '°C')}</div>
            </div>
            <div class="stat-card">
                <h4>Average Humidity</h4>
                <div class="stat-value">${this.formatMetric(stats.avg_humidity, '%')}</div>
            </div>
            <div class="stat-card">
                <h4>Average CPU</h4>
                <div class="stat-value">${this.formatMetric(stats.avg_cpu, '%')}</div>
            </div>
            <div class="stat-card">
                <h4>Total Readings</h4>
                <div class="stat-value">${stats.total_readings}</div>
            </div>
        `;
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new IoTDashboard();
});