function generateFilteredReport(reportType, format) {
    // For now, just call generateReport. You can extend this to add filters.
    generateReport(reportType, format);
}
// Dashboard JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add click animations to dashboard cards
    const dashboardCards = document.querySelectorAll('.dashboard-card');
    
    dashboardCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05) translateY(-10px)';
            this.style.transition = 'all 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1) translateY(0)';
        });
    });
    
    // Add loading animations for tables
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        table.style.opacity = '0';
        table.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            table.style.transition = 'all 0.6s ease';
            table.style.opacity = '1';
            table.style.transform = 'translateY(0)';
        }, 300);
    });
    
    // Auto-refresh data every 30 seconds
    setInterval(refreshDashboardData, 30000);
    
    // Update current time
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
});

function refreshDashboardData() {
    // This would make AJAX calls to update dashboard data
    console.log('Refreshing dashboard data...');
}

function updateCurrentTime() {
    const timeElement = document.getElementById('currentTime');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = now.toLocaleTimeString();
    }
}

// Feed Plan Management
function addFeedPlan() {
    const modal = new bootstrap.Modal(document.getElementById('addFeedPlanModal'));
    modal.show();
    }

    // Responsive Edit Feed Plan
    function editFeedPlan(planId) {
        // Fetch plan data (simulate for now, replace with AJAX in production)
        fetch(`/ajax/get_feed_plan/${planId}/`)
            .then(response => response.json())
            .then(plan => {
                document.getElementById('editPlanId').value = plan.id;
                document.getElementById('editSpecies').value = plan.species_name || '';
                document.getElementById('editFeedType').value = plan.feed_type || '';
                document.getElementById('editQuantity').value = plan.quantity_per_day || '';
                document.getElementById('editFeedingTimes').value = plan.feeding_times ? plan.feeding_times.join(', ') : '';
                document.getElementById('editStartDate').value = plan.start_date || '';
                document.getElementById('editEndDate').value = plan.end_date || '';
                document.getElementById('editIsActive').value = plan.is_active ? 'true' : 'false';
                const modal = new bootstrap.Modal(document.getElementById('editFeedPlanModal'));
                modal.show();
            });
    }

    document.addEventListener('DOMContentLoaded', function() {
        const editForm = document.getElementById('editFeedPlanForm');
        if (editForm) {
            editForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const planId = document.getElementById('editPlanId').value;
                const data = {
                    species: document.getElementById('editSpecies').value,
                    feed_type: document.getElementById('editFeedType').value,
                    quantity_per_day: document.getElementById('editQuantity').value,
                    feeding_times: document.getElementById('editFeedingTimes').value.split(',').map(t => t.trim()),
                    start_date: document.getElementById('editStartDate').value,
                    end_date: document.getElementById('editEndDate').value,
                    is_active: document.getElementById('editIsActive').value === 'true'
                };
                fetch(`/ajax/edit_feed_plan/${planId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        showAlert('Feed plan updated successfully!', 'success');
                        location.reload();
                    } else {
                        showAlert(result.message || 'Failed to update feed plan', 'danger');
                    }
                })
                .catch(() => {
                    showAlert('Error updating feed plan', 'danger');
                });
        });
    }
});

function deleteFeedPlan(planId) {
    if (confirm('Are you sure you want to delete this feed plan?')) {
        fetch(`/ajax/delete_feed_plan/${planId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(data.message, 'success');
                location.reload();
            } else {
                showAlert(data.message, 'error');
            }
        })
        .catch(error => {
            showAlert('Error deleting feed plan', 'error');
        });
    }
}

function deleteFeedingLog(logId) {
    if (confirm('Are you sure you want to delete this feeding log?')) {
        fetch(`/ajax/delete_feeding_log/${logId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(data.message, 'success');
                location.reload();
            } else {
                showAlert(data.message, 'error');
            }
        })
        .catch(error => {
            showAlert('Error deleting feeding log', 'error');
        });
    }
}

// Feeding Log Management
function addFeedingLog() {
    const modal = new bootstrap.Modal(document.getElementById('addFeedingLogModal'));
    modal.show();
}

// Utility Functions
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Report Generation
function generateReport(reportType, format) {
    showAlert('Generating report...', 'info');
    
    const link = document.createElement('a');
    link.href = `/generate_report/${reportType}/${format}/`;
    link.click();
    
    setTimeout(() => {
        showAlert('Report generated successfully!', 'success');
    }, 2000);
}

// Data Visualization
function initializeCharts() {
    // Initialize Chart.js charts for dashboards
    const ctx = document.getElementById('feedingChart');
    if (ctx) {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Feeding Quantity (kg)',
                    data: [120, 190, 300, 500, 200, 300],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

// Initialize charts when page loads
document.addEventListener('DOMContentLoaded', initializeCharts);