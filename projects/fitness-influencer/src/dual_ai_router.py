#!/usr/bin/env python3
"""
dual_ai_router.py - Dual-AI Decision Router (Claude + XAI/Grok)

Combines Claude (for conversation/intent) and XAI/Grok (for cost optimization)
to make intelligent, cost-effective decisions for fitness influencer workflows.

Architecture:
    User Message → Claude (understand intent, select tool)
                 → Grok (validate, optimize cost)
                 → Execute tool
                 → Return result

Cost Guardrails:
    - Operations >$0.10 require confirmation
    - Suggests cheaper alternatives when available
    - Tracks session costs

Usage:
    from dual_ai_router import DualAIRouter
    router = DualAIRouter()
    result = router.process_request("Create a video ad for my program")
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import anthropic
import requests
from dotenv import load_dotenv

load_dotenv()


class CostTier(Enum):
    FREE = "free"
    LOW = "low"      # < $0.10
    MEDIUM = "medium"  # $0.10 - $0.30
    HIGH = "high"    # > $0.30


@dataclass
class ToolDecision:
    """Represents the AI team's decision on which tool to use."""
    tool_name: str
    tool_input: Dict[str, Any]
    estimated_cost: float
    cost_tier: CostTier
    alternatives: List[Dict[str, Any]]  # Cheaper alternatives if available
    requires_confirmation: bool
    explanation: str


@dataclass
class CostBreakdown:
    """Cost breakdown for an operation."""
    total: float
    components: Dict[str, float]
    tier: CostTier


# Tool cost registry
TOOL_COSTS = {
    "edit_video": {"base": 0.0, "per_unit": 0.0, "tier": CostTier.FREE},
    "create_graphic": {"base": 0.0, "per_unit": 0.0, "tier": CostTier.FREE},
    "generate_ai_image": {"base": 0.0, "per_unit": 0.07, "tier": CostTier.LOW},
    "create_video_ad": {"base": 0.06, "per_unit": 0.07, "images": 4, "tier": CostTier.MEDIUM},
    "summarize_emails": {"base": 0.0, "per_unit": 0.0, "tier": CostTier.FREE},
    "revenue_report": {"base": 0.0, "per_unit": 0.0, "tier": CostTier.FREE},
    "create_workout_plan": {"base": 0.0, "per_unit": 0.0, "tier": CostTier.FREE},
    "create_nutrition_guide": {"base": 0.0, "per_unit": 0.0, "tier": CostTier.FREE},
}

# Confirmation threshold
CONFIRMATION_THRESHOLD = 0.10  # $0.10


