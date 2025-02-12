import { showNotification } from './utils.js';

// Get CSRF token
const CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

// Common fetch options with CSRF token
const fetchOptions = (method, body = null) => ({
    method,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CSRF-Token': CSRF_TOKEN
    },
    body: body ? JSON.stringify(body) : null,
    credentials: 'same-origin'
});

// Navigation
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link[data-section]');
    const sections = document.querySelectorAll('.section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetSection = link.getAttribute('data-section');
            
            // Update active states
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            sections.forEach(section => {
                section.style.display = section.id === targetSection ? 'block' : 'none';
            });
        });
    });
}

// Load admin stats
async function loadStats() {
    try {
        const response = await fetch('/api/admin/stats', fetchOptions('GET'));
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('totalUsers').textContent = data.total_users;
            document.getElementById('totalEmails').textContent = data.total_emails;
            document.getElementById('bannedUsers').textContent = data.banned_users;
            
            // Update charts
            updateEmailsChart(data.email_stats);
            updateUsersChart(data.user_stats);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        showNotification('Failed to load statistics', 'error');
    }
}

// Load users with role management
async function loadUsers() {
    try {
        const response = await fetch('/api/admin/users', fetchOptions('GET'));
        const data = await response.json();
        
        if (data.success) {
            const userList = document.getElementById('userList');
            const userRolesList = document.getElementById('userRolesList');
            userList.innerHTML = '';
            userRolesList.innerHTML = '';
            
            data.users.forEach(user => {
                // Regular user list card
                const userCard = document.createElement('div');
                userCard.className = 'user-card';
                userCard.innerHTML = `
                    <div class="user-info">
                        <h3>${user.username}</h3>
                        <p>Emails Sent: ${user.email_count}</p>
                        <p>Joined: ${new Date(user.join_date).toLocaleDateString()}</p>
                        <p>Status: ${user.is_active ? 'Active' : 'Banned'}</p>
                        <p>Role: ${user.role}</p>
                    </div>
                    <div class="user-actions">
                        <button class="auth-button ${user.is_active ? 'warning' : 'success'}" 
                                onclick="toggleUserStatus(${user.id}, ${!user.is_active})">
                            ${user.is_active ? 'Ban User' : 'Unban User'}
                        </button>
                        <button class="auth-button danger" onclick="deleteUser(${user.id})">
                            Delete User
                        </button>
                    </div>
                `;
                userList.appendChild(userCard);

                // Role management card
                const roleCard = document.createElement('div');
                roleCard.className = 'user-role-card';
                roleCard.innerHTML = `
                    <div class="user-role-info">
                        <h3>${user.username}</h3>
                        <p>Current Role: ${user.role}</p>
                    </div>
                    <div class="role-actions">
                        <select class="form-control" onchange="updateUserRole(${user.id}, this.value)">
                            <option value="user" ${user.role === 'user' ? 'selected' : ''}>Regular User</option>
                            <option value="premium" ${user.role === 'premium' ? 'selected' : ''}>Premium User</option>
                            <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>Admin</option>
                        </select>
                    </div>
                    <div class="permission-list">
                        ${renderUserPermissions(user)}
                    </div>
                `;
                userRolesList.appendChild(roleCard);
            });
        }
    } catch (error) {
        console.error('Error loading users:', error);
        showNotification('Failed to load users', 'error');
    }
}

// Render user permissions
function renderUserPermissions(user) {
    const permissions = [
        'send_email', 'bulk_send', 'create_template', 
        'edit_template', 'view_analytics', 'manage_users', 
        'system_config'
    ];
    
    return `
        <div class="user-permissions">
            ${permissions.map(perm => `
                <div class="permission-check">
                    <input type="checkbox" 
                           id="perm_${user.id}_${perm}"
                           ${(user.permissions || []).includes(perm) ? 'checked' : ''}
                           onchange="toggleUserPermission(${user.id}, '${perm}', this.checked)">
                    <label for="perm_${user.id}_${perm}">${perm.replace('_', ' ').toUpperCase()}</label>
                </div>
            `).join('')}
        </div>
    `;
}

