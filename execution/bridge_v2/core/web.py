"""Web fetch blueprint — /web/fetch"""

import time

from flask import Blueprint, jsonify, request
from execution.bridge_v2.app import (
    ErrorCode, make_error, make_success, validate_path, truncate_output,
    track_request,
)

web_bp = Blueprint('web', __name__)


@web_bp.route('/web/fetch', methods=['POST'])
def web_fetch():
    """Fetch content from a URL."""
    track_request('web/fetch')
    data = request.get_json() or {}
    url = data.get('url')
    method = data.get('method', 'GET').upper()
    headers = data.get('headers', {})
    body = data.get('body')
    timeout = min(data.get('timeout', 30), 60)  # Max 60 seconds
    extract_text = data.get('extract_text', True)

    if not url:
        return jsonify({"success": False, "error": "Missing 'url' parameter"}), 400

    # Validate URL
    if not url.startswith(('http://', 'https://')):
        return jsonify({"success": False, "error": "URL must start with http:// or https://"}), 400

    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return jsonify({
            "success": False,
            "error": "Required packages not installed: pip install requests beautifulsoup4"
        }), 500

    try:
        # Make request
        start_time = time.time()

        if method == 'GET':
            resp = requests.get(url, headers=headers, timeout=timeout)
        elif method == 'POST':
            resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        else:
            return jsonify({"success": False, "error": f"Unsupported method: {method}"}), 400

        duration_ms = int((time.time() - start_time) * 1000)

        # Get content
        content_type = resp.headers.get('Content-Type', '')

        if extract_text and 'text/html' in content_type:
            # Parse HTML and extract text
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()

            # Get text
            text = soup.get_text(separator='\n', strip=True)

            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = '\n'.join(lines)

            # Truncate if too long
            text, truncated = truncate_output(text, 50000)

            return jsonify({
                "success": True,
                "url": url,
                "status_code": resp.status_code,
                "content_type": content_type,
                "text": text,
                "duration_ms": duration_ms,
                "truncated": truncated
            })
        else:
            # Return raw content (truncated)
            content, truncated = truncate_output(resp.text, 50000)

            return jsonify({
                "success": True,
                "url": url,
                "status_code": resp.status_code,
                "content_type": content_type,
                "content": content,
                "duration_ms": duration_ms,
                "truncated": truncated
            })

    except requests.Timeout:
        return make_error(
            ErrorCode.REQUEST_TIMEOUT,
            f"Request to {url} timed out after {timeout} seconds",
            status=504,
            context={"url": url, "method": method, "timeout_seconds": timeout}
        )
    except requests.ConnectionError as e:
        return make_error(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to connect to {url}: {str(e)}",
            status=502,
            context={"url": url, "method": method, "error_type": "connection_error"}
        )
    except requests.RequestException as e:
        return make_error(
            ErrorCode.INTERNAL_ERROR,
            f"Request failed: {str(e)}",
            status=500,
            context={"url": url, "method": method, "error_type": type(e).__name__}
        )
    except Exception as e:
        return make_error(
            ErrorCode.INTERNAL_ERROR,
            f"Unexpected error fetching URL: {str(e)}",
            status=500,
            context={"url": url, "method": method, "error_type": type(e).__name__},
            include_tb=True
        )
