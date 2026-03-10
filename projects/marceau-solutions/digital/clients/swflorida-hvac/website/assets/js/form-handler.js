/**
 * Universal Form Handler for Marceau Solutions Multi-Business System
 *
 * Handles form submissions with:
 * - JSON data collection
 * - API submission to form handler
 * - Success/error UI feedback
 * - Loading states
 *
 * Works for: marceausolutions.com, swfloridacomfort.com, squarefootshipping.com
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        apiEndpoint: 'https://api.marceausolutions.com/forms/submit',
        timeout: 10000, // 10 seconds
    };

    /**
     * Initialize form handler on page load
     */
    function init() {
        const forms = document.querySelectorAll('form[data-form-handler]');
        forms.forEach(form => {
            form.addEventListener('submit', handleFormSubmit);
        });
    }

    /**
     * Handle form submission
     */
    async function handleFormSubmit(event) {
        event.preventDefault();

        const form = event.target;
        const formType = form.dataset.formHandler; // 'contact', 'inquiry', 'quote', etc.
        const submitButton = form.querySelector('button[type="submit"]');
        const successMessage = document.getElementById('successMessage');

        // Collect form data
        const formData = new FormData(form);
        const data = {
            form_type: formType,
            source: formData.get('source') || window.location.hostname,
            timestamp: new Date().toISOString(),
            page_url: window.location.href,
            referrer: document.referrer
        };

        // Add all form fields to data object
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }

        // Show loading state
        const originalButtonText = submitButton.innerHTML;
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="animate-pulse">Sending...</span>';

        try {
            // Submit to API
            const response = await fetch(CONFIG.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
                signal: AbortSignal.timeout(CONFIG.apiEndpoint)
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            const result = await response.json();

            // Show success message
            form.classList.add('hidden');
            if (successMessage) {
                successMessage.classList.add('show');
            }

            // Optional: Send analytics event
            if (typeof gtag !== 'undefined') {
                gtag('event', 'form_submission', {
                    'event_category': 'engagement',
                    'event_label': formType,
                    'value': 1
                });
            }

            // Reset form after delay
            setTimeout(() => {
                form.reset();
            }, 500);

        } catch (error) {
            console.error('Form submission error:', error);

            // Show error message
            alert('Sorry, there was a problem submitting your form. Please try calling us directly or emailing us instead.');

            // Restore button
            submitButton.disabled = false;
            submitButton.innerHTML = originalButtonText;
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
