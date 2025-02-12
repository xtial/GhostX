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

// Function to create an element from a template
function createElementFromTemplate(templateId) {
    const template = document.getElementById(templateId);
    return template.content.cloneNode(true).firstElementChild;
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
                // Create user list card
                const userCard = createElementFromTemplate('userListTemplate');
                
                // Set user card attributes and content
                userCard.id = `user_${user.id}`;
                userCard.classList.toggle('admin-user', user.is_admin);
                
                // Fill in user information
                userCard.querySelector('.username').textContent = user.username || 'Unknown User';
                userCard.querySelector('.user-role').textContent = formatPermissionName(user.role);
                userCard.querySelector('.join-date').textContent = `Joined: ${user.join_date ? new Date(user.join_date).toLocaleDateString() : 'Unknown'}`;
                
                // Setup role select
                const roleSelect = userCard.querySelector('.role-select');
                if (roleSelect) {
                    roleSelect.dataset.userId = user.id;
                    if (user.role) {
                        roleSelect.value = user.role;
                    }
                    roleSelect.addEventListener('change', (e) => updateUserRole(user.id, e.target.value));
                }
                
                // Setup status toggle button
                const statusBtn = userCard.querySelector('.status-toggle');
                if (statusBtn) {
                    statusBtn.classList.add(user.is_active ? 'warning' : 'success');
                    statusBtn.textContent = user.is_active ? 'Deactivate' : 'Activate';
                    statusBtn.addEventListener('click', () => toggleUserStatus(user.id, !user.is_active));
                }
                
                // Setup delete button
                const deleteBtn = userCard.querySelector('.delete-user');
                if (deleteBtn) {
                    deleteBtn.addEventListener('click', () => deleteUser(user.id));
                }
                
                // Setup permissions container
                const permissionsContainer = userCard.querySelector('.user-permissions');
                if (permissionsContainer) {
                    permissionsContainer.id = `permissions_${user.id}`;
                    permissionsContainer.dataset.userId = user.id;
                }
                
                userList.appendChild(userCard);

                // Create role management card
                const roleCard = createElementFromTemplate('userRoleTemplate');
                
                // Fill in role card information
                const usernameEl = roleCard.querySelector('.username');
                const roleStatusEl = roleCard.querySelector('.role-status');
                
                if (usernameEl) {
                    usernameEl.textContent = user.username || 'Unknown User';
                }
                if (roleStatusEl) {
                    roleStatusEl.textContent = `Current Role: ${formatPermissionName(user.role)}`;
                }
                
                // Setup role select
                const roleManageSelect = roleCard.querySelector('.role-select');
                if (roleManageSelect) {
                    roleManageSelect.dataset.userId = user.id;
                    if (user.role) {
                        roleManageSelect.value = user.role;
                    }
                    roleManageSelect.addEventListener('change', (e) => updateUserRole(user.id, e.target.value));
                }
                
                // Setup permissions container
                const rolePermissions = roleCard.querySelector('.user-permissions');
                if (rolePermissions) {
                    rolePermissions.id = `permissions_${user.id}`;
                    rolePermissions.dataset.userId = user.id;
                }
                
                userRolesList.appendChild(roleCard);
                
                // Load permissions for both containers
                loadUserPermissions(user.id);
            });
        }
    } catch (error) {
        console.error('Error loading users:', error);
        showNotification('Failed to load users', 'error');
    }
}

// Load permissions for a specific user
async function loadUserPermissions(userId) {
    try {
        const response = await fetch(`/admin/api/admin/user/${userId}/permissions`, fetchOptions('GET'));
        
        if (!response.ok) {
            throw new Error(`Failed to load permissions: ${response.statusText}`);
        }

        const data = await response.json();
        
        if (data.success) {
            const containers = document.querySelectorAll(`#permissions_${userId}`);
            containers.forEach(container => {
                if (container) {
                    updatePermissionsDisplay(container, data.permissions);
                }
            });
        } else {
            throw new Error(data.message || 'Failed to load permissions');
        }
    } catch (error) {
        console.error(`Error loading permissions for user ${userId}:`, error);
        // Don't show notification for 404s as they might be expected
        if (!error.message.includes('404')) {
            showNotification(`Failed to load permissions: ${error.message}`, 'error');
        }
    }
}

