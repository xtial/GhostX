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
        loadingIndicator.show();
        
        const response = await fetch('/api/admin/users', fetchOptions('GET'));
        const data = await response.json();
        
        if (data.success) {
            const userList = document.getElementById('userList');
            const userRolesList = document.getElementById('userRolesList');
            userList.innerHTML = '';
            userRolesList.innerHTML = '';
            
            for (const user of data.users) {
                const userCard = createElementFromTemplate('userListTemplate');
                
                // Apply terminal effect to username
                const usernameElement = userCard.querySelector('.username');
                await terminalEffects.glitchText(usernameElement, user.username || 'Unknown User');
                
                // Enhanced user card setup
                userCard.id = `user_${user.id}`;
                userCard.classList.toggle('admin-user', user.is_admin);
                
                userCard.querySelector('.user-role').textContent = formatPermissionName(user.role);
                userCard.querySelector('.join-date').textContent = `Joined: ${user.join_date ? new Date(user.join_date).toLocaleDateString() : 'Unknown'}`;
                
                // Add hover effects
                userCard.addEventListener('mouseenter', () => {
                    uiEffects.scanEffect(userCard);
                });
                
                // Setup enhanced role select
                const roleSelect = userCard.querySelector('.role-select');
                if (roleSelect) {
                    roleSelect.dataset.userId = user.id;
                    if (user.role) {
                        roleSelect.value = user.role;
                    }
                    roleSelect.addEventListener('change', async (e) => {
                        if (await userExperience.confirmAction('Are you sure you want to change this user\'s role?')) {
                            updateUserRole(user.id, e.target.value);
                        } else {
                            e.target.value = user.role; // Revert if cancelled
                        }
                    });
                }
                
                // Setup enhanced status toggle
                const statusBtn = userCard.querySelector('.status-toggle');
                if (statusBtn) {
                    statusBtn.classList.add(user.is_active ? 'warning' : 'success');
                    statusBtn.textContent = user.is_active ? 'Deactivate' : 'Activate';
                    statusBtn.addEventListener('click', async () => {
                        if (await userExperience.confirmAction(`Are you sure you want to ${user.is_active ? 'deactivate' : 'activate'} this user?`)) {
                            toggleUserStatus(user.id, !user.is_active);
                        }
                    });
                }
                
                // Setup enhanced delete button
                const deleteBtn = userCard.querySelector('.delete-user');
                if (deleteBtn) {
                    deleteBtn.addEventListener('click', async () => {
                        if (await userExperience.confirmAction('Are you sure you want to delete this user? This action cannot be undone.')) {
                            deleteUser(user.id);
                        }
                    });
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
                await loadUserPermissions(user.id);
            }
            
            notifications.show(`Loaded ${data.users.length} users successfully`, 'success');
        }
    } catch (error) {
        await errorHandler.handle(error, 'Loading Users');
    } finally {
        loadingIndicator.hide();
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
document.addEventListener('DOMContentLoaded', async function() {
    try {
        // Initialize navigation with effects
    initNavigation();
    
        // Initialize charts with animation
    initCharts();
    
        // Load initial data with loading indicators
        await Promise.all([
            loadStats(),
            loadUsers(),
            loadSettings(),
            loadTemplates()
        ]);
        
        // Add event listeners with enhanced confirmation
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
            settingsForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                if (await userExperience.confirmAction('Are you sure you want to save these settings?')) {
                    saveSettings(e);
    }
            });
    }
    
        // Enhanced logout handling
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
            logoutButton.addEventListener('click', async (e) => {
                e.preventDefault();
                if (await userExperience.confirmAction('Are you sure you want to log out?')) {
                    handleLogout(e);
                }
            });
        }
        
        // Initialize theme with enhanced effects
        initTheme();
        
        // Show welcome message
        await notifications.show('Welcome to GhostX Admin Control Center', 'success');
        
    } catch (error) {
        await errorHandler.handle(error, 'Initialization');
    }
});

// Add terminal-like effects and enhanced functionality
const terminalEffects = {
    typeWriter: (element, text, speed = 50) => {
        let i = 0;
        element.innerHTML = '';
        return new Promise(resolve => {
            function type() {
                if (i < text.length) {
                    element.innerHTML += text.charAt(i);
                    i++;
                    setTimeout(type, speed);
                } else {
                    resolve();
                }
            }
            type();
        });
    },

    glitchText: (element, finalText, duration = 1000) => {
        const glitchChars = '!@#$%^&*()_+-=[]{}|;:,.<>?';
        const steps = 10;
        const stepDuration = duration / steps;
        let step = 0;

        return new Promise(resolve => {
            const interval = setInterval(() => {
                if (step >= steps) {
                    clearInterval(interval);
                    element.textContent = finalText;
                    resolve();
                    return;
                }

                let glitchedText = '';
                for (let i = 0; i < finalText.length; i++) {
                    if (Math.random() > 0.7) {
                        glitchedText += glitchChars[Math.floor(Math.random() * glitchChars.length)];
                    } else {
                        glitchedText += finalText[i];
                    }
                }
                element.textContent = glitchedText;
                step++;
            }, stepDuration);
        });
    }
};

