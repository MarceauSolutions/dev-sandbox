#!/usr/bin/env python3
"""
Intelligent AI Router
Routes requests between Claude (Anthropic) and Grok (xAI) based on task type and cost optimization.

Architecture:
1. Claude Haiku handles intent detection (cheap, fast)
2. Based on intent, routes to appropriate service:
   - Image generation → xAI Grok ($0.07/image)
   - Text/reasoning → Claude (tiered by complexity)
   - Simple responses → Claude Haiku ($0.001)
   - Complex analysis → Claude Sonnet ($0.01)

Cost Optimization Strategy:
- Use Haiku for routing decisions (~$0.0002 per request)
- Use Haiku for simple text responses (~$0.001)
- Use Sonnet only for complex reasoning (~$0.01)
- Use xAI for all image generation ($0.07)
"""

import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import anthropic
import requests


class TaskType(Enum):
    """Types of tasks the router can handle."""
    IMAGE_GENERATION = "image_generation"
    VIDEO_EDITING = "video_editing"
    GRAPHIC_CREATION = "graphic_creation"
    TEXT_RESPONSE = "text_response"
    COMPLEX_ANALYSIS = "complex_analysis"
    EMAIL_DIGEST = "email_digest"
    REVENUE_ANALYTICS = "revenue_analytics"
    AD_CREATION = "ad_creation"
    UNKNOWN = "unknown"


class AIProvider(Enum):
    """Available AI providers."""
    CLAUDE_HAIKU = "claude-3-5-haiku-20241022"
    CLAUDE_SONNET = "claude-sonnet-4-20250514"
    XAI_GROK = "grok-2-image-1212"


@dataclass
class RoutingDecision:
    """Result of the routing decision."""
    task_type: TaskType
    provider: AIProvider
    enhanced_prompt: str
    confidence: float
    estimated_cost: float
    reasoning: str


@dataclass
class AIResponse:
    """Unified response from any AI provider."""
    success: bool
    content: Any  # Text, image URL, or structured data
    provider: str
    cost: float
    task_type: str
    error: Optional[str] = None


