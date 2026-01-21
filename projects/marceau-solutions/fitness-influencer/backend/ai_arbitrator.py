#!/usr/bin/env python3
"""
AI Arbitrator - Fair Dual-AI Decision System
Both Claude and Grok vote on who should handle each task.

How it works:
1. User sends a request
2. BOTH Claude and Grok receive the same request simultaneously
3. Each AI votes on who should handle it and why
4. An unbiased algorithm weighs the votes based on:
   - Task type expertise (images → Grok bias, text → Claude bias)
   - Cost efficiency
   - Confidence scores
   - Historical accuracy (future feature)
5. The winning AI executes the task

This prevents self-serving bias since both AIs have equal say.
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
from concurrent.futures import ThreadPoolExecutor


class Provider(Enum):
    CLAUDE = "claude"
    GROK = "grok"


@dataclass
class Vote:
    """A single AI's vote on who should handle the task."""
    voter: Provider
    recommended_handler: Provider
    confidence: float  # 0.0 - 1.0
    reasoning: str
    estimated_cost: float
    task_category: str  # image, text, analysis, etc.


@dataclass
class ArbitrationResult:
    """Final decision after both AIs vote."""
    winner: Provider
    claude_vote: Vote
    grok_vote: Vote
    final_confidence: float
    decision_reasoning: str
    total_arbitration_cost: float


@dataclass
class TaskResult:
    """Result after task execution."""
    success: bool
    content: Any
    executed_by: Provider
    cost: float
    arbitration_cost: float
    total_cost: float
    votes: Dict[str, Any]
    error: Optional[str] = None


