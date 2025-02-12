import { showNotification, apiRequest } from './utils.js';

// Initialize tooltips
tippy('[data-tippy-content]', {
    placement: 'bottom',
    animation: 'scale',
    theme: 'custom'
});

// Initialize Ace Editor
let editor;
const initializeAceEditor = () => {
    editor = ace.edit("htmlContent");
    editor.setTheme("ace/theme/monokai");
    editor.session.setMode("ace/mode/html");
    editor.setOptions({
        fontSize: "14px",
        showPrintMargin: false,
        showGutter: true,
        highlightActiveLine: true,
        enableLiveAutocompletion: true
    });
};

// Theme Toggle
const themeToggle = document.getElementById('themeToggle');
const body = document.body;
themeToggle.addEventListener('click', () => {
    body.classList.toggle('dark-theme');
    const isDark = body.classList.contains('dark-theme');
    themeToggle.innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    if (editor) {
        editor.setTheme(isDark ? "ace/theme/monokai" : "ace/theme/chrome");
    }
});

// Load saved theme
if (localStorage.getItem('theme') === 'dark') {
    body.classList.add('dark-theme');
    themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
}

// Tab Navigation with smooth scrolling
document.querySelectorAll('.nav-link[data-tab]').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const tabId = item.getAttribute('data-tab');
        
        // Update navigation items
        document.querySelectorAll('.nav-link').forEach(navItem => {
            navItem.classList.remove('active');
        });
        item.classList.add('active');
        
        // Smooth scroll to section
        document.getElementById(tabId).scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    });
});

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

// Load user stats and limits with progress bars
async function loadStats() {
    try {
        const response = await fetch('/api/limits', fetchOptions('GET'));
        const data = await response.json();
        
        if (data.success) {
            // Update numbers
            document.getElementById('emailCount').textContent = data.email_count;
            document.getElementById('hourlyLimit').textContent = data.hourly_remaining;
            document.getElementById('dailyLimit').textContent = data.daily_remaining;
            
            // Update progress bars
            const hourlyProgress = (data.hourly_remaining / data.hourly_total) * 100;
            const dailyProgress = (data.daily_remaining / data.daily_total) * 100;
            
            document.getElementById('hourlyProgress').style.width = `${hourlyProgress}%`;
            document.getElementById('dailyProgress').style.width = `${dailyProgress}%`;
            
            // Update trend
            const trend = ((data.email_count - data.previous_count) / data.previous_count) * 100;
            document.getElementById('emailTrend').textContent = `${trend.toFixed(1)}%`;
            const trendIcon = document.querySelector('.trend-icon i');
            trendIcon.className = trend >= 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down';
        } else {
            throw new Error(data.message || 'Failed to load limits');
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        showNotification('Failed to load email limits', 'error');
    }
}

// Template search and filtering
const templateSearch = document.getElementById('templateSearch');
const templateFilter = document.getElementById('templateFilter');

templateSearch.addEventListener('input', filterTemplates);
templateFilter.addEventListener('change', filterTemplates);

function filterTemplates() {
    const searchTerm = templateSearch.value.toLowerCase();
    const filterValue = templateFilter.value;
    const showFavoritesOnly = document.getElementById('showFavorites')?.checked || false;
    
    document.querySelectorAll('.template-card').forEach(card => {
        const templateName = card.querySelector('h3').textContent.toLowerCase();
        const templateType = card.dataset.type;
        const templateFilename = card.querySelector('.favorite-btn').dataset.template;
        const isFavorite = localStorage.getItem(`fav_${templateFilename}`) === 'true';
        
        const matchesSearch = templateName.includes(searchTerm);
        const matchesFilter = filterValue === 'all' || templateType === filterValue;
        const matchesFavorites = !showFavoritesOnly || isFavorite;
        
        if (matchesSearch && matchesFilter && matchesFavorites) {
            card.style.display = 'flex';
            card.style.opacity = '1';
        } else {
            card.style.display = 'none';
            card.style.opacity = '0';
        }
    });
}

// Handle custom email submission with preview
const toggleEditor = document.getElementById('toggleEditor');
const previewPane = document.getElementById('preview');
let isPreviewMode = false;

toggleEditor.addEventListener('click', () => {
    isPreviewMode = !isPreviewMode;
    previewPane.style.display = isPreviewMode ? 'block' : 'none';
    editor.container.style.display = isPreviewMode ? 'none' : 'block';
    toggleEditor.innerHTML = isPreviewMode ? 
        '<i class="fas fa-code"></i> Show Editor' : 
        '<i class="fas fa-eye"></i> Show Preview';
    
    if (isPreviewMode) {
        previewPane.srcdoc = editor.getValue();
    }
});

async function handleCustomEmail(event) {
    event.preventDefault();
    
    try {
        const formData = {
            recipient_email: document.getElementById('recipientEmail').value,
            sender_name: document.getElementById('senderName').value,
            sender_email: document.getElementById('senderEmail').value,
            subject: document.getElementById('emailSubject').value,
            html_content: editor.getValue()
        };
        
        const response = await fetch('/admin/send-email', fetchOptions('POST', formData));
        const data = await response.json();
        
        if (data.success) {
            showNotification('Email sent successfully', 'success');
            document.getElementById('customEmailForm').reset();
            editor.setValue('');
            loadStats(); // Refresh stats after sending email
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Error sending email:', error);
        showNotification(error.message || 'Failed to send email', 'error');
    }
}

// Load user data when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Load initial data
    loadStats();
    loadTemplates(); // Load templates first
    
    // Set up interval updates
    setInterval(loadStats, 60000); // Update stats every minute
    
    // Add event listeners for modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
    
    // Initialize tooltips
    tippy('[data-tippy-content]', {
        placement: 'bottom',
        animation: 'scale',
        theme: 'custom'
    });
    
    // Initialize template search and filters
    const templateSearch = document.getElementById('templateSearch');
    const templateFilter = document.getElementById('templateFilter');
    if (templateSearch && templateFilter) {
        templateSearch.addEventListener('input', filterTemplates);
        templateFilter.addEventListener('change', filterTemplates);
    }
    
    // Initialize editor if custom email section exists
    const customEmailSection = document.getElementById('custom-email');
    if (customEmailSection) {
        initializeAceEditor();
    }
});

