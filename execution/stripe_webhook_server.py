#!/usr/bin/env python3
"""
stripe_webhook_server.py - Stripe Webhook Receiver

WHAT: Flask server that receives Stripe webhooks and triggers downstream actions
WHY: Processes payment events in real-time -- sends notifications, updates CRM,
     triggers onboarding flows (SOP 19 Day 0 automation)
INPUT: Stripe webhook POST requests (signed with STRIPE_WEBHOOK_SECRET)
OUTPUT: SMS/email notifications, ClickUp task updates, event logs
COST: FREE (runs on EC2)

QUICK USAGE:
  python execution/stripe_webhook_server.py --port 5002
  # Then configure Stripe Dashboard webhook to: https://your-ec2/webhooks/stripe

DEPENDENCIES: flask, stripe, python-dotenv
API_KEYS: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, NOTIFICATION_PHONE (optional)
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
    from execution.twilio_sms import TwilioSMS
    HAS_SMS = True
except ImportError:
    HAS_SMS = False

try:
    from execution.clickup_api import update_task, add_comment, get_task
    HAS_CLICKUP = True
except ImportError:
    HAS_CLICKUP = False

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

    # Handle subscription cancellation
    if event_type == "customer.subscription.deleted":
        notify_subscription_cancelled(customer_id, event)

    # Handle failed payment
    if event_type == "invoice.payment_failed":
        attempt_count = event.get("attempt_count", 0)
        notify_payment_failed(amount_dollars, customer_id, attempt_count)

    # Update ClickUp if task ID in metadata
    task_id = event.get("metadata", {}).get("clickup_task_id")
    if task_id:
        update_clickup_status(task_id, amount_dollars, event_type)


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
            sms_client = TwilioSMS()
            sms_client.send_message(to=admin_phone, message=message)
            logger.info(f"SMS sent to {admin_phone}")
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")


def notify_subscription_cancelled(customer_id: Optional[str], event: dict):
    """Send notification when a subscription is cancelled."""
    admin_phone = os.getenv("NOTIFICATION_PHONE")

    message = f"Client subscription cancelled"
    if customer_id:
        message += f"\nCustomer: {customer_id}"
    message += f"\nAction: Check offboarding workflow"

    logger.info(f"Cancellation notification: {message}")

    if HAS_SMS and admin_phone:
        try:
            sms_client = TwilioSMS()
            sms_client.send_message(to=admin_phone, message=message, force_send=True)
        except Exception as e:
            logger.error(f"Failed to send cancellation SMS: {e}")


def notify_payment_failed(amount: float, customer_id: Optional[str], attempt_count: int):
    """Send notification when a payment fails."""
    admin_phone = os.getenv("NOTIFICATION_PHONE")

    message = f"Payment FAILED: ${amount:.2f}"
    if customer_id:
        message += f"\nCustomer: {customer_id}"
    message += f"\nAttempt: {attempt_count}"
    message += f"\nAction: Check dunning flow"

    logger.info(f"Payment failure notification: {message}")

    if HAS_SMS and admin_phone:
        try:
            sms_client = TwilioSMS()
            sms_client.send_message(to=admin_phone, message=message, force_send=True)
        except Exception as e:
            logger.error(f"Failed to send payment failure SMS: {e}")


def update_clickup_status(task_id: str, amount: float, event_type: str):
    """
    Update ClickUp task when payment is received.

    Args:
        task_id: ClickUp task ID from Stripe metadata
        amount: Payment amount in dollars
        event_type: Type of Stripe event
    """
    if not HAS_CLICKUP:
        logger.warning("ClickUp integration not available - skipping task update")
        return

    try:
        # Update task status to "paid" or "complete"
        update_task(task_id, status="paid")
        logger.info(f"Updated ClickUp task {task_id} status to 'paid'")

        # Add a comment with payment details
        comment = f"💰 Payment received: ${amount:.2f}\nEvent: {event_type}\nTimestamp: {datetime.now().isoformat()}"
        add_comment(task_id, comment)
        logger.info(f"Added payment comment to ClickUp task {task_id}")

    except Exception as e:
        logger.error(f"Failed to update ClickUp task {task_id}: {e}")


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
