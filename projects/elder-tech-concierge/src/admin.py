#!/usr/bin/env python3
"""
admin.py - Admin Dashboard Routes for Elder Tech Concierge

WHAT: Flask Blueprint for admin functionality
WHY: Manage clients, generate setup URLs, view analytics

ROUTES:
- GET /admin - Dashboard home
- GET /admin/clients - List all clients
- GET /admin/clients/<id> - View client details
- POST /admin/clients - Create new client
- PUT /admin/clients/<id> - Update client
- DELETE /admin/clients/<id> - Delete client
- GET /admin/stats - System statistics

SETUP ROUTES:
- GET /setup/<client_id> - Auto-configure client app (public)
"""

import os
import json
from functools import wraps
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response

from client_db import ClientDB

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Initialize database
db = ClientDB()

# Simple admin password (for MVP - replace with proper auth later)
ADMIN_PASSWORD = os.environ.get('ELDER_TECH_ADMIN_PASSWORD', 'eldertech2026')


# ============================================================================
# AUTHENTICATION (Simple for MVP)
# ============================================================================

def check_admin_auth():
    """Check if request has valid admin auth."""
    # Check cookie
    auth_cookie = request.cookies.get('admin_auth')
    if auth_cookie == ADMIN_PASSWORD:
        return True

    # Check header
    auth_header = request.headers.get('X-Admin-Password')
    if auth_header == ADMIN_PASSWORD:
        return True

    # Check query param (for initial login)
    auth_param = request.args.get('password')
    if auth_param == ADMIN_PASSWORD:
        return True

    return False