// Load email templates with enhanced UI
async function loadTemplates() {
    console.log('Loading templates...');
    try {
        const templateGrid = document.getElementById('templateGrid');
        if (!templateGrid) {
            console.error('Template grid element not found');
            return;
        }
        
        // Add loading animation
        templateGrid.innerHTML = `
            <div class="loading-animation">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Loading Templates...</p>
            </div>
        `;
        
        // Simulate loading delay for better UX
        await new Promise(resolve => setTimeout(resolve, 800));
        
        const templates = [
            {
                filename: 'coinbase_hold.html',
                name: 'Coinbase Hold',
                description: 'Professional Coinbase security and account verification template',
                type: 'coinbase',
                sender: {
                    name: 'Coinbase Support',
                    email: 'support@coinbase.com',
                    subject: 'Important: Action Required for Your Coinbase Account'
                }
            },
            {
                filename: 'coinbase_transaction.html',
                name: 'Coinbase Transaction',
                description: 'Coinbase transaction confirmation template',
                type: 'coinbase',
                sender: {
                    name: 'Coinbase',
                    email: 'no-reply@coinbase.com',
                    subject: 'Transaction Confirmation Required'
                }
            },
            {
                filename: 'trezor.html',
                name: 'Trezor Security',
                description: 'Trezor wallet security update template',
                type: 'trezor',
                sender: {
                    name: 'Trezor Team',
                    email: 'support@trezor.io',
                    subject: 'Important: Trezor Wallet Security Update'
                }
            },
            {
                filename: 'google_template.html',
                name: 'Google Security',
                description: 'Google account security alert template',
                type: 'google',
                sender: {
                    name: 'Google Account Team',
                    email: 'no-reply@google.com',
                    subject: 'Security Alert: Action Required'
                }
            },
            {
                filename: 'coinbase_secure_template.html',
                name: 'Coinbase Security',
                description: 'Coinbase account security verification template',
                type: 'coinbase',
                sender: {
                    name: 'Coinbase Security',
                    email: 'security@coinbase.com',
                    subject: 'Security Notice: Verify Your Account'
                }
            },
            {
                filename: 'coinbase_wallet_template.html',
                name: 'Coinbase Wallet',
                description: 'Coinbase wallet verification template',
                type: 'coinbase',
                sender: {
                    name: 'Coinbase Wallet',
                    email: 'wallet@coinbase.com',
                    subject: 'Wallet Verification Required'
                }
            },
            {
                filename: 'coinbase_template.html',
                name: 'Coinbase General',
                description: 'General Coinbase notification template',
                type: 'coinbase',
                sender: {
                    name: 'Coinbase',
                    email: 'info@coinbase.com',
                    subject: 'Important Account Notice'
                }
            },
            {
                filename: 'kraken.html',
                name: 'Kraken',
                description: 'Kraken exchange account verification template',
                type: 'kraken',
                sender: {
                    name: 'Kraken Support',
                    email: 'support@kraken.com',
                    subject: 'Important: Verify Your Kraken Account'
                }
            },
            {
                filename: 'gmail.html',
                name: 'Gmail Security',
                description: 'Gmail account security notification template',
                type: 'gmail',
                sender: {
                    name: 'Google',
                    email: 'no-reply@accounts.google.com',
                    subject: 'Critical Security Alert'
                }
            }
        ];
        
            templateGrid.innerHTML = '';
        console.log(`Processing ${templates.length} templates...`);
            
        templates.forEach((template, index) => {
                const templateCard = document.createElement('div');
                templateCard.className = 'template-card';
            templateCard.dataset.type = template.type;
            
            const senderInfoAttr = encodeURIComponent(JSON.stringify(template.sender));
            
                templateCard.innerHTML = `
                    <div class="template-content">
                    <div class="template-header">
                        <h3>${template.name}</h3>
                        <div class="template-badges">
                            <span class="template-badge ${template.type}">${template.type}</span>
                            <button class="favorite-btn ${localStorage.getItem(`fav_${template.filename}`) ? 'active' : ''}" 
                                    data-template="${template.filename}" 
                                    title="Add to favorites">
                                <i class="fas fa-star"></i>
                            </button>
                        </div>
                    </div>
                    <p>${template.description}</p>
                    <div class="template-meta">
                        <span><i class="fas fa-user"></i> ${template.sender.name}</span>
                        <span><i class="fas fa-envelope"></i> ${template.sender.email}</span>
                    </div>
                    <div class="template-actions">
                        <button class="auth-button use-template" data-template="${template.filename}" 
                                data-sender='${JSON.stringify(template.sender)}'>
                            <i class="fas fa-paper-plane"></i> Use
                        </button>
                        <button class="auth-button warning preview-template" data-template="${template.filename}">
                            <i class="fas fa-eye"></i> Preview
                        </button>
                        <button class="auth-button info share-btn" data-template="${template.filename}">
                            <i class="fas fa-share-alt"></i> Share
                        </button>
                    </div>
                    </div>
                `;
            
            // Add event listeners
            const useButton = templateCard.querySelector('.use-template');
            const previewButton = templateCard.querySelector('.preview-template');
            const shareButton = templateCard.querySelector('.share-btn');
            const favoriteButton = templateCard.querySelector('.favorite-btn');
            
            useButton.addEventListener('click', () => {
                const senderInfo = JSON.parse(useButton.dataset.sender);
                useTemplate(useButton.dataset.template, senderInfo);
            });
            
            previewButton.addEventListener('click', () => {
                previewTemplate(previewButton.dataset.template);
            });
            
            shareButton.addEventListener('click', () => {
                shareTemplate(shareButton.dataset.template);
            });
            
            favoriteButton.addEventListener('click', () => {
                toggleFavorite(favoriteButton.dataset.template);
                favoriteButton.classList.toggle('active');
            });
            
            templateGrid.appendChild(templateCard);
            console.log(`Added template card for ${template.name}`);
            
            // Add animation delay
            templateCard.style.animationDelay = `${index * 0.1}s`;
        });
    } catch (error) {
        console.error('Error loading templates:', error);
        showNotification('Failed to load email templates', 'error');
        
        // Show error state in grid
        if (templateGrid) {
            templateGrid.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <h3>Failed to Load Templates</h3>
                    <p>Please try refreshing the page</p>
                </div>
            `;
        }
    }
}

// Template functions with enhanced preview
async function useTemplate(templateFilename, senderInfo) {
    try {
        console.log(`Loading template: ${templateFilename}`);
        const response = await fetch(`/static/templates/${templateFilename}`);
        
        if (!response.ok) {
            throw new Error(`Failed to load template: ${response.statusText}`);
        }
        
        const templateContent = await response.text();
        console.log('Template content loaded successfully');
        
        // Set form values
        document.getElementById('senderName').value = senderInfo.name;
        document.getElementById('senderEmail').value = senderInfo.email;
        document.getElementById('emailSubject').value = senderInfo.subject;
        
        // Set editor content
        editor.setValue(templateContent);
        editor.clearSelection();
        
        // Scroll to the form with highlight effect
        const form = document.getElementById('customEmailForm');
        form.scrollIntoView({ behavior: 'smooth' });
        form.classList.add('highlight');
        setTimeout(() => form.classList.remove('highlight'), 1000);
        
        // Show success notification
        showNotification('Template loaded successfully', 'success');
        
        // Switch to the custom email section
        document.getElementById('custom-email').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error('Error in useTemplate:', error);
        showNotification(`Failed to load template: ${error.message}`, 'error');
    }
}

async function previewTemplate(templateFilename) {
    try {
        console.log(`Previewing template: ${templateFilename}`);
        
        // Create modal immediately with loading state
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2><i class="fas fa-eye"></i> Template Preview</h2>
                    <button class="close-button" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="loading-animation">
                        <i class="fas fa-spinner fa-spin"></i>
                        <p>Loading Preview...</p>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const response = await fetch(`/static/templates/${templateFilename}`);
        
        if (!response.ok) {
            throw new Error(`Failed to load template for preview: ${response.statusText}`);
        }
        
        const templateContent = await response.text();
        console.log('Template content loaded successfully for preview');
        
        // Update modal with template content
        const modalContent = modal.querySelector('.modal-content');
        modalContent.innerHTML = `
            <div class="modal-header">
                <h2><i class="fas fa-eye"></i> Template Preview</h2>
                <div class="modal-actions">
                    <button class="modal-button" id="copyTemplate">
                        <i class="fas fa-copy"></i> Copy HTML
                    </button>
                    <button class="close-button" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <div class="modal-body">
                <div class="preview-controls">
                    <button class="preview-button active" data-view="desktop">
                        <i class="fas fa-desktop"></i> Desktop
                    </button>
                    <button class="preview-button" data-view="tablet">
                        <i class="fas fa-tablet-alt"></i> Tablet
                    </button>
                    <button class="preview-button" data-view="mobile">
                        <i class="fas fa-mobile-alt"></i> Mobile
                    </button>
                </div>
                <div class="preview-container desktop">
                    <iframe srcdoc="${templateContent.replace(/"/g, '&quot;')}" 
                            class="preview-frame"></iframe>
                </div>
            </div>
        `;
        
        // Set up preview controls
        modal.querySelectorAll('.preview-button').forEach(button => {
            button.addEventListener('click', () => {
                modal.querySelectorAll('.preview-button').forEach(b => b.classList.remove('active'));
                button.classList.add('active');
                const view = button.dataset.view;
                const container = modal.querySelector('.preview-container');
                container.className = `preview-container ${view}`;
            });
        });
        
        // Set up copy button
        modal.querySelector('#copyTemplate').addEventListener('click', () => {
            navigator.clipboard.writeText(templateContent)
                .then(() => {
                    showNotification('Template HTML copied to clipboard', 'success');
                })
                .catch(() => showNotification('Failed to copy template HTML', 'error'));
        });
        
        // Add click event to close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        // Add escape key event to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && document.querySelector('.modal')) {
                document.querySelector('.modal').remove();
            }
        });
    } catch (error) {
        console.error('Error in previewTemplate:', error);
        showNotification(`Failed to preview template: ${error.message}`, 'error');
    }
}

// Keep only necessary window functions
window.showTemplates = () => {
    document.querySelector('#templates').scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
    });
};

window.showStats = () => {
    document.querySelector('#stats').scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
    });
};

// Template favorites
function toggleFavorite(templateFilename) {
    const key = `fav_${templateFilename}`;
    const isFavorite = localStorage.getItem(key) === 'true';
    
    if (isFavorite) {
        localStorage.removeItem(key);
        showNotification('Removed from favorites', 'info');
    } else {
        localStorage.setItem(key, 'true');
        showNotification('Added to favorites', 'success');
    }
    
    // Update favorite button state
    const favoriteBtn = document.querySelector(`.favorite-btn[data-template="${templateFilename}"]`);
    if (favoriteBtn) {
        favoriteBtn.classList.toggle('active', !isFavorite);
    }
    
    filterTemplates(); // Refresh template display
}

// Template sharing
async function shareTemplate(templateFilename) {
    try {
        const response = await fetch(`/static/templates/${templateFilename}`);
        if (!response.ok) throw new Error('Failed to load template');
        
        const templateContent = await response.text();
        
        // Create share modal
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2><i class="fas fa-share-alt"></i> Share Template</h2>
                    <button class="close-button" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="share-options">
                        <button class="share-option" data-type="copy">
                            <i class="fas fa-copy"></i>
                            <span>Copy Template Code</span>
                        </button>
                        <button class="share-option" data-type="download">
                            <i class="fas fa-download"></i>
                            <span>Download Template</span>
                        </button>
                        <button class="share-option" data-type="link">
                            <i class="fas fa-link"></i>
                            <span>Copy Share Link</span>
                        </button>
                    </div>
        </div>
        </div>
    `;
    
        document.body.appendChild(modal);
        
        // Handle share options
        modal.querySelectorAll('.share-option').forEach(button => {
            button.addEventListener('click', async () => {
                const type = button.dataset.type;
                
                switch(type) {
                    case 'copy':
                        await navigator.clipboard.writeText(templateContent);
                        showNotification('Template code copied to clipboard', 'success');
                        break;
                        
                    case 'download':
                        const blob = new Blob([templateContent], { type: 'text/html' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = templateFilename;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                        showNotification('Template downloaded successfully', 'success');
                        break;
                        
                    case 'link':
                        const shareLink = `${window.location.origin}/template/share/${templateFilename}`;
                        await navigator.clipboard.writeText(shareLink);
                        showNotification('Share link copied to clipboard', 'success');
                        break;
                }
                
                modal.remove();
            });
        });
        
    } catch (error) {
        console.error('Error sharing template:', error);
        showNotification('Failed to share template', 'error');
    }
}

// Rate Limiting Functions
async function loadQuota() {
    try {
        const response = await fetch('/api/quota', fetchOptions('GET'));
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        if (data.success) {
            updateQuotaDisplay(data.quota);
        } else {
            throw new Error(data.message || 'Failed to load quota');
        }
    } catch (error) {
        console.error('Error loading quota:', error);
        showNotification('Failed to load quota information', 'error');
    }
}

function updateQuotaDisplay(quota) {
    // Update hourly quota
    const hourlyLimit = document.getElementById('hourlyLimit');
    const hourlyProgress = document.getElementById('hourlyProgress');
    const hourlyReset = document.getElementById('hourlyReset');
    
    if (hourlyLimit && hourlyProgress && hourlyReset) {
        hourlyLimit.textContent = quota.hourly.remaining;
        const hourlyPercent = ((quota.hourly.limit - quota.hourly.remaining) / quota.hourly.limit) * 100;
        hourlyProgress.style.width = `${hourlyPercent}%`;
        updateResetTimer('hourlyReset', new Date(quota.hourly.reset_time));
    }
    
    // Update daily quota
    const dailyLimit = document.getElementById('dailyLimit');
    const dailyProgress = document.getElementById('dailyProgress');
    const dailyReset = document.getElementById('dailyReset');
    
    if (dailyLimit && dailyProgress && dailyReset) {
        dailyLimit.textContent = quota.daily.remaining;
        const dailyPercent = ((quota.daily.limit - quota.daily.remaining) / quota.daily.limit) * 100;
        dailyProgress.style.width = `${dailyPercent}%`;
        updateResetTimer('dailyReset', new Date(quota.daily.reset_time));
    }
}

function updateResetTimer(elementId, resetTime) {
    const element = document.getElementById(elementId);
    
    function updateTimer() {
        const now = new Date();
        const diff = resetTime - now;
        
        if (diff <= 0) {
            element.textContent = 'Resetting...';
            setTimeout(loadQuota, 1000);
            return;
        }
        
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        element.textContent = `Resets in: ${hours}h ${minutes}m`;
    }
    
    updateTimer();
    setInterval(updateTimer, 60000); // Update every minute
}

// Remove campaign functions
// Remove loadCampaigns()
// Remove renderCampaigns()
// Remove createCampaign()
// Remove showCampaignDetails()
// Remove updateCampaignDetailsModal()
// Remove pauseCampaign()
// Remove resumeCampaign()
// Remove stopCampaign()

// Remove campaign modal functions
window.showNewCampaignModal = undefined;
window.closeNewCampaignModal = undefined;
window.closeCampaignDetailsModal = undefined;
window.showCampaignDetails = undefined;