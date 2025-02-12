import { showNotification } from './utils.js';

// Get CSRF token from meta tag
const getCSRFToken = () => {
    const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    if (!token) {
        throw new Error('CSRF token not found');
    }
    return token;
};

// Common fetch options with CSRF token
const fetchWithCSRF = async (url, method, data = null) => {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCSRFToken()
        },
        credentials: 'same-origin'
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    return fetch(url, options);
};

// Form toggle functionality
function toggleForms() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    if (loginForm && registerForm) {
        loginForm.classList.toggle('active');
        registerForm.classList.toggle('active');
    }
}

// Toggle password visibility
function togglePasswordVisibility(inputId, buttonId) {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);
    
    if (input && button) {
        if (input.type === 'password') {
            input.type = 'text';
            button.innerHTML = '<i class="fas fa-eye-slash"></i>';
        } else {
            input.type = 'password';
            button.innerHTML = '<i class="fas fa-eye"></i>';
        }
    }
}

// Validate username format
function validateUsername(username) {
    return /^[a-zA-Z0-9_]{3,20}$/.test(username);
}

// Calculate password strength
function calculatePasswordStrength(password) {
    let strength = 0;
    let feedback = [];
    
    // Length check
    if (password.length >= 8) {
        strength += 20;
    } else {
        feedback.push('at least 8 characters');
    }
    
    // Uppercase check
    if (/[A-Z]/.test(password)) {
        strength += 20;
    } else {
        feedback.push('uppercase letter');
    }
    
    // Lowercase check
    if (/[a-z]/.test(password)) {
        strength += 20;
    } else {
        feedback.push('lowercase letter');
    }
    
    // Number check
    if (/[0-9]/.test(password)) {
        strength += 20;
    } else {
        feedback.push('number');
    }
    
    // Special character check
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
        strength += 20;
    } else {
        feedback.push('special character');
    }
    
    return {
        score: strength,
        feedback: feedback
    };
}

// Update password strength UI
function updatePasswordStrength(password) {
    const strengthBar = document.querySelector('.strength-bar');
    const strengthText = document.querySelector('.strength-text');
    
    if (!strengthBar || !strengthText) return;
    
    const { score, feedback } = calculatePasswordStrength(password);
    
    // Update strength bar
    strengthBar.style.width = `${score}%`;
    strengthBar.className = 'strength-bar';
    
    if (score < 40) {
        strengthBar.classList.add('weak');
        strengthText.textContent = 'Weak';
    } else if (score < 80) {
        strengthBar.classList.add('medium');
        strengthText.textContent = 'Medium';
    } else {
        strengthBar.classList.add('strong');
        strengthText.textContent = 'Strong';
    }
    
    if (feedback.length > 0) {
        strengthText.textContent += ` (needs ${feedback.join(', ')})`;
    }
}

// Validate password strength
function isPasswordStrong(password) {
    const { score, feedback } = calculatePasswordStrength(password);
    
    if (score < 100) {
        return { 
            valid: false, 
            message: `Password must contain ${feedback.join(', ')}`
        };
    }
    
    return { valid: true };
}

// Handle Login
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errorElement = document.getElementById('loginError');
    const form = event.target;
    
    // Disable form while processing
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = true;
    }
    
    // Clear previous error
    if (errorElement) {
        errorElement.style.display = 'none';
        errorElement.textContent = '';
    }
    
    try {
        // Validate input
        if (!username || !password) {
            throw new Error('Please fill in all fields');
        }
        
        console.log('Sending login request...');
        
        // Make API request using fetchWithCSRF
        const response = await fetchWithCSRF('/api/login', 'POST', {
            username,
            password
        });
        
        console.log('Response received:', response.status, response.statusText);
        console.log('Response headers:', Object.fromEntries([...response.headers]));
        
        // Check content type before trying to parse JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            console.error('Invalid content type:', contentType);
            throw new Error('Server returned invalid response format');
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (!response.ok) {
            throw new Error(data.message || `Error: ${response.status}`);
        }
        
        if (data.success) {
            showNotification(data.message || 'Login successful!', 'success');
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 500);
        } else {
            throw new Error(data.message || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        const errorMessage = error.message || 'An error occurred during login';
        showNotification(errorMessage, 'error');
        
        if (errorElement) {
            errorElement.textContent = errorMessage;
            errorElement.style.display = 'block';
        }
    } finally {
        // Re-enable form
        if (submitButton) {
            submitButton.disabled = false;
        }
    }
}