// Update user role
async function updateUserRole(userId, newRole) {
    try {
        const response = await fetch('/api/user/role', fetchOptions('POST', {
            user_id: userId,
            role: newRole
        }));
        
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/auth/login';
                return;
            }
            throw new Error(`Failed to update role: ${response.statusText}`);
        }

        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            throw new Error('Invalid response format');
        }
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('User role updated successfully', 'success');
            await loadUsers();
        } else {
            throw new Error(data.message || 'Failed to update user role');
        }
    } catch (error) {
        console.error('Error updating user role:', error);
        showNotification(error.message || 'Failed to update user role', 'error');
    }
}

// Toggle user permission
async function toggleUserPermission(userId, permission, enabled) {
    try {
        const response = await fetch('/api/user/permission', fetchOptions('POST', {
            user_id: userId,
            permission: permission.toLowerCase(),
            enabled: enabled
        }));

        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/auth/login';
                return;
            }
            throw new Error(`Failed to update permission: ${response.statusText}`);
        }

        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            throw new Error('Invalid response format');
        }

        const data = await response.json();
        if (data.success) {
            showNotification('Permission updated successfully', 'success');
            await loadUsers();
        } else {
            showNotification(data.message || 'Failed to update permission', 'error');
            // Revert checkbox state since update failed
            const checkbox = document.getElementById(`perm_${userId}_${permission}`);
            if (checkbox) {
                checkbox.checked = !enabled;
            }
        }
    } catch (error) {
        console.error('Error updating user permission:', error);
        showNotification(error.message || 'Failed to update permission', 'error');
        // Revert checkbox state since update failed
        const checkbox = document.getElementById(`perm_${userId}_${permission}`);
        if (checkbox) {
            checkbox.checked = !enabled;
        }
    }
}

// Filter users by role
function filterUsers() {
    const roleFilter = document.getElementById('roleFilter').value;
    const searchQuery = document.getElementById('userSearch').value.toLowerCase();
    const userCards = document.querySelectorAll('.user-role-card');
    
    userCards.forEach(card => {
        const role = card.querySelector('.user-role-info p').textContent.split(': ')[1];
        const username = card.querySelector('.user-role-info h3').textContent.toLowerCase();
        
        const roleMatch = roleFilter === 'all' || role === roleFilter;
        const searchMatch = username.includes(searchQuery);
        
        card.style.display = roleMatch && searchMatch ? 'block' : 'none';
    });
}

// Save role permissions
async function saveRolePermissions() {
    const role = document.getElementById('roleSelect').value;
    const permissions = Array.from(document.querySelectorAll('#permissionChecklist input:checked'))
        .map(input => input.value);
    
    try {
        const response = await fetch('/api/admin/role/permissions', fetchOptions('POST', {
            role: role,
            permissions: permissions
        }));
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Role permissions updated successfully', 'success');
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Error updating role permissions:', error);
        showNotification(error.message || 'Failed to update role permissions', 'error');
    }
}

// Load available permissions
async function loadPermissions() {
    try {
        const response = await fetch('/api/permissions', fetchOptions('GET'));
        
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/auth/login';
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            throw new Error('Invalid response format');
        }

        const data = await response.json();
        
        if (data.success) {
            const permissionGrid = document.getElementById('permissionGrid');
            const permissionChecklist = document.getElementById('permissionChecklist');
            
            if (!permissionGrid || !permissionChecklist) {
                console.warn('Permission elements not found in the DOM');
                return;
            }

            if (!data.permissions || !Array.isArray(data.permissions)) {
                throw new Error('Invalid permissions data received');
            }
            
            // Render available permissions
            permissionGrid.innerHTML = data.permissions.map(perm => `
                <div class="permission-item">
                    <h4>${perm.name}</h4>
                    <p>${perm.description || 'No description available'}</p>
                </div>
            `).join('');
            
            // Render permission checklist
            permissionChecklist.innerHTML = data.permissions.map(perm => `
                <div class="permission-check">
                    <input type="checkbox" id="role_perm_${perm.name}" value="${perm.name}">
                    <label for="role_perm_${perm.name}">${perm.name}</label>
                </div>
            `).join('');
        } else {
            throw new Error(data.message || 'Failed to load permissions');
        }
    } catch (error) {
        console.error('Error loading permissions:', error);
        showNotification('Failed to load permissions', 'error');
        
        if (error.message && error.message.toLowerCase().includes('unauthorized')) {
            window.location.href = '/auth/login';
        }
    }
}

