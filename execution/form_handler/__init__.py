"""
Multi-Business Form Handler - Form submission system for multiple websites

Handles form submissions from:
- marceausolutions.com
- swfloridacomfort.com
- squarefootshipping.com

Routes each submission to the correct:
1. ClickUp CRM list (per business)
2. Google Sheets (per business)
3. Owner notifications (per business)
4. Customer auto-responses
5. Nurturing sequences

Usage:
    from execution.form_handler import MultiBusinessFormHandler

    handler = MultiBusinessFormHandler()
    result = handler.process_submission(form_data)
    # Automatically routes to correct business based on source

Legacy single-business usage:
    from execution.form_handler import FormHandler

    handler = FormHandler()
    result = handler.process_submission(form_data)
"""

from .handler import FormHandler
from .models import FormSubmission, LeadSource
from .multi_business_handler import MultiBusinessFormHandler
from .business_config import BusinessConfig, get_business_config, get_all_businesses

__all__ = [
    'FormHandler',
    'MultiBusinessFormHandler',
    'FormSubmission',
    'LeadSource',
    'BusinessConfig',
    'get_business_config',
    'get_all_businesses',
]
__version__ = '2.0.0'
