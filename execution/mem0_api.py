"""
Mem0 Shared Memory API — Lightweight REST server for cross-agent memory.

Runs on EC2 at localhost:5020. All three agents (Claude Code, Clawdbot, Ralph)
can store and retrieve memories through this API.

Uses ChromaDB for vector storage (local files, no external DB needed).
Requires: pip install mem0ai fastapi uvicorn

Endpoints:
  GET  /health              - Health check
  POST /memory              - Add a memory
  GET  /memory/search       - Search memories by query
  GET  /memory/all          - List all memories (optional agent_id filter)
  DELETE /memory/{memory_id} - Delete a memory

Run: uvicorn execution.mem0_api:app --host 0.0.0.0 --port 5020
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException, Query
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("Missing dependencies. Run: pip install fastapi uvicorn")
    sys.exit(1)

try:
    from mem0 import Memory
    from mem0.llms.anthropic import AnthropicLLM
except ImportError:
    print("Missing mem0. Run: pip install mem0ai")
    sys.exit(1)


# Monkey-patch: Anthropic API rejects requests with both temperature and top_p.
# Mem0's LLMBase._get_common_params() returns both from config defaults.
# Fix: override _get_common_params to drop top_p for Anthropic.
_orig_get_common_params = AnthropicLLM._get_common_params
def _patched_get_common_params(self, **kwargs):
    params = _orig_get_common_params(self, **kwargs)
    params.pop("top_p", None)
    return params
AnthropicLLM._get_common_params = _patched_get_common_params

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mem0-api")

# --- Configuration ---
MEM0_DB_PATH = os.environ.get("MEM0_DB_PATH", os.path.expanduser("~/.mem0/chroma_db"))

config = {
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "agent_memory",
            "path": MEM0_DB_PATH,
        },
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "all-MiniLM-L6-v2",
        },
    },
    "llm": {
        "provider": "anthropic",
        "config": {
            "model": "claude-haiku-4-5-20251001",
            "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
        },
    },
    "version": "v1.1",
}

# Initialize memory
os.makedirs(MEM0_DB_PATH, exist_ok=True)
memory = Memory.from_config(config)

app = FastAPI(title="Mem0 Agent Memory API", version="1.0.0")


# --- Models ---
class AddMemoryRequest(BaseModel):
    agent_id: str  # claude-code, clawdbot, ralph
    content: str
    metadata: Optional[dict] = None


class AddMemoryResponse(BaseModel):
    success: bool
    memory_id: Optional[str] = None
    message: str


# --- Endpoints ---
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "mem0-api",
        "timestamp": datetime.utcnow().isoformat(),
        "db_path": MEM0_DB_PATH,
    }


@app.post("/memory", response_model=AddMemoryResponse)
def add_memory(req: AddMemoryRequest):
    """Add a memory for an agent."""
    try:
        meta = req.metadata or {}
        meta["agent_id"] = req.agent_id
        meta["added_at"] = datetime.utcnow().isoformat()

        result = memory.add(req.content, user_id=req.agent_id, metadata=meta)

        memory_id = None
        if isinstance(result, dict) and "results" in result:
            results = result["results"]
            if results and len(results) > 0:
                memory_id = results[0].get("id")
        elif isinstance(result, list) and len(result) > 0:
            memory_id = result[0].get("id") if isinstance(result[0], dict) else str(result[0])

        return AddMemoryResponse(
            success=True,
            memory_id=memory_id,
            message=f"Memory added for {req.agent_id}",
        )
    except Exception as e:
        logger.error(f"Failed to add memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/search")
def search_memory(
    q: str = Query(..., description="Search query"),
    agent_id: Optional[str] = Query(None, description="Filter by agent"),
    limit: int = Query(5, description="Max results"),
):
    """Search memories by semantic similarity."""
    try:
        kwargs = {"query": q, "limit": limit}
        if agent_id:
            kwargs["user_id"] = agent_id

        results = memory.search(**kwargs)

        memories = []
        if isinstance(results, dict) and "results" in results:
            raw = results["results"]
        elif isinstance(results, list):
            raw = results
        else:
            raw = []

        for item in raw[:limit]:
            if isinstance(item, dict):
                memories.append({
                    "id": item.get("id"),
                    "content": item.get("memory", item.get("text", "")),
                    "score": item.get("score", 0),
                    "metadata": item.get("metadata", {}),
                })

        return {"results": memories, "count": len(memories), "query": q}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/all")
def list_memories(
    agent_id: Optional[str] = Query(None, description="Filter by agent"),
    user_id: Optional[str] = Query(None, description="Filter by user (alias for agent_id)"),
    limit: int = Query(50, description="Max results"),
):
    """List all memories, optionally filtered by agent/user."""
    try:
        effective_id = agent_id or user_id
        if not effective_id:
            raise HTTPException(
                status_code=400,
                detail="agent_id or user_id query parameter is required",
            )

        results = memory.get_all(user_id=effective_id)

        memories = []
        if isinstance(results, dict) and "results" in results:
            raw = results["results"]
        elif isinstance(results, list):
            raw = results
        else:
            raw = []

        for item in raw[:limit]:
            if isinstance(item, dict):
                memories.append({
                    "id": item.get("id"),
                    "content": item.get("memory", item.get("text", "")),
                    "metadata": item.get("metadata", {}),
                })

        return {"memories": memories, "count": len(memories)}
    except Exception as e:
        logger.error(f"List failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memory/{memory_id}")
def delete_memory(memory_id: str):
    """Delete a specific memory."""
    try:
        memory.delete(memory_id)
        return {"success": True, "message": f"Memory {memory_id} deleted"}
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.environ.get("MEM0_PORT", 5020))
    uvicorn.run(app, host="0.0.0.0", port=port)