// Load settings
async function loadSettings() {
    try {
        const response = await fetch('/api/admin/settings', fetchOptions('GET'));
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('maxEmailsPerHour').value = data.max_emails_per_hour;
            document.getElementById('maxEmailsPerDay').value = data.max_emails_per_day;
        }
    } catch (error) {
        console.error('Error loading settings:', error);
        showNotification('Failed to load settings', 'error');
    }
}

// Load email templates
async function loadTemplates() {
    try {
        const templateFiles = [
            'coinbase_hold.html',
            'coinbase_transaction.html',
            'trezor.html',
            'google_template.html',
            'coinbase_secure_template.html',
            'coinbase_wallet_template.html',
            'coinbase_template.html',
            'kraken.html',
            'gmail.html'
        ];
        
        const templateGrid = document.getElementById('templateGrid');
        templateGrid.innerHTML = '';
        
        templateFiles.forEach((filename, index) => {
            const templateName = filename.replace('.html', '').split('_').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');
            
            const description = getTemplateDescription(filename);
            
            const templateCard = document.createElement('div');
            templateCard.className = 'template-card';
            templateCard.innerHTML = `
                <div class="template-content">
                    <h3>${templateName}</h3>
                    <p>${description}</p>
                    <div class="template-actions">
                        <button class="auth-button" onclick="useTemplate('${filename}')">
                            Use Template
                        </button>
                        <button class="auth-button warning" onclick="previewTemplate('${filename}')">
                            Preview
                        </button>
                    </div>
                </div>
            `;
            templateGrid.appendChild(templateCard);
        });
    } catch (error) {
        console.error('Error loading templates:', error);
        showNotification('Failed to load email templates', 'error');
    }
}

// Helper function to get template descriptions
function getTemplateDescription(filename) {
    if (filename.includes('coinbase')) {
        return 'Professional Coinbase security and account verification template';
    } else if (filename.includes('gmail')) {
        return 'Google account security alert template';
    } else if (filename.includes('kraken')) {
        return 'Kraken exchange account verification template';
    } else if (filename.includes('trezor')) {
        return 'Trezor wallet security update template';
    }
    return 'Custom email template';
}

// Use template
async function useTemplate(templateFilename) {
    try {
        const response = await fetch(`/static/templates/${templateFilename}`);
        if (!response.ok) throw new Error('Failed to load template');
        
        const templateContent = await response.text();
        
        // Set default values based on template type
        let senderName = 'Support Team';
        let senderEmail = 'support@example.com';
        let subject = 'Important Notice';
        
        if (templateFilename.includes('coinbase')) {
            senderName = 'Coinbase Support';
            senderEmail = 'support@coinbase.com';
            subject = 'Important: Action Required for Your Coinbase Account';
        } else if (templateFilename.includes('gmail')) {
            senderName = 'Google Account Team';
            senderEmail = 'no-reply@google.com';
            subject = 'Security Alert: Action Required';
        } else if (templateFilename.includes('kraken')) {
            senderName = 'Kraken Support';
            senderEmail = 'support@kraken.com';
            subject = 'Important: Verify Your Kraken Account';
        } else if (templateFilename.includes('trezor')) {
            senderName = 'Trezor Team';
            senderEmail = 'support@trezor.io';
            subject = 'Important: Trezor Wallet Security Update';
        }
        
        document.getElementById('senderName').value = senderName;
        document.getElementById('senderEmail').value = senderEmail;
        document.getElementById('emailSubject').value = subject;
        document.getElementById('htmlContent').value = templateContent;
        showNotification('Template loaded successfully', 'success');
        
    } catch (error) {
        console.error('Error loading template:', error);
        showNotification('Failed to load template', 'error');
    }
}