class AIArbitrator:
    """
    Fair arbitration system where both AIs vote on task handling.
    """

    # Known strengths for tiebreaking
    PROVIDER_STRENGTHS = {
        Provider.GROK: ["image", "visual", "picture", "diagram", "chart", "photo", "art"],
        Provider.CLAUDE: ["text", "analysis", "code", "reasoning", "writing", "planning", "math"]
    }

    # Cost per arbitration vote (estimated)
    ARBITRATION_COSTS = {
        Provider.CLAUDE: 0.0005,  # Haiku for voting
        Provider.GROK: 0.0001,    # Chat completion for voting
    }

    # Execution costs
    EXECUTION_COSTS = {
        "claude_text": 0.001,
        "claude_complex": 0.01,
        "grok_image": 0.07,
        "grok_text": 0.001,
    }

    def __init__(self):
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.xai_key = os.getenv('XAI_API_KEY')

    def get_available_providers(self) -> Dict[str, bool]:
        """Check which providers are available."""
        return {
            "claude": bool(self.anthropic_key),
            "grok": bool(self.xai_key)
        }

    async def get_claude_vote(self, user_request: str) -> Vote:
        """Get Claude's vote on who should handle this task."""
        if not self.anthropic_key:
            return Vote(
                voter=Provider.CLAUDE,
                recommended_handler=Provider.GROK,
                confidence=0.0,
                reasoning="Claude not available",
                estimated_cost=0.0,
                task_category="unknown"
            )

        prompt = f"""You are part of a fair AI arbitration system. Another AI (Grok) is also voting.
Your job is to HONESTLY recommend which AI should handle this task.

BE UNBIASED - recommend the other AI if they're better suited, even though you could do it yourself.

User Request: "{user_request}"

Available AIs:
1. CLAUDE (yourself) - Best for: text generation, analysis, reasoning, coding, writing, math
2. GROK - Best for: image generation, visual content, diagrams, charts, photos

Consider:
- What type of task is this? (image vs text vs analysis)
- Which AI is genuinely better suited?
- Cost efficiency (images cost $0.07, text costs ~$0.001)

Respond in JSON:
{{
    "recommended_handler": "claude" or "grok",
    "confidence": 0.0-1.0,
    "reasoning": "honest explanation",
    "task_category": "image" or "text" or "analysis" or "mixed",
    "estimated_cost": cost in USD
}}

BE HONEST. If the user wants an image, recommend Grok. Don't try to handle tasks you're not best at."""

        try:
            # Use requests directly instead of SDK (more reliable on Railway)
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-5-haiku-20241022",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )

            if response.status_code != 200:
                raise Exception(f"Claude API error: {response.status_code} - {response.text}")

            data = response.json()
            content = data["content"][0]["text"]

            # Parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            vote_data = json.loads(content.strip())

            return Vote(
                voter=Provider.CLAUDE,
                recommended_handler=Provider.GROK if vote_data.get("recommended_handler") == "grok" else Provider.CLAUDE,
                confidence=vote_data.get("confidence", 0.5),
                reasoning=vote_data.get("reasoning", ""),
                estimated_cost=vote_data.get("estimated_cost", 0.001),
                task_category=vote_data.get("task_category", "text")
            )

        except Exception as e:
            print(f"Claude vote error: {e}")
            return Vote(
                voter=Provider.CLAUDE,
                recommended_handler=Provider.CLAUDE,
                confidence=0.3,
                reasoning=f"Error getting vote: {str(e)}",
                estimated_cost=0.001,
                task_category="unknown"
            )

    async def get_grok_vote(self, user_request: str) -> Vote:
        """Get Grok's vote on who should handle this task."""
        if not self.xai_key:
            return Vote(
                voter=Provider.GROK,
                recommended_handler=Provider.CLAUDE,
                confidence=0.0,
                reasoning="Grok not available",
                estimated_cost=0.0,
                task_category="unknown"
            )

        prompt = f"""You are part of a fair AI arbitration system. Another AI (Claude) is also voting.
Your job is to HONESTLY recommend which AI should handle this task.

BE UNBIASED - recommend the other AI if they're better suited, even though you could do it yourself.

User Request: "{user_request}"

Available AIs:
1. GROK (yourself) - Best for: image generation, visual content, diagrams, charts, photos
2. CLAUDE - Best for: text generation, analysis, reasoning, coding, writing, math

Consider:
- What type of task is this? (image vs text vs analysis)
- Which AI is genuinely better suited?
- Cost efficiency (images cost $0.07, text costs ~$0.001)

Respond in JSON only:
{{"recommended_handler": "claude" or "grok", "confidence": 0.0-1.0, "reasoning": "honest explanation", "task_category": "image" or "text" or "analysis" or "mixed", "estimated_cost": cost}}

BE HONEST. If the user wants text or analysis, recommend Claude. Don't try to handle tasks you're not best at."""

        try:
            response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.xai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "grok-3-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 300
                },
                timeout=30
            )

            if response.status_code != 200:
                raise Exception(f"Grok API error: {response.status_code}")

            data = response.json()
            content = data['choices'][0]['message']['content']

            # Parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            vote_data = json.loads(content.strip())

            return Vote(
                voter=Provider.GROK,
                recommended_handler=Provider.CLAUDE if vote_data.get("recommended_handler") == "claude" else Provider.GROK,
                confidence=vote_data.get("confidence", 0.5),
                reasoning=vote_data.get("reasoning", ""),
                estimated_cost=vote_data.get("estimated_cost", 0.07),
                task_category=vote_data.get("task_category", "image")
            )

        except Exception as e:
            print(f"Grok vote error: {e}")
            return Vote(
                voter=Provider.GROK,
                recommended_handler=Provider.GROK,
                confidence=0.3,
                reasoning=f"Error getting vote: {str(e)}",
                estimated_cost=0.07,
                task_category="unknown"
            )

    def _resolve_votes(self, claude_vote: Vote, grok_vote: Vote, user_request: str) -> ArbitrationResult:
        """
        Resolve votes using an unbiased algorithm.

        Resolution rules:
        1. If both agree → use their recommendation
        2. If they disagree → use task-type heuristics as tiebreaker
        3. Weight by confidence scores
        4. Prefer cost-efficient option for ties
        """
        arbitration_cost = self.ARBITRATION_COSTS[Provider.CLAUDE] + self.ARBITRATION_COSTS[Provider.GROK]

        # Case 1: Both agree
        if claude_vote.recommended_handler == grok_vote.recommended_handler:
            winner = claude_vote.recommended_handler
            avg_confidence = (claude_vote.confidence + grok_vote.confidence) / 2
            return ArbitrationResult(
                winner=winner,
                claude_vote=claude_vote,
                grok_vote=grok_vote,
                final_confidence=avg_confidence,
                decision_reasoning=f"Both AIs agree: {winner.value} should handle this task",
                total_arbitration_cost=arbitration_cost
            )

        # Case 2: Disagreement - use task type heuristics
        lower_request = user_request.lower()

        # Check for image-related keywords
        is_image_task = any(kw in lower_request for kw in self.PROVIDER_STRENGTHS[Provider.GROK])
        is_text_task = any(kw in lower_request for kw in self.PROVIDER_STRENGTHS[Provider.CLAUDE])

        # Calculate weighted scores
        claude_score = claude_vote.confidence
        grok_score = grok_vote.confidence

        # Apply task-type bonuses (unbiased based on actual strengths)
        if is_image_task and not is_text_task:
            grok_score += 0.3  # Grok is objectively better at images
        elif is_text_task and not is_image_task:
            claude_score += 0.3  # Claude is objectively better at text

        # Self-recommendation penalty (to counteract self-serving bias)
        if claude_vote.recommended_handler == Provider.CLAUDE:
            claude_score -= 0.1  # Slight penalty for self-recommendation
        if grok_vote.recommended_handler == Provider.GROK:
            grok_score -= 0.1  # Slight penalty for self-recommendation

        # Determine winner
        if grok_score > claude_score:
            winner = Provider.GROK
            reasoning = f"Grok wins arbitration (score: {grok_score:.2f} vs {claude_score:.2f})"
        elif claude_score > grok_score:
            winner = Provider.CLAUDE
            reasoning = f"Claude wins arbitration (score: {claude_score:.2f} vs {grok_score:.2f})"
        else:
            # True tie - prefer cheaper option
            if claude_vote.estimated_cost <= grok_vote.estimated_cost:
                winner = Provider.CLAUDE
                reasoning = "Tie resolved by cost efficiency (Claude cheaper)"
            else:
                winner = Provider.GROK
                reasoning = "Tie resolved by cost efficiency (Grok cheaper)"

        final_confidence = max(claude_score, grok_score) / 1.3  # Normalize

        return ArbitrationResult(
            winner=winner,
            claude_vote=claude_vote,
            grok_vote=grok_vote,
            final_confidence=min(final_confidence, 1.0),
            decision_reasoning=reasoning,
            total_arbitration_cost=arbitration_cost
        )

    async def arbitrate(self, user_request: str) -> ArbitrationResult:
        """
        Main arbitration function - gets votes from both AIs simultaneously.
        """
        # Get votes in parallel
        claude_vote, grok_vote = await asyncio.gather(
            self.get_claude_vote(user_request),
            self.get_grok_vote(user_request)
        )

        # Resolve the votes
        return self._resolve_votes(claude_vote, grok_vote, user_request)

    async def execute_with_winner(self, arbitration: ArbitrationResult,
                                   user_request: str,
                                   enhanced_prompt: Optional[str] = None) -> TaskResult:
        """
        Execute the task with the winning AI.
        """
        prompt = enhanced_prompt or user_request

        try:
            if arbitration.winner == Provider.GROK:
                # Check if this is actually an image task
                if arbitration.grok_vote.task_category == "image" or \
                   arbitration.claude_vote.task_category == "image":
                    result = await self._execute_grok_image(prompt)
                else:
                    result = await self._execute_grok_text(prompt)
            else:
                result = await self._execute_claude_text(prompt)

            return TaskResult(
                success=result["success"],
                content=result["content"],
                executed_by=arbitration.winner,
                cost=result["cost"],
                arbitration_cost=arbitration.total_arbitration_cost,
                total_cost=result["cost"] + arbitration.total_arbitration_cost,
                votes={
                    "claude": {
                        "recommended": arbitration.claude_vote.recommended_handler.value,
                        "confidence": arbitration.claude_vote.confidence,
                        "reasoning": arbitration.claude_vote.reasoning
                    },
                    "grok": {
                        "recommended": arbitration.grok_vote.recommended_handler.value,
                        "confidence": arbitration.grok_vote.confidence,
                        "reasoning": arbitration.grok_vote.reasoning
                    },
                    "final_decision": arbitration.decision_reasoning
                },
                error=result.get("error")
            )

        except Exception as e:
            return TaskResult(
                success=False,
                content=None,
                executed_by=arbitration.winner,
                cost=0.0,
                arbitration_cost=arbitration.total_arbitration_cost,
                total_cost=arbitration.total_arbitration_cost,
                votes={},
                error=str(e)
            )

    async def _execute_grok_image(self, prompt: str) -> Dict[str, Any]:
        """Generate image with Grok."""
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
                return {"success": False, "content": None, "cost": 0.0, "error": response.text}

            data = response.json()
            images = data.get('data', [])
            urls = [img.get('url') for img in images if img.get('url')]

            return {
                "success": True,
                "content": {"urls": urls, "primary_url": urls[0] if urls else None},
                "cost": 0.07,
                "error": None
            }

        except Exception as e:
            return {"success": False, "content": None, "cost": 0.0, "error": str(e)}

    async def _execute_grok_text(self, prompt: str) -> Dict[str, Any]:
        """Generate text with Grok."""
        try:
            response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.xai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "grok-3-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000
                },
                timeout=30
            )

            if response.status_code != 200:
                return {"success": False, "content": None, "cost": 0.0, "error": response.text}

            data = response.json()
            content = data['choices'][0]['message']['content']

            return {
                "success": True,
                "content": content,
                "cost": 0.001,
                "error": None
            }

        except Exception as e:
            return {"success": False, "content": None, "cost": 0.0, "error": str(e)}

    async def _execute_claude_text(self, prompt: str) -> Dict[str, Any]:
        """Generate text with Claude using direct API calls."""
        if not self.anthropic_key:
            return {"success": False, "content": None, "cost": 0.0, "error": "Claude not configured"}

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-5-haiku-20241022",
                    "max_tokens": 1000,
                    "system": "You are a helpful AI assistant for fitness influencers. Be concise and practical.",
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )

            if response.status_code != 200:
                return {"success": False, "content": None, "cost": 0.0, "error": f"Claude API error: {response.text}"}

            data = response.json()
            content = data["content"][0]["text"]

            return {
                "success": True,
                "content": content,
                "cost": 0.001,
                "error": None
            }

        except Exception as e:
            return {"success": False, "content": None, "cost": 0.0, "error": str(e)}


