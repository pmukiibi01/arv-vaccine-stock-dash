// ARV and Vaccine Stock-Out Prediction System - Frontend JavaScript

let currentSection = 'dashboard';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    loadDashboardStats();
    loadFacilities();
    loadCommodities();
    loadPredictions();
    loadAlerts();
    loadStockBalances();
    setupFileUpload();
}

// Navigation functions
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Show selected section
    document.getElementById(sectionName + '-section').style.display = 'block';
    
    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    event.target.classList.add('active');
    
    currentSection = sectionName;
    
    // Load section-specific data
    switch(sectionName) {
        case 'dashboard':
            loadDashboardStats();
            break;
        case 'predictions':
            loadPredictions();
            break;
        case 'alerts':
            loadAlerts();
            break;
        case 'stock-balances':
            loadStockBalances();
            break;
    }
}

// Dashboard functions
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/dashboard/stats');
        const data = await response.json();
        
        if (data.error) {
            console.error('Error loading dashboard stats:', data.error);
            return;
        }
        
        // Update stats cards
        document.getElementById('total-facilities').textContent = data.total_facilities;
        document.getElementById('total-commodities').textContent = data.total_commodities;
        document.getElementById('active-alerts').textContent = data.active_alerts;
        document.getElementById('recent-predictions').textContent = data.recent_predictions.length;
        
        // Update recent predictions table
        const tableBody = document.getElementById('recent-predictions-table');
        if (data.recent_predictions.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center">No recent predictions</td></tr>';
        } else {
            tableBody.innerHTML = data.recent_predictions.map(pred => `
                <tr>
                    <td>${pred.facility_name}</td>
                    <td>${pred.commodity_name}</td>
                    <td>${pred.predicted_date ? new Date(pred.predicted_date).toLocaleDateString() : 'N/A'}</td>
                    <td><span class="risk-${pred.risk_level.toLowerCase()}">${pred.risk_level}</span></td>
                    <td>${pred.confidence ? (pred.confidence * 100).toFixed(1) + '%' : 'N/A'}</td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

// Facilities and commodities loading
async function loadFacilities() {
    try {
        const response = await fetch('/api/facilities');
        const facilities = await response.json();
        
        if (facilities.error) {
            console.error('Error loading facilities:', facilities.error);
            return;
        }
        
        // Populate facility filter
        const facilityFilter = document.getElementById('facility-filter');
        facilityFilter.innerHTML = '<option value="">All Facilities</option>' +
            facilities.map(f => `<option value="${f.id}">${f.facility_name}</option>`).join('');
    } catch (error) {
        console.error('Error loading facilities:', error);
    }
}

async function loadCommodities() {
    try {
        const response = await fetch('/api/commodities');
        const commodities = await response.json();
        
        if (commodities.error) {
            console.error('Error loading commodities:', commodities.error);
            return;
        }
        
        // Populate commodity filter
        const commodityFilter = document.getElementById('commodity-filter');
        commodityFilter.innerHTML = '<option value="">All Commodities</option>' +
            commodities.map(c => `<option value="${c.id}">${c.commodity_name}</option>`).join('');
    } catch (error) {
        console.error('Error loading commodities:', error);
    }
}

// Predictions functions
async function loadPredictions() {
    try {
        const facilityId = document.getElementById('facility-filter').value;
        const commodityId = document.getElementById('commodity-filter').value;
        
        let url = '/api/predictions';
        const params = new URLSearchParams();
        if (facilityId) params.append('facility_id', facilityId);
        if (commodityId) params.append('commodity_id', commodityId);
        if (params.toString()) url += '?' + params.toString();
        
        const response = await fetch(url);
        const predictions = await response.json();
        
        if (predictions.error) {
            console.error('Error loading predictions:', predictions.error);
            return;
        }
        
        // Update predictions table
        const tableBody = document.getElementById('predictions-table');
        if (predictions.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center">No predictions found</td></tr>';
        } else {
            tableBody.innerHTML = predictions.map(pred => `
                <tr>
                    <td>${pred.facility_name}</td>
                    <td>${pred.commodity_name}</td>
                    <td>${new Date(pred.prediction_date).toLocaleDateString()}</td>
                    <td>${pred.predicted_stock_out_date ? new Date(pred.predicted_stock_out_date).toLocaleDateString() : 'N/A'}</td>
                    <td><span class="risk-${pred.risk_level.toLowerCase()}">${pred.risk_level}</span></td>
                    <td>${pred.confidence_score ? (pred.confidence_score * 100).toFixed(1) + '%' : 'N/A'}</td>
                    <td>${pred.model_used}</td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading predictions:', error);
    }
}

