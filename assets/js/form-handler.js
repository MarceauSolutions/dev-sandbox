/**
 * Unified Form Handler - Marceau Solutions
 *
 * This script handles form submissions across all website pages.
 * It submits to our backend API which:
 * 1. Saves to JSON files
 * 2. Creates ClickUp CRM tasks
 * 3. Updates Google Sheets
 * 4. Sends notifications
 * 5. Triggers workflows
 *
 * With fallback to Formspree if our API is unavailable.
 *
 * Usage:
 *   <script src="/assets/js/form-handler.js"></script>
 *   <form data-form-handler="inquiry" ...>
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        // Primary API endpoint (our backend)
        apiEndpoint: window.FORM_API_ENDPOINT || 'https://api.marceausolutions.com/api/form/submit',

        // Fallback to Formspree if API fails
        fallbackEndpoint: 'https://formspree.io/f/xvgoznaw',

        // Email fallback for offline/error scenarios
        fallbackEmail: 'wmarceau@marceausolutions.com',

        // Timeout for API calls (ms)
        timeout: 10000,

        // Debug mode
        debug: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    };

    /**
     * Log debug messages
     */
    function log(...args) {
        if (CONFIG.debug) {
            console.log('[FormHandler]', ...args);
        }
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
            utm_term: params.get('utm_term') || '',
            utm_content: params.get('utm_content') || ''
        };
    }

    /**
     * Collect form data with metadata
     */
    function collectFormData(form) {
        const formData = new FormData(form);
        const data = {};

        // Convert FormData to object
        for (const [key, value] of formData.entries()) {
            // Handle checkboxes
            if (form.elements[key] && form.elements[key].type === 'checkbox') {
                data[key] = form.elements[key].checked;
            } else {
                data[key] = value;
            }
        }

        // Handle checkboxes that aren't checked (they won't be in FormData)
        const checkboxes = form.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => {
            if (!(cb.name in data)) {
                data[cb.name] = false;
            }
        });

        // Add metadata
        data.timestamp = new Date().toISOString();
        data.page_url = window.location.href;
        data.page_title = document.title;
        data.referrer = document.referrer;

        // Add UTM parameters
        Object.assign(data, getUTMParams());

        // Ensure source is set
        if (!data.source) {
            data.source = detectSource();
        }

        return data;
    }

    /**
     * Detect source from page URL
     */
    function detectSource() {
        const path = window.location.pathname.toLowerCase();

        if (path.includes('fitness-influencer')) return 'fitness_influencer_landing';
        if (path.includes('interview-prep')) return 'interview_prep_landing';
        if (path.includes('amazon-seller')) return 'amazon_seller_landing';
        if (path.includes('contact')) return 'contact-page';
        if (path === '/' || path.includes('index')) return 'home-page';

        return 'other';
    }

    /**
     * Submit to primary API
     */
    async function submitToPrimaryAPI(data) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.timeout);

        try {
            const response = await fetch(CONFIG.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(data),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`API returned ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            clearTimeout(timeoutId);
            throw error;
        }
    }

    /**
     * Submit to Formspree fallback
     */
    async function submitToFormspree(data) {
        const response = await fetch(CONFIG.fallbackEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`Formspree returned ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Open email client as last resort
     */
    function openEmailFallback(data) {
        const subject = encodeURIComponent(`Website Form Submission - ${data.source || 'Unknown'}`);

        let body = '';
        for (const [key, value] of Object.entries(data)) {
            if (value && typeof value !== 'object') {
                body += `${key}: ${value}\n`;
            }
        }
        body = encodeURIComponent(body);

        window.location.href = `mailto:${CONFIG.fallbackEmail}?subject=${subject}&body=${body}`;
    }

    /**
     * Show success message
     */
    function showSuccess(form, message) {
        // Hide the form
        form.style.display = 'none';

        // Find or create success message element
        let successEl = form.parentElement.querySelector('.form-success-message');
        if (!successEl) {
            successEl = document.createElement('div');
            successEl.className = 'form-success-message';
            successEl.style.cssText = `
                background: #dcfce7;
                color: #166534;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
            `;
            form.parentElement.appendChild(successEl);
        }

        successEl.innerHTML = `
            <h4 style="margin-bottom: 8px;">🎉 ${message || 'Thank you!'}</h4>
            <p>We've received your submission and will be in touch soon.</p>
        `;
        successEl.style.display = 'block';
    }

    /**
     * Show error message
     */
    function showError(form, message) {
        let errorEl = form.querySelector('.form-error-message');
        if (!errorEl) {
            errorEl = document.createElement('div');
            errorEl.className = 'form-error-message';
            errorEl.style.cssText = `
                background: #fef2f2;
                color: #991b1b;
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 15px;
            `;
            form.insertBefore(errorEl, form.firstChild);
        }

        errorEl.textContent = message;
        errorEl.style.display = 'block';
    }

    /**
     * Reset button state
     */
    function resetButton(button, originalText) {
        button.textContent = originalText;
        button.disabled = false;
    }

    /**
     * Handle form submission
     */
    async function handleSubmit(event) {
        event.preventDefault();

        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        const originalBtnText = submitBtn ? submitBtn.textContent : 'Submit';

        // Update button state
        if (submitBtn) {
            submitBtn.textContent = 'Submitting...';
            submitBtn.disabled = true;
        }

        // Clear previous errors
        const errorEl = form.querySelector('.form-error-message');
        if (errorEl) errorEl.style.display = 'none';

        // Collect form data
        const data = collectFormData(form);
        log('Form data collected:', data);

        try {
            // Try primary API first
            log('Submitting to primary API...');
            const result = await submitToPrimaryAPI(data);
            log('Primary API success:', result);

            showSuccess(form, result.message || 'Request Received!');

            // Track conversion if analytics available
            if (typeof gtag !== 'undefined') {
                gtag('event', 'form_submission', {
                    'event_category': 'engagement',
                    'event_label': data.source,
                    'value': 1
                });
            }

        } catch (primaryError) {
            log('Primary API failed:', primaryError.message);

            try {
                // Try Formspree fallback
                log('Submitting to Formspree fallback...');
                await submitToFormspree(data);
                log('Formspree success');

                showSuccess(form, 'Request Received!');

            } catch (fallbackError) {
                log('Formspree failed:', fallbackError.message);

                // Last resort: open email client
                if (confirm('We\'re having trouble submitting your form. Would you like to send it via email instead?')) {
                    openEmailFallback(data);
                } else {
                    showError(form, 'Unable to submit form. Please try again or contact us directly.');
                    if (submitBtn) resetButton(submitBtn, originalBtnText);
                }
            }
        }
    }

    /**
     * Initialize form handlers
     */
    function init() {
        log('Initializing form handlers...');

        // Find all forms with data-form-handler attribute or common IDs
        const forms = document.querySelectorAll(
            'form[data-form-handler], ' +
            '#inquiryForm, #contactForm, #waitlistForm, #earlyAccessForm'
        );

        forms.forEach(form => {
            // Remove any existing listeners
            form.removeEventListener('submit', handleSubmit);

            // Add our handler
            form.addEventListener('submit', handleSubmit);

            log('Attached handler to form:', form.id || form.className);
        });

        log(`Initialized ${forms.length} form(s)`);
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
        config: CONFIG
    };

})();
