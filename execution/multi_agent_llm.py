#!/usr/bin/env python3
"""
Multi-Agent LLM Communication System

Enables back-and-forth dialogue between multiple LLMs for:
- Strategic decision making (Grok strength)
- Code execution & analysis (Claude strength)  
- Creative solutions & different perspectives (GPT-4 strength)
- Fast iteration & validation (Groq/Llama strength)

Agent Roles:
  GROK (xAI)     — Strategic architect, big-picture thinking, creative solutions
  CLAUDE         — Primary executor, detailed analysis, coding, thorough reasoning
  GPT-4          — Alternative perspective, validation, creative writing
  GROQ/LLAMA     — Fast validation, quick checks, high-throughput tasks

Communication Patterns:
  1. CONSULTATION  — One agent asks another for advice on a decision
  2. REVIEW        — One agent reviews another's output
  3. BRAINSTORM    — Multiple agents contribute ideas
  4. VALIDATION    — Cross-check conclusions across agents
  5. ESCALATION    — Difficult problem escalated to stronger/different agent

Usage:
    from execution.multi_agent_llm import AgentCouncil, ConsultationType
    
    council = AgentCouncil()
    
    # Simple consultation
    response = council.consult(
        question="Should we use SMS or email for initial outreach?",
        primary_agent="claude",
        consult_agent="grok",
        context={"industry": "HVAC", "lead_count": 50}
    )
    
    # Multi-agent brainstorm
    ideas = council.brainstorm(
        topic="How to increase response rate from cold outreach",
        agents=["grok", "claude", "gpt4"],
        rounds=2
    )
    
    # Decision with validation
    decision = council.decide(
        question="What's the best pricing strategy for AI services?",
        options=["$297/mo", "$497/mo", "$997/mo"],
        agents=["grok", "claude"]
    )
"""

import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field, asdict
from enum import Enum
import anthropic
import openai
import requests

# Setup
REPO_ROOT = Path(__file__).parent.parent
from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger("multi_agent")

# Conversation log
DIALOGUE_LOG = REPO_ROOT / "data" / "agent_dialogues.jsonl"
DIALOGUE_LOG.parent.mkdir(parents=True, exist_ok=True)


class ConsultationType(str, Enum):
    """Types of agent consultation."""
    STRATEGIC = "strategic"      # Big-picture decisions
    TECHNICAL = "technical"      # Code/architecture choices
    CREATIVE = "creative"        # Ideas and brainstorming
    VALIDATION = "validation"    # Cross-check conclusions
    REVIEW = "review"            # Review another agent's work
    ESCALATION = "escalation"    # Difficult problem needs help


@dataclass
class AgentConfig:
    """Configuration for an LLM agent."""
    name: str
    provider: str  # anthropic, xai, openai, groq
    model: str
    api_key_env: str
    strengths: List[str]
    weaknesses: List[str]
    best_for: List[ConsultationType]
    fallback_agent: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7


@dataclass 
class DialogueTurn:
    """A single turn in an agent dialogue."""
    agent: str
    role: str  # "questioner", "responder", "reviewer"
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tokens_used: int = 0
    latency_ms: int = 0


@dataclass
class AgentDialogue:
    """Complete dialogue between agents."""
    id: str
    consultation_type: ConsultationType
    topic: str
    context: Dict[str, Any]
    turns: List[DialogueTurn]
    conclusion: Optional[str] = None
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    

# =============================================================================
# AGENT DEFINITIONS
# =============================================================================