// Helper function to update permissions display
function updatePermissionsDisplay(container, permissions) {
    if (!container || !permissions) return;
    
    container.innerHTML = permissions.map(perm => `
        <div class="permission-check">
            <input type="checkbox" 
                   id="perm_${container.dataset.userId}_${perm.name}"
                   ${perm.enabled ? 'checked' : ''}
                   data-permission="${perm.name}"
                   ${perm.is_admin_only ? 'disabled' : ''}>
            <label for="perm_${container.dataset.userId}_${perm.name}" 
                   title="${perm.description}">
                ${formatPermissionName(perm.name)}
            </label>
        </div>
    `).join('');
    
    // Add event listeners to checkboxes
    container.querySelectorAll('input[type="checkbox"]:not([disabled])').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            toggleUserPermission(container.dataset.userId, e.target.dataset.permission, e.target.checked);
        });
    });
}

// Update user role
async function updateUserRole(userId, newRole) {
    // Store the select element
    const roleSelect = document.querySelector(`select[data-user-id="${userId}"]`);
    const originalRole = roleSelect ? roleSelect.value : null;
    
    try {
        const response = await fetch('/admin/api/user/role', fetchOptions('POST', {
            user_id: userId,
            role: newRole
        }));
        
        const data = await response.json();
        
        if (response.status === 401) {
            // Session expired
            localStorage.clear();
            sessionStorage.clear();
            window.location.href = '/login';
                return;
        }

        if (!response.ok) {
            throw new Error(data.message || 'Failed to update role');
        }
        
        if (data.success) {
            showNotification('Role updated successfully', 'success');
            // Keep the new role selected
            if (roleSelect) {
                roleSelect.value = newRole;
            }
            // Update permissions display
            const permissionsContainer = document.querySelector(`#permissions_${userId}`);
            if (permissionsContainer && data.user.permissions) {
                updatePermissionsDisplay(permissionsContainer, data.user.permissions);
            }
            // Update user card if admin status changed
            const userCard = document.querySelector(`#user_${userId}`);
            if (userCard) {
                userCard.classList.toggle('admin-user', data.user.is_admin);
            }
            // Refresh the user list to show updated roles and permissions
            await loadUsers();
        } else {
            showNotification(data.message || 'Failed to update role', 'error');
            // Revert role selection since update failed
            if (roleSelect && originalRole) {
                roleSelect.value = originalRole;
            }
        }
    } catch (error) {
        console.error('Error updating user role:', error);
        showNotification(error.message || 'Failed to update role', 'error');
        // Revert role selection
        if (roleSelect && originalRole) {
            roleSelect.value = originalRole;
        }
    }
}

// Helper function to format permission names
function formatPermissionName(permission) {
    if (!permission) return 'Unknown';
    
    return permission.toString()
        .toLowerCase()
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Load available roles
async function loadRoles() {
    try {
        const response = await fetch('/admin/api/roles');
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Failed to load roles');
        }
        
        if (data.success) {
            // Update role selects
            const roleSelects = document.querySelectorAll('.role-select');
            roleSelects.forEach(select => {
                // Keep current selected value
                const currentValue = select.value;
                // Clear existing options
                select.innerHTML = '';
                // Add new options
                data.roles.forEach(role => {
                    const option = document.createElement('option');
                    option.value = role.name;
                    option.textContent = formatPermissionName(role.name);
                    if (role.name === 'SUPER_ADMIN') {
                        option.disabled = true;
                    }
                    select.appendChild(option);
                });
                // Restore selected value if it exists in new options
                if (currentValue && [...select.options].some(opt => opt.value === currentValue)) {
                    select.value = currentValue;
                }
            });
        }
    } catch (error) {
        console.error('Error loading roles:', error);
        showNotification('Failed to load roles', 'error');
    }
}