class AIRouter:
    """
    Intelligent router that decides which AI to use based on task and cost.
    """

    # Cost estimates (USD)
    COSTS = {
        "claude_haiku_input": 0.0000008,   # per token
        "claude_haiku_output": 0.000004,   # per token
        "claude_sonnet_input": 0.000003,   # per token
        "claude_sonnet_output": 0.000015,  # per token
        "xai_image": 0.07,                 # per image
    }

    def __init__(self):
        """Initialize the AI router with available API keys."""
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.xai_key = os.getenv('XAI_API_KEY')

        self.anthropic_client = None
        if self.anthropic_key:
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)

        # Track usage for cost reporting
        self.session_costs = {
            "claude_haiku": 0.0,
            "claude_sonnet": 0.0,
            "xai_grok": 0.0,
            "total": 0.0
        }

    def get_available_providers(self) -> Dict[str, bool]:
        """Check which AI providers are configured."""
        return {
            "anthropic": bool(self.anthropic_key),
            "xai": bool(self.xai_key),
        }

    async def route_request(self, user_message: str, context: Optional[Dict] = None) -> RoutingDecision:
        """
        Use Claude Haiku to intelligently route the request.

        Args:
            user_message: The user's input message
            context: Optional context (conversation history, user preferences, etc.)

        Returns:
            RoutingDecision with task type, provider, and enhanced prompt
        """
        if not self.anthropic_client:
            # Fallback to keyword-based routing if no Anthropic key
            return self._fallback_routing(user_message)

        routing_prompt = f"""Analyze this user request and determine the best way to handle it.

User Request: "{user_message}"

Available tools:
1. IMAGE_GENERATION - Create AI images (diagrams, charts, photos, visuals) - Cost: $0.07
2. VIDEO_EDITING - Edit videos with jump cuts - Requires video file
3. GRAPHIC_CREATION - Create branded social media graphics with text
4. TEXT_RESPONSE - Answer questions, provide advice, have conversations - Cost: ~$0.001
5. COMPLEX_ANALYSIS - Deep analysis, planning, multi-step reasoning - Cost: ~$0.01
6. EMAIL_DIGEST - Summarize emails - Requires email access
7. REVENUE_ANALYTICS - Analyze financial data - Requires spreadsheet
8. AD_CREATION - Create full advertisement packages

Respond in JSON format:
{{
    "task_type": "one of the types above",
    "confidence": 0.0-1.0,
    "enhanced_prompt": "if image generation, write an optimal prompt for the image. Otherwise, leave as the original request",
    "reasoning": "brief explanation of your routing decision",
    "needs_clarification": false,
    "clarification_question": null
}}

Important:
- For image requests, enhance the prompt to be detailed and specific for best results
- If the request is ambiguous, set needs_clarification to true
- Choose TEXT_RESPONSE for general questions and conversations
- Choose COMPLEX_ANALYSIS only for multi-step reasoning tasks"""

        try:
            response = self.anthropic_client.messages.create(
                model=AIProvider.CLAUDE_HAIKU.value,
                max_tokens=500,
                messages=[{"role": "user", "content": routing_prompt}]
            )

            # Parse the response
            content = response.content[0].text

            # Extract JSON from response
            try:
                # Handle potential markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                decision_data = json.loads(content.strip())
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract key info
                decision_data = {
                    "task_type": "TEXT_RESPONSE",
                    "confidence": 0.5,
                    "enhanced_prompt": user_message,
                    "reasoning": "Failed to parse routing response, defaulting to text"
                }

            # Map task type to enum
            task_type_str = decision_data.get("task_type", "UNKNOWN").upper()
            try:
                task_type = TaskType[task_type_str]
            except KeyError:
                task_type = TaskType.TEXT_RESPONSE

            # Determine provider based on task
            provider = self._select_provider(task_type)

            # Estimate cost
            estimated_cost = self._estimate_cost(task_type, user_message)

            # Track routing cost (Haiku)
            routing_cost = self._calculate_claude_cost(
                routing_prompt, content, is_haiku=True
            )
            self.session_costs["claude_haiku"] += routing_cost
            self.session_costs["total"] += routing_cost

            return RoutingDecision(
                task_type=task_type,
                provider=provider,
                enhanced_prompt=decision_data.get("enhanced_prompt", user_message),
                confidence=decision_data.get("confidence", 0.8),
                estimated_cost=estimated_cost,
                reasoning=decision_data.get("reasoning", "")
            )

        except Exception as e:
            print(f"Routing error: {e}")
            return self._fallback_routing(user_message)

    def _fallback_routing(self, message: str) -> RoutingDecision:
        """Keyword-based fallback routing when Claude isn't available."""
        lower = message.lower()

        if any(kw in lower for kw in ['generate', 'create', 'make']) and \
           any(kw in lower for kw in ['image', 'picture', 'diagram', 'chart', 'visual', 'photo']):
            return RoutingDecision(
                task_type=TaskType.IMAGE_GENERATION,
                provider=AIProvider.XAI_GROK,
                enhanced_prompt=message,
                confidence=0.7,
                estimated_cost=0.07,
                reasoning="Keyword match: image generation"
            )

        if 'video' in lower and any(kw in lower for kw in ['edit', 'cut', 'jump']):
            return RoutingDecision(
                task_type=TaskType.VIDEO_EDITING,
                provider=AIProvider.CLAUDE_HAIKU,
                enhanced_prompt=message,
                confidence=0.7,
                estimated_cost=0.001,
                reasoning="Keyword match: video editing"
            )

        # Default to text response
        return RoutingDecision(
            task_type=TaskType.TEXT_RESPONSE,
            provider=AIProvider.CLAUDE_HAIKU,
            enhanced_prompt=message,
            confidence=0.5,
            estimated_cost=0.001,
            reasoning="Default: text response"
        )

    def _select_provider(self, task_type: TaskType) -> AIProvider:
        """Select the best provider for a given task type."""
        provider_map = {
            TaskType.IMAGE_GENERATION: AIProvider.XAI_GROK,
            TaskType.VIDEO_EDITING: AIProvider.CLAUDE_HAIKU,  # Just orchestration
            TaskType.GRAPHIC_CREATION: AIProvider.CLAUDE_HAIKU,
            TaskType.TEXT_RESPONSE: AIProvider.CLAUDE_HAIKU,
            TaskType.COMPLEX_ANALYSIS: AIProvider.CLAUDE_SONNET,
            TaskType.EMAIL_DIGEST: AIProvider.CLAUDE_HAIKU,
            TaskType.REVENUE_ANALYTICS: AIProvider.CLAUDE_SONNET,
            TaskType.AD_CREATION: AIProvider.CLAUDE_SONNET,
            TaskType.UNKNOWN: AIProvider.CLAUDE_HAIKU,
        }
        return provider_map.get(task_type, AIProvider.CLAUDE_HAIKU)

    def _estimate_cost(self, task_type: TaskType, message: str) -> float:
        """Estimate the cost for a task."""
        if task_type == TaskType.IMAGE_GENERATION:
            return 0.07
        elif task_type in [TaskType.COMPLEX_ANALYSIS, TaskType.REVENUE_ANALYTICS, TaskType.AD_CREATION]:
            return 0.01
        else:
            return 0.001

    def _calculate_claude_cost(self, input_text: str, output_text: str, is_haiku: bool = True) -> float:
        """Calculate actual Claude API cost based on token estimates."""
        # Rough token estimate: 1 token ≈ 4 characters
        input_tokens = len(input_text) / 4
        output_tokens = len(output_text) / 4

        if is_haiku:
            return (input_tokens * self.COSTS["claude_haiku_input"] +
                    output_tokens * self.COSTS["claude_haiku_output"])
        else:
            return (input_tokens * self.COSTS["claude_sonnet_input"] +
                    output_tokens * self.COSTS["claude_sonnet_output"])

    async def execute_task(self, decision: RoutingDecision,
                           user_message: str,
                           files: Optional[List] = None) -> AIResponse:
        """
        Execute the task using the selected provider.

        Args:
            decision: The routing decision
            user_message: Original user message
            files: Optional uploaded files

        Returns:
            AIResponse with the result
        """
        try:
            if decision.task_type == TaskType.IMAGE_GENERATION:
                return await self._generate_image(decision.enhanced_prompt)

            elif decision.task_type == TaskType.TEXT_RESPONSE:
                return await self._text_response(user_message, decision.provider)

            elif decision.task_type == TaskType.COMPLEX_ANALYSIS:
                return await self._complex_analysis(user_message)

            else:
                # For other task types, return instructions
                return AIResponse(
                    success=True,
                    content=f"Task type '{decision.task_type.value}' identified. {decision.reasoning}",
                    provider=decision.provider.value,
                    cost=0.001,
                    task_type=decision.task_type.value
                )

        except Exception as e:
            return AIResponse(
                success=False,
                content=None,
                provider=decision.provider.value,
                cost=0.0,
                task_type=decision.task_type.value,
                error=str(e)
            )

    async def _generate_image(self, prompt: str) -> AIResponse:
        """Generate an image using xAI Grok."""
        if not self.xai_key:
            return AIResponse(
                success=False,
                content=None,
                provider="xai",
                cost=0.0,
                task_type="image_generation",
                error="XAI_API_KEY not configured"
            )

        try:
            response = requests.post(
                "https://api.x.ai/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {self.xai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt,
                    "n": 1,
                    "model": "grok-2-image-1212"
                },
                timeout=60
            )

            if response.status_code != 200:
                return AIResponse(
                    success=False,
                    content=None,
                    provider="xai",
                    cost=0.0,
                    task_type="image_generation",
                    error=f"xAI API error: {response.text}"
                )

            data = response.json()
            images = data.get('data', [])
            image_urls = [img.get('url') for img in images if img.get('url')]

            cost = len(image_urls) * 0.07
            self.session_costs["xai_grok"] += cost
            self.session_costs["total"] += cost

            return AIResponse(
                success=True,
                content={
                    "urls": image_urls,
                    "primary_url": image_urls[0] if image_urls else None,
                    "prompt_used": prompt
                },
                provider="xai_grok",
                cost=cost,
                task_type="image_generation"
            )

        except Exception as e:
            return AIResponse(
                success=False,
                content=None,
                provider="xai",
                cost=0.0,
                task_type="image_generation",
                error=str(e)
            )

    async def _text_response(self, message: str, provider: AIProvider) -> AIResponse:
        """Generate a text response using Claude."""
        if not self.anthropic_client:
            return AIResponse(
                success=False,
                content=None,
                provider="anthropic",
                cost=0.0,
                task_type="text_response",
                error="ANTHROPIC_API_KEY not configured"
            )

        system_prompt = """You are a helpful AI assistant for fitness influencers. You help with:
- Content creation ideas and strategies
- Fitness and nutrition advice
- Business and marketing guidance
- Social media optimization

Be concise, practical, and encouraging. Use emoji sparingly."""

        try:
            response = self.anthropic_client.messages.create(
                model=provider.value,
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": message}]
            )

            content = response.content[0].text
            is_haiku = provider == AIProvider.CLAUDE_HAIKU
            cost = self._calculate_claude_cost(message, content, is_haiku)

            if is_haiku:
                self.session_costs["claude_haiku"] += cost
            else:
                self.session_costs["claude_sonnet"] += cost
            self.session_costs["total"] += cost

            return AIResponse(
                success=True,
                content=content,
                provider=provider.value,
                cost=cost,
                task_type="text_response"
            )

        except Exception as e:
            return AIResponse(
                success=False,
                content=None,
                provider=provider.value,
                cost=0.0,
                task_type="text_response",
                error=str(e)
            )

    async def _complex_analysis(self, message: str) -> AIResponse:
        """Handle complex analysis tasks using Claude Sonnet."""
        return await self._text_response(message, AIProvider.CLAUDE_SONNET)

    def get_session_costs(self) -> Dict[str, float]:
        """Get the current session's cost breakdown."""
        return self.session_costs.copy()

    def reset_session_costs(self):
        """Reset session cost tracking."""
        self.session_costs = {
            "claude_haiku": 0.0,
            "claude_sonnet": 0.0,
            "xai_grok": 0.0,
            "total": 0.0
        }


# Convenience function for simple usage
async def process_request(message: str, files: Optional[List] = None) -> Dict[str, Any]:
    """
    Process a user request through the AI router.

    Args:
        message: User's input message
        files: Optional list of uploaded files

    Returns:
        Dict with response, cost info, and metadata
    """
    router = AIRouter()

    # Route the request
    decision = await router.route_request(message)

    # Execute the task
    response = await router.execute_task(decision, message, files)

    return {
        "success": response.success,
        "content": response.content,
        "provider": response.provider,
        "task_type": response.task_type,
        "cost": response.cost,
        "routing": {
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "enhanced_prompt": decision.enhanced_prompt
        },
        "session_costs": router.get_session_costs(),
        "error": response.error
    }
