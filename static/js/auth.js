/**
 * Authentication Module
 * Handles login form submission, token management, and redirects
 */

console.log('auth.js loaded');

// Check if user is already logged in when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded event fired');
    const token = localStorage.getItem('access_token');
    const loginForm = document.getElementById('loginForm');
    const profileSection = document.getElementById('profileSection');
    const signupLink = document.getElementById('signupLink');

    console.log('Token exists:', !!token);
    console.log('loginForm element:', !!loginForm);
    console.log('profileSection element:', !!profileSection);

    if (token) {
        // User is already logged in
        console.log('User already logged in, showing profile section');
        if (loginForm) loginForm.style.display = 'none';
        if (signupLink) signupLink.style.display = 'none';
        if (profileSection) profileSection.classList.remove('hidden');
    } else {
        // User is not logged in
        console.log('User not logged in, showing login form');
        if (loginForm) loginForm.style.display = 'block';
        if (signupLink) signupLink.style.display = 'block';
        if (profileSection) profileSection.classList.add('hidden');
    }
});

const loginForm = document.getElementById('loginForm');
if (loginForm) {
    console.log('Attaching submit listener to login form');
    loginForm.addEventListener('submit', handleLoginSubmit);
} else {
    console.error('loginForm element not found!');
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    console.log('Form submitted');

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('errorMessage');
    const loadingState = document.getElementById('loadingState');
    const submitBtn = document.getElementById('submitBtn');

    console.log('Attempting login for user:', username);

    // Reset error message
    if (errorMessage) errorMessage.classList.add('hidden');
    if (loadingState) loadingState.classList.remove('hidden');
    if (submitBtn) submitBtn.disabled = true;

    try {
        console.log('Sending login request to /users/login');
        
        // Send login request
        const response = await fetch('/users/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        console.log('Login response status:', response.status);

        const data = await response.json();
        console.log('Login response data:', data);

        if (response.ok && data.access_token) {
            // Store token in localStorage
            console.log('Login successful! Token length:', data.access_token.length);
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('token_type', data.token_type || 'bearer');

            // Verify token was stored
            const storedToken = localStorage.getItem('access_token');
            console.log('Token stored in localStorage:', !!storedToken);

            // Redirect to admin dashboard
            if (loadingState) loadingState.textContent = 'Login successful! Redirecting...';
            console.log('Redirecting to /admin in 500ms');
            setTimeout(() => {
                console.log('Executing redirect to /admin');
                window.location.href = '/admin';
            }, 500);
        } else {
            // Handle error response
            console.log('Login failed with response:', data);
            showError(data.detail || 'Login failed. Please try again.');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('Connection error. Please check your internet and try again.');
    } finally {
        if (loadingState) loadingState.classList.add('hidden');
        if (submitBtn) submitBtn.disabled = false;
    }
}

/**
 * Display error message to user
 * @param {string} message - Error message to display
 */
function showError(message) {
    console.log('Showing error:', message);
    const errorMessage = document.getElementById('errorMessage');
    if (errorMessage) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }
}

/**
 * Redirect to admin dashboard
 */
function goToAdmin() {
    console.log('goToAdmin() called');
    window.location.href = '/admin';
}

/**
 * Handle user logout
 */
function handleLogout() {
    console.log('handleLogout() called');
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
    location.reload();
}
