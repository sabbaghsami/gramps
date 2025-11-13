// Password strength indicator
const passwordInput = document.getElementById('password');
const strengthBar = document.getElementById('strengthBar');

if (passwordInput && strengthBar) {
    passwordInput.addEventListener('input', function() {
        const password = this.value;
        let strength = 0;

        // Check length
        if (password.length >= 10) strength++;
        if (password.length >= 15) strength++;

        // Check for numbers
        if (/\d/.test(password)) strength++;

        // Check for special characters
        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++;

        // Check for uppercase and lowercase
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;

        // Update visual indicator
        strengthBar.className = 'password-strength-bar';
        if (strength <= 2) {
            strengthBar.classList.add('strength-weak');
        } else if (strength <= 3) {
            strengthBar.classList.add('strength-medium');
        } else {
            strengthBar.classList.add('strength-strong');
        }
    });
}

// Client-side validation
const signupForm = document.getElementById('signupForm');
if (signupForm) {
    signupForm.addEventListener('submit', function(e) {
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;

        if (password.length < 10) {
            e.preventDefault();
            alert('Password must be at least 10 characters long');
            return;
        }

        if (!/\d/.test(password)) {
            e.preventDefault();
            alert('Password must contain at least one number');
            return;
        }

        if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
            e.preventDefault();
            alert('Password must contain at least one special character');
            return;
        }

        if (password !== confirmPassword) {
            e.preventDefault();
            alert('Passwords do not match');
            return;
        }
    });
}