AGENTS: Dict[str, AgentConfig] = {
    "grok": AgentConfig(
        name="Grok",
        provider="xai",
        model="grok-3-latest",
        api_key_env="XAI_API_KEY",
        strengths=[
            "Strategic thinking and big-picture analysis",
            "Creative and unconventional solutions",
            "Cutting through complexity to core issues",
            "Honest, direct feedback without hedging",
            "Good at prioritization and focus"
        ],
        weaknesses=[
            "May oversimplify technical details",
            "Less thorough on implementation specifics",
            "Can be overconfident"
        ],
        best_for=[
            ConsultationType.STRATEGIC,
            ConsultationType.CREATIVE,
            ConsultationType.REVIEW
        ],
        fallback_agent="claude",
        temperature=0.8
    ),
    
    "claude": AgentConfig(
        name="Claude",
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        api_key_env="ANTHROPIC_API_KEY",
        strengths=[
            "Thorough analysis and detailed reasoning",
            "Strong coding and technical implementation",
            "Careful consideration of edge cases",
            "Good at breaking down complex problems",
            "Reliable execution and follow-through"
        ],
        weaknesses=[
            "Can be overly cautious or verbose",
            "May miss creative/unconventional solutions",
            "Sometimes gets stuck in analysis paralysis"
        ],
        best_for=[
            ConsultationType.TECHNICAL,
            ConsultationType.VALIDATION,
            ConsultationType.REVIEW
        ],
        fallback_agent="gpt4",
        temperature=0.7
    ),
    
    "gpt4": AgentConfig(
        name="GPT-4",
        provider="openai",
        model="gpt-4o",
        api_key_env="OPENAI_API_KEY",
        strengths=[
            "Strong general knowledge",
            "Good at creative writing and content",
            "Different perspective from Claude",
            "Good at explaining complex topics simply"
        ],
        weaknesses=[
            "Can be generic or safe in responses",
            "May hallucinate details",
            "Less consistent on technical tasks"
        ],
        best_for=[
            ConsultationType.CREATIVE,
            ConsultationType.VALIDATION
        ],
        fallback_agent="claude",
        temperature=0.7
    ),
    
    "groq": AgentConfig(
        name="Groq/Llama",
        provider="groq",
        model="llama-3.3-70b-versatile",
        api_key_env="GROQ_API_KEY",
        strengths=[
            "Extremely fast responses",
            "Good for quick validation",
            "High throughput for batch tasks",
            "Cost-effective for simple queries"
        ],
        weaknesses=[
            "Less sophisticated reasoning",
            "May miss nuance",
            "Not as strong on complex tasks"
        ],
        best_for=[
            ConsultationType.VALIDATION
        ],
        fallback_agent="claude",
        max_tokens=2048,
        temperature=0.5
    )
}


# =============================================================================
# LLM CLIENT
# =============================================================================

