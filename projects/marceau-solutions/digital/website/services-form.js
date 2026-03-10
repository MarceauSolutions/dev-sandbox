// Services Form Handler - Marceau Solutions
// Handles lead capture, opt-ins, Google Sheets integration, and Calendly redirect

const CALENDLY_URL = 'https://calendly.com/wmarceau/30min';
const BACKEND_API_URL = 'https://web-production-44ade.up.railway.app';

// Form validation and submission
document.getElementById('inquiryForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    e.stopPropagation();

    const form = this;
    const submitBtn = document.getElementById('submitBtn');

    // Bootstrap validation
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
    }

    // Disable submit button to prevent double submission
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';

    // Collect form data
    const formData = {
        firstName: document.getElementById('firstName').value.trim(),
        lastName: document.getElementById('lastName').value.trim(),
        businessName: document.getElementById('businessName').value.trim(),
        email: document.getElementById('email').value.trim(),
        phone: document.getElementById('phone').value.trim(),
        projectDescription: document.getElementById('projectDescription').value.trim(),
        smsOptIn: document.getElementById('smsOptIn').checked,
        emailOptIn: document.getElementById('emailOptIn').checked,
        termsAgreement: document.getElementById('termsAgreement').checked,
        timestamp: new Date().toISOString(),
        source: 'services-page'
    };

    try {
        // Submit to Google Sheets via backend webhook
        await submitToGoogleSheets(formData);

        // If SMS opt-in, trigger SMS webhook
        if (formData.smsOptIn) {
            await handleSMSOptIn(formData);
        }

        // If email opt-in, trigger email webhook
        if (formData.emailOptIn) {
            await handleEmailOptIn(formData);
        }

        // Show success message
        showSuccessMessage();

        // Redirect to Calendly after 2 seconds
        setTimeout(() => {
            window.location.href = CALENDLY_URL;
        }, 2000);

    } catch (error) {
        console.error('Form submission error:', error);
        showErrorMessage(error.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Submit & Book Your Call';
    }
});

// Submit form data to Google Sheets
async function submitToGoogleSheets(formData) {
    try {
        const response = await fetch(`${BACKEND_API_URL}/api/leads/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            // If backend endpoint doesn't exist yet, use Google Apps Script Web App
            // Fallback to direct Google Sheets submission
            return await submitToGoogleSheetsDirectly(formData);
        }

        const data = await response.json();
        console.log('Form submitted to Google Sheets:', data);
        return data;
    } catch (error) {
        console.error('Google Sheets submission error:', error);
        // Continue anyway - we'll still redirect to Calendly
        return { success: false, error: error.message };
    }
}

// Direct Google Sheets submission (fallback)
async function submitToGoogleSheetsDirectly(formData) {
    // This will be replaced with Google Apps Script Web App URL
    // For now, we'll store in localStorage and log to console
    console.log('Storing form data locally (Google Sheets webhook pending):', formData);

    // Store in localStorage for now
    const leads = JSON.parse(localStorage.getItem('leads') || '[]');
    leads.push(formData);
    localStorage.setItem('leads', JSON.stringify(leads));

    return { success: true, method: 'localStorage' };
}

// Handle SMS opt-in
async function handleSMSOptIn(formData) {
    try {
        const response = await fetch(`${BACKEND_API_URL}/api/sms/optin`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                phone: formData.phone,
                firstName: formData.firstName,
                lastName: formData.lastName,
                timestamp: formData.timestamp
            })
        });

        if (response.ok) {
            console.log('SMS opt-in successful');
        } else {
            console.warn('SMS opt-in failed, but continuing');
        }
    } catch (error) {
        console.error('SMS opt-in error:', error);
        // Don't block the main flow
    }
}

// Handle email opt-in
async function handleEmailOptIn(formData) {
    try {
        const response = await fetch(`${BACKEND_API_URL}/api/email/optin`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: formData.email,
                firstName: formData.firstName,
                lastName: formData.lastName,
                businessName: formData.businessName,
                timestamp: formData.timestamp
            })
        });

        if (response.ok) {
            console.log('Email opt-in successful');
        } else {
            console.warn('Email opt-in failed, but continuing');
        }
    } catch (error) {
        console.error('Email opt-in error:', error);
        // Don't block the main flow
    }
}

// Show success message
function showSuccessMessage() {
    const form = document.getElementById('inquiryForm');
    const submitBtn = document.getElementById('submitBtn');

    submitBtn.innerHTML = '✓ Success! Redirecting to Calendly...';
    submitBtn.classList.remove('btn-gold');
    submitBtn.classList.add('btn-success');

    // Show success alert
    const successAlert = document.createElement('div');
    successAlert.className = 'alert alert-success mt-3';
    successAlert.innerHTML = '<strong>✓ Thank you!</strong> Your information has been submitted. Redirecting you to schedule your call...';
    form.insertAdjacentElement('beforebegin', successAlert);
}

// Show error message
function showErrorMessage(message) {
    const form = document.getElementById('inquiryForm');

    const errorAlert = document.createElement('div');
    errorAlert.className = 'alert alert-danger mt-3';
    errorAlert.innerHTML = `<strong>Error:</strong> ${message}. Please try again or contact us directly at <a href="mailto:support@marceausolutions.com">support@marceausolutions.com</a>`;
    form.insertAdjacentElement('beforebegin', errorAlert);

    // Auto-remove after 5 seconds
    setTimeout(() => errorAlert.remove(), 5000);
}

// Phone number formatting
document.getElementById('phone').addEventListener('input', function(e) {
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

// Smooth scroll to form when clicking CTA buttons
document.querySelectorAll('a[href="#inquiry-form"]').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        document.getElementById('inquiry-form').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    });
});