class DualAIRouter:
    """
    Dual-AI router that combines Claude and Grok for intelligent decision-making.

    Claude handles:
    - Natural language understanding
    - Intent classification
    - Tool selection
    - Conversation flow

    Grok handles:
    - Image generation
    - Cost optimization suggestions
    - Alternative recommendations
    """

    def __init__(self):
        # Initialize Claude
        self.claude = None
        if os.getenv("ANTHROPIC_API_KEY"):
            self.claude = anthropic.Anthropic()

        # Initialize Grok
        self.grok_api_key = os.getenv("XAI_API_KEY")
        self.grok_url = "https://api.x.ai/v1/chat/completions"

        # Session cost tracking
        self.session_costs = 0.0
        self.operation_history = []

        # Tool definitions for Claude
        self.tools = self._define_tools()

    def _define_tools(self) -> List[Dict]:
        """Define tools for Claude's function calling."""
        return [
            {
                "name": "edit_video",
                "description": "Remove silence and create jump cuts in a video. FREE operation.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "silence_threshold": {
                            "type": "number",
                            "description": "Silence threshold in dB (default -40)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "create_graphic",
                "description": "Create educational fitness graphics for social media. FREE operation.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "points": {"type": "array", "items": {"type": "string"}},
                        "platform": {
                            "type": "string",
                            "enum": ["instagram_post", "instagram_story", "youtube_thumbnail"]
                        }
                    },
                    "required": ["title", "points"]
                }
            },
            {
                "name": "generate_ai_image",
                "description": "Generate AI images using Grok. COSTS $0.07 per image.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "count": {"type": "integer", "default": 1, "maximum": 4}
                    },
                    "required": ["prompt"]
                }
            },
            {
                "name": "create_video_ad",
                "description": "Create video ad with AI images. COSTS $0.34 (4 images + video).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "theme": {"type": "string"},
                        "cta": {"type": "string"},
                        "handle": {"type": "string"},
                        "image_count": {"type": "integer", "default": 4, "minimum": 2, "maximum": 6}
                    },
                    "required": ["theme"]
                }
            },
            {
                "name": "summarize_emails",
                "description": "Summarize and categorize inbox emails. FREE operation.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "hours_back": {"type": "integer", "default": 24}
                    },
                    "required": []
                }
            },
            {
                "name": "revenue_report",
                "description": "Generate revenue analytics report. FREE operation.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "month": {"type": "string"}
                    },
                    "required": []
                }
            },
            {
                "name": "create_workout_plan",
                "description": "Generate personalized workout plan. FREE operation.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "goal": {"type": "string", "enum": ["muscle_building", "fat_loss", "strength", "endurance"]},
                        "days_per_week": {"type": "integer", "default": 4},
                        "experience": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]}
                    },
                    "required": ["goal"]
                }
            },
            {
                "name": "create_nutrition_guide",
                "description": "Create personalized nutrition guide. FREE operation.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "weight_lbs": {"type": "number"},
                        "goal": {"type": "string", "enum": ["fat_loss", "muscle_gain", "maintenance"]},
                        "activity_level": {"type": "string"}
                    },
                    "required": ["weight_lbs", "goal"]
                }
            }
        ]

    def _calculate_cost(self, tool_name: str, tool_input: Dict[str, Any]) -> CostBreakdown:
        """Calculate the cost of a tool operation."""
        cost_info = TOOL_COSTS.get(tool_name, {"base": 0.0, "per_unit": 0.0, "tier": CostTier.FREE})

        components = {}
        total = cost_info["base"]

        if tool_name == "generate_ai_image":
            count = tool_input.get("count", 1)
            image_cost = count * cost_info["per_unit"]
            components["images"] = image_cost
            total = image_cost

        elif tool_name == "create_video_ad":
            image_count = tool_input.get("image_count", 4)
            image_cost = image_count * 0.07
            video_cost = 0.06
            components["images"] = image_cost
            components["video"] = video_cost
            total = image_cost + video_cost

        # Determine tier
        if total == 0:
            tier = CostTier.FREE
        elif total < 0.10:
            tier = CostTier.LOW
        elif total < 0.30:
            tier = CostTier.MEDIUM
        else:
            tier = CostTier.HIGH

        return CostBreakdown(total=total, components=components, tier=tier)

    def _get_alternatives(self, tool_name: str, tool_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get cheaper alternatives for an operation."""
        alternatives = []

        if tool_name == "create_video_ad":
            current_images = tool_input.get("image_count", 4)

            if current_images > 2:
                # Budget option
                budget_cost = 2 * 0.07 + 0.06
                alternatives.append({
                    "name": "Budget (2 images)",
                    "cost": budget_cost,
                    "input": {**tool_input, "image_count": 2}
                })

            if current_images < 6:
                # Premium option
                premium_cost = 6 * 0.07 + 0.06
                alternatives.append({
                    "name": "Premium (6 images)",
                    "cost": premium_cost,
                    "input": {**tool_input, "image_count": 6}
                })

        elif tool_name == "generate_ai_image":
            current_count = tool_input.get("count", 1)

            if current_count > 1:
                alternatives.append({
                    "name": f"Single image",
                    "cost": 0.07,
                    "input": {**tool_input, "count": 1}
                })

            if current_count < 4:
                alternatives.append({
                    "name": "4 images (batch)",
                    "cost": 0.28,
                    "input": {**tool_input, "count": 4}
                })

        return alternatives

    def _call_grok_for_optimization(self, tool_name: str, tool_input: Dict[str, Any], cost: float) -> Optional[str]:
        """
        Call Grok to validate and potentially optimize the decision.
        Only used for paid operations to get cost optimization suggestions.
        """
        if not self.grok_api_key or cost == 0:
            return None

        try:
            prompt = f"""You are a cost optimization assistant. A fitness influencer is about to run:

Tool: {tool_name}
Input: {json.dumps(tool_input)}
Estimated Cost: ${cost:.2f}

Briefly confirm this is the right choice OR suggest a more cost-effective alternative.
Keep response under 50 words."""

            response = requests.post(
                self.grok_url,
                headers={
                    "Authorization": f"Bearer {self.grok_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "grok-2-latest",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 100
                },
                timeout=10
            )

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Grok optimization call failed: {e}")

        return None

    def process_request(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        skip_confirmation: bool = False
    ) -> Dict[str, Any]:
        """
        Process a user request using the dual-AI system.

        Args:
            message: User's message
            history: Conversation history
            skip_confirmation: Skip cost confirmation (for pre-approved requests)

        Returns:
            Dict with:
            - decision: ToolDecision object
            - response: Text response for user
            - requires_confirmation: Whether to confirm before executing
        """
        if not self.claude:
            return {
                "error": "Claude API not configured",
                "response": "I'm sorry, the AI service is not configured. Please check the API keys."
            }

        # Build messages
        messages = []
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": message})

        # System prompt
        system = """You are a helpful AI assistant for fitness influencers. Help them with:
- Content creation (video editing, graphics, AI images, video ads)
- Business management (email summaries, revenue analytics)
- Fitness planning (workout plans, nutrition guides)

IMPORTANT: Always mention the cost for paid operations:
- AI Images: $0.07 each
- Video Ads: $0.34 (4 images + video)
- Everything else: FREE

Be concise and helpful. Use tools when appropriate."""

        try:
            # Call Claude for intent understanding and tool selection
            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system,
                tools=self.tools,
                messages=messages
            )

            # Process response
            text_response = ""
            tool_decision = None

            for block in response.content:
                if block.type == "text":
                    text_response += block.text
                elif block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    # Calculate cost
                    cost = self._calculate_cost(tool_name, tool_input)

                    # Get alternatives
                    alternatives = self._get_alternatives(tool_name, tool_input)

                    # Check if confirmation needed
                    requires_confirmation = (
                        cost.total >= CONFIRMATION_THRESHOLD and
                        not skip_confirmation
                    )

                    # Get Grok's optimization suggestion for paid ops
                    grok_suggestion = None
                    if cost.total > 0:
                        grok_suggestion = self._call_grok_for_optimization(
                            tool_name, tool_input, cost.total
                        )

                    tool_decision = ToolDecision(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        estimated_cost=cost.total,
                        cost_tier=cost.tier,
                        alternatives=alternatives,
                        requires_confirmation=requires_confirmation,
                        explanation=grok_suggestion or ""
                    )

            return {
                "decision": tool_decision,
                "response": text_response,
                "requires_confirmation": tool_decision.requires_confirmation if tool_decision else False,
                "session_total": self.session_costs
            }

        except Exception as e:
            return {
                "error": str(e),
                "response": f"I encountered an error: {str(e)}"
            }

    def confirm_and_execute(self, decision: ToolDecision) -> Dict[str, Any]:
        """
        Execute a confirmed operation and track costs.

        Args:
            decision: The approved ToolDecision

        Returns:
            Execution result
        """
        # Track cost
        self.session_costs += decision.estimated_cost
        self.operation_history.append({
            "tool": decision.tool_name,
            "cost": decision.estimated_cost,
            "input": decision.tool_input
        })

        # Return execution info (actual execution happens in chat_api.py)
        return {
            "execute": True,
            "tool_name": decision.tool_name,
            "tool_input": decision.tool_input,
            "cost": decision.estimated_cost,
            "session_total": self.session_costs
        }

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of session costs and operations."""
        return {
            "total_cost": self.session_costs,
            "operation_count": len(self.operation_history),
            "operations": self.operation_history
        }


# Singleton instance
_router_instance = None

def get_router() -> DualAIRouter:
    """Get or create the dual AI router instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = DualAIRouter()
    return _router_instance


if __name__ == "__main__":
    # Test the router
    router = DualAIRouter()

    test_messages = [
        "Edit my video and remove silence",
        "Create a fitness tip graphic about protein",
        "Generate 2 AI images for my promotion",
        "Create a video ad for my summer program",
    ]

    for msg in test_messages:
        print(f"\n{'='*60}")
        print(f"Request: {msg}")
        result = router.process_request(msg)
        print(f"Response: {result.get('response', '')[:100]}...")
        if result.get("decision"):
            d = result["decision"]
            print(f"Tool: {d.tool_name}")
            print(f"Cost: ${d.estimated_cost:.2f} ({d.cost_tier.value})")
            print(f"Needs confirmation: {d.requires_confirmation}")
