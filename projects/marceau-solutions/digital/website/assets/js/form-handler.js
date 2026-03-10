/**
 * Unified Form Handler for Marceau Solutions
 * Handles form submissions to https://api.marceausolutions.com/api/form/submit
 */

const API_ENDPOINT = 'https://api.marceausolutions.com/api/form/submit';

// Handle all forms with data-form-handler attribute
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('[data-form-handler]');

    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });
});

async function handleFormSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const formType = form.getAttribute('data-form-handler');
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;

    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.innerHTML = 'Submitting...';

    try {
        // Collect form data
        const formData = collectFormData(form, formType);

        // Submit to API
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok && result.success) {
            // Show success message
            showSuccess(form);
        } else {
            throw new Error(result.message || 'Submission failed');
        }

    } catch (error) {
        console.error('Form submission error:', error);
        showError(form, error.message);

        // Re-enable button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
    }
}

function collectFormData(form, formType) {
    const formData = new FormData(form);
    const data = {
        formType: formType,
        timestamp: new Date().toISOString(),
    };

    // Convert FormData to object
    for (let [key, value] of formData.entries()) {
        // Handle checkboxes
        if (form.querySelector(`[name="${key}"][type="checkbox"]`)) {
            data[key] = form.querySelector(`[name="${key}"]`).checked;
        } else {
            data[key] = value;
        }
    }

    return data;
}

function showSuccess(form) {
    // Hide form
    form.classList.add('hidden');

    // Show success message
    const successMessage = document.getElementById('successMessage');
    if (successMessage) {
        successMessage.classList.add('show');
    }
}

function showError(form, message) {
    // Create or update error message
    let errorDiv = form.querySelector('.form-error');

    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'form-error';
        errorDiv.style.cssText = 'background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: #ef4444; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;';
        form.insertBefore(errorDiv, form.firstChild);
    }

    errorDiv.innerHTML = `
        <strong>Submission Error</strong><br>
        ${message}<br>
        <span style="font-size: 0.9em; opacity: 0.8;">
            Please try again or contact us directly at
            <a href="mailto:wmarceau@marceausolutions.com" style="color: #fbbf24;">wmarceau@marceausolutions.com</a>
        </span>
    `;

    // Scroll error into view
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Phone number formatting
document.addEventListener('DOMContentLoaded', function() {
    const phoneInputs = document.querySelectorAll('input[type="tel"]');

    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');

            if (value.length > 0) {
                if (value.length <= 3) {
                    value = `(${value}`;
                } else if (value.length <= 6) {
                    value = `(${value.slice(0, 3)}) ${value.slice(3)}`;
                } else {
                    value = `(${value.slice(0, 3)}) ${value.slice(3, 6)}-${value.slice(6, 10)}`;
                }
            }

            e.target.value = value;
        });
    });
});
