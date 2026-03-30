#!/usr/bin/env python3
"""
AI Systems Tower - Flask API Server

Independent Flask app with 7 blueprint modules covering 95 routes.
Extracted and refactored from monolithic agent_bridge_api.py.

Run: python -m projects.ai_systems.src.app
Port: 5013

Modules:
  cost_tracking  (5 routes)  /cost/*
  memory         (5 routes)  /memory/*
  orchestration  (12 routes) /templates/*, /orchestration/*, /scheduler/*
  knowledge      (5 routes)  /kb/*
  plugins        (7 routes)  /plugins/*
  intelligence   (45 routes) /learning/*, /recording/*, /context/*, /agents/*,
                             /personas/*, /goals/*, /macros/*, /audit/*
  media          (16 routes) /behavior/*, /media/*, /error/*, /notify/*, /agent/*
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    """Create the AI Systems Flask application with all blueprints."""
    from flask import Flask, jsonify

    app = Flask(__name__)

    # Register all 8 blueprint modules
    from .cost_tracking import cost_tracking_bp
    from .memory import memory_bp
    from .orchestration import orchestration_bp
    from .knowledge import knowledge_bp
    from .plugins import plugins_bp
    from .intelligence import intelligence_bp
    from .media import media_bp
    from .state_summary import state_summary_bp

    app.register_blueprint(cost_tracking_bp)
    app.register_blueprint(memory_bp)
    app.register_blueprint(orchestration_bp)
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(plugins_bp)
    app.register_blueprint(intelligence_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(state_summary_bp)

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            "tower": "ai-systems",
            "status": "healthy",
            "version": "1.3.0",
            "modules": {
                "cost_tracking": 5,
                "memory": 5,
                "orchestration": 12,
                "knowledge": 5,
                "plugins": 7,
                "intelligence": 45,
                "media": 16,
                "state_summary": 1,
            },
            "total_routes": 96,
        })

    return app


if __name__ == '__main__':
    port = int(os.getenv('AI_TOWER_PORT', 5013))
    logger.info(f"AI Systems Tower starting on port {port}")
    application = create_app()
    application.run(host='0.0.0.0', port=port, debug=False)
