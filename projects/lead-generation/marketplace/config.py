"""
Marketplace configuration — loads from root .env, sane defaults for local/dev.

Pay structure (mirrors RoofProspect.ai): prepaid CREDIT WALLET -> pay-per-exclusive-appointment.
Credits are stored in CENTS everywhere (1 credit == $0.01) to avoid float drift.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    # root .env (4 levels up: marketplace -> lead-generation -> projects -> dev-sandbox)
    _root = Path(__file__).resolve().parents[3]
    load_dotenv(_root / ".env")
except Exception:
    pass


def _b(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _i(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip())
    except (ValueError, AttributeError):
        return default


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.getenv("MARKETPLACE_DB", str(BASE_DIR / "marketplace.db"))

BRAND = {
    "name": os.getenv("MARKETPLACE_BRAND", "Marceau Air Marketplace"),
    "tagline": "Pre-qualified HVAC appointments. Pay only for what you win.",
    "gold": "#C9963C",
    "charcoal": "#333333",
    "support_email": os.getenv("SUPPORT_EMAIL", "wmarceau@marceausolutions.com"),
    "support_phone": os.getenv("SUPPORT_PHONE", "(239) 398-5676"),
}

# --- Pay structure knobs ---
SIGNUP_PROMO_CENTS = _i("MARKETPLACE_PROMO_CENTS", 30000)   # $300 free credits on signup (RoofProspect parity)
PROMO_CODE = os.getenv("MARKETPLACE_PROMO_CODE", "")        # if set, required to receive promo credits ("" = always grant)
MIN_TOPUP_CENTS = _i("MARKETPLACE_MIN_TOPUP_CENTS", 5000)   # $50 minimum credit purchase

# --- Marceau-Air-first gating ---
# When False, public self-signup is closed (invite/admin-created contractors only).
PUBLIC_SIGNUP = _b("MARKETPLACE_PUBLIC_SIGNUP", False)

# --- Payments ---
# 'manual'  -> credits added by admin only (safe for testing; NO Stripe calls)
# 'stripe'  -> real Stripe Checkout (uses STRIPE_SECRET_KEY; live key charges real money!)
PAYMENT_MODE = os.getenv("MARKETPLACE_PAYMENT_MODE", "manual").strip().lower()
STRIPE_SECRET_KEY = os.getenv("STRIPE_TEST_SECRET_KEY") or os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_TEST_PUBLIC_KEY") or os.getenv("STRIPE_PUBLIC_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_TEST_WEBHOOK_SECRET") or os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_IS_LIVE = STRIPE_SECRET_KEY.startswith("sk_live")

# --- App ---
SECRET_KEY = os.getenv("MARKETPLACE_SECRET_KEY", "dev-insecure-change-me")
ADMIN_EMAIL = os.getenv("MARKETPLACE_ADMIN_EMAIL", "wmarceau@marceausolutions.com")
ADMIN_PASSWORD = os.getenv("MARKETPLACE_ADMIN_PASSWORD", "changeme-admin")
PORT = _i("MARKETPLACE_PORT", 8767)
BASE_URL = os.getenv("MARKETPLACE_BASE_URL", f"http://127.0.0.1:{PORT}")

# --- Notifications (best-effort; failures never block a purchase) ---
NOTIFY_TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5692454753")
NOTIFY_ENABLED = _b("MARKETPLACE_NOTIFY", True)


def dollars(cents: int) -> str:
    return f"${cents / 100:,.2f}"