def admin_required(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_admin_auth():
            return jsonify({
                'success': False,
                'error': 'Admin authentication required',
                'hint': 'Add ?password=XXX or set X-Admin-Password header'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# ADMIN DASHBOARD ROUTES
# ============================================================================

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard home."""
    stats = db.get_stats()
    clients = db.list_clients(limit=10)

    # Return JSON for API calls, HTML for browser
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'success': True,
            'stats': stats,
            'recent_clients': clients
        })

    return render_template('admin/dashboard.html', stats=stats, clients=clients)


@admin_bp.route('/clients')
@admin_required
def list_clients():
    """List all clients."""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    clients = db.list_clients(limit=limit, offset=offset)

    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'success': True,
            'clients': clients,
            'count': len(clients)
        })

    return render_template('admin/clients.html', clients=clients)


@admin_bp.route('/clients/<client_id>')
@admin_required
def get_client(client_id):
    """Get client details."""
    client = db.get_client(client_id)

    if not client:
        return jsonify({
            'success': False,
            'error': 'Client not found'
        }), 404

    activity = db.get_activity(client_id, limit=20)

    if request.headers.get('Accept') == 'application/json':
        from dataclasses import asdict
        return jsonify({
            'success': True,
            'client': {
                'id': client.id,
                'name': client.name,
                'email': client.email,
                'phone': client.phone,
                'subscription_status': client.subscription_status,
                'subscription_tier': client.subscription_tier,
                'emergency_contacts': [asdict(c) for c in client.emergency_contacts],
                'family_contacts': [asdict(c) for c in client.family_contacts],
                'preferences': asdict(client.preferences),
                'created_at': client.created_at,
                'last_active': client.last_active,
                'setup_completed': client.setup_completed
            },
            'activity': activity
        })

    return render_template('admin/client_detail.html', client=client, activity=activity)


@admin_bp.route('/clients', methods=['POST'])
@admin_required
def create_client():
    """Create a new client."""
    data = request.get_json() or request.form.to_dict()

    # Required field
    name = data.get('name', '').strip()
    if not name:
        return jsonify({
            'success': False,
            'error': 'Client name is required'
        }), 400

    # Parse contacts if provided as JSON strings
    emergency_contacts = data.get('emergency_contacts', [])
    if isinstance(emergency_contacts, str):
        emergency_contacts = json.loads(emergency_contacts)

    family_contacts = data.get('family_contacts', [])
    if isinstance(family_contacts, str):
        family_contacts = json.loads(family_contacts)

    # Parse preferences
    preferences = data.get('preferences', {})
    if isinstance(preferences, str):
        preferences = json.loads(preferences)

    try:
        client_id = db.create_client(
            name=name,
            email=data.get('email'),
            phone=data.get('phone'),
            emergency_contacts=emergency_contacts,
            family_contacts=family_contacts,
            preferences=preferences,
            subscription_tier=data.get('subscription_tier', 'basic'),
            notes=data.get('notes')
        )

        # Generate setup URL
        setup_url = f"/setup/{client_id}"

        return jsonify({
            'success': True,
            'client_id': client_id,
            'setup_url': setup_url,
            'message': f"Client '{name}' created successfully"
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/clients/<client_id>', methods=['PUT'])
@admin_required
def update_client(client_id):
    """Update client details."""
    data = request.get_json() or request.form.to_dict()

    # Check client exists
    client = db.get_client(client_id)
    if not client:
        return jsonify({
            'success': False,
            'error': 'Client not found'
        }), 404

    # Update client fields
    update_fields = {}
    for field in ['name', 'email', 'phone', 'subscription_status',
                  'subscription_tier', 'notes']:
        if field in data:
            update_fields[field] = data[field]

    if update_fields:
        db.update_client(client_id, **update_fields)

    # Update contacts if provided
    if 'emergency_contacts' in data:
        emergency = data['emergency_contacts']
        if isinstance(emergency, str):
            emergency = json.loads(emergency)
        db.update_contacts(client_id, emergency_contacts=emergency)

    if 'family_contacts' in data:
        family = data['family_contacts']
        if isinstance(family, str):
            family = json.loads(family)
        db.update_contacts(client_id, family_contacts=family)

    # Update preferences if provided
    if 'preferences' in data:
        prefs = data['preferences']
        if isinstance(prefs, str):
            prefs = json.loads(prefs)
        db.update_preferences(client_id, **prefs)

    return jsonify({
        'success': True,
        'message': f"Client '{client_id}' updated successfully"
    })


@admin_bp.route('/clients/<client_id>', methods=['DELETE'])
@admin_required
def delete_client(client_id):
    """Delete a client."""
    client = db.get_client(client_id)
    if not client:
        return jsonify({
            'success': False,
            'error': 'Client not found'
        }), 404

    db.delete_client(client_id)

    return jsonify({
        'success': True,
        'message': f"Client '{client.name}' deleted successfully"
    })


@admin_bp.route('/stats')
@admin_required
def get_stats():
    """Get system statistics."""
    stats = db.get_stats()

    return jsonify({
        'success': True,
        'stats': stats
    })


# ============================================================================
# LOGIN ROUTE
# ============================================================================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login."""
    if request.method == 'POST':
        password = request.form.get('password') or request.json.get('password')

        if password == ADMIN_PASSWORD:
            response = make_response(redirect(url_for('admin.dashboard')))
            response.set_cookie('admin_auth', password, max_age=86400)  # 24 hours
            return response
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid password'
            }), 401

    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    """Admin logout."""
    response = make_response(redirect(url_for('admin.login')))
    response.delete_cookie('admin_auth')
    return response


# ============================================================================
# PUBLIC SETUP ROUTE (No auth required)
# ============================================================================

def register_setup_route(app):
    """Register the public setup route on the main app."""

    @app.route('/setup/<client_id>')
    def setup_client(client_id):
        """
        Auto-configure client app from setup URL.

        This is the magic URL that seniors visit to configure their iPad.
        It loads their pre-configured contacts and preferences.
        """
        client_config = db.get_client_config(client_id)

        if not client_config:
            return jsonify({
                'success': False,
                'error': 'Invalid setup link'
            }), 404

        # Mark setup as started
        db.log_activity(client_id, 'setup_started', {
            'user_agent': request.headers.get('User-Agent'),
            'ip': request.remote_addr
        })

        # Set client config in cookie (encrypted in production)
        response = make_response(redirect('/'))

        # Store config in cookie (for client-side JavaScript)
        config_json = json.dumps(client_config)
        response.set_cookie(
            'client_config',
            config_json,
            max_age=365 * 24 * 60 * 60,  # 1 year
            httponly=False,  # JavaScript needs to read this
            samesite='Lax'
        )

        # Also store client_id for server-side tracking
        response.set_cookie(
            'client_id',
            client_id,
            max_age=365 * 24 * 60 * 60,
            httponly=True,
            samesite='Lax'
        )

        # Mark setup completed
        db.update_client(client_id, setup_completed=True)
        db.log_activity(client_id, 'setup_completed')

        return response

    @app.route('/api/client-config')
    def get_client_config_api():
        """
        API endpoint to get current client config.

        Used by client-side JavaScript to check if configured.
        """
        client_id = request.cookies.get('client_id')

        if not client_id:
            return jsonify({
                'success': False,
                'configured': False,
                'message': 'No client configuration found'
            })

        client_config = db.get_client_config(client_id)

        if not client_config:
            return jsonify({
                'success': False,
                'configured': False,
                'message': 'Client configuration not found'
            })

        return jsonify({
            'success': True,
            'configured': True,
            'config': client_config
        })
