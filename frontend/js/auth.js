/**
 * Beyond Horizons — Authentication (Login & Registration) Client Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  // If user is already authenticated, redirect them to dashboard
  checkExistingSession();

  // Password visibility toggles
  document.querySelectorAll('[data-toggle]').forEach(button => {
    button.addEventListener('click', () => {
      const targetId = button.getAttribute('data-toggle');
      const input = document.getElementById(targetId);
      if (!input) return;

      const isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';
      button.textContent = isPassword ? 'Hide' : 'Show';
      button.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
    });
  });

  // Registration Form
  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', handleRegisterSubmit);
  }

  // Login Form
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', handleLoginSubmit);
  }
});

async function checkExistingSession() {
  try {
    const res = await fetch('/api/auth/me', { credentials: 'include' });
    if (res.ok) {
      const data = await res.json();
      if (data && data.authenticated && data.user) {
        window.location.replace('/dashboard');
      }
    }
  } catch (_) {
    // Ignore error on initial check
  }
}

function showAlert(message, type = 'error') {
  const alertBox = document.getElementById('auth-alert');
  if (!alertBox) return;

  alertBox.textContent = message;
  alertBox.className = `form-message-box ${type}`;
  alertBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function clearAlert() {
  const alertBox = document.getElementById('auth-alert');
  if (!alertBox) return;
  alertBox.textContent = '';
  alertBox.className = 'form-message-box';
}

function setBtnLoading(button, isLoading, text) {
  if (!button) return;
  button.disabled = isLoading;
  const firstSpan = button.querySelector('span:first-child');
  if (firstSpan) {
    firstSpan.textContent = isLoading ? 'Please wait…' : text;
  } else {
    button.textContent = isLoading ? 'Please wait…' : text;
  }
}

async function handleRegisterSubmit(event) {
  event.preventDefault();
  clearAlert();

  const nameInput = document.getElementById('name');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const confirmInput = document.getElementById('confirm-password');
  const termsCheckbox = document.getElementById('terms');
  const submitBtn = document.getElementById('submit-btn');

  const name = nameInput.value.trim();
  const email = emailInput.value.trim().toLowerCase();
  const password = passwordInput.value;
  const confirmPassword = confirmInput.value;

  // Validation
  if (!name || name.length < 2) {
    showAlert('Please enter your full name (minimum 2 characters).');
    nameInput.focus();
    return;
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!email || !emailRegex.test(email)) {
    showAlert('Please enter a valid email address.');
    emailInput.focus();
    return;
  }

  if (!password || password.length < 8) {
    showAlert('Password must be at least 8 characters long.');
    passwordInput.focus();
    return;
  }

  if (password !== confirmPassword) {
    showAlert('Passwords do not match. Please re-enter your password.');
    confirmInput.focus();
    return;
  }

  if (termsCheckbox && !termsCheckbox.checked) {
    showAlert('Please agree to the confirmation checkbox to continue.');
    termsCheckbox.focus();
    return;
  }

  setBtnLoading(submitBtn, true, 'Create account');

  try {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ name, email, password, confirmPassword })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Registration failed. Please try again.');
    }

    showAlert(data.message || 'Account created successfully! Redirecting...', 'success');
    setTimeout(() => {
      window.location.href = '/dashboard';
    }, 700);

  } catch (error) {
    showAlert(error.message, 'error');
    setBtnLoading(submitBtn, false, 'Create account');
  }
}

async function handleLoginSubmit(event) {
  event.preventDefault();
  clearAlert();

  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const submitBtn = document.getElementById('submit-btn');

  const email = emailInput.value.trim().toLowerCase();
  const password = passwordInput.value;

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!email || !emailRegex.test(email)) {
    showAlert('Please enter a valid email address.');
    emailInput.focus();
    return;
  }

  if (!password) {
    showAlert('Please enter your password.');
    passwordInput.focus();
    return;
  }

  setBtnLoading(submitBtn, true, 'Sign in');

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Login failed. Please check your credentials.');
    }

    showAlert('Signed in successfully! Redirecting to dashboard...', 'success');
    setTimeout(() => {
      window.location.href = '/dashboard';
    }, 500);

  } catch (error) {
    showAlert(error.message, 'error');
    setBtnLoading(submitBtn, false, 'Sign in');
  }
}
