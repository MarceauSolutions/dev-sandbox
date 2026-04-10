#!/usr/bin/env python3
"""
Amazon Seller Tower - Flask API Server

Minimal entry point for tower independence.
Exposes health check and SP-API status.

Port: 5014
Status: Dormant (no active Amazon business)
"""

import os
import logging
from flask import Flask, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            "tower": "amazon-seller",
            "status": "dormant",
            "version": "1.0.0-dev",
            "note": "No active Amazon SKUs. Tower activates when selling begins.",
            "capabilities": ["calculate_fees", "check_inventory"],
        })

    @app.route('/fees/calculate', methods=['POST'])
    def calculate_fees():
        """Calculate FBA fees for a product — callable via tower_protocol."""
        from flask import request
        data = request.get_json() or {}
        try:
            from .amazon_fee_calculator import FBAFeeCalculator
            calc = FBAFeeCalculator()
            result = calc.calculate(
                asin=data.get("asin", ""),
                price=float(data.get("price", 0)),
                cost=float(data.get("cost", 0)),
            )
            return jsonify({"success": True, **result})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})

    return app


if __name__ == '__main__':
    port = int(os.getenv('AS_TOWER_PORT', 5014))
    logger.info(f"Amazon Seller Tower starting on port {port}")
    create_app().run(host='0.0.0.0', port=port, debug=False)
