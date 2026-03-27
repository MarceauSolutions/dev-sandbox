"""
AI Systems Tower - Knowledge Bases And Rag (Retrieval-Augmented Generation)

Knowledge bases and RAG (retrieval-augmented generation).
Extracted from monolithic agent_bridge_api.py, refactored into Flask blueprint.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify

from .models import (
    KNOWLEDGE_BASES,
    KnowledgeBase,
    FileIndex,
)

knowledge_bp = Blueprint('knowledge', __name__)


@knowledge_bp.route('/kb/create', methods=['POST'])
def kb_create():
    """Create a new knowledge base."""
    data = request.get_json() or {}
    name = data.get('name')
    root_paths = data.get('root_paths', [])
    description = data.get('description', '')
    include_patterns = data.get('include_patterns')
    exclude_patterns = data.get('exclude_patterns')

    if not name:
        return jsonify({"success": False, "error": "Missing 'name' parameter"}), 400
    if not root_paths:
        return jsonify({"success": False, "error": "Missing 'root_paths' parameter"}), 400

    # Validate paths
    for path in root_paths:
        if not validate_path(path):
            return jsonify({"success": False, "error": f"Path not allowed: {path}"}), 403

    kb = create_knowledge_base(
        name=name,
        root_paths=root_paths,
        description=description,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns
    )

    return jsonify({
        "success": True,
        **kb.to_dict()
    })


@knowledge_bp.route('/kb/list', methods=['GET', 'POST'])
def kb_list():
    """List all knowledge bases."""
    kbs = [kb.to_dict() for kb in KNOWLEDGE_BASES.values()]
    return jsonify({
        "success": True,
        "knowledge_bases": kbs,
        "total": len(kbs)
    })


@knowledge_bp.route('/kb/index', methods=['POST'])
def kb_index():
    """Index files into a knowledge base."""
    import glob as glob_module

    data = request.get_json() or {}
    kb_id = data.get('kb_id')
    max_files = data.get('max_files', 100)

    if not kb_id:
        return jsonify({"success": False, "error": "Missing 'kb_id' parameter"}), 400

    if kb_id not in KNOWLEDGE_BASES:
        return jsonify({"success": False, "error": f"Knowledge base not found: {kb_id}"}), 404

    kb = KNOWLEDGE_BASES[kb_id]
    indexed_count = 0
    errors = []

    for root_path in kb.root_paths:
        for pattern in kb.include_patterns:
            full_pattern = os.path.join(root_path, pattern)
            for file_path in glob_module.glob(full_pattern, recursive=True)[:max_files]:
                # Check exclude patterns
                skip = False
                for exclude in kb.exclude_patterns:
                    if exclude.replace('**/', '') in file_path:
                        skip = True
                        break
                if skip:
                    continue

                result = index_file(kb, file_path)
                if result:
                    indexed_count += 1
                else:
                    errors.append(file_path)

    return jsonify({
        "success": True,
        "kb_id": kb_id,
        "indexed_files": indexed_count,
        "total_files": len(kb.files),
        "total_chunks": kb.total_chunks,
        "errors": errors[:10]  # Limit errors in response
    })


@knowledge_bp.route('/kb/search', methods=['POST'])
def kb_search():
    """Search a knowledge base."""
    data = request.get_json() or {}
    kb_id = data.get('kb_id')
    query = data.get('query')
    top_k = min(data.get('top_k', 5), 20)

    if not kb_id:
        return jsonify({"success": False, "error": "Missing 'kb_id' parameter"}), 400
    if not query:
        return jsonify({"success": False, "error": "Missing 'query' parameter"}), 400

    if kb_id not in KNOWLEDGE_BASES:
        return jsonify({"success": False, "error": f"Knowledge base not found: {kb_id}"}), 404

    kb = KNOWLEDGE_BASES[kb_id]
    results = search_knowledge_base(kb, query, top_k)

    return jsonify({
        "success": True,
        "query": query,
        "results": results,
        "total_results": len(results)
    })


@knowledge_bp.route('/kb/delete', methods=['POST'])
def kb_delete():
    """Delete a knowledge base."""
    data = request.get_json() or {}
    kb_id = data.get('kb_id')

    if not kb_id:
        return jsonify({"success": False, "error": "Missing 'kb_id' parameter"}), 400

    if kb_id not in KNOWLEDGE_BASES:
        return jsonify({"success": False, "error": f"Knowledge base not found: {kb_id}"}), 404

    del KNOWLEDGE_BASES[kb_id]

    return jsonify({
        "success": True,
        "deleted": kb_id
    })
