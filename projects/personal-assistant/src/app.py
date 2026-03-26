#!/usr/bin/env python3
"""
Personal Assistant Tower API Server
Provides email and communication services.
"""

from flask import Flask
from flask_cors import CORS
from .api.gmail import gmail_bp

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)

    # Register blueprints
    app.register_blueprint(gmail_bp)

    @app.route('/health')
    def health():
        """Tower health check."""
        return {
            'status': 'healthy',
            'tower': 'personal-assistant',
            'services': ['gmail']
        }

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5011, debug=True)