// Toggle user permission
async function toggleUserPermission(userId, permission, enabled) {
    // Store the checkbox element
    const checkbox = document.getElementById(`perm_${userId}_${permission}`);
    
    try {
        const response = await fetch('/admin/api/user/permission', fetchOptions('POST', {
            user_id: userId,
            permission: permission,
            enabled: enabled
        }));

        if (response.status === 401) {
            // Session expired
            localStorage.clear();
            sessionStorage.clear();
            window.location.href = '/login';
            return;
        }

        if (!response.ok) {
            if (response.status === 401) {
                // Unauthorized, redirect to login
                window.location.href = '/login';
                return;
            }
            throw new Error(`Failed to update permission: ${response.statusText}`);
        }

        const data = await response.json();
        if (data.success) {
            showNotification('Permission updated successfully', 'success');
            // Keep the checkbox in its new state since update was successful
            if (checkbox) {
                checkbox.checked = enabled;
            }
        } else {
            showNotification(data.message || 'Failed to update permission', 'error');
            // Revert checkbox state since update failed
            if (checkbox) {
                checkbox.checked = !enabled;
            }
        }
    } catch (error) {
        console.error('Error updating user permission:', error);
        showNotification(error.message || 'Failed to update permission', 'error');
        // Revert checkbox state on error
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
async function saveRolePermissions(role, permission, enabled) {
    try {
        const response = await fetch('/admin/api/role/permission', fetchOptions('POST', {
            role: role,
            permission: permission,
            enabled: enabled
        }));
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Role permission updated successfully', 'success');
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Error updating role permission:', error);
        showNotification(error.message || 'Failed to update role permission', 'error');
    }
}

// Load available permissions
async function loadPermissions() {
    try {
        const response = await fetch('/admin/api/permissions', {
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            }
        });
        
        if (response.status === 401) {
            localStorage.clear();
            sessionStorage.clear();
            window.location.href = '/login';
            return;
        }
        
        if (!response.ok) {
            if (response.status === 401) {
                // Unauthorized, redirect to login
                window.location.href = '/login';
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            throw new Error('Invalid response format');
        }

        const data = await response.json();
        
        if (!data.success || !data.permissions) {
                throw new Error('Invalid permissions data received');
            }
            
        const permissionsContainer = document.getElementById('permissionsContainer');
        if (!permissionsContainer) return;

        // Render permissions by category
        permissionsContainer.innerHTML = Object.entries(data.categories).map(([category, permissions]) => `
            <div class="permission-category">
                <h3>${category}</h3>
                <div class="permission-grid">
                    ${permissions.map(perm => `
                        <div class="permission-card ${perm.is_admin_only ? 'admin-only' : ''} 
                                                   ${!perm.can_be_modified ? 'locked' : ''}">
                            <div class="permission-header">
                                <h4>${perm.description}</h4>
                                ${perm.is_admin_only ? '<span class="badge admin">Admin Only</span>' : ''}
                                ${!perm.can_be_modified ? '<i class="fas fa-lock" title="Cannot be modified"></i>' : ''}
                            </div>
                            <div class="permission-details">
                                ${perm.required_roles.length > 0 ? `
                                    <div class="required-roles">
                                        <strong>Required for:</strong>
                                        ${perm.required_roles.join(', ')}
                                    </div>
                                ` : ''}
                                ${perm.dependencies.length > 0 ? `
                                    <div class="dependencies">
                                        <strong>Requires:</strong>
                                        ${perm.dependencies.join(', ')}
                                    </div>
                                ` : ''}
                                ${perm.conflicts_with.length > 0 ? `
                                    <div class="conflicts">
                                        <strong>Conflicts with:</strong>
                                        ${perm.conflicts_with.join(', ')}
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
                </div>
            `).join('');

        // Add event listeners to checkboxes
        permissionChecklist.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', async (e) => {
                const permission = e.target.dataset.permission;
                const enabled = e.target.checked;
                const role = roleSelect ? roleSelect.value : null;

                if (role) {
                    try {
                        await saveRolePermissions(role, permission, enabled);
                    } catch (error) {
                        console.error('Error updating permission:', error);
                        e.target.checked = !enabled; // Revert on error
                        showNotification('Failed to update permission', 'error');
                    }
                }
            });
        });

        // If role select exists, add change handler
        if (roleSelect) {
            roleSelect.addEventListener('change', async () => {
                const selectedRole = roleSelect.value;
                try {
                    const rolePermsResponse = await fetch(`/admin/api/role/${selectedRole}/permissions`, 
                        fetchOptions('GET')
                    );
                    
                    if (!rolePermsResponse.ok) {
                        throw new Error('Failed to fetch role permissions');
                    }

                    const rolePermsData = await rolePermsResponse.json();
                    if (rolePermsData.success) {
                        // Update checkboxes based on role permissions
                        const checkboxes = permissionChecklist.querySelectorAll('input[type="checkbox"]');
                        checkboxes.forEach(checkbox => {
                            checkbox.checked = rolePermsData.permissions.includes(checkbox.dataset.permission);
                        });
                    }
                } catch (error) {
                    console.error('Error loading role permissions:', error);
                    showNotification('Failed to load role permissions', 'error');
                }
            });

            // Load initial permissions for selected role
            roleSelect.dispatchEvent(new Event('change'));
        }

    } catch (error) {
        console.error('Error loading permissions:', error);
        showNotification('Failed to load permissions', 'error');
        
        if (error.message && error.message.toLowerCase().includes('unauthorized')) {
            window.location.href = '/login';
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
    } catch (error) {
        console.error('Error during logout:', error);
        // Still redirect to login page on error
        window.location.href = '/login';
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

    // Role management event listeners
    const roleSelects = document.querySelectorAll('.role-select');
    roleSelects.forEach(select => {
        select.addEventListener('change', function() {
            const userId = this.getAttribute('data-user-id');
            const newRole = this.value;
            updateUserRole(userId, newRole);
        });
    });

    // Role permission checkboxes
    const rolePermissionChecks = document.querySelectorAll('.role-permission-check');
    rolePermissionChecks.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const role = this.getAttribute('data-role');
            const permission = this.getAttribute('data-permission');
            updateRolePermission(role, permission, this.checked);
        });
    });

    // Load initial roles
    loadRoles();
});

