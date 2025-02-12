// Tab Navigation
document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const tabId = item.getAttribute('data-tab');
        
        // Update navigation items
        document.querySelectorAll('.nav-item').forEach(navItem => {
            navItem.classList.remove('active');
        });
        item.classList.add('active');
        
        // Show selected tab
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        document.getElementById(tabId).classList.add('active');
    });
});

// Load User Stats
async function loadUserStats() {
    try {
        const response = await fetch('/api/get_user_stats');
        const data = await response.json();
        
        document.getElementById('emailCount').textContent = data.email_count;
        document.getElementById('joinDate').textContent = new Date(data.join_date).toLocaleDateString();
        
        // Add to activity log
        addActivityItem('Logged in', 'login');
    } catch (error) {
        showNotification('Failed to load user stats', 'error');
    }
}

// Load Templates
async function loadTemplates() {
    try {
        const response = await fetch('/api/get_templates');
        const templates = await response.json();
        
        // Add templates to select dropdown
        const templateSelect = document.getElementById('template');
        Object.entries(templates).forEach(([key, value]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = value;
            templateSelect.appendChild(option);
        });
        
        // Add template previews
        const templateGrid = document.querySelector('#templates .template-grid');
        Object.entries(templates).forEach(([key, value]) => {
            const template = document.createElement('div');
            template.className = 'template-preview';
            template.innerHTML = `
                <img src="/assets/img/${key}.jpg" alt="${key} template">
                <div class="template-info">
                    <h3>${key.charAt(0).toUpperCase() + key.slice(1)}</h3>
                    <p>Click to preview</p>
                </div>
            `;
            templateGrid.appendChild(template);
            
            // Add click handler for preview
            template.addEventListener('click', () => {
                fetch(`/assets/templates/${value}`)
                    .then(response => response.text())
                    .then(html => {
                        document.getElementById('customHtml').value = html;
                        document.getElementById('template').value = key;
                        // Switch to spoofer tab
                        document.querySelector('[data-tab="spoofer"]').click();
                    });
            });
        });
    } catch (error) {
        showNotification('Failed to load templates', 'error');
    }
}

// Handle Template Selection
document.getElementById('template').addEventListener('change', function() {
    const customHtmlGroup = document.getElementById('customHtmlGroup');
    if (this.value === 'custom') {
        customHtmlGroup.style.display = 'block';
        document.getElementById('customHtml').value = '';
    } else {
        customHtmlGroup.style.display = 'none';
        // Load selected template
        fetch(`/assets/templates/${this.value}`)
            .then(response => response.text())
            .then(html => {
                document.getElementById('customHtml').value = html;
            });
    }
});

// Handle Email Sending
document.getElementById('spooferForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = {
        victim_email: document.getElementById('victimEmail').value,
        subject: document.getElementById('subject').value,
        sender_name: document.getElementById('senderName').value,
        display_email: document.getElementById('displayEmail').value,
        html_content: document.getElementById('customHtml').value
    };
    
    try {
        const response = await fetch('/api/send_email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Email sent successfully!', 'success');
            addActivityItem('Email sent', 'email');
            loadUserStats(); // Refresh stats
        } else {
            showNotification(result.message || 'Failed to send email', 'error');
        }
    } catch (error) {
        showNotification('Failed to send email', 'error');
    }
});

// Activity Log
function addActivityItem(message, type) {
    const activityLog = document.getElementById('activityLog');
    const item = document.createElement('div');
    item.className = 'activity-item';
    
    const icon = type === 'email' ? 'fa-envelope' : 'fa-sign-in-alt';
    
    item.innerHTML = `
        <div class="activity-icon">
            <i class="fas ${icon}"></i>
        </div>
        <div class="activity-info">
            <p>${message}</p>
            <small>${new Date().toLocaleTimeString()}</small>
        </div>
    `;
    
    activityLog.insertBefore(item, activityLog.firstChild);
}

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.getElementById('notifications').appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }, 100);
}

// Settings
document.getElementById('darkMode').addEventListener('change', function() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', this.checked);
});

document.getElementById('notifications').addEventListener('change', function() {
    localStorage.setItem('notifications', this.checked);
});

// Load saved preferences
document.getElementById('darkMode').checked = localStorage.getItem('darkMode') === 'true';
document.getElementById('notifications').checked = localStorage.getItem('notifications') === 'true';
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
}

// Initialize
loadUserStats();
loadTemplates(); 