async function generatePrediction() {
    const facilityId = document.getElementById('facility-filter').value;
    const commodityId = document.getElementById('commodity-filter').value;
    
    if (!facilityId || !commodityId) {
        alert('Please select both facility and commodity');
        return;
    }
    
    try {
        const response = await fetch('/api/predictions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                facility_id: parseInt(facilityId),
                commodity_id: parseInt(commodityId)
            })
        });
        
        const result = await response.json();
        
        if (result.error) {
            alert('Error generating prediction: ' + result.error);
            return;
        }
        
        alert(`Prediction generated successfully!\nRisk Level: ${result.risk_level}\nPredicted Stock-Out: ${result.predicted_date}`);
        loadPredictions();
    } catch (error) {
        console.error('Error generating prediction:', error);
        alert('Error generating prediction');
    }
}

// Alerts functions
async function loadAlerts() {
    try {
        const response = await fetch('/api/alerts');
        const alerts = await response.json();
        
        if (alerts.error) {
            console.error('Error loading alerts:', alerts.error);
            return;
        }
        
        // Update alerts table
        const tableBody = document.getElementById('alerts-table');
        if (alerts.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center">No alerts found</td></tr>';
        } else {
            tableBody.innerHTML = alerts.map(alert => `
                <tr>
                    <td>${alert.facility_name}</td>
                    <td>${alert.commodity_name}</td>
                    <td>${alert.alert_type}</td>
                    <td><span class="badge bg-${getAlertBadgeColor(alert.alert_level)}">${alert.alert_level}</span></td>
                    <td>${alert.message}</td>
                    <td><span class="badge bg-${alert.is_resolved ? 'success' : 'warning'}">${alert.is_resolved ? 'Resolved' : 'Active'}</span></td>
                    <td>${new Date(alert.created_at).toLocaleDateString()}</td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

function getAlertBadgeColor(level) {
    switch (level) {
        case 'CRITICAL': return 'danger';
        case 'WARNING': return 'warning';
        case 'INFO': return 'info';
        default: return 'secondary';
    }
}

// Stock balances functions
async function loadStockBalances() {
    try {
        const response = await fetch('/api/stock-balances');
        const balances = await response.json();
        
        if (balances.error) {
            console.error('Error loading stock balances:', balances.error);
            return;
        }
        
        // Update stock balances table
        const tableBody = document.getElementById('stock-balances-table');
        if (balances.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No stock balances found</td></tr>';
        } else {
            tableBody.innerHTML = balances.map(balance => `
                <tr>
                    <td>${balance.facility_name}</td>
                    <td>${balance.commodity_name}</td>
                    <td>${balance.current_stock}</td>
                    <td>${balance.reorder_level}</td>
                    <td>${balance.maximum_stock}</td>
                    <td><span class="badge bg-${balance.stock_status === 'LOW' ? 'warning' : 'success'}">${balance.stock_status}</span></td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading stock balances:', error);
    }
}

// File upload functions
function setupFileUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    // Click to upload
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    // File input change
    fileInput.addEventListener('change', handleFileUpload);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload({ target: { files: files } });
        }
    });
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    // Show progress
    const progressDiv = document.getElementById('upload-progress');
    const progressBar = progressDiv.querySelector('.progress-bar');
    progressDiv.style.display = 'block';
    progressBar.style.width = '0%';
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        // Update progress
        progressBar.style.width = '100%';
        
        // Show result
        const resultDiv = document.getElementById('upload-result');
        if (result.error) {
            resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${result.error}</div>`;
        } else {
            resultDiv.innerHTML = `<div class="alert alert-success">${result.message}</div>`;
            // Reload relevant data
            loadDashboardStats();
            loadStockBalances();
            loadAlerts();
        }
        
        // Hide progress after a delay
        setTimeout(() => {
            progressDiv.style.display = 'none';
        }, 2000);
        
    } catch (error) {
        console.error('Error uploading file:', error);
        document.getElementById('upload-result').innerHTML = `<div class="alert alert-danger">Upload failed: ${error.message}</div>`;
    }
}

// Export functions
async function exportData(type) {
    try {
        const response = await fetch(`/api/export/${type}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${type}_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const error = await response.json();
            alert('Export failed: ' + error.error);
        }
    } catch (error) {
        console.error('Error exporting data:', error);
        alert('Export failed');
    }
}

// Sample data download
async function downloadSample(type) {
    try {
        const response = await fetch(`/api/sample-data/${type}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `sample_${type}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const error = await response.json();
            alert('Download failed: ' + error.error);
        }
    } catch (error) {
        console.error('Error downloading sample data:', error);
        alert('Download failed');
    }
}

// Filter change handlers
document.addEventListener('DOMContentLoaded', function() {
    const facilityFilter = document.getElementById('facility-filter');
    const commodityFilter = document.getElementById('commodity-filter');
    
    if (facilityFilter) {
        facilityFilter.addEventListener('change', loadPredictions);
    }
    
    if (commodityFilter) {
        commodityFilter.addEventListener('change', loadPredictions);
    }
});