async function loadRolePermissions(role) {
    try {
        const response = await fetch(`/admin/api/role/${role}/permissions`, {
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to load role permissions: ${response.statusText}`);
        }

        const data = await response.json();
        if (data.success) {
            // Update permission checkboxes for the role
            const permissions = data.permissions;
            const checkboxes = document.querySelectorAll('.permission-check input[type="checkbox"]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = permissions.includes(checkbox.value);
            });
        } else {
            showNotification(data.message || 'Failed to load role permissions', 'error');
        }
    } catch (error) {
        console.error('Error loading role permissions:', error);
        showNotification(error.message || 'Failed to load role permissions', 'error');
    }
}

async function updateRolePermission(role, permission, enabled) {
    try {
        // Find all checkboxes for this permission across roles
        const relatedCheckboxes = document.querySelectorAll(
            `input[data-permission="${permission}"]`
        );

        const response = await fetch('/admin/api/role/permission', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': CSRF_TOKEN
            },
            body: JSON.stringify({
                role,
                permission,
                enabled
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to update role permission: ${response.statusText}`);
        }

        const data = await response.json();
        if (data.success) {
            showNotification(`Permission ${enabled ? 'enabled' : 'disabled'} for ${data.updated_users} users`, 'success');
            
            // If this is a dependency or conflicting permission, update related checkboxes
            if (enabled) {
                // Enable required dependencies
                const dependencies = relatedCheckboxes[0]?.dataset.dependencies?.split(',') || [];
                for (const dep of dependencies) {
                    const depCheckbox = document.querySelector(
                        `input[data-role="${role}"][data-permission="${dep}"]:not(:checked)`
                    );
                    if (depCheckbox) {
                        depCheckbox.checked = true;
                        await updateRolePermission(role, dep, true);
                    }
                }

                // Disable conflicting permissions
                const conflicts = relatedCheckboxes[0]?.dataset.conflicts?.split(',') || [];
                for (const conflict of conflicts) {
                    const conflictCheckbox = document.querySelector(
                        `input[data-role="${role}"][data-permission="${conflict}"]:checked`
                    );
                    if (conflictCheckbox) {
                        conflictCheckbox.checked = false;
                        await updateRolePermission(role, conflict, false);
                    }
                }
            }
        } else {
            throw new Error(data.message || 'Failed to update permission');
        }
    } catch (error) {
        console.error('Error updating role permission:', error);
        showNotification(error.message || 'Failed to update permission', 'error');
        
        // Revert checkbox state
        const checkbox = document.querySelector(
            `input[data-role="${role}"][data-permission="${permission}"]`
        );
        if (checkbox) {
            checkbox.checked = !enabled;
        }
    }
} 