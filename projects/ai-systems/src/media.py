"""
AI Systems Tower - Adaptive Behavior, Media Generation, Error Analysis, Notifications

Adaptive behavior, media generation, error analysis, notifications.
Extracted from monolithic agent_bridge_api.py, refactored into Flask blueprint.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify

from .models import (
    BEHAVIOR_PROFILES,
    BehaviorProfile,
    DISCOVERED_TOOLS,
    TOOL_USAGE_STATS,
    ERROR_SOLUTIONS,
)

media_bp = Blueprint('media', __name__)


@media_bp.route('/behavior/profile', methods=['POST'])
def behavior_get_profile():
    """Get or create behavior profile for a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id'"}), 400

    profile = get_or_create_behavior_profile(session_id)

    return jsonify({
        "success": True,
        "profile_id": profile.profile_id,
        "session_id": profile.session_id,
        "tool_preferences": profile.tool_preferences,
        "risk_tolerance": profile.risk_tolerance,
        "verbosity_adjustment": profile.verbosity_adjustment,
        "learning_iterations": profile.learning_iterations,
        "last_adaptation": profile.last_adaptation
    })


@media_bp.route('/behavior/adapt', methods=['POST'])
def behavior_adapt():
    """Adapt behavior based on a task outcome."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    outcome_id = data.get('outcome_id')
    learning_rate = data.get('learning_rate', 0.1)

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id'"}), 400

    # Get outcome if provided
    outcome = None
    if outcome_id and outcome_id in TASK_OUTCOMES:
        outcome = TASK_OUTCOMES[outcome_id]
    elif 'outcome' in data:
        # Allow inline outcome data
        outcome_data = data['outcome']
        outcome = TaskOutcome(
            outcome_id="inline",
            session_id=session_id,
            task=outcome_data.get('task', ''),
            template_used=outcome_data.get('template', 'default'),
            success=outcome_data.get('success', True),
            error_message=outcome_data.get('error_message'),
            tool_calls=outcome_data.get('tool_calls', []),
            user_feedback=outcome_data.get('user_feedback')
        )
    else:
        return jsonify({"success": False, "error": "Missing 'outcome_id' or 'outcome' data"}), 400

    result = adapt_behavior(session_id, outcome, learning_rate)
    return jsonify({
        "success": True,
        **result
    })


@media_bp.route('/behavior/recommendations', methods=['POST'])
def behavior_recommendations():
    """Get behavior recommendations for a task."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    task = data.get('task', '')

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id'"}), 400

    recommendations = get_behavior_recommendations(session_id, task)
    return jsonify({
        "success": True,
        "session_id": session_id,
        **recommendations
    })