async def optimize_prompt(user_request: str, api_key: str) -> Dict[str, Any]:
    """
    Optimize a casual user prompt into a structured CLEAR framework prompt.

    CLEAR Framework:
    - Context: Background information and situation
    - Limitations: Constraints, requirements, boundaries
    - Examples: Reference examples or desired style
    - Audience: Who this is for
    - Request: The specific ask, broken down clearly

    Uses Claude Haiku for speed and cost efficiency (~$0.0003 per optimization).

    Returns:
        Dict with optimized_prompt, original_prompt, optimization_notes, cost
    """
    if not api_key:
        return {
            "success": False,
            "optimized_prompt": user_request,
            "original_prompt": user_request,
            "optimization_notes": "No API key - using original prompt",
            "cost": 0.0
        }

    optimization_prompt = f"""You are a prompt optimization expert. Transform the user's casual request into a well-structured prompt that will get better AI results.

USER'S ORIGINAL REQUEST:
"{user_request}"

OPTIMIZE using the CLEAR framework:
1. **Context**: Add relevant background (fitness influencer context, social media, content creation)
2. **Limitations**: Infer reasonable constraints (brand-safe, professional, engaging)
3. **Examples**: Suggest style references if applicable (modern, minimal, bold, etc.)
4. **Audience**: Identify target audience (fitness enthusiasts, beginners, etc.)
5. **Request**: Restate the ask clearly with specific details

OUTPUT FORMAT - Return ONLY the optimized prompt text, nothing else. Make it natural and detailed but not overly long. The optimized prompt should be 2-4 sentences that capture all the CLEAR elements naturally.

IMPORTANT:
- Keep the core intent exactly the same
- Add helpful specificity without changing what they're asking for
- For image requests, add visual style details
- For video requests, add format/style details
- For text requests, add tone/voice details"""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": optimization_prompt}]
            },
            timeout=15
        )

        if response.status_code != 200:
            print(f"[PromptOptimizer] API error: {response.status_code}")
            return {
                "success": False,
                "optimized_prompt": user_request,
                "original_prompt": user_request,
                "optimization_notes": f"API error - using original",
                "cost": 0.0
            }

        data = response.json()
        optimized = data["content"][0]["text"].strip()

        # Clean up any markdown or extra formatting
        optimized = optimized.strip('"\'')

        print(f"[PromptOptimizer] Original: {user_request[:50]}...")
        print(f"[PromptOptimizer] Optimized: {optimized[:80]}...")

        return {
            "success": True,
            "optimized_prompt": optimized,
            "original_prompt": user_request,
            "optimization_notes": "Prompt enhanced with CLEAR framework",
            "cost": 0.0003  # Haiku is very cheap
        }

    except Exception as e:
        print(f"[PromptOptimizer] Error: {e}")
        return {
            "success": False,
            "optimized_prompt": user_request,
            "original_prompt": user_request,
            "optimization_notes": f"Error: {str(e)}",
            "cost": 0.0
        }