// Handle Registration
async function handleRegister(event) {
    event.preventDefault();
    
    const username = document.getElementById('registerUsername').value.trim();
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const errorElement = document.getElementById('registerError');
    
    // Clear previous error
    if (errorElement) {
        errorElement.style.display = 'none';
        errorElement.textContent = '';
    }
    
    // Validate username
    if (!validateUsername(username)) {
        const message = 'Username must be 3-20 characters and contain only letters, numbers, and underscores';
        showNotification(message, 'error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
        return;
    }
    
    // Validate password match
    if (password !== confirmPassword) {
        const message = 'Passwords do not match';
        showNotification(message, 'error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
        return;
    }
    
    // Validate password strength
    const passwordCheck = isPasswordStrong(password);
    if (!passwordCheck.valid) {
        showNotification(passwordCheck.message, 'error');
        if (errorElement) {
            errorElement.textContent = passwordCheck.message;
            errorElement.style.display = 'block';
        }
        return;
    }
    
    try {
        const response = await fetch('/api/register', fetchOptions('POST', {
            username,
            password,
            confirm_password: confirmPassword
        }));
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Registration successful!', 'success');
            window.location.href = data.redirect;
        } else {
            if (errorElement) {
                errorElement.textContent = data.message || 'Registration failed';
                errorElement.style.display = 'block';
            }
            showNotification(data.message || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showNotification('An error occurred during registration', 'error');
        if (errorElement) {
            errorElement.textContent = 'An error occurred during registration';
            errorElement.style.display = 'block';
        }
    }
}

// Handle Logout
function handleLogout(e) {
    if (e) {
        e.preventDefault();
    }
    // Clear any client-side storage
    localStorage.clear();
    sessionStorage.clear();
    
    // Redirect to logout page
    window.location.href = '/logout';
}

// Handle form submissions
document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    const loginForm = document.getElementById('loginForm');

    // Register form handler
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const username = document.getElementById('registerUsername').value.trim();
            const password = document.getElementById('registerPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            const errorDiv = document.getElementById('registerError');
            const submitButton = this.querySelector('button[type="submit"]');

            try {
                submitButton.disabled = true;
                const response = await fetchWithCSRF('/api/register', 'POST', {
                    username,
                    password,
                    confirm_password: confirmPassword
                });

                const data = await response.json();
                
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    errorDiv.textContent = data.message;
                    errorDiv.style.display = 'block';
                }
            } catch (error) {
                console.error('Registration error:', error);
                errorDiv.textContent = 'An error occurred. Please try again.';
                errorDiv.style.display = 'block';
            } finally {
                submitButton.disabled = false;
            }
        });
    }

    // Login form handler
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const username = document.getElementById('loginUsername').value.trim();
            const password = document.getElementById('loginPassword').value;
            const errorDiv = document.getElementById('loginError');
            const submitButton = this.querySelector('button[type="submit"]');

            try {
                submitButton.disabled = true;
                const response = await fetchWithCSRF('/api/login', 'POST', {
                    username,
                    password
                });

                const data = await response.json();
                
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    errorDiv.textContent = data.message;
                    errorDiv.style.display = 'block';
                }
            } catch (error) {
                console.error('Login error:', error);
                errorDiv.textContent = 'An error occurred. Please try again.';
                errorDiv.style.display = 'block';
            } finally {
                submitButton.disabled = false;
            }
        });
    }

    // Password toggle functionality
    const passwordToggles = document.querySelectorAll('.password-toggle');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const input = this.parentElement.querySelector('input');
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });

    // Clear any existing error messages
    const errorMessages = document.querySelectorAll('.error-message');
    errorMessages.forEach(msg => msg.style.display = 'none');
    
    // Get form elements
    const loginButton = document.getElementById('loginButton');
    const passwordToggle = document.getElementById('passwordToggle');
    const loginPassword = document.getElementById('loginPassword');
    const errorElement = document.getElementById('loginError');

    // Password toggle functionality
    if (passwordToggle && loginPassword) {
        passwordToggle.addEventListener('click', () => {
            const type = loginPassword.type === 'password' ? 'text' : 'password';
            loginPassword.type = type;
            passwordToggle.innerHTML = type === 'password' ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
        });
    }

    // Login form handler
    if (loginForm) {
        loginForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            // Disable button while processing
            if (loginButton) {
                loginButton.disabled = true;
            }
            
            // Clear previous error
            if (errorElement) {
                errorElement.style.display = 'none';
                errorElement.textContent = '';
            }
            
            const username = document.getElementById('loginUsername').value.trim();
            const password = loginPassword.value;
            
            try {
                // Validate input
                if (!username || !password) {
                    throw new Error('Please fill in all fields');
                }
                
                console.log('Sending login request...');
                
                // Make API request using fetchWithCSRF
                const response = await fetchWithCSRF('/api/login', 'POST', {
                    username,
                    password
                });
                
                console.log('Response received:', response.status, response.statusText);
                console.log('Response headers:', Object.fromEntries([...response.headers]));
                
                // Check content type before trying to parse JSON
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    console.error('Invalid content type:', contentType);
                    throw new Error('Server returned invalid response format');
                }
                
                const data = await response.json();
                console.log('Response data:', data);
                
                if (!response.ok) {
                    throw new Error(data.message || `Error: ${response.status}`);
                }
                
                if (data.success) {
                    showNotification(data.message || 'Login successful!', 'success');
                    setTimeout(() => {
                        window.location.href = data.redirect;
                    }, 500);
                } else {
                    throw new Error(data.message || 'Login failed');
                }
            } catch (error) {
                console.error('Login error:', error);
                const errorMessage = error.message || 'An error occurred during login';
                showNotification(errorMessage, 'error');
                
                if (errorElement) {
                    errorElement.textContent = errorMessage;
                    errorElement.style.display = 'block';
                }
            } finally {
                // Re-enable button
                if (loginButton) {
                    loginButton.disabled = false;
                }
            }
        });
    }
    
    // Register form handler
    const showRegisterLink = document.getElementById('showRegister');
    const showLoginLink = document.getElementById('showLogin');
    
    if (showRegisterLink) {
        showRegisterLink.addEventListener('click', function(e) {
            e.preventDefault();
            toggleForms();
        });
    }
    
    if (showLoginLink) {
        showLoginLink.addEventListener('click', function(e) {
            e.preventDefault();
            toggleForms();
        });
    }

    // Logout button handler
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', function(e) {
            e.preventDefault();
            handleLogout();
        });
    }
}); 