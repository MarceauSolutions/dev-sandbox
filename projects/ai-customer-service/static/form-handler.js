/**
 * Multi-Business Form Handler
 *
 * Handles form submissions from any website and routes to the correct pipeline.
 *
 * Usage:
 * 1. Include this script in your HTML
 * 2. Add data-form-handler attribute to your form
 * 3. Add data-business="swfloridacomfort" attribute (or let it auto-detect from domain)
 *
 * Example:
 * <form data-form-handler data-business="swfloridacomfort">
 *   <input name="name" placeholder="Your Name" required>
 *   <input name="email" type="email" placeholder="Email" required>
 *   <input name="phone" placeholder="Phone">
 *   <select name="interest">
 *     <option value="AC Repair">AC Repair</option>
 *     <option value="AC Installation">New Installation</option>
 *   </select>
 *   <textarea name="message" placeholder="How can we help?"></textarea>
 *   <button type="submit">Get Free Quote</button>
 * </form>
 */

(function() {
    'use strict';

    // API Configuration
    const API_BASE_URL = 'https://api.marceausolutions.com';
    const FORM_ENDPOINT = '/api/form/submit';

    // Business detection based on domain
    const DOMAIN_BUSINESS_MAP = {
        'swfloridacomfort.com': 'swfloridacomfort',
        'www.swfloridacomfort.com': 'swfloridacomfort',
        'squarefootshipping.com': 'squarefootshipping',
        'www.squarefootshipping.com': 'squarefootshipping',
        'marceausolutions.com': 'marceausolutions',
        'www.marceausolutions.com': 'marceausolutions',
        'localhost': 'marceausolutions',  // Default for local dev
    };

    /**
     * Detect business from current domain or form attribute
     */
    function detectBusiness(form) {
        // First check form attribute
        if (form.dataset.business) {
            return form.dataset.business;
        }

        // Then check domain
        const hostname = window.location.hostname;
        return DOMAIN_BUSINESS_MAP[hostname] || 'marceausolutions';
    }

    /**
     * Get UTM parameters from URL
     */
    function getUTMParams() {
        const params = new URLSearchParams(window.location.search);
        return {
            utm_source: params.get('utm_source') || '',
            utm_medium: params.get('utm_medium') || '',
            utm_campaign: params.get('utm_campaign') || '',
        };
    }

    /**
     * Format phone number
     */
    function formatPhone(phone) {
        if (!phone) return '';
        // Remove non-digits
        const digits = phone.replace(/\D/g, '');
        // Add +1 if 10 digits (US number)
        if (digits.length === 10) {
            return '+1' + digits;
        }
        // Already has country code
        if (digits.length === 11 && digits.startsWith('1')) {
            return '+' + digits;
        }
        return phone;
    }

    /**
     * Show success message
     */
    function showSuccess(form, message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'form-success';
        successDiv.innerHTML = `
            <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 8px; margin-top: 20px;">
                <h3 style="color: #155724; margin: 0 0 10px 0;">✓ ${message || 'Thank you!'}</h3>
                <p style="color: #155724; margin: 0;">We'll be in touch shortly.</p>
            </div>
        `;
        form.style.display = 'none';
        form.parentNode.insertBefore(successDiv, form.nextSibling);
    }

    /**
     * Show error message
     */
    function showError(form, message) {
        // Remove any existing error
        const existingError = form.querySelector('.form-error');
        if (existingError) existingError.remove();

        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error';
        errorDiv.innerHTML = `
            <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <p style="color: #721c24; margin: 0;">${message}</p>
            </div>
        `;
        form.insertBefore(errorDiv, form.firstChild);
    }

    /**
     * Handle form submission
     */
    async function handleSubmit(event) {
        event.preventDefault();

        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        const originalText = submitBtn.textContent || submitBtn.value;

        // Disable button and show loading
        submitBtn.disabled = true;
        if (submitBtn.tagName === 'BUTTON') {
            submitBtn.textContent = 'Sending...';
        } else {
            submitBtn.value = 'Sending...';
        }

        // Gather form data
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // Add business detection
        data.business_id = detectBusiness(form);
        data.source = form.dataset.source || window.location.pathname;

        // Add UTM params
        const utmParams = getUTMParams();
        Object.assign(data, utmParams);

        // Format phone
        if (data.phone) {
            data.phone = formatPhone(data.phone);
        }

        // Handle checkboxes for opt-ins
        data.email_opt_in = form.querySelector('[name="email_opt_in"]')?.checked !== false;
        data.sms_opt_in = form.querySelector('[name="sms_opt_in"]')?.checked || false;

        try {
            const response = await fetch(API_BASE_URL + FORM_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            const result = await response.json();

            if (result.status === 'success' || result.status === 'partial') {
                showSuccess(form, 'Request received!');

                // Track conversion if analytics present
                if (window.gtag) {
                    gtag('event', 'form_submission', {
                        'form_id': form.id || 'contact-form',
                        'business_id': data.business_id,
                    });
                }
            } else {
                throw new Error(result.message || 'Submission failed');
            }
        } catch (error) {
            console.error('Form submission error:', error);
            showError(form, 'Sorry, there was an error. Please call us directly or try again.');

            // Re-enable button
            submitBtn.disabled = false;
            if (submitBtn.tagName === 'BUTTON') {
                submitBtn.textContent = originalText;
            } else {
                submitBtn.value = originalText;
            }
        }
    }

    /**
     * Initialize form handlers
     */
    function init() {
        // Find all forms with data-form-handler attribute
        const forms = document.querySelectorAll('form[data-form-handler]');

        forms.forEach(form => {
            form.addEventListener('submit', handleSubmit);
        });

        console.log(`Form handler initialized for ${forms.length} form(s)`);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose for manual initialization
    window.FormHandler = {
        init: init,
        submit: handleSubmit,
    };
})();