async def process_with_arbitration(user_request: str, optimize: bool = True) -> Dict[str, Any]:
    """
    Main entry point - process a request with full AI arbitration.

    Args:
        user_request: The user's raw request
        optimize: Whether to optimize the prompt using CLEAR framework (default: True)
    """
    arbitrator = AIArbitrator()
    original_request = user_request
    optimization_result = None
    optimization_cost = 0.0

    lower_original = user_request.lower()

    # Check for brand research request FIRST (before optimization)
    is_brand_research = any(kw in lower_original for kw in ['research', 'analyze', 'look up', 'study']) and \
                        any(kw in lower_original for kw in ['brand', '@', 'instagram', 'tiktok', 'account', 'profile'])

    if is_brand_research:
        print(f"[Arbitrator] Detected brand research request")
        return await process_brand_research(arbitrator, user_request)

    # Step 0: Optimize prompt using CLEAR framework (if enabled)
    if optimize and arbitrator.anthropic_key:
        print(f"[Arbitrator] Optimizing prompt with CLEAR framework...")
        optimization_result = await optimize_prompt(user_request, arbitrator.anthropic_key)
        if optimization_result["success"]:
            user_request = optimization_result["optimized_prompt"]
            optimization_cost = optimization_result["cost"]
            print(f"[Arbitrator] Using optimized prompt")
        else:
            print(f"[Arbitrator] Optimization failed, using original prompt")

    lower_request = user_request.lower()

    # Check for multi-step tasks (ad creation, complex content)
    is_ad_request = any(kw in lower_request for kw in ['advertisement', 'ad ', ' ad', 'promo', 'commercial', 'video ad', 'create a', 'make a'])
    needs_images = any(kw in lower_request for kw in ['image', 'visual', 'picture', 'generate'])
    needs_video_plan = any(kw in lower_request for kw in ['video', 'downloadable', 'second', 'transitions', 'music'])

    # Extract brand handle if mentioned (for personalized ad creation)
    brand_handle = _extract_brand_handle(original_request)

    # Handle complex multi-step requests (needs BOTH AIs)
    # Also trigger for video ad requests even without explicit "image" keywords
    if is_ad_request and (needs_images or needs_video_plan):
        print(f"[Arbitrator] Detected ad creation request: is_ad={is_ad_request}, needs_images={needs_images}, needs_video={needs_video_plan}")
        result = await process_ad_creation(arbitrator, user_request, brand_handle=brand_handle)
        # Add optimization info to result
        if optimization_result:
            result["prompt_optimization"] = {
                "original": original_request,
                "optimized": user_request,
                "cost": optimization_cost
            }
            result["costs"]["optimization"] = optimization_cost
            result["costs"]["total"] = result["costs"].get("total", 0) + optimization_cost
        return result

    # Step 1: Both AIs vote
    arbitration = await arbitrator.arbitrate(user_request)

    # Step 2: Execute with winner
    # Use the optimized prompt for execution
    enhanced_prompt = user_request if optimization_result and optimization_result["success"] else None

    result = await arbitrator.execute_with_winner(arbitration, user_request, enhanced_prompt)

    response = {
        "success": result.success,
        "content": result.content,
        "executed_by": result.executed_by.value,
        "task_type": arbitration.claude_vote.task_category or arbitration.grok_vote.task_category,
        "costs": {
            "arbitration": result.arbitration_cost,
            "execution": result.cost,
            "optimization": optimization_cost,
            "total": result.total_cost + optimization_cost
        },
        "arbitration": {
            "claude_vote": {
                "recommended": arbitration.claude_vote.recommended_handler.value,
                "confidence": arbitration.claude_vote.confidence,
                "reasoning": arbitration.claude_vote.reasoning
            },
            "grok_vote": {
                "recommended": arbitration.grok_vote.recommended_handler.value,
                "confidence": arbitration.grok_vote.confidence,
                "reasoning": arbitration.grok_vote.reasoning
            },
            "decision": arbitration.decision_reasoning,
            "final_confidence": arbitration.final_confidence
        },
        "error": result.error
    }

    # Add prompt optimization info if optimization was performed
    if optimization_result:
        response["prompt_optimization"] = {
            "original": original_request,
            "optimized": user_request,
            "cost": optimization_cost
        }

    return response