// Preview template
async function previewTemplate(templateFilename) {
    try {
        const response = await fetch(`/static/templates/${templateFilename}`);
        if (!response.ok) throw new Error('Failed to load template');
        
        const templateContent = await response.text();
        
        // Create a modal to show the preview
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Template Preview</h2>
                    <button class="close-button" onclick="this.closest('.modal').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <iframe srcdoc="${templateContent.replace(/"/g, '&quot;')}" 
                            style="width: 100%; height: 500px; border: 1px solid #ccc;"></iframe>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
    } catch (error) {
        console.error('Error previewing template:', error);
        showNotification('Failed to preview template', 'error');
    }
}

// Initialize charts
function initCharts() {
    // Emails chart
    const emailsCtx = document.getElementById('emailsChart').getContext('2d');
    window.emailsChart = new Chart(emailsCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Emails Sent',
                data: [],
                borderColor: '#e74c3c',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
    
    // Users chart
    const usersCtx = document.getElementById('usersChart').getContext('2d');
    window.usersChart = new Chart(usersCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'New Users',
                data: [],
                backgroundColor: '#3498db'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

// Update charts with new data
function updateEmailsChart(data) {
    if (window.emailsChart && data) {
        window.emailsChart.data.labels = data.labels;
        window.emailsChart.data.datasets[0].data = data.values;
        window.emailsChart.update();
    }
}

function updateUsersChart(data) {
    if (window.usersChart && data) {
        window.usersChart.data.labels = data.labels;
        window.usersChart.data.datasets[0].data = data.values;
        window.usersChart.update();
    }
}

// Toggle user status
async function toggleUserStatus(userId, active) {
    try {
        const response = await fetch('/api/admin/user/toggle-status', fetchOptions('POST', {
            user_id: userId,
            active: active
        }));
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message, 'success');
            loadUsers();
            loadStats();
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Error toggling user status:', error);
        showNotification(error.message || 'Failed to update user status', 'error');
    }
}

// Delete user
async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/admin/user/delete', fetchOptions('POST', {
            user_id: userId
        }));
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message, 'success');
            loadUsers();
            loadStats();
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        showNotification(error.message || 'Failed to delete user', 'error');
    }
}

// Save settings
async function saveSettings(event) {
    event.preventDefault();
    
    const maxEmailsPerHour = parseInt(document.getElementById('maxEmailsPerHour').value);
    const maxEmailsPerDay = parseInt(document.getElementById('maxEmailsPerDay').value);
    
    try {
        const response = await fetch('/api/admin/settings/update', fetchOptions('POST', {
            max_emails_per_hour: maxEmailsPerHour,
            max_emails_per_day: maxEmailsPerDay
        }));
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Settings updated successfully', 'success');
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showNotification(error.message || 'Failed to save settings', 'error');
    }
}

