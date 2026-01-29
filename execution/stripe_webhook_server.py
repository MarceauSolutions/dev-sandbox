#!/usr/bin/env python3
"""
Stripe Webhook Server

Simple Flask server to receive Stripe webhooks on EC2.
Processes payment events and updates ClickUp/sends notifications.

DEPLOYMENT:
1. Add to .env:
   STRIPE_WEBHOOK_SECRET=whsec_xxx

2. Run on EC2:
   python execution/stripe_webhook_server.py --port 5002

3. Configure Stripe webhook:
   URL: http://your-ec2-ip:5002/webhooks/stripe
   Events: checkout.session.completed, invoice.paid, payment_intent.succeeded

4. (Optional) Put behind nginx with SSL for production

Usage:
    python -m execution.stripe_webhook_server --port 5002
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Import our modules
from execution.stripe_payments import StripePayments

# Optional integrations
try:
    from execution.twilio_sms import send_sms
    HAS_SMS = True
except ImportError:
    HAS_SMS = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Initialize Stripe
stripe_payments = None


def get_stripe():
    """Lazy load Stripe client."""
    global stripe_payments
    if stripe_payments is None:
        stripe_payments = StripePayments()
    return stripe_payments


# =============================================================================
# WEBHOOK ENDPOINTS
# =============================================================================

@app.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Handle incoming Stripe webhooks."""
    payload = request.data
    signature = request.headers.get('Stripe-Signature')

    if not signature:
        return jsonify({"error": "No signature"}), 400

    try:
        sp = get_stripe()
        result = sp.handle_webhook(payload, signature)

        # Process the result
        if result.get("processed"):
            handle_payment_event(result)

        return jsonify({"status": "success", "result": result}), 200

    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        return jsonify({"error": "Invalid payload"}), 400

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500


def handle_payment_event(event: dict):
    """
    Process payment events - send notifications, update CRM, etc.

    Args:
        event: Processed webhook event data
    """
    event_type = event.get("event_type", "unknown")
    amount = event.get("amount", 0)
    customer_id = event.get("customer_id")

    logger.info(f"Processing payment event: {event_type}")

    # Format amount
    amount_dollars = amount / 100 if amount > 100 else amount

    # Send SMS notification for significant payments
    if event_type in ["checkout.session.completed", "invoice.paid", "payment_intent.succeeded"]:
        notify_payment_received(amount_dollars, event_type, customer_id)

    # Update ClickUp if task ID in metadata
    # task_id = event.get("metadata", {}).get("clickup_task_id")
    # if task_id:
    #     update_clickup_status(task_id, "Payment Received")


def notify_payment_received(amount: float, event_type: str, customer_id: Optional[str] = None):
    """Send notification when payment is received."""
    admin_phone = os.getenv("NOTIFICATION_PHONE")

    message = f"💰 Payment received: ${amount:.2f}"
    if customer_id:
        message += f"\nCustomer: {customer_id}"
    message += f"\nType: {event_type}"

    logger.info(f"Payment notification: {message}")

    if HAS_SMS and admin_phone:
        try:
            send_sms(admin_phone, message)
            logger.info(f"SMS sent to {admin_phone}")
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "stripe-webhook-server",
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with info."""
    return jsonify({
        "service": "Stripe Webhook Server",
        "endpoints": {
            "/webhooks/stripe": "POST - Stripe webhook endpoint",
            "/health": "GET - Health check"
        },
        "status": "running"
    }), 200


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Stripe Webhook Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5002, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Verify Stripe is configured
    try:
        get_stripe()
        logger.info("Stripe configured successfully")
    except Exception as e:
        logger.error(f"Stripe configuration error: {e}")
        logger.error("Add STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET to .env")
        return 1

    logger.info(f"Starting Stripe webhook server on {args.host}:{args.port}")
    logger.info(f"Webhook URL: http://{args.host}:{args.port}/webhooks/stripe")

    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )


if __name__ == "__main__":
    main()
