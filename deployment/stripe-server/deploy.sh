#!/bin/bash
###############################################################################
# deploy.sh - Deploy Stripe API Server to EC2
#
# This script sets up:
# - Systemd service for the Stripe server
# - Nginx reverse proxy (optional)
# - Let's Encrypt SSL (optional)
# - Log directories
#
# USAGE:
#   ./deploy.sh                     # Deploy service only
#   ./deploy.sh --with-nginx        # Deploy with nginx
#   ./deploy.sh --with-ssl DOMAIN   # Deploy with nginx + SSL
#
# Prerequisites:
#   - Python 3.10+ with Flask, stripe installed
#   - .env file with Stripe credentials
#   - (For SSL) Domain pointing to this server
#
# Created: 2026-01-29
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    log "${RED}ERROR: $1${NC}"
    exit 1
}

success() {
    log "${GREEN}SUCCESS: $1${NC}"
}

# Configuration
SERVICE_NAME="stripe-server"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
NGINX_CONF="/etc/nginx/conf.d/stripe.conf"
LOG_DIR="/var/log/stripe-server"
DEV_SANDBOX="/home/clawdbot/dev-sandbox"
DEPLOYMENT_DIR="$DEV_SANDBOX/deployment/stripe-server"

# Parse arguments
WITH_NGINX=false
WITH_SSL=false
DOMAIN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --with-nginx)
            WITH_NGINX=true
            shift
            ;;
        --with-ssl)
            WITH_SSL=true
            WITH_NGINX=true
            DOMAIN="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--with-nginx] [--with-ssl DOMAIN]"
            exit 1
            ;;
    esac
done

# Check running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    error "Please run as root or with sudo"
fi

log "Deploying Stripe API Server..."

# =============================================================================
# 1. Create log directory
# =============================================================================
log "Creating log directory..."
mkdir -p "$LOG_DIR"
chown clawdbot:clawdbot "$LOG_DIR"
success "Log directory created: $LOG_DIR"

# =============================================================================
# 2. Install systemd service
# =============================================================================
log "Installing systemd service..."

# Copy service file
cp "$DEPLOYMENT_DIR/stripe-server.service" "$SERVICE_FILE"

# Reload systemd
systemctl daemon-reload

# Enable and start service
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

# Check status
if systemctl is-active --quiet "$SERVICE_NAME"; then
    success "Service started successfully"
else
    error "Service failed to start. Check: journalctl -u $SERVICE_NAME"
fi

# =============================================================================
# 3. Install nginx (if requested)
# =============================================================================
if [ "$WITH_NGINX" = true ]; then
    log "Setting up nginx..."

    # Install nginx if not present
    if ! command -v nginx &> /dev/null; then
        log "Installing nginx..."
        if command -v yum &> /dev/null; then
            yum install -y nginx
        elif command -v apt-get &> /dev/null; then
            apt-get update && apt-get install -y nginx
        else
            error "Could not install nginx - unknown package manager"
        fi
    fi

    # Copy nginx config
    cp "$DEPLOYMENT_DIR/nginx-stripe.conf" "$NGINX_CONF"

    # Update domain in config if provided
    if [ -n "$DOMAIN" ]; then
        sed -i "s/api.yourdomain.com/$DOMAIN/g" "$NGINX_CONF"
    fi

    # Test nginx config
    nginx -t || error "Nginx configuration test failed"

    # Enable and restart nginx
    systemctl enable nginx
    systemctl restart nginx

    success "Nginx configured"
fi

# =============================================================================
# 4. Install SSL with Let's Encrypt (if requested)
# =============================================================================
if [ "$WITH_SSL" = true ]; then
    if [ -z "$DOMAIN" ]; then
        error "Domain required for SSL. Use: --with-ssl yourdomain.com"
    fi

    log "Setting up SSL for $DOMAIN..."

    # Install certbot if not present
    if ! command -v certbot &> /dev/null; then
        log "Installing certbot..."
        if command -v yum &> /dev/null; then
            yum install -y certbot python3-certbot-nginx
        elif command -v apt-get &> /dev/null; then
            apt-get update && apt-get install -y certbot python3-certbot-nginx
        else
            error "Could not install certbot"
        fi
    fi

    # Get certificate
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@$DOMAIN || {
        log "${YELLOW}Certbot failed - you may need to run manually:${NC}"
        log "sudo certbot --nginx -d $DOMAIN"
    }

    success "SSL configured for $DOMAIN"
fi

# =============================================================================
# 5. Print summary
# =============================================================================
echo ""
echo "=============================================="
echo "  Stripe API Server Deployment Complete"
echo "=============================================="
echo ""
echo "Service Status:"
systemctl status "$SERVICE_NAME" --no-pager | head -10
echo ""
echo "Endpoints:"
if [ "$WITH_SSL" = true ] && [ -n "$DOMAIN" ]; then
    echo "  https://$DOMAIN/             - API info"
    echo "  https://$DOMAIN/health       - Health check"
    echo "  https://$DOMAIN/webhooks/stripe - Stripe webhook"
    echo "  https://$DOMAIN/api/...      - API endpoints"
    echo ""
    echo "Configure Stripe webhook:"
    echo "  URL: https://$DOMAIN/webhooks/stripe"
elif [ "$WITH_NGINX" = true ]; then
    echo "  http://YOUR_IP/              - API info"
    echo "  http://YOUR_IP/health        - Health check"
    echo "  http://YOUR_IP/webhooks/stripe - Stripe webhook"
    echo ""
    log "${YELLOW}Note: SSL not configured. For production, run:${NC}"
    echo "  sudo certbot --nginx -d yourdomain.com"
else
    echo "  http://YOUR_IP:5002/         - API info"
    echo "  http://YOUR_IP:5002/health   - Health check"
    echo "  http://YOUR_IP:5002/webhooks/stripe - Stripe webhook"
    echo ""
    log "${YELLOW}Note: Running without nginx. For production, use --with-nginx${NC}"
fi
echo ""
echo "Logs:"
echo "  Server: $LOG_DIR/server.log"
echo "  Errors: $LOG_DIR/error.log"
echo "  Systemd: journalctl -u $SERVICE_NAME -f"
echo ""
echo "Commands:"
echo "  sudo systemctl status $SERVICE_NAME"
echo "  sudo systemctl restart $SERVICE_NAME"
echo "  sudo systemctl stop $SERVICE_NAME"
echo ""
