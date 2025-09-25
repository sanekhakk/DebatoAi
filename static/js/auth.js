// static/js/auth.js

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
});

async function handleLogin(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    const errorMessageDiv = document.getElementById('error-message');

    try {
        const response = await fetch('/api/auth/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify(data),
        });

        const result = await response.json();

        if (response.ok) {
            window.location.href = '/'; // Redirect to homepage on successful login
        } else {
            const errorText = Object.values(result).join('\n');
            errorMessageDiv.textContent = errorText;
            errorMessageDiv.style.display = 'block';
        }
    } catch (error) {
        errorMessageDiv.textContent = 'An unexpected error occurred. Please try again.';
        errorMessageDiv.style.display = 'block';
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    const errorMessageDiv = document.getElementById('error-message');
    
    try {
        const response = await fetch('/api/auth/register/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify(data),
        });

        const result = await response.json();

        if (response.ok) {
            window.location.href = '/'; // Redirect to homepage on successful registration
        } else {
            // Format errors from Django serializer for display
            let errorText = '';
            for (const key in result) {
                errorText += `${key}: ${result[key].join(', ')}\n`;
            }
            errorMessageDiv.textContent = errorText;
            errorMessageDiv.style.display = 'block';
        }
    } catch (error) {
        errorMessageDiv.textContent = 'An unexpected error occurred. Please try again.';
        errorMessageDiv.style.display = 'block';
    }
}

function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}