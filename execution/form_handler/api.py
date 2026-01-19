#!/usr/bin/env python3
"""
Multi-Business Form Submission API

Handles form submissions from multiple websites:
- marceausolutions.com
- swfloridacomfort.com
- squarefootshipping.com

Routes each submission to the correct:
- ClickUp CRM list
- Google Sheets
- Owner notifications
- Customer auto-responses
- Nurturing sequences

Usage (local):
    python -m execution.form_handler.api

Usage (test):
    curl -X POST http://localhost:5002/api/form/submit \\
        -H "Content-Type: application/json" \\
        -d '{"email": "test@example.com", "name": "Test User", "source": "swfloridacomfort", "interest": "AC Repair"}'
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from execution.form_handler.multi_business_handler import MultiBusinessFormHandler
from execution.form_handler.business_config import get_business_config, get_all_businesses

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from all websites

handler = MultiBusinessFormHandler()


@app.route('/api/form/submit', methods=['POST', 'OPTIONS'])
def submit_form():
    """
    Handle form submission from any website.

    Accepts JSON or form-encoded data.
    Automatically routes to correct business based on source/referrer.
    Returns submission result with IDs.
    """
    if request.method == 'OPTIONS':
        # CORS preflight
        return '', 204

    try:
        # Get data from JSON or form
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        # Add metadata
        data['ip_address'] = request.remote_addr
        data['user_agent'] = request.headers.get('User-Agent', '')
        data['referrer'] = request.headers.get('Referer', '')
        data['origin'] = request.headers.get('Origin', '')

        # Extract UTM parameters from referer or data
        data['utm_source'] = data.get('utm_source', request.args.get('utm_source', ''))
        data['utm_medium'] = data.get('utm_medium', request.args.get('utm_medium', ''))
        data['utm_campaign'] = data.get('utm_campaign', request.args.get('utm_campaign', ''))

        # Process the submission (multi-business routing happens inside)
        result = handler.process_submission(data)

        if result['success']:
            return jsonify({
                "status": "success",
                "message": "Form submitted successfully",
                "submission_id": result['submission_id'],
                "business_id": result.get('business_id', 'unknown'),
                "task_url": f"https://app.clickup.com/t/{result['clickup_task_id']}" if result.get('clickup_task_id') else None,
                "auto_responses": result.get('auto_responses_sent', [])
            }), 200
        else:
            return jsonify({
                "status": "partial",
                "message": "Form received with some integration errors",
                "submission_id": result['submission_id'],
                "business_id": result.get('business_id', 'unknown'),
                "errors": result.get('errors', [])
            }), 200  # Still 200 since we saved the data

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/form/health', methods=['GET'])
def health_check():
    """Health check endpoint with business info."""
    businesses = get_all_businesses()
    return jsonify({
        "status": "healthy",
        "service": "multi-business-form-handler",
        "businesses_configured": len(businesses),
        "business_ids": list(businesses.keys()),
        "integrations": {
            "clickup": bool(handler.clickup_token),
            "google_sheets": bool(handler.sheets_spreadsheet_id),
            "email": bool(handler.smtp_username),
            "sms": bool(handler.twilio_sid)
        }
    })


@app.route('/api/form/businesses', methods=['GET'])
def list_businesses():
    """List all configured businesses."""
    businesses = get_all_businesses()
    return jsonify({
        "count": len(businesses),
        "businesses": [
            {
                "id": config.business_id,
                "name": config.business_name,
                "domain": config.domain,
                "clickup_configured": bool(config.clickup_list_id),
                "sheets_configured": bool(config.google_sheet_id),
                "auto_response_enabled": config.auto_response_enabled,
            }
            for config in businesses.values()
        ]
    })


@app.route('/api/form/submissions', methods=['GET'])
def list_submissions():
    """
    List recent submissions.

    Query params:
        - date: YYYY-MM-DD (optional, defaults to all)
        - limit: Number of results (optional, defaults to 50)
    """
    # Simple auth check (in production, use proper auth)
    auth_token = request.headers.get('Authorization', '')
    expected_token = os.getenv('FORM_API_TOKEN', 'dev-token')
    if auth_token != f"Bearer {expected_token}":
        return jsonify({"error": "Unauthorized"}), 401

    date = request.args.get('date')
    limit = int(request.args.get('limit', 50))

    if date:
        submissions = handler.get_submissions_by_date(date)
    else:
        submissions = handler.get_all_submissions()

    # Sort by timestamp descending and limit
    submissions.sort(key=lambda s: s.timestamp, reverse=True)
    submissions = submissions[:limit]

    return jsonify({
        "count": len(submissions),
        "submissions": [s.to_dict() for s in submissions]
    })


def main():
    """Run the Flask development server."""
    port = int(os.getenv('FORM_API_PORT', 5002))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'

    print(f"Starting Form Handler API on port {port}")
    print(f"Health check: http://localhost:{port}/api/form/health")
    print(f"Submit endpoint: http://localhost:{port}/api/form/submit")

    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()