class LLMClient:
    """Unified client for multiple LLM providers."""
    
    def __init__(self):
        self.clients = {}
        self._init_clients()
    
    def _init_clients(self):
        """Initialize API clients for available providers."""
        # Anthropic
        key = os.getenv("ANTHROPIC_API_KEY")
        if key:
            self.clients["anthropic"] = anthropic.Anthropic(api_key=key)
        
        # OpenAI
        key = os.getenv("OPENAI_API_KEY")
        if key:
            self.clients["openai"] = openai.OpenAI(api_key=key)
        
        # xAI (Grok) - uses OpenAI-compatible API
        key = os.getenv("XAI_API_KEY")
        if key:
            self.clients["xai"] = openai.OpenAI(
                api_key=key,
                base_url="https://api.x.ai/v1"
            )
        
        # Groq
        key = os.getenv("GROQ_API_KEY")
        if key:
            self.clients["groq"] = openai.OpenAI(
                api_key=key,
                base_url="https://api.groq.com/openai/v1"
            )
        
        logger.info(f"Initialized LLM clients: {list(self.clients.keys())}")
    
    def call(
        self,
        agent_name: str,
        messages: List[Dict[str, str]],
        system_prompt: str = None,
        max_tokens: int = None,
        temperature: float = None
    ) -> Dict[str, Any]:
        """
        Call an LLM agent.
        
        Returns:
            Dict with 'content', 'tokens_used', 'latency_ms'
        """
        agent = AGENTS.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        provider = agent.provider
        client = self.clients.get(provider)
        
        if not client:
            # Try fallback
            if agent.fallback_agent:
                logger.warning(f"{agent_name} unavailable, using fallback {agent.fallback_agent}")
                return self.call(agent.fallback_agent, messages, system_prompt, max_tokens, temperature)
            raise ValueError(f"No client for provider: {provider}")
        
        max_tokens = max_tokens or agent.max_tokens
        temperature = temperature if temperature is not None else agent.temperature
        
        start_time = time.time()
        
        try:
            if provider == "anthropic":
                # Anthropic has different API
                response = client.messages.create(
                    model=agent.model,
                    max_tokens=max_tokens,
                    system=system_prompt or "You are a helpful AI assistant.",
                    messages=messages
                )
                content = response.content[0].text
                tokens = response.usage.input_tokens + response.usage.output_tokens
                
            else:
                # OpenAI-compatible (OpenAI, xAI, Groq)
                msgs = []
                if system_prompt:
                    msgs.append({"role": "system", "content": system_prompt})
                msgs.extend(messages)
                
                response = client.chat.completions.create(
                    model=agent.model,
                    messages=msgs,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                content = response.choices[0].message.content
                tokens = response.usage.total_tokens if response.usage else 0
            
            latency = int((time.time() - start_time) * 1000)
            
            return {
                "content": content,
                "tokens_used": tokens,
                "latency_ms": latency,
                "agent": agent_name,
                "model": agent.model
            }
            
        except Exception as e:
            logger.error(f"Error calling {agent_name}: {e}")
            # Try fallback
            if agent.fallback_agent:
                logger.info(f"Trying fallback: {agent.fallback_agent}")
                return self.call(agent.fallback_agent, messages, system_prompt, max_tokens, temperature)
            raise


# =============================================================================
# AGENT COUNCIL
# =============================================================================

class AgentCouncil:
    """
    Orchestrates multi-agent LLM communication.
    
    Provides patterns for agents to consult each other:
    - consult(): Ask another agent for advice
    - review(): Have an agent review another's work
    - brainstorm(): Multiple agents contribute ideas
    - decide(): Make a decision with multiple perspectives
    - escalate(): Hand off to a stronger agent
    """
    
    def __init__(self):
        self.llm = LLMClient()
        self.dialogues: List[AgentDialogue] = []
    
    def _log_dialogue(self, dialogue: AgentDialogue):
        """Log dialogue to file."""
        with open(DIALOGUE_LOG, "a") as f:
            f.write(json.dumps(asdict(dialogue)) + "\n")
    
    def _select_agent_for_task(self, task_type: ConsultationType) -> str:
        """Select best agent for a task type."""
        for name, agent in AGENTS.items():
            if task_type in agent.best_for:
                return name
        return "claude"  # Default
    
    def consult(
        self,
        question: str,
        primary_agent: str = "claude",
        consult_agent: str = "grok",
        context: Dict[str, Any] = None,
        consultation_type: ConsultationType = ConsultationType.STRATEGIC,
        max_rounds: int = 2
    ) -> Dict[str, Any]:
        """
        Have one agent consult another for advice.
        
        Pattern:
          Primary asks question → Consult agent responds →
          Primary can follow up → Final synthesis
        
        Returns:
            Dict with 'conclusion', 'dialogue', 'agents_used'
        """
        dialogue_id = f"consult_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        dialogue = AgentDialogue(
            id=dialogue_id,
            consultation_type=consultation_type,
            topic=question[:100],
            context=context or {},
            turns=[]
        )
        
        # Build context string
        context_str = ""
        if context:
            context_str = "\n\nContext:\n" + json.dumps(context, indent=2)
        
        # Primary agent formulates the question
        primary_system = f"""You are the primary decision-maker. You need advice on a {consultation_type.value} matter.

Your role: Ask clear, specific questions and synthesize the advice you receive into actionable conclusions.
Your strengths: {', '.join(AGENTS[primary_agent].strengths[:3])}

After receiving advice, either:
1. Ask a clarifying follow-up question
2. Synthesize the advice into a conclusion starting with "CONCLUSION:"
"""
        
        consult_system = f"""You are being consulted for your expertise in {consultation_type.value} matters.

Your role: Provide direct, actionable advice. Don't hedge or be overly cautious.
Your strengths: {', '.join(AGENTS[consult_agent].strengths[:3])}

Be concise but thorough. The other agent will ask follow-ups if needed.
"""
        
        # Round 1: Primary asks, Consult responds
        primary_msg = f"I need your advice on this: {question}{context_str}"
        
        dialogue.turns.append(DialogueTurn(
            agent=primary_agent,
            role="questioner",
            message=primary_msg
        ))
        
        # Get consult agent's response
        consult_response = self.llm.call(
            consult_agent,
            [{"role": "user", "content": primary_msg}],
            system_prompt=consult_system
        )
        
        dialogue.turns.append(DialogueTurn(
            agent=consult_agent,
            role="responder",
            message=consult_response["content"],
            tokens_used=consult_response["tokens_used"],
            latency_ms=consult_response["latency_ms"]
        ))
        
        # Check if more rounds needed
        messages = [
            {"role": "user", "content": primary_msg},
            {"role": "assistant", "content": consult_response["content"]}
        ]
        
        for round_num in range(1, max_rounds):
            # Primary agent decides: follow up or conclude
            followup_prompt = f"""Based on this advice, do one of:
1. Ask a specific follow-up question if you need clarification
2. If you have enough information, synthesize into a conclusion starting with "CONCLUSION:"

Their advice: {consult_response['content'][:1000]}"""
            
            primary_response = self.llm.call(
                primary_agent,
                [{"role": "user", "content": followup_prompt}],
                system_prompt=primary_system
            )
            
            dialogue.turns.append(DialogueTurn(
                agent=primary_agent,
                role="questioner",
                message=primary_response["content"],
                tokens_used=primary_response["tokens_used"],
                latency_ms=primary_response["latency_ms"]
            ))
            
            # Check if concluded
            if "CONCLUSION:" in primary_response["content"]:
                conclusion = primary_response["content"].split("CONCLUSION:")[-1].strip()
                dialogue.conclusion = conclusion
                break
            
            # Get another response from consult agent
            messages.append({"role": "user", "content": primary_response["content"]})
            
            consult_response = self.llm.call(
                consult_agent,
                messages,
                system_prompt=consult_system
            )
            
            dialogue.turns.append(DialogueTurn(
                agent=consult_agent,
                role="responder",
                message=consult_response["content"],
                tokens_used=consult_response["tokens_used"],
                latency_ms=consult_response["latency_ms"]
            ))
            
            messages.append({"role": "assistant", "content": consult_response["content"]})
        
        # If no conclusion yet, force one
        if not dialogue.conclusion:
            synthesis = self.llm.call(
                primary_agent,
                [{"role": "user", "content": f"Synthesize this advice into a final conclusion:\n\n{consult_response['content'][:1500]}"}],
                system_prompt="Provide a clear, actionable conclusion."
            )
            dialogue.conclusion = synthesis["content"]
            dialogue.turns.append(DialogueTurn(
                agent=primary_agent,
                role="synthesizer",
                message=f"CONCLUSION: {synthesis['content']}",
                tokens_used=synthesis["tokens_used"],
                latency_ms=synthesis["latency_ms"]
            ))
        
        dialogue.completed_at = datetime.now().isoformat()
        self._log_dialogue(dialogue)
        
        return {
            "conclusion": dialogue.conclusion,
            "dialogue": dialogue,
            "agents_used": [primary_agent, consult_agent],
            "total_turns": len(dialogue.turns),
            "total_tokens": sum(t.tokens_used for t in dialogue.turns)
        }
    
    def brainstorm(
        self,
        topic: str,
        agents: List[str] = None,
        context: Dict[str, Any] = None,
        rounds: int = 2
    ) -> Dict[str, Any]:
        """
        Multiple agents contribute ideas on a topic.
        
        Each agent builds on previous agents' ideas.
        
        Returns:
            Dict with 'ideas', 'synthesis', 'dialogue'
        """
        agents = agents or ["grok", "claude", "gpt4"]
        
        dialogue_id = f"brainstorm_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        dialogue = AgentDialogue(
            id=dialogue_id,
            consultation_type=ConsultationType.CREATIVE,
            topic=topic[:100],
            context=context or {},
            turns=[]
        )
        
        all_ideas = []
        context_str = f"\n\nContext: {json.dumps(context)}" if context else ""
        
        for round_num in range(rounds):
            for agent_name in agents:
                # Build on previous ideas
                prev_ideas = ""
                if all_ideas:
                    prev_ideas = f"\n\nPrevious ideas from other agents:\n" + "\n".join(f"- {idea}" for idea in all_ideas[-6:])
                
                prompt = f"""Brainstorming topic: {topic}{context_str}{prev_ideas}

Contribute 2-3 unique, actionable ideas. Build on others' ideas but add new value.
Be specific and practical, not generic."""
                
                response = self.llm.call(
                    agent_name,
                    [{"role": "user", "content": prompt}],
                    system_prompt=f"You are {AGENTS[agent_name].name}, known for {AGENTS[agent_name].strengths[0].lower()}."
                )
                
                dialogue.turns.append(DialogueTurn(
                    agent=agent_name,
                    role="contributor",
                    message=response["content"],
                    tokens_used=response["tokens_used"],
                    latency_ms=response["latency_ms"]
                ))
                
                # Extract ideas (simple heuristic)
                for line in response["content"].split("\n"):
                    line = line.strip()
                    if line and (line.startswith("-") or line.startswith("•") or line[0].isdigit()):
                        all_ideas.append(f"[{agent_name}] {line}")
        
        # Synthesize best ideas
        synthesis_prompt = f"""Topic: {topic}

All brainstormed ideas:
{chr(10).join(all_ideas)}

Select and synthesize the top 5 most actionable ideas. Combine related ideas where useful."""
        
        synthesis = self.llm.call(
            "claude",
            [{"role": "user", "content": synthesis_prompt}],
            system_prompt="Synthesize the best ideas into a clear, prioritized list."
        )
        
        dialogue.conclusion = synthesis["content"]
        dialogue.completed_at = datetime.now().isoformat()
        self._log_dialogue(dialogue)
        
        return {
            "ideas": all_ideas,
            "synthesis": synthesis["content"],
            "dialogue": dialogue,
            "agents_used": agents,
            "total_turns": len(dialogue.turns)
        }
    
    def decide(
        self,
        question: str,
        options: List[str] = None,
        agents: List[str] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Make a decision with multiple agent perspectives.
        
        Each agent votes and explains reasoning, then synthesis.
        
        Returns:
            Dict with 'decision', 'votes', 'reasoning', 'dialogue'
        """
        agents = agents or ["grok", "claude"]
        
        dialogue_id = f"decide_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        dialogue = AgentDialogue(
            id=dialogue_id,
            consultation_type=ConsultationType.STRATEGIC,
            topic=question[:100],
            context=context or {},
            turns=[]
        )
        
        options_str = ""
        if options:
            options_str = "\n\nOptions:\n" + "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options))
        
        context_str = f"\n\nContext: {json.dumps(context)}" if context else ""
        
        votes = {}
        reasoning = {}
        
        for agent_name in agents:
            prompt = f"""Decision needed: {question}{options_str}{context_str}

Provide your recommendation and brief reasoning.
Format: 
RECOMMENDATION: [your choice]
REASONING: [2-3 sentences why]"""
            
            response = self.llm.call(
                agent_name,
                [{"role": "user", "content": prompt}],
                system_prompt=f"You are {AGENTS[agent_name].name}. Be decisive and direct."
            )
            
            dialogue.turns.append(DialogueTurn(
                agent=agent_name,
                role="voter",
                message=response["content"],
                tokens_used=response["tokens_used"],
                latency_ms=response["latency_ms"]
            ))
            
            # Extract vote and reasoning
            content = response["content"]
            if "RECOMMENDATION:" in content:
                rec = content.split("RECOMMENDATION:")[-1].split("\n")[0].strip()
                votes[agent_name] = rec
            if "REASONING:" in content:
                reason = content.split("REASONING:")[-1].strip()
                reasoning[agent_name] = reason[:500]
        
        # Final decision synthesis
        votes_summary = "\n".join(f"- {agent}: {vote}" for agent, vote in votes.items())
        reasoning_summary = "\n".join(f"- {agent}: {reason}" for agent, reason in reasoning.items())
        
        synthesis = self.llm.call(
            "claude",
            [{"role": "user", "content": f"""Decision question: {question}

Agent votes:
{votes_summary}

Agent reasoning:
{reasoning_summary}

Make the final decision. If agents agree, confirm. If they disagree, weigh their reasoning and decide.
Format: DECISION: [choice] - [brief explanation]"""}],
            system_prompt="Make a clear, decisive recommendation."
        )
        
        dialogue.conclusion = synthesis["content"]
        dialogue.completed_at = datetime.now().isoformat()
        self._log_dialogue(dialogue)
        
        return {
            "decision": synthesis["content"],
            "votes": votes,
            "reasoning": reasoning,
            "dialogue": dialogue,
            "agents_used": agents,
            "consensus": len(set(votes.values())) == 1
        }
    
    def review(
        self,
        work: str,
        work_type: str = "code",
        reviewer_agent: str = "grok",
        author_agent: str = "claude",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Have one agent review another's work.
        
        Returns:
            Dict with 'feedback', 'approved', 'suggestions', 'dialogue'
        """
        dialogue_id = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        dialogue = AgentDialogue(
            id=dialogue_id,
            consultation_type=ConsultationType.REVIEW,
            topic=f"Review {work_type}",
            context=context or {},
            turns=[]
        )
        
        context_str = f"\n\nContext: {json.dumps(context)}" if context else ""
        
        review_prompt = f"""Review this {work_type} produced by {AGENTS[author_agent].name}:{context_str}

```
{work[:3000]}
```

Provide:
1. APPROVED: Yes/No
2. STRENGTHS: What's good
3. ISSUES: What needs fixing (be specific)
4. SUGGESTIONS: How to improve

Be direct and constructive."""
        
        response = self.llm.call(
            reviewer_agent,
            [{"role": "user", "content": review_prompt}],
            system_prompt=f"You are {AGENTS[reviewer_agent].name}, reviewing work as a peer. Be honest but constructive."
        )
        
        dialogue.turns.append(DialogueTurn(
            agent=reviewer_agent,
            role="reviewer",
            message=response["content"],
            tokens_used=response["tokens_used"],
            latency_ms=response["latency_ms"]
        ))
        
        dialogue.conclusion = response["content"]
        dialogue.completed_at = datetime.now().isoformat()
        self._log_dialogue(dialogue)
        
        # Parse response
        approved = "APPROVED: Yes" in response["content"] or "APPROVED: YES" in response["content"]
        
        return {
            "feedback": response["content"],
            "approved": approved,
            "reviewer": reviewer_agent,
            "author": author_agent,
            "dialogue": dialogue
        }


# =============================================================================
# TOWER INTEGRATION
# =============================================================================

def get_council() -> AgentCouncil:
    """Get a shared AgentCouncil instance."""
    return AgentCouncil()


def consult_on_decision(
    question: str,
    context: Dict = None,
    primary: str = "claude",
    consult: str = "grok"
) -> str:
    """
    Quick helper for consulting on a decision.
    
    Use this in tower code when you need a second opinion.
    
    Example:
        from execution.multi_agent_llm import consult_on_decision
        
        advice = consult_on_decision(
            "Should I send email or SMS for this follow-up?",
            context={"lead_quality": "warm", "days_since_contact": 3}
        )
    """
    council = get_council()
    result = council.consult(
        question=question,
        context=context,
        primary_agent=primary,
        consult_agent=consult
    )
    return result["conclusion"]


def brainstorm_solutions(
    problem: str,
    context: Dict = None,
    agents: List[str] = None
) -> List[str]:
    """
    Quick helper for brainstorming solutions.
    
    Returns list of synthesized ideas.
    """
    council = get_council()
    result = council.brainstorm(
        topic=problem,
        context=context,
        agents=agents or ["grok", "claude"]
    )
    return result["ideas"]


def get_decision(
    question: str,
    options: List[str] = None,
    context: Dict = None
) -> str:
    """
    Quick helper for getting a multi-agent decision.
    
    Returns the final decision.
    """
    council = get_council()
    result = council.decide(
        question=question,
        options=options,
        context=context
    )
    return result["decision"]


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Agent LLM Communication")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Consult command
    consult_p = subparsers.add_parser("consult", help="Consult an agent")
    consult_p.add_argument("question", help="Question to ask")
    consult_p.add_argument("--primary", default="claude")
    consult_p.add_argument("--consult", default="grok")
    
    # Brainstorm command
    brain_p = subparsers.add_parser("brainstorm", help="Brainstorm with agents")
    brain_p.add_argument("topic", help="Topic to brainstorm")
    brain_p.add_argument("--agents", nargs="+", default=["grok", "claude"])
    
    # Decide command
    decide_p = subparsers.add_parser("decide", help="Make a decision")
    decide_p.add_argument("question", help="Decision question")
    decide_p.add_argument("--options", nargs="+")
    
    # Review command
    review_p = subparsers.add_parser("review", help="Review work")
    review_p.add_argument("--file", required=True, help="File to review")
    review_p.add_argument("--reviewer", default="grok")
    
    # Status command
    subparsers.add_parser("status", help="Show available agents")
    
    args = parser.parse_args()
    council = AgentCouncil()
    
    if args.command == "consult":
        print(f"\n🤝 Consulting {args.consult} about: {args.question}\n")
        result = council.consult(
            question=args.question,
            primary_agent=args.primary,
            consult_agent=args.consult
        )
        print("=" * 60)
        print("DIALOGUE:")
        for turn in result["dialogue"].turns:
            print(f"\n[{turn.agent.upper()}] ({turn.role})")
            print(turn.message[:500] + "..." if len(turn.message) > 500 else turn.message)
        print("\n" + "=" * 60)
        print(f"\n✅ CONCLUSION:\n{result['conclusion']}")
        print(f"\n📊 Stats: {result['total_turns']} turns, {result['total_tokens']} tokens")
    
    elif args.command == "brainstorm":
        print(f"\n🧠 Brainstorming: {args.topic}\n")
        result = council.brainstorm(
            topic=args.topic,
            agents=args.agents
        )
        print("=" * 60)
        print("IDEAS:")
        for idea in result["ideas"]:
            print(f"  {idea}")
        print("\n" + "=" * 60)
        print(f"\n✅ SYNTHESIS:\n{result['synthesis']}")
    
    elif args.command == "decide":
        print(f"\n⚖️ Deciding: {args.question}\n")
        result = council.decide(
            question=args.question,
            options=args.options
        )
        print("VOTES:")
        for agent, vote in result["votes"].items():
            print(f"  {agent}: {vote}")
        print(f"\nConsensus: {'Yes' if result['consensus'] else 'No'}")
        print(f"\n✅ DECISION:\n{result['decision']}")
    
    elif args.command == "review":
        content = Path(args.file).read_text()
        print(f"\n📝 Reviewing: {args.file}\n")
        result = council.review(
            work=content,
            reviewer_agent=args.reviewer
        )
        print(f"Approved: {'✅ Yes' if result['approved'] else '❌ No'}")
        print(f"\nFeedback:\n{result['feedback']}")
    
    elif args.command == "status":
        print("\n📊 Available Agents:\n")
        for name, agent in AGENTS.items():
            print(f"  {agent.name} ({name})")
            print(f"    Provider: {agent.provider}")
            print(f"    Model: {agent.model}")
            print(f"    Best for: {', '.join(t.value for t in agent.best_for)}")
            print(f"    Strengths: {agent.strengths[0]}")
            print()


if __name__ == "__main__":
    main()
