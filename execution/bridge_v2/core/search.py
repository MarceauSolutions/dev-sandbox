"""Search operations blueprint — /search/grep, /search/web"""

import json
import subprocess

from flask import Blueprint, jsonify, request
from execution.bridge_v2.app import (
    ErrorCode, make_error, make_success, validate_path, truncate_output,
    ALLOWED_BASE_PATHS,
    track_request,
)

search_bp = Blueprint('search', __name__)


@search_bp.route('/search/grep', methods=['POST'])
def search_grep():
    """Search file contents using ripgrep or grep."""
    track_request('search/grep')
    data = request.get_json() or {}
    pattern = data.get('pattern')
    path = data.get('path', ALLOWED_BASE_PATHS[0])
    file_type = data.get('type')  # e.g., 'py', 'js', 'ts'
    glob_pattern = data.get('glob')  # e.g., '*.py', '**/*.ts'
    context_before = data.get('context_before', 0)  # -B
    context_after = data.get('context_after', 0)  # -A
    context = data.get('context', 0)  # -C (both before and after)
    case_insensitive = data.get('case_insensitive', False)
    max_results = min(data.get('max_results', 100), 500)
    output_mode = data.get('output_mode', 'content')  # 'content', 'files_only', 'count'

    if not pattern:
        return jsonify({"success": False, "error": "Missing 'pattern' parameter"}), 400

    # Validate path
    valid, resolved_path = validate_path(path)
    if not valid:
        return jsonify({"success": False, "error": resolved_path}), 403

    try:
        # Build grep/rg command
        # Prefer ripgrep if available, fallback to grep
        rg_available = subprocess.run(['which', 'rg'], capture_output=True).returncode == 0

        if rg_available:
            cmd = ['rg', '--json' if output_mode == 'content' else '-l']
            if case_insensitive:
                cmd.append('-i')
            if context > 0:
                cmd.extend(['-C', str(context)])
            else:
                if context_before > 0:
                    cmd.extend(['-B', str(context_before)])
                if context_after > 0:
                    cmd.extend(['-A', str(context_after)])
            if file_type:
                cmd.extend(['--type', file_type])
            if glob_pattern:
                cmd.extend(['--glob', glob_pattern])
            cmd.extend(['-m', str(max_results)])  # Max matches
            cmd.append(pattern)
            cmd.append(resolved_path)
        else:
            # Fallback to grep
            cmd = ['grep', '-r', '-n']
            if case_insensitive:
                cmd.append('-i')
            if context > 0:
                cmd.extend(['-C', str(context)])
            else:
                if context_before > 0:
                    cmd.extend(['-B', str(context_before)])
                if context_after > 0:
                    cmd.extend(['-A', str(context_after)])
            if output_mode == 'files_only':
                cmd.append('-l')
            cmd.append(pattern)
            cmd.append(resolved_path)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse results
        matches = []
        if rg_available and output_mode == 'content':
            # Parse ripgrep JSON output
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    if item.get('type') == 'match':
                        match_data = item.get('data', {})
                        matches.append({
                            "file": match_data.get('path', {}).get('text', ''),
                            "line_number": match_data.get('line_number'),
                            "text": match_data.get('lines', {}).get('text', '').rstrip()
                        })
                except json.JSONDecodeError:
                    continue
        elif output_mode == 'files_only':
            matches = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        else:
            # Parse standard grep output
            for line in result.stdout.strip().split('\n')[:max_results]:
                if not line:
                    continue
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    matches.append({
                        "file": parts[0],
                        "line_number": int(parts[1]) if parts[1].isdigit() else None,
                        "text": parts[2]
                    })

        output, truncated = truncate_output(result.stdout)

        return jsonify({
            "success": True,
            "pattern": pattern,
            "path": resolved_path,
            "matches": matches[:max_results],
            "match_count": len(matches),
            "truncated": truncated or len(matches) > max_results,
            "tool": "ripgrep" if rg_available else "grep"
        })

    except subprocess.TimeoutExpired:
        return make_error(
            ErrorCode.SEARCH_TIMEOUT,
            "Search timed out after 60 seconds",
            status=504,
            context={
                "pattern": pattern,
                "path": resolved_path,
                "suggestion": "Try a more specific pattern or narrow the search path"
            }
        )
    except Exception as e:
        return make_error(
            ErrorCode.INTERNAL_ERROR,
            f"Search error: {str(e)}",
            status=500,
            context={"pattern": pattern, "path": resolved_path, "error_type": type(e).__name__},
            include_tb=True
        )


@search_bp.route('/search/web', methods=['POST'])
def search_web():
    """Search the web using DuckDuckGo or configured search API."""
    track_request('search/web')
    data = request.get_json() or {}
    query = data.get('query')
    max_results = min(data.get('max_results', 10), 20)
    search_type = data.get('type', 'web')  # 'web', 'news', 'images'

    if not query:
        return jsonify({"success": False, "error": "Missing 'query' parameter"}), 400

    try:
        # Try DuckDuckGo HTML search (no API key needed)
        import requests
        from bs4 import BeautifulSoup
        import urllib.parse

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # DuckDuckGo HTML search
        encoded_query = urllib.parse.quote_plus(query)
        url = f'https://html.duckduckgo.com/html/?q={encoded_query}'

        resp = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')

        results = []
        for result in soup.select('.result')[:max_results]:
            title_elem = result.select_one('.result__title')
            snippet_elem = result.select_one('.result__snippet')
            link_elem = result.select_one('.result__url')

            if title_elem:
                title = title_elem.get_text(strip=True)
                link = ''
                if link_elem:
                    link = link_elem.get_text(strip=True)
                    if not link.startswith('http'):
                        link = 'https://' + link
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                results.append({
                    "title": title,
                    "url": link,
                    "snippet": snippet
                })

        return jsonify({
            "success": True,
            "query": query,
            "results": results,
            "count": len(results),
            "source": "duckduckgo"
        })

    except ImportError:
        return jsonify({
            "success": False,
            "error": "Required packages not installed: pip install requests beautifulsoup4"
        }), 500
    except requests.Timeout:
        return jsonify({
            "success": False,
            "error": "Search timed out after 30 seconds"
        }), 504
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