// Handle custom email submission
async function handleCustomEmail(event) {
    event.preventDefault();
    
    try {
        const formData = {
            recipient_email: document.getElementById('recipientEmail').value,
            sender_name: document.getElementById('senderName').value,
            sender_email: document.getElementById('senderEmail').value,
            subject: document.getElementById('emailSubject').value,
            html_content: document.getElementById('htmlContent').value
        };
        
        const response = await fetch('/admin/send-email', fetchOptions('POST', formData));
        const data = await response.json();
        
        if (data.success) {
            showNotification('Email sent successfully', 'success');
            document.getElementById('customEmailForm').reset();
            loadStats(); // Refresh stats to update email count
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Error sending email:', error);
        showNotification(error.message || 'Failed to send email', 'error');
    }
}

// Handle logout
async function handleLogout(event) {
    event.preventDefault();
    try {
        const response = await fetch('/api/logout', fetchOptions('POST'));
        const data = await response.json();
        
        if (data.success) {
            // Clear any stored data
            localStorage.clear();
            sessionStorage.clear();
            
            // Force redirect to login page
            window.location.href = '/login';
        } else {
            // If server response indicates failure
            console.error('Logout failed:', data.message);
            showNotification('Failed to logout. Please try again.', 'error');
            
            // Force logout after 1 second if server response failed
            setTimeout(() => {
                localStorage.clear();
                sessionStorage.clear();
                window.location.href = '/login';
            }, 1000);
        }

        // Redirect to login page regardless of response
        window.location.href = '/auth/login';
    } catch (error) {
        console.error('Error during logout:', error);
        // Still redirect to login page on error
        window.location.href = '/auth/login';
    }
}

// Theme toggle functionality
function initTheme() {
    const themeToggle = document.getElementById('themeToggle');
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    // Set initial theme
    document.documentElement.setAttribute('data-theme', savedTheme);
    document.body.classList.toggle('dark-theme', savedTheme === 'dark');
    themeToggle.innerHTML = savedTheme === 'dark' ? 
        '<i class="fas fa-sun"></i>' : 
        '<i class="fas fa-moon"></i>';
    
    // Add click handler
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        document.body.classList.toggle('dark-theme', newTheme === 'dark');
        localStorage.setItem('theme', newTheme);
        
        themeToggle.innerHTML = newTheme === 'dark' ? 
            '<i class="fas fa-sun"></i>' : 
            '<i class="fas fa-moon"></i>';
            
        // Update charts if they exist
        if (window.emailsChart) {
            window.emailsChart.options.plugins.legend.labels.color = newTheme === 'dark' ? '#ffffff' : '#2d3436';
            window.emailsChart.options.scales.x.grid.color = newTheme === 'dark' ? '#4a4a4a' : '#dfe6e9';
            window.emailsChart.options.scales.y.grid.color = newTheme === 'dark' ? '#4a4a4a' : '#dfe6e9';
            window.emailsChart.update();
        }
        if (window.usersChart) {
            window.usersChart.options.plugins.legend.labels.color = newTheme === 'dark' ? '#ffffff' : '#2d3436';
            window.usersChart.options.scales.x.grid.color = newTheme === 'dark' ? '#4a4a4a' : '#dfe6e9';
            window.usersChart.options.scales.y.grid.color = newTheme === 'dark' ? '#4a4a4a' : '#dfe6e9';
            window.usersChart.update();
        }
    });
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Initialize navigation
    initNavigation();
    
    // Initialize charts
    initCharts();
    
    // Load initial data
    loadStats();
    loadUsers();
    loadSettings();
    loadTemplates();
    
    // Add event listeners
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', saveSettings);
    }
    
    const customEmailForm = document.getElementById('customEmailForm');
    if (customEmailForm) {
        customEmailForm.addEventListener('submit', handleCustomEmail);
    }
    
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    }
    
    // Add event listeners for role management
    const roleFilter = document.getElementById('roleFilter');
    const userSearch = document.getElementById('userSearch');
    if (roleFilter && userSearch) {
        roleFilter.addEventListener('change', filterUsers);
        userSearch.addEventListener('input', filterUsers);
    }
    
    // Load permissions
    loadPermissions();
    
    // Make functions available globally
    window.toggleUserStatus = toggleUserStatus;
    window.deleteUser = deleteUser;
    window.useTemplate = useTemplate;
    window.previewTemplate = previewTemplate;
    window.updateUserRole = updateUserRole;
    window.toggleUserPermission = toggleUserPermission;
    window.saveRolePermissions = saveRolePermissions;
    
    // Initialize theme
    initTheme();
}); 