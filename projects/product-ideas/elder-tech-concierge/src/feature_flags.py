#!/usr/bin/env python3
"""
feature_flags.py - Tesla-Style Feature Flag System for Elder Tech

WHAT: Server-side feature toggles that propagate to client apps
WHY: Enable rolling out features gradually without app updates

HOW IT WORKS (Tesla-Style OTA Updates):
1. Admin enables/disables features per client in dashboard
2. Client app polls /api/features on startup and periodically
3. App dynamically shows/hides UI elements based on flags
4. No app update required - changes apply on next poll

FEATURE CATEGORIES:
- Core: Essential features (always enabled)
- Standard: Features for Standard tier and above
- Premium: Features for Premium tier only
- Beta: Features in testing (opt-in per client)

USAGE:
    from feature_flags import FeatureFlags, get_client_features

    # Get features for a client
    features = get_client_features(client_id)

    # Check if feature is enabled
    if features.is_enabled('music_player'):
        show_music_button()
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


# ============================================================================
# FEATURE DEFINITIONS
# ============================================================================

@dataclass
class FeatureDefinition:
    """Definition of a feature that can be toggled."""
    id: str
    name: str
    description: str
    category: str  # core, standard, premium, beta
    default_enabled: bool
    tier_required: str  # basic, standard, premium
    dependencies: List[str]  # Other features this depends on
    rollout_percentage: int = 100  # For gradual rollouts


# All available features
FEATURE_CATALOG = {
    # Core features (always enabled for all tiers)
    'voice_assistant': FeatureDefinition(
        id='voice_assistant',
        name='Voice Assistant',
        description='Talk to Claude AI',
        category='core',
        default_enabled=True,
        tier_required='basic',
        dependencies=[]
    ),
    'emergency_button': FeatureDefinition(
        id='emergency_button',
        name='Emergency Button',
        description='One-tap emergency alert',
        category='core',
        default_enabled=True,
        tier_required='basic',
        dependencies=[]
    ),
    'call_contacts': FeatureDefinition(
        id='call_contacts',
        name='Call Family',
        description='Tap to call family contacts',
        category='core',
        default_enabled=True,
        tier_required='basic',
        dependencies=[]
    ),

    # Standard features (Standard tier and above)
    'sms_messaging': FeatureDefinition(
        id='sms_messaging',
        name='SMS Messaging',
        description='Send text messages to contacts',
        category='standard',
        default_enabled=True,
        tier_required='standard',
        dependencies=[]
    ),
    'email_reading': FeatureDefinition(
        id='email_reading',
        name='Email Reading',
        description='Read emails aloud',
        category='standard',
        default_enabled=True,
        tier_required='standard',
        dependencies=[]
    ),
    'music_player': FeatureDefinition(
        id='music_player',
        name='Music Player',
        description='Play radio and music',
        category='standard',
        default_enabled=True,
        tier_required='standard',
        dependencies=[]
    ),

    # Premium features (Premium tier only)
    'calendar_integration': FeatureDefinition(
        id='calendar_integration',
        name='Calendar',
        description='View and manage schedule',
        category='premium',
        default_enabled=True,
        tier_required='premium',
        dependencies=['email_reading']
    ),
    'family_dashboard': FeatureDefinition(
        id='family_dashboard',
        name='Family Dashboard',
        description='Family members can view activity',
        category='premium',
        default_enabled=True,
        tier_required='premium',
        dependencies=[]
    ),
    'activity_reports': FeatureDefinition(
        id='activity_reports',
        name='Activity Reports',
        description='Daily/weekly activity summaries',
        category='premium',
        default_enabled=True,
        tier_required='premium',
        dependencies=['family_dashboard']
    ),

    # Beta features (opt-in, any tier)
    'voice_speaker': FeatureDefinition(
        id='voice_speaker',
        name='Voice Speaker',
        description='Connect external voice speaker',
        category='beta',
        default_enabled=False,
        tier_required='basic',
        dependencies=['voice_assistant'],
        rollout_percentage=10  # Only 10% of clients initially
    ),
    'video_calls': FeatureDefinition(
        id='video_calls',
        name='Video Calls',
        description='Video call with family',
        category='beta',
        default_enabled=False,
        tier_required='standard',
        dependencies=['call_contacts'],
        rollout_percentage=5  # Only 5% of clients initially
    ),
    'medication_reminders': FeatureDefinition(
        id='medication_reminders',
        name='Medication Reminders',
        description='Voice reminders for medications',
        category='beta',
        default_enabled=False,
        tier_required='standard',
        dependencies=['calendar_integration'],
        rollout_percentage=20
    ),

    # Accessibility features (any tier)
    'high_contrast': FeatureDefinition(
        id='high_contrast',
        name='High Contrast Mode',
        description='High contrast colors for visibility',
        category='accessibility',
        default_enabled=False,
        tier_required='basic',
        dependencies=[]
    ),
    'extra_large_text': FeatureDefinition(
        id='extra_large_text',
        name='Extra Large Text',
        description='Larger text throughout app',
        category='accessibility',
        default_enabled=False,
        tier_required='basic',
        dependencies=[]
    ),
    'slow_speech': FeatureDefinition(
        id='slow_speech',
        name='Slower Speech',
        description='AI speaks at slower pace',
        category='accessibility',
        default_enabled=False,
        tier_required='basic',
        dependencies=[]
    ),
}


# Tier hierarchy for feature access
TIER_HIERARCHY = {
    'basic': 1,
    'standard': 2,
    'premium': 3
}


# ============================================================================
# FEATURE FLAG MANAGER
# ============================================================================

class FeatureFlags:
    """Manages feature flags for a client."""

    def __init__(self, client_id: str, client_tier: str, custom_flags: Dict[str, bool] = None):
        self.client_id = client_id
        self.client_tier = client_tier
        self.tier_level = TIER_HIERARCHY.get(client_tier, 1)
        self.custom_flags = custom_flags or {}
        self._resolved_flags = None

    def _resolve_flags(self) -> Dict[str, bool]:
        """Resolve all feature flags based on tier and custom settings."""
        if self._resolved_flags is not None:
            return self._resolved_flags

        flags = {}

        for feature_id, feature in FEATURE_CATALOG.items():
            # Check tier requirement
            required_tier_level = TIER_HIERARCHY.get(feature.tier_required, 1)
            tier_allowed = self.tier_level >= required_tier_level

            # Check if feature is in rollout (for beta features)
            in_rollout = self._is_in_rollout(feature_id, feature.rollout_percentage)

            # Determine enabled status
            if feature_id in self.custom_flags:
                # Custom override takes precedence
                enabled = self.custom_flags[feature_id] and tier_allowed
            elif feature.category == 'beta':
                # Beta features require opt-in and rollout eligibility
                enabled = in_rollout and tier_allowed
            else:
                # Standard features based on tier
                enabled = feature.default_enabled and tier_allowed

            # Check dependencies
            if enabled:
                for dep_id in feature.dependencies:
                    if not flags.get(dep_id, False):
                        enabled = False
                        break

            flags[feature_id] = enabled

        self._resolved_flags = flags
        return flags

    def _is_in_rollout(self, feature_id: str, percentage: int) -> bool:
        """Check if client is in rollout for gradual feature releases."""
        if percentage >= 100:
            return True
        # Use hash of client_id + feature_id for consistent assignment
        hash_val = hash(f"{self.client_id}:{feature_id}") % 100
        return hash_val < percentage

    def is_enabled(self, feature_id: str) -> bool:
        """Check if a specific feature is enabled."""
        flags = self._resolve_flags()
        return flags.get(feature_id, False)

    def get_all_flags(self) -> Dict[str, bool]:
        """Get all resolved feature flags."""
        return self._resolve_flags()

    def get_enabled_features(self) -> List[str]:
        """Get list of enabled feature IDs."""
        return [fid for fid, enabled in self._resolve_flags().items() if enabled]

    def get_feature_details(self) -> List[Dict]:
        """Get detailed info about all features for UI display."""
        flags = self._resolve_flags()
        details = []

        for feature_id, feature in FEATURE_CATALOG.items():
            required_tier = TIER_HIERARCHY.get(feature.tier_required, 1)
            tier_allowed = self.tier_level >= required_tier

            details.append({
                'id': feature.id,
                'name': feature.name,
                'description': feature.description,
                'category': feature.category,
                'enabled': flags[feature_id],
                'tier_required': feature.tier_required,
                'tier_allowed': tier_allowed,
                'is_beta': feature.category == 'beta',
                'custom_override': feature_id in self.custom_flags
            })

        return details

    def to_json(self) -> str:
        """Serialize feature flags to JSON for client consumption."""
        return json.dumps({
            'client_id': self.client_id,
            'tier': self.client_tier,
            'flags': self.get_all_flags(),
            'enabled_features': self.get_enabled_features(),
            'updated_at': datetime.now().isoformat()
        })


# ============================================================================
# DATABASE INTEGRATION
# ============================================================================

def get_client_features(client_id: str) -> Optional[FeatureFlags]:
    """
    Get feature flags for a client from the database.

    This is the main entry point for the app to get feature flags.
    """
    from client_db import ClientDB

    db = ClientDB()
    client = db.get_client(client_id)

    if not client:
        return None

    # Get custom flags from preferences if stored
    custom_flags = {}
    if hasattr(client.preferences, 'custom_settings'):
        settings = client.preferences.custom_settings
        if settings and isinstance(settings, dict):
            custom_flags = settings.get('feature_flags', {})

    return FeatureFlags(
        client_id=client_id,
        client_tier=client.subscription_tier,
        custom_flags=custom_flags
    )


def update_client_features(client_id: str, feature_updates: Dict[str, bool]) -> bool:
    """
    Update custom feature flags for a client.

    This is called from the admin dashboard when toggling features.
    """
    from client_db import ClientDB

    db = ClientDB()
    return db.update_preferences(client_id, feature_flags=feature_updates)


# ============================================================================
# FLASK ROUTES
# ============================================================================

def register_feature_routes(app):
    """Register feature flag API routes."""

    @app.route('/api/features')
    def get_features():
        """
        Get feature flags for current client.

        The client app calls this on startup and periodically to get
        the latest feature configuration (Tesla-style OTA update).
        """
        from flask import request, jsonify

        client_id = request.cookies.get('client_id')

        if not client_id:
            # Return default features for non-configured clients
            return jsonify({
                'success': True,
                'configured': False,
                'flags': {f.id: f.default_enabled and f.tier_required == 'basic'
                         for f in FEATURE_CATALOG.values()},
                'message': 'Using default features - configure client for full access'
            })

        features = get_client_features(client_id)

        if not features:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404

        return jsonify({
            'success': True,
            'configured': True,
            'client_id': client_id,
            'tier': features.client_tier,
            'flags': features.get_all_flags(),
            'enabled_features': features.get_enabled_features(),
            'details': features.get_feature_details()
        })

    @app.route('/api/features/catalog')
    def get_feature_catalog():
        """
        Get the full feature catalog (for admin/documentation).
        """
        from flask import jsonify

        catalog = []
        for feature_id, feature in FEATURE_CATALOG.items():
            catalog.append({
                'id': feature.id,
                'name': feature.name,
                'description': feature.description,
                'category': feature.category,
                'tier_required': feature.tier_required,
                'default_enabled': feature.default_enabled,
                'dependencies': feature.dependencies,
                'rollout_percentage': feature.rollout_percentage
            })

        return jsonify({
            'success': True,
            'catalog': catalog,
            'tiers': list(TIER_HIERARCHY.keys()),
            'categories': ['core', 'standard', 'premium', 'beta', 'accessibility']
        })


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == '__main__':
    import sys

    print("Elder Tech Feature Flag System\n")

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'catalog':
            print("Available Features:\n")
            for cat in ['core', 'standard', 'premium', 'beta', 'accessibility']:
                print(f"  {cat.upper()}:")
                for fid, f in FEATURE_CATALOG.items():
                    if f.category == cat:
                        print(f"    - {f.name} ({fid})")
                        print(f"      {f.description}")
                        print(f"      Tier: {f.tier_required}, Default: {f.default_enabled}")
                print()

        elif command == 'check' and len(sys.argv) > 2:
            client_id = sys.argv[2]
            features = get_client_features(client_id)
            if features:
                print(f"Features for client {client_id} ({features.client_tier} tier):\n")
                for f in features.get_feature_details():
                    status = "[OK]" if f['enabled'] else "[--]"
                    beta = " (BETA)" if f['is_beta'] else ""
                    override = " *" if f['custom_override'] else ""
                    print(f"  {status} {f['name']}{beta}{override}")
            else:
                print(f"Client {client_id} not found")

        else:
            print("Usage:")
            print("  python feature_flags.py catalog - Show all features")
            print("  python feature_flags.py check <client_id> - Check features for client")
    else:
        # Show summary
        print("Feature Categories:")
        for cat in ['core', 'standard', 'premium', 'beta', 'accessibility']:
            count = sum(1 for f in FEATURE_CATALOG.values() if f.category == cat)
            print(f"  {cat}: {count} features")

        print("\nSubscription Tiers:")
        for tier, level in TIER_HIERARCHY.items():
            count = sum(1 for f in FEATURE_CATALOG.values()
                       if TIER_HIERARCHY.get(f.tier_required, 1) <= level)
            print(f"  {tier}: {count} features available")

        print("\nRun 'python feature_flags.py catalog' for full list")
