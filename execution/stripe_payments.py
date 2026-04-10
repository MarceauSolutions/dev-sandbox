#!/usr/bin/env python3
"""
stripe_payments.py - Stripe Payment Processing

WHAT: Customer creation, payment links, invoices, subscriptions, and webhook handling
WHY: Automates revenue collection for coaching ($197/mo) and future services
INPUT: Customer email/name, service key or amount, webhook payloads
OUTPUT: Payment links, invoices, revenue reports, webhook processing results
COST: 2.9% + $0.30 per transaction (Stripe fees)

QUICK USAGE:
  python execution/stripe_payments.py create-customer --email "client@example.com" --name "John"
  python execution/stripe_payments.py create-link --service coaching_monthly
  python execution/stripe_payments.py report --days 30
  python execution/stripe_payments.py services

DEPENDENCIES: stripe, python-dotenv
API_KEYS: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path

try:
    import stripe
except ImportError:
    print("Install stripe: pip install stripe")
    stripe = None

from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class StripePayments:
    """Stripe payment processing for automated revenue collection."""

    def __init__(self):
        """Initialize Stripe with API key from environment."""
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        if not self.api_key:
            raise ValueError("STRIPE_SECRET_KEY not found in .env")

        if stripe:
            stripe.api_key = self.api_key

        # Service catalog for standardized offerings
        self.services = self._load_service_catalog()

        # Data storage path
        self.data_dir = Path(__file__).parent.parent / "data" / "stripe"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _load_service_catalog(self) -> Dict[str, Any]:
        """Load service catalog from JSON file."""
        catalog_path = Path(__file__).parent.parent / "config" / "service_catalog.json"

        if catalog_path.exists():
            with open(catalog_path, 'r') as f:
                return json.load(f)

        # Default catalog -- fitness coaching primary, legacy services kept for flexibility
        return {
            "coaching_monthly": {
                "name": "1:1 Coaching - Monthly",
                "price": 197,
                "currency": "usd",
                "description": "Monthly 1:1 fitness coaching with peptide-informed protocols",
                "deliverables": [
                    "Custom training program (PDF)",
                    "Nutrition protocol with macro targets",
                    "Weekly check-ins via SMS",
                    "Monthly progress review (video call)",
                    "Peptide education resources"
                ],
                "sla_days": 2,
                "recurring": True
            },
            "strategy_call": {
                "name": "Free Strategy Call",
                "price": 0,
                "currency": "usd",
                "description": "30-minute no-pitch strategy call",
                "deliverables": ["Goal mapping", "Training history review", "Recommendation"],
                "sla_days": 0
            },
            "website_setup": {
                "name": "Business Website Setup",
                "price": 1500,
                "currency": "usd",
                "description": "5-page professional website with form integration",
                "deliverables": ["Domain setup", "5-page responsive site", "Contact form", "Basic SEO"],
                "sla_days": 7
            },
            "lead_gen_setup": {
                "name": "Lead Generation System",
                "price": 2500,
                "currency": "usd",
                "description": "Complete lead generation and nurturing system",
                "deliverables": ["Apollo integration", "SMS campaigns", "CRM setup", "Follow-up sequences"],
                "sla_days": 14
            },
            "automation_consulting": {
                "name": "Automation Consulting (Hourly)",
                "price": 150,
                "currency": "usd",
                "description": "Expert automation consulting and implementation",
                "deliverables": ["1 hour of consulting", "Implementation guidance", "Documentation"],
                "sla_days": 1
            },
            "custom_mcp": {
                "name": "Custom MCP Development",
                "price": 3000,
                "currency": "usd",
                "description": "Custom Model Context Protocol server development",
                "deliverables": ["Requirements analysis", "MCP development", "Testing", "Documentation", "PyPI publishing"],
                "sla_days": 21
            }
        }

    # =========================================================================
    # CUSTOMER MANAGEMENT
    # =========================================================================

    def create_customer(
        self,
        email: str,
        name: str,
        phone: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a Stripe customer.

        Args:
            email: Customer email
            name: Customer/company name
            phone: Optional phone number
            metadata: Optional metadata (e.g., clickup_task_id, lead_source)

        Returns:
            Stripe customer ID (cus_xxx)
        """
        if not stripe:
            raise ImportError("stripe package not installed")

        customer_data = {
            "email": email,
            "name": name,
            "metadata": metadata or {}
        }

        if phone:
            customer_data["phone"] = phone

        # Add source tracking
        customer_data["metadata"]["created_via"] = "marceau_automation"
        customer_data["metadata"]["created_at"] = datetime.now().isoformat()

        customer = stripe.Customer.create(**customer_data)

        # Log creation
        self._log_event("customer_created", {
            "customer_id": customer.id,
            "email": email,
            "name": name
        })

        return customer.id

    def get_or_create_customer(self, email: str, name: str, **kwargs) -> str:
        """
        Get existing customer by email or create new one.

        Args:
            email: Customer email
            name: Customer/company name
            **kwargs: Additional args for create_customer

        Returns:
            Stripe customer ID
        """
        if not stripe:
            raise ImportError("stripe package not installed")

        # Search for existing customer
        customers = stripe.Customer.list(email=email, limit=1)

        if customers.data:
            return customers.data[0].id

        return self.create_customer(email, name, **kwargs)

    # =========================================================================
    # PAYMENT LINKS
    # =========================================================================

    def create_payment_link(
        self,
        amount: int,
        description: str,
        customer_id: Optional[str] = None,
        service_key: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a Stripe payment link for one-time payment.

        Args:
            amount: Amount in cents (e.g., 1500 = $15.00) or dollars if > 100
            description: Payment description
            customer_id: Optional Stripe customer ID to associate
            service_key: Optional service catalog key
            metadata: Optional metadata

        Returns:
            Payment link URL
        """
        if not stripe:
            raise ImportError("stripe package not installed")

        # Auto-convert if amount looks like dollars
        if amount >= 100 and amount % 100 == 0 and amount < 100000:
            amount_cents = amount * 100  # Convert dollars to cents
        else:
            amount_cents = amount

        # Use service catalog if provided
        if service_key and service_key in self.services:
            service = self.services[service_key]
            description = service["name"]
            amount_cents = service["price"] * 100

        # Create a price for this payment
        price = stripe.Price.create(
            unit_amount=amount_cents,
            currency="usd",
            product_data={
                "name": description
            }
        )

        # Create payment link
        link_data = {
            "line_items": [{"price": price.id, "quantity": 1}],
            "metadata": metadata or {}
        }

        link_data["metadata"]["created_via"] = "marceau_automation"

        if service_key:
            link_data["metadata"]["service_key"] = service_key

        payment_link = stripe.PaymentLink.create(**link_data)

        # Log creation
        self._log_event("payment_link_created", {
            "link_id": payment_link.id,
            "url": payment_link.url,
            "amount_cents": amount_cents,
            "description": description,
            "customer_id": customer_id
        })

        return payment_link.url

    def create_checkout_session(
        self,
        amount: int,
        description: str,
        customer_id: str,
        success_url: str = "https://marceausolutions.com/thank-you",
        cancel_url: str = "https://marceausolutions.com/",
        metadata: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Create a Stripe Checkout session (more control than payment link).

        Args:
            amount: Amount in cents
            description: Payment description
            customer_id: Stripe customer ID
            success_url: Redirect URL after successful payment
            cancel_url: Redirect URL if payment cancelled
            metadata: Optional metadata

        Returns:
            Dict with session_id and url
        """
        if not stripe:
            raise ImportError("stripe package not installed")

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": description},
                    "unit_amount": amount
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata or {}
        )

        return {
            "session_id": session.id,
            "url": session.url
        }

    # =========================================================================
    # INVOICING
    # =========================================================================

    def create_invoice(
        self,
        customer_id: str,
        items: List[Dict[str, Any]],
        due_days: int = 7,
        auto_send: bool = True,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create and optionally send an invoice.

        Args:
            customer_id: Stripe customer ID
            items: List of items, each with 'description', 'amount' (cents), 'quantity'
            due_days: Days until due
            auto_send: Whether to automatically email the invoice
            metadata: Optional metadata

        Returns:
            Invoice details including ID and hosted URL
        """
        if not stripe:
            raise ImportError("stripe package not installed")

        # Add invoice items
        for item in items:
            stripe.InvoiceItem.create(
                customer=customer_id,
                amount=item.get("amount", 0),
                currency="usd",
                description=item.get("description", "Service"),
                quantity=item.get("quantity", 1)
            )

        # Create invoice
        invoice = stripe.Invoice.create(
            customer=customer_id,
            collection_method="send_invoice",
            days_until_due=due_days,
            metadata=metadata or {}
        )

        # Finalize invoice
        invoice = stripe.Invoice.finalize_invoice(invoice.id)

        # Send invoice email
        if auto_send:
            stripe.Invoice.send_invoice(invoice.id)

        # Log
        self._log_event("invoice_created", {
            "invoice_id": invoice.id,
            "customer_id": customer_id,
            "total": invoice.total,
            "hosted_invoice_url": invoice.hosted_invoice_url
        })

        return {
            "invoice_id": invoice.id,
            "status": invoice.status,
            "total": invoice.total,
            "hosted_invoice_url": invoice.hosted_invoice_url,
            "pdf": invoice.invoice_pdf,
            "due_date": invoice.due_date
        }

    def create_invoice_from_service(
        self,
        customer_id: str,
        service_key: str,
        quantity: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create invoice from service catalog.

        Args:
            customer_id: Stripe customer ID
            service_key: Key from service catalog
            quantity: Number of units
            **kwargs: Additional args for create_invoice

        Returns:
            Invoice details
        """
        if service_key not in self.services:
            raise ValueError(f"Unknown service: {service_key}")

        service = self.services[service_key]

        items = [{
            "description": service["name"],
            "amount": service["price"] * 100,  # Convert to cents
            "quantity": quantity
        }]

        return self.create_invoice(customer_id, items, **kwargs)

    # =========================================================================
    # WEBHOOK HANDLING
    # =========================================================================

    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Handle incoming Stripe webhook.

        Args:
            payload: Raw request body bytes
            signature: Stripe-Signature header value

        Returns:
            Processed event data
        """
        if not stripe:
            raise ImportError("stripe package not installed")

        if not self.webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET not configured")

        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, signature, self.webhook_secret
        )

        event_type = event["type"]
        data = event["data"]["object"]

        # Log event
        self._log_event(f"webhook_{event_type}", {
            "event_id": event["id"],
            "data": data
        })

        # Handle specific events
        result = {"event_type": event_type, "processed": False}

        if event_type == "checkout.session.completed":
            result = self._handle_checkout_completed(data)
        elif event_type == "invoice.paid":
            result = self._handle_invoice_paid(data)
        elif event_type == "invoice.payment_failed":
            result = self._handle_payment_failed(data)
        elif event_type == "payment_intent.succeeded":
            result = self._handle_payment_succeeded(data)
        elif event_type == "customer.subscription.created":
            result = self._handle_subscription_created(data)
        elif event_type == "customer.subscription.deleted":
            result = self._handle_subscription_cancelled(data)

        return result

    def _handle_checkout_completed(self, session: Dict) -> Dict[str, Any]:
        """Handle completed checkout session."""
        customer_id = session.get("customer")
        amount = session.get("amount_total", 0)
        metadata = session.get("metadata", {})

        return {
            "event_type": "checkout.session.completed",
            "processed": True,
            "customer_id": customer_id,
            "amount": amount,
            "metadata": metadata,
            "action": "payment_received"
        }

    def _handle_invoice_paid(self, invoice: Dict) -> Dict[str, Any]:
        """Handle paid invoice."""
        customer_id = invoice.get("customer")
        amount = invoice.get("amount_paid", 0)
        metadata = invoice.get("metadata", {})

        return {
            "event_type": "invoice.paid",
            "processed": True,
            "customer_id": customer_id,
            "amount": amount,
            "invoice_id": invoice.get("id"),
            "metadata": metadata,
            "action": "invoice_paid"
        }

    def _handle_payment_succeeded(self, payment_intent: Dict) -> Dict[str, Any]:
        """Handle successful payment intent."""
        metadata = payment_intent.get("metadata", {})

        return {
            "event_type": "payment_intent.succeeded",
            "processed": True,
            "payment_intent_id": payment_intent.get("id"),
            "amount": payment_intent.get("amount", 0),
            "metadata": metadata,
            "action": "payment_succeeded"
        }

    def _handle_subscription_created(self, subscription: Dict) -> Dict[str, Any]:
        """Handle new subscription."""
        return {
            "event_type": "customer.subscription.created",
            "processed": True,
            "subscription_id": subscription.get("id"),
            "customer_id": subscription.get("customer"),
            "action": "subscription_created"
        }

    def _handle_subscription_cancelled(self, subscription: Dict) -> Dict[str, Any]:
        """Handle subscription cancellation (triggers offboarding flow)."""
        return {
            "event_type": "customer.subscription.deleted",
            "processed": True,
            "subscription_id": subscription.get("id"),
            "customer_id": subscription.get("customer"),
            "cancel_at": subscription.get("canceled_at"),
            "action": "subscription_cancelled"
        }

    def _handle_payment_failed(self, invoice: Dict) -> Dict[str, Any]:
        """Handle failed payment (triggers dunning SMS via coaching_payment_failed template)."""
        return {
            "event_type": "invoice.payment_failed",
            "processed": True,
            "invoice_id": invoice.get("id"),
            "customer_id": invoice.get("customer"),
            "amount": invoice.get("amount_due", 0),
            "attempt_count": invoice.get("attempt_count", 0),
            "next_attempt": invoice.get("next_payment_attempt"),
            "action": "payment_failed"
        }

    # =========================================================================
    # REPORTING
    # =========================================================================

    def get_revenue_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate revenue report for date range.

        Args:
            start_date: Start of period (default: 30 days ago)
            end_date: End of period (default: now)

        Returns:
            Revenue summary with breakdown
        """
        if not stripe:
            raise ImportError("stripe package not installed")

        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # Get charges in date range
        charges = stripe.Charge.list(
            created={
                "gte": int(start_date.timestamp()),
                "lte": int(end_date.timestamp())
            },
            limit=100
        )

        # Calculate totals
        total_revenue = 0
        successful_charges = 0
        failed_charges = 0
        by_customer = {}

        for charge in charges.auto_paging_iter():
            if charge.status == "succeeded":
                total_revenue += charge.amount
                successful_charges += 1

                customer_id = charge.customer or "anonymous"
                if customer_id not in by_customer:
                    by_customer[customer_id] = {"count": 0, "total": 0}
                by_customer[customer_id]["count"] += 1
                by_customer[customer_id]["total"] += charge.amount
            else:
                failed_charges += 1

        # Get pending invoices
        pending_invoices = stripe.Invoice.list(status="open", limit=100)
        pending_amount = sum(inv.amount_due for inv in pending_invoices.data)

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_revenue_cents": total_revenue,
                "total_revenue_dollars": total_revenue / 100,
                "successful_charges": successful_charges,
                "failed_charges": failed_charges,
                "pending_invoices": len(pending_invoices.data),
                "pending_amount_cents": pending_amount,
                "pending_amount_dollars": pending_amount / 100
            },
            "by_customer": by_customer
        }

    def get_recent_payments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent successful payments."""
        if not stripe:
            raise ImportError("stripe package not installed")

        charges = stripe.Charge.list(limit=limit)

        payments = []
        for charge in charges.data:
            if charge.status == "succeeded":
                payments.append({
                    "id": charge.id,
                    "amount": charge.amount / 100,
                    "currency": charge.currency,
                    "customer": charge.customer,
                    "description": charge.description,
                    "created": datetime.fromtimestamp(charge.created).isoformat(),
                    "receipt_url": charge.receipt_url
                })

        return payments

    # =========================================================================
    # UTILITIES
    # =========================================================================

    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Log Stripe event to file."""
        log_file = self.data_dir / "events.jsonl"

        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }

        with open(log_file, 'a') as f:
            f.write(json.dumps(event) + "\n")

    def list_services(self) -> Dict[str, Any]:
        """List available services from catalog."""
        return self.services

    def get_service(self, service_key: str) -> Optional[Dict[str, Any]]:
        """Get service details by key."""
        return self.services.get(service_key)


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """CLI interface for Stripe operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Stripe Payments CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create customer
    customer_parser = subparsers.add_parser("create-customer", help="Create customer")
    customer_parser.add_argument("--email", required=True)
    customer_parser.add_argument("--name", required=True)
    customer_parser.add_argument("--phone")

    # Create payment link
    link_parser = subparsers.add_parser("create-link", help="Create payment link")
    link_parser.add_argument("--amount", type=int, help="Amount in dollars")
    link_parser.add_argument("--description", help="Payment description")
    link_parser.add_argument("--customer-id")
    link_parser.add_argument("--service", help="Service catalog key")
    link_parser.add_argument("--clickup-task", help="ClickUp task ID to auto-update on payment")

    # Create invoice
    invoice_parser = subparsers.add_parser("create-invoice", help="Create invoice")
    invoice_parser.add_argument("--customer-id", required=True)
    invoice_parser.add_argument("--service", required=True, help="Service catalog key")
    invoice_parser.add_argument("--quantity", type=int, default=1)

    # Revenue report
    report_parser = subparsers.add_parser("report", help="Revenue report")
    report_parser.add_argument("--days", type=int, default=30)

    # Recent payments
    recent_parser = subparsers.add_parser("recent", help="Recent payments")
    recent_parser.add_argument("--limit", type=int, default=10)

    # List services
    subparsers.add_parser("services", help="List service catalog")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        sp = StripePayments()

        if args.command == "create-customer":
            customer_id = sp.create_customer(args.email, args.name, args.phone)
            print(f"Created customer: {customer_id}")

        elif args.command == "create-link":
            metadata = {}
            if args.clickup_task:
                metadata["clickup_task_id"] = args.clickup_task

            if args.service:
                url = sp.create_payment_link(0, "", service_key=args.service, metadata=metadata if metadata else None)
            else:
                if not args.amount or not args.description:
                    print("Error: --amount and --description are required (or use --service)")
                    return 1
                url = sp.create_payment_link(args.amount, args.description, args.customer_id, metadata=metadata if metadata else None)
            print(f"Payment link: {url}")
            if args.clickup_task:
                print(f"ClickUp task {args.clickup_task} will auto-update on payment")

        elif args.command == "create-invoice":
            result = sp.create_invoice_from_service(args.customer_id, args.service, args.quantity)
            print(f"Invoice created: {result['invoice_id']}")
            print(f"Amount: ${result['total'] / 100:.2f}")
            print(f"Pay at: {result['hosted_invoice_url']}")

        elif args.command == "report":
            start = datetime.now() - timedelta(days=args.days)
            report = sp.get_revenue_report(start)
            print(f"\nRevenue Report ({args.days} days)")
            print("=" * 40)
            print(f"Total Revenue: ${report['summary']['total_revenue_dollars']:.2f}")
            print(f"Successful Charges: {report['summary']['successful_charges']}")
            print(f"Pending Invoices: {report['summary']['pending_invoices']}")
            print(f"Pending Amount: ${report['summary']['pending_amount_dollars']:.2f}")

        elif args.command == "recent":
            payments = sp.get_recent_payments(args.limit)
            print(f"\nRecent Payments ({len(payments)})")
            print("=" * 40)
            for p in payments:
                print(f"${p['amount']:.2f} - {p['description'] or 'No description'} - {p['created']}")

        elif args.command == "services":
            services = sp.list_services()
            print("\nService Catalog")
            print("=" * 40)
            for key, service in services.items():
                print(f"\n{key}:")
                print(f"  Name: {service['name']}")
                print(f"  Price: ${service['price']}")
                print(f"  SLA: {service['sla_days']} days")

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    main()