async def process_ad_creation(arbitrator: AIArbitrator, user_request: str, brand_handle: str = None) -> Dict[str, Any]:
    """
    Handle complex ad creation requests using BOTH AIs collaboratively.

    Workflow:
    1. Load brand profile if available (for personalization)
    2. Claude creates the ad plan (script, image descriptions, music suggestions)
    3. Grok generates the actual images based on Claude's descriptions
    4. Return combined result with plan + generated images
    """
    total_cost = 0.0
    brand_profile = None

    # Step 0: Load brand profile if handle provided
    if brand_handle:
        try:
            from brand_research import get_brand_profile
            brand_profile = get_brand_profile(brand_handle)
            if brand_profile:
                print(f"[AdCreation] Using brand profile for @{brand_handle}")
        except Exception as e:
            print(f"[AdCreation] Could not load brand profile: {e}")

    # Build personalized prompt based on brand profile
    brand_context = ""
    if brand_profile:
        brand_context = f"""
BRAND PROFILE FOR PERSONALIZATION:
- Brand Name: {brand_profile.get('brand_name', 'Unknown')}
- Brand Voice: {brand_profile.get('brand_voice', {}).get('tone', 'motivational')}, {brand_profile.get('brand_voice', {}).get('personality', 'coach')}
- Visual Style: {brand_profile.get('visual_style', {}).get('aesthetic', 'bold')}, Colors: {', '.join(brand_profile.get('visual_style', {}).get('color_palette', ['#000', '#FFD700']))}
- Content Themes: {', '.join(brand_profile.get('content_themes', {}).get('primary_topics', ['fitness']))}
- Target Audience: {brand_profile.get('target_audience', {}).get('demographics', 'fitness enthusiasts')}
- Unique Style: {brand_profile.get('unique_differentiator', 'Authentic fitness journey')}

IMPORTANT: Make sure all content matches this brand's voice, visual style, and resonates with their target audience.
"""

    # Step 1: Claude creates the ad plan
    plan_prompt = f"""Create a detailed advertisement plan for the following request:

"{user_request}"
{brand_context}
Provide:
1. A 15-second video script with exact timing
2. 3-4 specific image prompts for AI image generation (be very detailed and specific for best results)
3. Music/audio recommendations
4. Transition suggestions

Format your image prompts as a JSON array within your response like this:
IMAGE_PROMPTS: ["prompt 1", "prompt 2", "prompt 3"]

Make the image prompts detailed and specific for AI image generation."""

    plan_result = await arbitrator._execute_claude_text(plan_prompt)
    total_cost += plan_result.get("cost", 0)

    if not plan_result["success"]:
        return {
            "success": False,
            "error": f"Failed to create ad plan: {plan_result.get('error')}",
            "content": None,
            "executed_by": "claude",
            "task_type": "ad_creation",
            "costs": {"total": total_cost}
        }

    ad_plan = plan_result["content"]

    # Step 2: Extract image prompts and generate images with Grok
    generated_images = []
    image_prompts = []

    # Try to extract image prompts from the plan
    if "IMAGE_PROMPTS:" in ad_plan:
        try:
            prompts_section = ad_plan.split("IMAGE_PROMPTS:")[1]
            # Find the JSON array
            start = prompts_section.find("[")
            end = prompts_section.find("]") + 1
            if start != -1 and end > start:
                image_prompts = json.loads(prompts_section[start:end])
        except:
            pass

    # If no structured prompts, generate default fitness ad images
    if not image_prompts:
        image_prompts = [
            "Professional fitness influencer in modern gym, energetic pose, high quality lighting, social media ready",
            "Dynamic workout action shot, athletic person exercising, motivational fitness content",
            "Clean modern fitness studio background, professional equipment, bright and inviting atmosphere"
        ]

    # Generate images (limit to 3 to control costs)
    for i, prompt in enumerate(image_prompts[:3]):
        img_result = await arbitrator._execute_grok_image(prompt)
        total_cost += img_result.get("cost", 0)

        if img_result["success"] and img_result["content"]:
            generated_images.append({
                "prompt": prompt,
                "url": img_result["content"].get("primary_url"),
                "index": i + 1
            })

    # Step 3: Check if video generation is requested
    lower_request = user_request.lower()
    wants_video = any(kw in lower_request for kw in ['video', 'downloadable', 'mp4', 'render'])

    video_result = None
    if wants_video and generated_images:
        # Try to generate video from images using Shotstack
        video_result = await _generate_video_ad(
            image_urls=[img["url"] for img in generated_images if img.get("url")],
            headline=_extract_headline(ad_plan),
            user_request=user_request
        )
        if video_result.get("success"):
            total_cost += video_result.get("cost", 0.05)

    # Step 4: Combine results
    content = {
        "type": "ad_package",
        "plan": ad_plan,
        "images": generated_images,
        "image_count": len(generated_images)
    }

    # Add video if generated
    if video_result and video_result.get("success"):
        content["video"] = {
            "url": video_result.get("video_url"),
            "status": video_result.get("status"),
            "render_id": video_result.get("render_id")
        }
        content["type"] = "ad_package_with_video"

    return {
        "success": True,
        "content": content,
        "executed_by": "both",
        "task_type": "ad_creation",
        "costs": {
            "planning": plan_result.get("cost", 0),
            "images": len(generated_images) * 0.07,
            "video": video_result.get("cost", 0) if video_result else 0,
            "total": total_cost
        },
        "arbitration": {
            "claude_vote": {"recommended": "both", "reasoning": "Complex ad creation requires both AIs"},
            "grok_vote": {"recommended": "both", "reasoning": "Complex ad creation requires both AIs"},
            "decision": "Multi-step task: Claude for planning, Grok for images" + (", Shotstack for video" if video_result else "")
        },
        "error": None
    }