// Enhanced notification system
const notifications = {
    queue: [],
    isProcessing: false,

    show: async (message, type = 'info', duration = 3000) => {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icon = document.createElement('i');
        icon.className = `fas fa-${type === 'success' ? 'check-circle' : 
                                 type === 'error' ? 'exclamation-circle' : 
                                 type === 'warning' ? 'exclamation-triangle' : 'info-circle'}`;
        
        const textSpan = document.createElement('span');
        notification.appendChild(icon);
        notification.appendChild(textSpan);
        
        document.body.appendChild(notification);
        
        await terminalEffects.typeWriter(textSpan, message, 30);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in forwards';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, duration);
    }
};

// Enhanced loading indicator
const loadingIndicator = {
    show: () => {
        const loader = document.querySelector('.loading-indicator');
        if (loader) {
            loader.style.display = 'block';
            loader.innerHTML = `
                <div class="loader-content">
                    <div class="loader-spinner"></div>
                    <div class="loader-text">Processing...</div>
                    <div class="loader-progress">
                        <div class="progress-bar"></div>
                    </div>
                </div>
            `;
        }
    },
    
    hide: () => {
        const loader = document.querySelector('.loading-indicator');
        if (loader) {
            loader.style.display = 'none';
        }
    },
    
    updateProgress: (progress) => {
        const progressBar = document.querySelector('.loader-progress .progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
    }
};

// Enhanced user interface effects
const uiEffects = {
    scanEffect: (element) => {
        element.style.position = 'relative';
        const scan = document.createElement('div');
        scan.className = 'scan-effect';
        element.appendChild(scan);
        
        setTimeout(() => {
            element.removeChild(scan);
        }, 2000);
    },
    
    pulseEffect: (element) => {
        element.classList.add('pulse');
        setTimeout(() => {
            element.classList.remove('pulse');
        }, 1000);
    },
    
    glitchEffect: (element) => {
        element.classList.add('glitch');
        setTimeout(() => {
            element.classList.remove('glitch');
        }, 1000);
    }
};

// Enhanced error handling
const errorHandler = {
    handle: async (error, context = '') => {
        console.error(`Error in ${context}:`, error);
        
        const errorMessage = error.message || 'An unknown error occurred';
        await notifications.show(`[ERROR] ${context}: ${errorMessage}`, 'error');
        
        // Log to server
        try {
            await fetch('/api/admin/log-error', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': CSRF_TOKEN
                },
                body: JSON.stringify({
                    context,
                    error: errorMessage,
                    stack: error.stack,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (e) {
            console.error('Failed to log error:', e);
        }
    }
};

// Enhanced security features
const security = {
    // Use DOMPurify for HTML sanitization
    sanitizeHTML: (input) => {
        if (typeof input !== 'string') return '';
        return DOMPurify.sanitize(input, {
            ALLOWED_TAGS: ['p', 'br', 'b', 'i', 'em', 'strong', 'a', 'ul', 'ol', 'li'],
            ALLOWED_ATTR: ['href', 'target', 'rel'],
            FORBID_TAGS: ['script', 'style', 'iframe', 'form', 'input', 'button'],
            FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'onmouseout', 'style'],
            ALLOW_DATA_ATTR: false,
            USE_PROFILES: { html: true },
            SANITIZE_DOM: true,
            KEEP_CONTENT: true,
            RETURN_DOM_FRAGMENT: false,
            RETURN_DOM: false,
            FORCE_BODY: false,
            SAFE_FOR_TEMPLATES: true
        });
    },

    validateInput: (input) => {
        if (typeof input !== 'string') return false;
        
        // Comprehensive list of dangerous patterns
        const dangerousPatterns = [
            // Script tags with various formats
            /<[^>]*script/gi,
            /<[^>]*\\script/gi,
            /script\s*:/gi,
            /javascript\s*:/gi,
            /vbscript\s*:/gi,
            /livescript\s*:/gi,
            /&#/gi,  // HTML entities
            /data\s*:[^;]*base64/gi,
            
            // Event handlers
            /\bon\w+\s*=/gi,
            /\bfunction\s*\(/gi,
            
            // Data attributes that could contain scripts
            /data-[^=]*=/gi,
            
            // Other dangerous patterns
            /expression\s*\(/gi,
            /url\s*\(/gi,
            /eval\s*\(/gi,
            /alert\s*\(/gi,
            /document\s*\./gi,
            /window\s*\./gi,
            /\[\s*["'].*["']\s*\]/gi,  // Array access notation
            /\(\s*["'].*["']\s*\)/gi   // Function calls with string arguments
        ];

        // Check for dangerous patterns
        return !dangerousPatterns.some(pattern => pattern.test(input));
    },

    escapeHTML: (str) => {
        if (typeof str !== 'string') return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    // Validate URLs
    validateURL: (url) => {
        if (typeof url !== 'string') return false;
        try {
            const parsedUrl = new URL(url);
            return ['http:', 'https:'].includes(parsedUrl.protocol);
        } catch {
            return false;
        }
    },

    // Sanitize file names
    sanitizeFileName: (filename) => {
        if (typeof filename !== 'string') return '';
        return filename.replace(/[^a-zA-Z0-9._-]/g, '_');
    },

    // Validate JSON input
    validateJSON: (input) => {
        try {
            if (typeof input === 'string') {
                JSON.parse(input);
            }
            return true;
        } catch {
            return false;
        }
    },

    // Rate limiting helper
    rateLimiter: (() => {
        const limits = new Map();
        return {
            check: (key, maxAttempts = 5, timeWindow = 60000) => {
                const now = Date.now();
                const attempts = limits.get(key) || [];
                const recentAttempts = attempts.filter(time => now - time < timeWindow);
                limits.set(key, recentAttempts);
                if (recentAttempts.length >= maxAttempts) return false;
                recentAttempts.push(now);
                limits.set(key, recentAttempts);
                return true;
            }
        };
    })()
};

// Add DOMPurify configuration
document.addEventListener('DOMContentLoaded', () => {
    if (typeof DOMPurify !== 'undefined') {
        DOMPurify.setConfig({
            ADD_TAGS: ['meta', 'link'],
            ADD_ATTR: ['target', 'rel'],
            FORBID_CONTENTS: ['style', 'script', 'iframe', 'form', 'input'],
            WHOLE_DOCUMENT: false,
            FORCE_BODY: true,
            RETURN_DOM_FRAGMENT: false,
            RETURN_DOM: false,
            SANITIZE_DOM: true
        });
        
        // Add custom hooks
        DOMPurify.addHook('beforeSanitizeElements', (node) => {
            if (node.hasAttribute && node.hasAttribute('href')) {
                const href = node.getAttribute('href');
                if (!security.validateURL(href)) {
                    node.removeAttribute('href');
                }
            }
            return node;
        });
    }
});

// Enhanced user experience features
const userExperience = {
    confirmAction: (message) => {
        return new Promise(resolve => {
            const modal = document.createElement('div');
            modal.className = 'modal confirmation-modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <h3>Confirm Action</h3>
                    <p>${message}</p>
                    <div class="modal-actions">
                        <button class="auth-button confirm">Confirm</button>
                        <button class="auth-button cancel">Cancel</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            modal.querySelector('.confirm').addEventListener('click', () => {
                document.body.removeChild(modal);
                resolve(true);
            });
            
            modal.querySelector('.cancel').addEventListener('click', () => {
                document.body.removeChild(modal);
                resolve(false);
            });
        });
    }
};

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

// Security Monitoring Functions
function initializeSecurityMonitoring() {
    // Initialize Chart.js for metrics
    const ctx = document.getElementById('securityMetricsChart').getContext('2d');
    window.securityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Login Attempts',
                borderColor: '#e74c3c',
                data: []
            }, {
                label: 'API Requests',
                borderColor: '#2ecc71',
                data: []
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff'
                    }
                }
            }
        }
    });

    // Start real-time updates
    updateSecurityStatus();
    loadActiveSessions();
    setInterval(updateSecurityStatus, 30000); // Update every 30 seconds
    setInterval(updateMetrics, 5000); // Update metrics every 5 seconds
}

async function updateSecurityStatus() {
    try {
        const response = await fetch('/api/admin/system-status', fetchOptions('GET'));
        const data = await response.json();
        
        if (data.success) {
            // Update status indicators
            updateStatusIndicator('apiStatus', data.api_status);
            updateStatusIndicator('dbStatus', data.db_status);
            updateStatusIndicator('emailStatus', data.email_status);
        } else {
            throw new Error(data.message || 'Failed to update system status');
        }
    } catch (error) {
        console.error('Error updating system status:', error);
        showNotification('Failed to update system status', 'error');
    }
}

function updateStatusIndicator(elementId, status) {
    const indicator = document.getElementById(elementId);
    if (indicator) {
        indicator.className = 'status-indicator ' + status.toLowerCase();
        indicator.title = `Last checked: ${new Date().toLocaleTimeString()}`;
    }
}

async function loadActiveSessions() {
    try {
        const response = await fetch('/api/admin/active-sessions', fetchOptions('GET'));
        const data = await response.json();
        
        if (data.success) {
            const sessionsList = document.getElementById('activeSessions');
            sessionsList.innerHTML = data.sessions.map(session => `
                <div class="session-item">
                    <div class="session-info">
                        <span class="session-user">${session.username}</span>
                        <span class="session-details">IP: ${session.ip} | Last active: ${session.last_active}</span>
                    </div>
                    <div class="session-actions">
                        <button onclick="terminateSession('${session.id}')">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            throw new Error(data.message || 'Failed to load active sessions');
        }
    } catch (error) {
        console.error('Error loading active sessions:', error);
        showNotification('Failed to load active sessions', 'error');
    }
}

async function updateMetrics() {
    try {
        const response = await fetch('/api/admin/security-metrics', fetchOptions('GET'));
        const data = await response.json();
        
        if (data.success) {
            const chart = window.securityChart;
            
            // Update chart data
            chart.data.labels = data.timestamps;
            chart.data.datasets[0].data = data.login_attempts;
            chart.data.datasets[1].data = data.api_requests;
            
            chart.update();
            
            // Update alerts
            updateSecurityAlerts(data.alerts);
        } else {
            throw new Error(data.message || 'Failed to update metrics');
        }
    } catch (error) {
        console.error('Error updating metrics:', error);
        showNotification('Failed to update metrics', 'error');
    }
}

function updateSecurityAlerts(alerts) {
    const alertsList = document.getElementById('securityAlerts');
    if (alertsList) {
        alertsList.innerHTML = alerts.map(alert => `
            <div class="alert-item ${alert.severity.toLowerCase()}">
                <div class="alert-icon">
                    <i class="fas fa-${getAlertIcon(alert.severity)}"></i>
                </div>
                <div class="alert-content">
                    <div class="alert-title">${alert.title}</div>
                    <div class="alert-message">${alert.message}</div>
                    <div class="alert-time">${new Date(alert.timestamp).toLocaleString()}</div>
                </div>
            </div>
        `).join('');
    }
}

function getAlertIcon(severity) {
    switch (severity.toLowerCase()) {
        case 'high':
            return 'exclamation-triangle';
        case 'medium':
            return 'exclamation-circle';
        case 'low':
            return 'info-circle';
        default:
            return 'bell';
    }
}

async function terminateSession(sessionId) {
    try {
        if (!await userExperience.confirmAction('Are you sure you want to terminate this session?')) {
            return;
        }

        const response = await fetch('/api/admin/terminate-session', fetchOptions('POST', {
            session_id: sessionId
        }));
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Session terminated successfully', 'success');
            loadActiveSessions();
        } else {
            throw new Error(data.message || 'Failed to terminate session');
        }
    } catch (error) {
        console.error('Error terminating session:', error);
        showNotification(error.message || 'Failed to terminate session', 'error');
    }
}

async function terminateAllSessions() {
    try {
        if (!await userExperience.confirmAction('Are you sure you want to terminate all sessions? This will log out all users.')) {
            return;
        }

        const response = await fetch('/api/admin/terminate-all-sessions', fetchOptions('POST'));
        const data = await response.json();
        
        if (data.success) {
            showNotification('All sessions terminated successfully', 'success');
            loadActiveSessions();
        } else {
            throw new Error(data.message || 'Failed to terminate all sessions');
        }
    } catch (error) {
        console.error('Error terminating all sessions:', error);
        showNotification(error.message || 'Failed to terminate all sessions', 'error');
    }
}

async function exportSecurityLogs() {
    try {
        const response = await fetch('/api/admin/security-logs', {
            ...fetchOptions('GET'),
            headers: {
                ...fetchOptions('GET').headers,
                'Accept': 'text/plain'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to export security logs');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `security-logs-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showNotification('Security logs exported successfully', 'success');
    } catch (error) {
        console.error('Error exporting security logs:', error);
        showNotification(error.message || 'Failed to export security logs', 'error');
    }
}

// Initialize security monitoring when the page loads
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('security')) {
        initializeSecurityMonitoring();
    }
}); 