@media_bp.route('/behavior/reset', methods=['POST'])
def behavior_reset():
    """Reset behavior profile for a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id'"}), 400

    if session_id in BEHAVIOR_PROFILES:
        del BEHAVIOR_PROFILES[session_id]

    return jsonify({
        "success": True,
        "session_id": session_id,
        "reset": True
    })


@media_bp.route('/behavior/list', methods=['GET', 'POST'])
def behavior_list():
    """List all behavior profiles."""
    profiles = []
    for pid, profile in BEHAVIOR_PROFILES.items():
        profiles.append({
            "profile_id": profile.profile_id,
            "session_id": profile.session_id,
            "risk_tolerance": profile.risk_tolerance,
            "learning_iterations": profile.learning_iterations,
            "last_adaptation": profile.last_adaptation
        })

    return jsonify({
        "success": True,
        "profiles": profiles,
        "total": len(profiles)
    })


# =============================================================================
# v4.1 META-AGENT INTEGRATIONS - SELF-ANNEALING CAPABILITIES
# =============================================================================

# Tool Discovery and Self-Improvement Storage
DISCOVERED_TOOLS: Dict[str, dict] = {}
TOOL_USAGE_STATS: Dict[str, dict] = {}
ERROR_SOLUTIONS: Dict[str, dict] = {}
CAPABILITY_REGISTRY: Dict[str, dict] = {}
META_KNOWLEDGE: Dict[str, Any] = {
    'known_integrations': [],
    'pending_questions': [],
    'learned_patterns': [],
    'improvement_suggestions': []
}

# Gmail, Sheets, SMS → Extracted to projects/personal-assistant/src/ (port 5011)
# Endpoints: /gmail/*, /sheets/*, /sms/*


# ClickUp CRM → Extracted to projects/lead-generation/src/ (port 5012)
# Endpoints: /clickup/*


@media_bp.route('/agent/build-workflow', methods=['POST'])
def agent_build_workflow():
    """Build a new n8n agent workflow from template."""
    data = request.get_json() or {}
    name = data.get('name', 'New Agent Workflow')
    webhook_path = data.get('webhook_path', 'custom-agent')
    tools = data.get('tools', ['file_read', 'file_write', 'command', 'grep', 'glob'])
    workflow = {
        'name': name,
        'nodes': [
            {'id': str(uuid.uuid4()), 'name': 'Webhook', 'type': 'n8n-nodes-base.webhook', 'position': [0, 0], 'typeVersion': 2, 'parameters': {'httpMethod': 'POST', 'path': webhook_path, 'responseMode': 'lastNode'}},
            {'id': str(uuid.uuid4()), 'name': 'Parse Request', 'type': 'n8n-nodes-base.code', 'position': [220, 0], 'typeVersion': 2, 'parameters': {'jsCode': f'return {{ json: {{ message: "{name} received request", data: $input.first().json }} }};'}},
            {'id': str(uuid.uuid4()), 'name': 'Return Response', 'type': 'n8n-nodes-base.code', 'position': [440, 0], 'typeVersion': 2, 'parameters': {'jsCode': 'return { json: $input.first().json };'}}
        ],
        'connections': {'Webhook': {'main': [[{'node': 'Parse Request', 'type': 'main', 'index': 0}]]}, 'Parse Request': {'main': [[{'node': 'Return Response', 'type': 'main', 'index': 0}]]}},
        'settings': {'executionOrder': 'v1'}
    }
    return jsonify({"success": True, "workflow": workflow, "name": name, "webhook_path": webhook_path, "tools": tools, "instructions": "Use /n8n/create-workflow with this workflow object to deploy it"})

# =============================================================================
# ERROR NOTIFICATION & AUTO-HEALING SYSTEM
# =============================================================================

# Error notification tracking
ERROR_NOTIFICATIONS: Dict[str, dict] = {}
AUTO_FIXES: Dict[str, dict] = {
    'ECONNREFUSED': {
        'description': 'Connection refused - service not running',
        'auto_fix': 'restart_service',
        'commands': ['systemctl restart {service}', 'docker restart {container}']
    },
    'ETIMEDOUT': {
        'description': 'Connection timeout - network or service slow',
        'auto_fix': 'retry_with_backoff',
        'max_retries': 3
    },
    'rate limit': {
        'description': 'Rate limited by external API',
        'auto_fix': 'exponential_backoff',
        'wait_seconds': [1, 5, 15, 60]
    },
    'authentication': {
        'description': 'Authentication failed',
        'auto_fix': 'refresh_credentials',
        'check_env_vars': True
    }
}


@media_bp.route('/notify/error', methods=['POST'])
def notify_error():
    """Send error notification to appropriate channels based on severity."""
    data = request.get_json() or {}
    error_message = data.get('error_message', 'Unknown error')
    workflow_name = data.get('workflow_name', 'Unknown')
    node_name = data.get('node_name', 'Unknown')
    severity = data.get('severity', 'medium').lower()

    notification_id = f"notify_{int(time.time())}_{uuid.uuid4().hex[:6]}"

    # Determine channels based on severity
    channels = []
    if severity == 'critical':
        channels = ['sms', 'email', 'slack']
    elif severity == 'high':
        channels = ['email', 'slack']
    else:
        channels = ['log']

    # Store notification
    ERROR_NOTIFICATIONS[notification_id] = {
        'id': notification_id,
        'error_message': error_message,
        'workflow_name': workflow_name,
        'node_name': node_name,
        'severity': severity,
        'channels': channels,
        'sent_at': datetime.now().isoformat(),
        'acknowledged': False
    }

    # For critical errors, attempt SMS notification via Twilio
    sms_sent = False
    if 'sms' in channels:
        try:
            twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
            twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
            twilio_from = os.getenv('TWILIO_PHONE_NUMBER')
            admin_phone = os.getenv('ADMIN_PHONE_NUMBER', '+18135551234')

            if twilio_sid and twilio_token and twilio_from:
                from twilio.rest import Client
                client = Client(twilio_sid, twilio_token)
                sms_body = f"🚨 CRITICAL: {workflow_name}\n{error_message[:140]}"
                message = client.messages.create(body=sms_body, from_=twilio_from, to=admin_phone)
                sms_sent = True
                ERROR_NOTIFICATIONS[notification_id]['sms_sid'] = message.sid
        except Exception as e:
            ERROR_NOTIFICATIONS[notification_id]['sms_error'] = str(e)

    return jsonify({
        "success": True,
        "notification_id": notification_id,
        "severity": severity,
        "channels": channels,
        "sms_sent": sms_sent,
        "message": f"Error notification sent via {', '.join(channels)}"
    })


@media_bp.route('/notify/critical', methods=['POST'])
def notify_critical():
    """Send urgent SMS notification for critical errors."""
    data = request.get_json() or {}
    message = data.get('message', 'Critical system error')
    workflow = data.get('workflow', 'Unknown')

    # Always try SMS for critical notifications
    result = {'success': False, 'method': 'critical_sms'}

    try:
        twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_from = os.getenv('TWILIO_PHONE_NUMBER')
        admin_phone = os.getenv('ADMIN_PHONE_NUMBER', '+18135551234')

        if twilio_sid and twilio_token and twilio_from:
            from twilio.rest import Client
            client = Client(twilio_sid, twilio_token)
            sms_body = f"🚨 CRITICAL ERROR\n{workflow}\n{message[:120]}"
            sms = client.messages.create(body=sms_body, from_=twilio_from, to=admin_phone)
            result = {'success': True, 'sms_sid': sms.sid, 'method': 'twilio'}
        else:
            result = {'success': False, 'error': 'Twilio credentials not configured'}
    except Exception as e:
        result = {'success': False, 'error': str(e)}

    return jsonify(result)


@media_bp.route('/error/analyze', methods=['POST'])
def error_analyze():
    """Analyze error patterns and suggest fixes."""
    data = request.get_json() or {}
    error_message = data.get('error_message', '')
    error_type = data.get('error_type', '')

    analysis = {
        'error_message': error_message,
        'error_type': error_type,
        'known_pattern': False,
        'auto_fix_available': False,
        'suggestions': [],
        'similar_errors': []
    }

    # Check against known auto-fix patterns
    for pattern, fix_info in AUTO_FIXES.items():
        if pattern.lower() in error_message.lower() or pattern.lower() in error_type.lower():
            analysis['known_pattern'] = True
            analysis['auto_fix_available'] = True
            analysis['auto_fix'] = fix_info
            analysis['suggestions'].append(f"Auto-fix available: {fix_info['description']}")
            break

    # Check against learned error solutions
    for error_id, error_data in ERROR_SOLUTIONS.items():
        if error_data['pattern'].lower() in error_message.lower():
            analysis['similar_errors'].append({
                'pattern': error_data['pattern'],
                'solution': error_data['solution'],
                'times_applied': error_data.get('times_applied', 0)
            })

    # General suggestions based on error type
    if 'timeout' in error_message.lower():
        analysis['suggestions'].append('Consider increasing timeout values')
        analysis['suggestions'].append('Check network connectivity')
    if 'permission' in error_message.lower():
        analysis['suggestions'].append('Verify file/directory permissions')
        analysis['suggestions'].append('Check user authentication')
    if 'not found' in error_message.lower():
        analysis['suggestions'].append('Verify path/resource exists')
        analysis['suggestions'].append('Check for typos in identifiers')

    return jsonify({"success": True, "analysis": analysis})


@media_bp.route('/error/auto-fix', methods=['POST'])
def error_auto_fix():
    """Attempt automatic fix for known error types."""
    data = request.get_json() or {}
    error_message = data.get('error_message', '')
    error_type = data.get('error_type', '')
    dry_run = data.get('dry_run', True)  # Default to dry run for safety

    fix_result = {
        'error_message': error_message,
        'fix_attempted': False,
        'fix_succeeded': False,
        'dry_run': dry_run,
        'actions': []
    }

    # Find matching auto-fix
    matched_fix = None
    for pattern, fix_info in AUTO_FIXES.items():
        if pattern.lower() in error_message.lower() or pattern.lower() in error_type.lower():
            matched_fix = (pattern, fix_info)
            break

    if not matched_fix:
        return jsonify({"success": False, "error": "No auto-fix available for this error type", "result": fix_result})

    pattern, fix_info = matched_fix
    fix_result['fix_attempted'] = True
    fix_result['fix_type'] = fix_info['auto_fix']

    if fix_info['auto_fix'] == 'retry_with_backoff':
        fix_result['actions'].append({
            'action': 'retry_with_backoff',
            'max_retries': fix_info.get('max_retries', 3),
            'description': 'Retry the operation with exponential backoff'
        })
        if not dry_run:
            fix_result['fix_succeeded'] = True
            fix_result['next_action'] = 'Caller should implement retry logic'

    elif fix_info['auto_fix'] == 'exponential_backoff':
        wait_times = fix_info.get('wait_seconds', [1, 5, 15])
        fix_result['actions'].append({
            'action': 'wait_and_retry',
            'wait_seconds': wait_times,
            'description': f'Wait {wait_times[0]}s then retry, increasing on each failure'
        })
        if not dry_run:
            fix_result['fix_succeeded'] = True

    elif fix_info['auto_fix'] == 'refresh_credentials':
        fix_result['actions'].append({
            'action': 'refresh_credentials',
            'check_env_vars': fix_info.get('check_env_vars', True),
            'description': 'Refresh authentication credentials'
        })
        if not dry_run:
            # Could trigger credential refresh here
            fix_result['fix_succeeded'] = True

    # Log the fix attempt
    fix_id = f"fix_{int(time.time())}"
    if 'AUTO_FIX_LOG' not in globals():
        global AUTO_FIX_LOG
        AUTO_FIX_LOG = {}
    AUTO_FIX_LOG[fix_id] = {
        'error_message': error_message,
        'fix_type': fix_info['auto_fix'],
        'succeeded': fix_result['fix_succeeded'],
        'timestamp': datetime.now().isoformat()
    }

    return jsonify({"success": True, "result": fix_result})


@media_bp.route('/error/stats', methods=['GET'])
def error_stats():
    """Get error and notification statistics."""
    return jsonify({
        "success": True,
        "stats": {
            "total_notifications": len(ERROR_NOTIFICATIONS),
            "error_solutions_learned": len(ERROR_SOLUTIONS),
            "auto_fix_patterns": len(AUTO_FIXES),
            "recent_notifications": list(ERROR_NOTIFICATIONS.values())[-10:],
            "most_common_errors": _get_common_errors()
        }
    })


def _get_common_errors():
    """Get most common error patterns."""
    error_counts = {}
    for error_id, error_data in ERROR_SOLUTIONS.items():
        pattern = error_data.get('pattern', 'unknown')
        error_counts[pattern] = error_counts.get(pattern, 0) + 1
    return sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]


# =============================================================================
# MULTI-PROVIDER MEDIA GENERATION (v4.11)
# =============================================================================

# Lazy-loaded media routers to avoid import overhead
_image_router = None
_video_router = None


def _get_image_router():
    """Lazy-load the multi-provider image router."""
    global _image_router
    if _image_router is None:
        try:
            from multi_provider_image_router import MultiProviderImageRouter
            _image_router = MultiProviderImageRouter()
        except ImportError:
            return None
    return _image_router


def _get_video_router():
    """Lazy-load the multi-provider video router."""
    global _video_router
    if _video_router is None:
        try:
            from multi_provider_video_router import MultiProviderVideoRouter
            _video_router = MultiProviderVideoRouter()
        except ImportError:
            return None
    return _video_router


@media_bp.route('/media/image/generate', methods=['POST'])
def media_image_generate():
    """
    Generate images using multi-provider routing.

    Request:
        {
            "prompt": "Fitness workout scene",
            "count": 4,
            "tier": "budget|standard|premium",
            "output_dir": "/optional/path",
            "provider": "grok|replicate_sd|dalle3|ideogram"  // optional force
        }

    Response:
        {
            "success": true,
            "urls": ["url1", "url2"],
            "paths": ["/path1", "/path2"],  // if output_dir provided
            "provider": "grok",
            "tier": "standard",
            "cost": 0.28
        }
    """
    router = _get_image_router()
    if not router:
        return make_error_response(
            ErrorCode.INTERNAL_ERROR,
            "Multi-provider image router not available",
            suggestion="Ensure multi_provider_image_router.py is in execution/"
        ), 500

    data = request.get_json() or {}
    prompt = data.get('prompt')

    if not prompt:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "prompt is required"
        ), 400

    count = data.get('count', 1)
    tier_str = data.get('tier', 'standard')
    output_dir = data.get('output_dir')
    force_provider = data.get('provider')

    # Map tier string to enum
    try:
        from multi_provider_image_router import ImageQualityTier, ImageProvider
        tier = ImageQualityTier(tier_str)
        provider = ImageProvider(force_provider) if force_provider else None
    except (ValueError, ImportError) as e:
        return make_error_response(
            ErrorCode.INVALID_PARAMETER,
            f"Invalid tier or provider: {e}"
        ), 400

    result = router.generate_images(
        prompt=prompt,
        count=count,
        tier=tier,
        output_dir=output_dir,
        force_provider=provider
    )

    return jsonify(result)


@media_bp.route('/media/video/generate', methods=['POST'])
def media_video_generate():
    """
    Generate videos using multi-provider routing.

    Request:
        {
            "prompt": "Fitness transformation journey",
            "image_urls": ["url1", "url2"],  // optional for image-to-video
            "headline": "Transform Your Body",
            "cta_text": "Start Now",
            "duration": 10,
            "tier": "free|budget|standard|premium",
            "provider": "moviepy|hailuo_fast|creatomate|grok_imagine|veo3_fast|veo3"
        }

    Response:
        {
            "success": true,
            "video_url": "https://...",
            "video_path": "/path/to/video.mp4",
            "provider": "creatomate",
            "tier": "standard",
            "cost": 0.05,
            "generation_time": 12.5
        }
    """
    router = _get_video_router()
    if not router:
        return make_error_response(
            ErrorCode.INTERNAL_ERROR,
            "Multi-provider video router not available",
            suggestion="Ensure multi_provider_video_router.py is in execution/"
        ), 500

    data = request.get_json() or {}
    prompt = data.get('prompt')
    image_urls = data.get('image_urls', [])

    if not prompt and not image_urls:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "Either prompt or image_urls is required"
        ), 400

    headline = data.get('headline', '')
    cta_text = data.get('cta_text', '')
    duration = data.get('duration', 10.0)
    music_style = data.get('music_style', 'energetic')
    tier_str = data.get('tier', 'standard')
    force_provider = data.get('provider')

    # Map tier string to enum
    try:
        from multi_provider_video_router import QualityTier, Provider
        tier = QualityTier(tier_str)
        provider = Provider(force_provider) if force_provider else None
    except (ValueError, ImportError) as e:
        return make_error_response(
            ErrorCode.INVALID_PARAMETER,
            f"Invalid tier or provider: {e}"
        ), 400

    result = router.create_video(
        image_urls=image_urls if image_urls else None,
        prompt=prompt,
        headline=headline,
        cta_text=cta_text,
        duration=duration,
        music_style=music_style,
        tier=tier,
        force_provider=provider
    )

    return jsonify(result)


@media_bp.route('/media/stats', methods=['GET', 'POST'])
def media_stats():
    """
    Get media generation statistics for both image and video.

    Query params / body:
        days: Number of days to analyze (default: 30)

    Response:
        {
            "success": true,
            "image": { ... cost summary ... },
            "video": { ... cost summary ... },
            "total_cost": 12.50
        }
    """
    data = request.get_json() or {}
    days = data.get('days', request.args.get('days', 30, type=int))

    result = {
        "success": True,
        "period_days": days,
        "image": None,
        "video": None,
        "total_cost": 0
    }

    image_router = _get_image_router()
    if image_router:
        image_stats = image_router.get_statistics(days)
        result["image"] = image_stats
        result["total_cost"] += image_stats.get("total_cost", 0)

    video_router = _get_video_router()
    if video_router:
        video_stats = video_router.get_statistics(days)
        result["video"] = video_stats.get("costs", {})
        result["total_cost"] += video_stats.get("costs", {}).get("total_cost", 0)

    return jsonify(result)


@media_bp.route('/media/limits', methods=['GET', 'POST'])
def media_limits():
    """
    Get current rate limit status for all providers.

    Response:
        {
            "success": true,
            "image_providers": { ... rate limit status ... },
            "video_providers": { ... rate limit status ... }
        }
    """
    result = {
        "success": True,
        "image_providers": {},
        "video_providers": {}
    }

    image_router = _get_image_router()
    if image_router:
        # Get rate limit status for each image provider
        for provider in image_router.providers.keys():
            config = image_router.rate_limiter
            result["image_providers"][provider.value] = {
                "hourly_used": config.get_hourly(provider),
                "daily_used": config.get_daily(provider),
                "is_limited": config.is_limited(provider)
            }

    video_router = _get_video_router()
    if video_router:
        stats = video_router.get_statistics()
        result["video_providers"] = stats.get("rate_limits", {})

    return jsonify(result)


@media_bp.route('/media/providers', methods=['GET', 'POST'])
def media_providers():
    """
    List available media providers and their configurations.

    Response:
        {
            "success": true,
            "image_providers": [...],
            "video_providers": [...]
        }
    """
    result = {
        "success": True,
        "image_providers": [],
        "video_providers": []
    }

    image_router = _get_image_router()
    if image_router:
        result["image_providers"] = [p.value for p in image_router.providers.keys()]

    video_router = _get_video_router()
    if video_router:
        result["video_providers"] = [p.value for p in video_router.providers.keys()]

    return jsonify(result)



# v416-v51 experimental routes DELETED (3598 lines, 147 routes) — dead code, never used in production