def _extract_headline(ad_plan: str) -> str:
    """Extract headline from ad plan text."""
    lines = ad_plan.split('\n')
    for line in lines:
        lower = line.lower()
        if 'headline' in lower or 'title' in lower:
            # Try to extract text after colon
            if ':' in line:
                return line.split(':', 1)[1].strip().strip('"\'')
    # Default headline
    return "Transform Your Body"


async def _generate_video_ad(
    image_urls: List[str],
    headline: str,
    user_request: str
) -> Dict[str, Any]:
    """
    Generate video ad using Shotstack.

    Args:
        image_urls: URLs of generated images
        headline: Ad headline text
        user_request: Original user request for context

    Returns:
        Dict with video_url if successful
    """
    try:
        from shotstack_video import create_video_ad

        # Extract CTA if mentioned
        cta = "Start Your Journey"
        lower = user_request.lower()
        if "cta" in lower or "call to action" in lower:
            # Try to find CTA in request
            pass  # Use default for now

        result = await create_video_ad(
            image_urls=image_urls,
            headline=headline,
            cta_text=cta,
            duration=15.0
        )

        return result

    except ImportError:
        return {
            "success": False,
            "error": "Shotstack video module not available"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _extract_brand_handle(text: str) -> Optional[str]:
    """
    Extract a social media handle from text.

    Looks for patterns like:
    - @username
    - "for username"
    - "for @username"
    - "boabfit" mentioned as a brand name
    """
    import re

    # Look for @handle pattern
    at_match = re.search(r'@(\w+)', text)
    if at_match:
        return at_match.group(1).lower()

    # Look for "for [brand]" pattern
    for_match = re.search(r'for\s+(\w+)', text.lower())
    if for_match:
        potential = for_match.group(1)
        # Filter out common words
        if potential not in ['a', 'an', 'the', 'my', 'their', 'this', 'that', 'me', 'them']:
            return potential

    return None


async def process_brand_research(arbitrator: AIArbitrator, user_request: str) -> Dict[str, Any]:
    """
    Handle brand research requests.

    Extracts the handle from the request and researches their brand.
    """
    from brand_research import research_brand, format_brand_profile_for_display

    # Extract handle from request
    handle = _extract_brand_handle(user_request)

    if not handle:
        # Try to extract any word that looks like a handle/brand name
        import re
        words = re.findall(r'\b[A-Za-z][A-Za-z0-9_]+\b', user_request)
        # Filter out common words
        stopwords = {'research', 'analyze', 'brand', 'look', 'study', 'the', 'for', 'on', 'instagram',
                     'tiktok', 'youtube', 'social', 'media', 'account', 'profile', 'fitness', 'influencer',
                     'create', 'make', 'based', 'their', 'posts', 'content', 'can', 'you', 'please', 'help',
                     'me', 'want', 'need', 'like', 'would', 'could', 'should', 'about', 'from', 'with'}
        potential_handles = [w.lower() for w in words if w.lower() not in stopwords and len(w) > 2]
        if potential_handles:
            handle = potential_handles[0]

    if not handle:
        return {
            "success": False,
            "content": "I couldn't identify a brand handle in your request. Please specify like: 'Research @boabfit' or 'Analyze the brand boabfit'",
            "executed_by": "system",
            "task_type": "brand_research",
            "costs": {"total": 0},
            "arbitration": {
                "claude_vote": {"recommended": "system"},
                "grok_vote": {"recommended": "system"},
                "decision": "Missing brand handle"
            },
            "error": "No brand handle found in request"
        }

    print(f"[BrandResearch] Researching brand: @{handle}")

    try:
        profile = await research_brand(handle)
        formatted = format_brand_profile_for_display(profile)

        return {
            "success": True,
            "content": {
                "type": "brand_profile",
                "handle": handle,
                "profile": profile,
                "formatted": formatted
            },
            "executed_by": "claude",
            "task_type": "brand_research",
            "costs": {
                "research": 0.002,  # Approximate Claude cost
                "total": 0.002
            },
            "arbitration": {
                "claude_vote": {"recommended": "claude", "reasoning": "Brand analysis requires AI understanding"},
                "grok_vote": {"recommended": "claude", "reasoning": "Text analysis task"},
                "decision": f"Brand research completed for @{handle}"
            },
            "error": None
        }

    except Exception as e:
        print(f"[BrandResearch] Error: {e}")
        return {
            "success": False,
            "content": f"Error researching brand @{handle}: {str(e)}",
            "executed_by": "system",
            "task_type": "brand_research",
            "costs": {"total": 0},
            "arbitration": {
                "claude_vote": {"recommended": "system"},
                "grok_vote": {"recommended": "system"},
                "decision": "Brand research failed"
            },
            "error": str(e)
        }
