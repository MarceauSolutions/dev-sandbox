#!/usr/bin/env python3
"""
Intent Router for Interview Prep AI Assistant

Routes user requests to appropriate workflows using AI interpretation.
This enables a unified conversational interface where users can describe
what they need in natural language.

Architecture:
    User Input → Intent Classification → Route to Handler → Execute → Response

Supported Intents:
    - research: Research company and role
    - presentation: Generate PowerPoint
    - mock_interview: Start mock interview practice
    - cheat_sheet: Generate one-page cheat sheet
    - talking_points: Generate talking points
    - flashcards: Generate practice flashcards
    - checklist: Generate day-of checklist
    - edit: Edit existing presentation
    - help: Show available capabilities
    - unknown: Request clarification

Usage:
    # Route a user request
    python intent_router.py --input "Help me prepare for my Google PM interview"

    # Get structured intent
    python intent_router.py --input "Practice interview with me" --json

    # Interactive mode
    python intent_router.py --interactive
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
from enum import Enum

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from anthropic import Anthropic
except ImportError:
    print("Error: anthropic package required. Install with: pip install anthropic")
    sys.exit(1)


class Intent(Enum):
    """Supported user intents."""
    RESEARCH = "research"
    PRESENTATION = "presentation"
    MOCK_INTERVIEW = "mock_interview"
    CHEAT_SHEET = "cheat_sheet"
    TALKING_POINTS = "talking_points"
    FLASHCARDS = "flashcards"
    CHECKLIST = "checklist"
    EDIT = "edit"
    DOWNLOAD = "download"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class RoutedIntent:
    """Structured representation of a routed intent."""
    intent: str
    confidence: float  # 0.0 - 1.0
    company: Optional[str]
    role: Optional[str]
    parameters: dict
    suggested_response: str
    workflow: str  # Path to workflow file or command


class IntentRouter:
    """Routes user requests to appropriate interview prep workflows."""

    INTENT_DESCRIPTIONS = {
        Intent.RESEARCH: "Research a company and role for interview preparation",
        Intent.PRESENTATION: "Generate a PowerPoint presentation for interview prep",
        Intent.MOCK_INTERVIEW: "Practice with a simulated interview",
        Intent.CHEAT_SHEET: "Generate a one-page quick reference cheat sheet",
        Intent.TALKING_POINTS: "Generate key talking points and messages",
        Intent.FLASHCARDS: "Generate Q&A flashcards for practice",
        Intent.CHECKLIST: "Generate a day-of interview checklist",
        Intent.EDIT: "Edit an existing presentation",
        Intent.DOWNLOAD: "Download or export a file",
        Intent.HELP: "Show available capabilities",
        Intent.UNKNOWN: "Request needs clarification",
    }

    WORKFLOWS = {
        Intent.RESEARCH: "workflows/generate-presentation.md",
        Intent.PRESENTATION: "workflows/generate-presentation.md",
        Intent.MOCK_INTERVIEW: "workflows/mock-interview.md",
        Intent.CHEAT_SHEET: "workflows/quick-outputs.md",
        Intent.TALKING_POINTS: "workflows/quick-outputs.md",
        Intent.FLASHCARDS: "workflows/quick-outputs.md",
        Intent.CHECKLIST: "workflows/quick-outputs.md",
        Intent.EDIT: "workflows/live-editing-session.md",
        Intent.DOWNLOAD: "workflows/generate-presentation.md",
        Intent.HELP: None,
        Intent.UNKNOWN: None,
    }

    COMMANDS = {
        Intent.RESEARCH: "python execution/interview_research.py --company \"{company}\" --role \"{role}\"",
        Intent.PRESENTATION: "python execution/interview_research.py --company \"{company}\" --role \"{role}\" && python execution/pptx_generator.py --input .tmp/interview_research_{company_slug}.json",
        Intent.MOCK_INTERVIEW: "python interview-prep-pptx/src/mock_interview.py --company \"{company}\" --role \"{role}\" --type {interview_type}",
        Intent.CHEAT_SHEET: "python interview-prep-pptx/src/pdf_outputs.py --input .tmp/interview_research_{company_slug}.json --output cheat-sheet",
        Intent.TALKING_POINTS: "python interview-prep-pptx/src/pdf_outputs.py --input .tmp/interview_research_{company_slug}.json --output talking-points",
        Intent.FLASHCARDS: "python interview-prep-pptx/src/pdf_outputs.py --input .tmp/interview_research_{company_slug}.json --output flashcards",
        Intent.CHECKLIST: "python interview-prep-pptx/src/pdf_outputs.py --input .tmp/interview_research_{company_slug}.json --output checklist",
        Intent.EDIT: "python execution/live_editor.py --start {file_path}",
        Intent.DOWNLOAD: "python execution/download_pptx.py --input {file_path}",
        Intent.HELP: None,
        Intent.UNKNOWN: None,
    }

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")
        self.client = Anthropic(api_key=api_key)
        self.session_context = {
            "company": None,
            "role": None,
            "research_file": None,
            "presentation_file": None,
        }

    def classify_intent(self, user_input: str) -> RoutedIntent:
        """Classify user input and extract relevant parameters."""
        prompt = f"""You are an intent classifier for an Interview Prep AI Assistant.

Given the user's input, determine:
1. What they want to do (intent)
2. Key parameters (company name, role, etc.)
3. Confidence level

AVAILABLE INTENTS:
- research: User wants to research a company/role
- presentation: User wants to create a PowerPoint presentation
- mock_interview: User wants to practice interviewing
- cheat_sheet: User wants a one-page quick reference
- talking_points: User wants key messages to communicate
- flashcards: User wants Q&A practice cards
- checklist: User wants a day-of preparation checklist
- edit: User wants to modify an existing presentation
- download: User wants to download/export something
- help: User wants to know what they can do
- unknown: Request is unclear or unsupported

USER INPUT:
"{user_input}"

Respond in this exact JSON format:
{{
    "intent": "<intent_name>",
    "confidence": <0.0-1.0>,
    "company": "<company name or null>",
    "role": "<role/position or null>",
    "parameters": {{
        "interview_type": "<behavioral/technical/case/mixed or null>",
        "file_path": "<file path if mentioned or null>",
        "other": "<any other relevant parameters>"
    }},
    "reasoning": "<brief explanation of classification>"
}}

Return ONLY the JSON, no other text."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            result = json.loads(response.content[0].text)

            intent = Intent(result.get("intent", "unknown"))
            company = result.get("company") or self.session_context.get("company")
            role = result.get("role") or self.session_context.get("role")

            # Update session context
            if company:
                self.session_context["company"] = company
            if role:
                self.session_context["role"] = role

            # Build suggested response and workflow
            suggested_response = self._build_response(intent, company, role, result.get("parameters", {}))
            workflow = self._build_workflow(intent, company, role, result.get("parameters", {}))

            return RoutedIntent(
                intent=intent.value,
                confidence=result.get("confidence", 0.5),
                company=company,
                role=role,
                parameters=result.get("parameters", {}),
                suggested_response=suggested_response,
                workflow=workflow,
            )

        except Exception as e:
            # Fallback for errors
            return RoutedIntent(
                intent=Intent.UNKNOWN.value,
                confidence=0.0,
                company=None,
                role=None,
                parameters={"error": str(e)},
                suggested_response="I'm not sure what you'd like to do. Could you rephrase that?",
                workflow="",
            )

    def _build_response(self, intent: Intent, company: Optional[str], role: Optional[str], params: dict) -> str:
        """Build a suggested response for the classified intent."""
        responses = {
            Intent.RESEARCH: f"I'll research {company or '[company]'} for the {role or '[role]'} position. This will gather company info, role requirements, common interview questions, and talking points.",

            Intent.PRESENTATION: f"I'll create a PowerPoint presentation for your {role or '[role]'} interview at {company or '[company]'}. This includes company overview, role analysis, interview questions, and talking points.",

            Intent.MOCK_INTERVIEW: f"Let's practice! I'll conduct a {params.get('interview_type', 'behavioral')} mock interview for the {role or '[role]'} position at {company or '[company]'}. Ready to begin?",

            Intent.CHEAT_SHEET: f"I'll generate a one-page cheat sheet for your {company or '[company]'} interview. This is perfect for a quick review before the interview.",

            Intent.TALKING_POINTS: f"I'll create a talking points document with your key messages for the {company or '[company]'} interview.",

            Intent.FLASHCARDS: f"I'll generate Q&A flashcards based on common interview questions for {company or '[company]'}. Great for practice!",

            Intent.CHECKLIST: f"I'll create a day-of checklist to make sure you're fully prepared for your {company or '[company]'} interview.",

            Intent.EDIT: "I'll start a live editing session for the presentation. What changes would you like to make?",

            Intent.DOWNLOAD: "I'll help you download the file. Where would you like it saved?",

            Intent.HELP: """Here's what I can help you with:

**Research & Preparation**
- Research a company and role
- Create a PowerPoint presentation

**Practice**
- Mock interview (behavioral, technical, case)

**Quick References**
- One-page cheat sheet
- Talking points
- Q&A flashcards
- Day-of checklist

**Editing**
- Edit existing presentations
- Download files

What would you like to do?""",

            Intent.UNKNOWN: "I'm not sure what you'd like to do. Could you tell me:\n- Which company you're interviewing with?\n- What role/position?\n- What kind of help you need?",
        }

        return responses.get(intent, responses[Intent.UNKNOWN])

    def _build_workflow(self, intent: Intent, company: Optional[str], role: Optional[str], params: dict) -> str:
        """Build the command/workflow to execute."""
        command_template = self.COMMANDS.get(intent)
        if not command_template:
            return ""

        company_slug = (company or "").lower().replace(" ", "_")

        return command_template.format(
            company=company or "[COMPANY]",
            role=role or "[ROLE]",
            company_slug=company_slug,
            interview_type=params.get("interview_type", "behavioral"),
            file_path=params.get("file_path", ".tmp/interview_prep_{}.pptx".format(company_slug)),
        )

    def get_help_text(self) -> str:
        """Get help text showing available capabilities."""
        return """
# Interview Prep AI Assistant

## What I Can Do

### Research & Documents
- "Research [Company] for a [Role] interview"
- "Create a presentation for my [Company] interview"
- "Make me a cheat sheet"
- "Generate talking points"
- "Create flashcards for practice"
- "Make a day-of checklist"

### Practice
- "Practice interview with me"
- "Ask me behavioral questions"
- "Do a technical mock interview"
- "Quiz me on interview questions"

### Editing
- "Edit slide 3"
- "Make the theme consistent"
- "Download the presentation"

### Examples
- "Help me prepare for my Google PM interview"
- "I have an interview at Apple for Software Engineer next week"
- "Practice interviewing me for a Data Scientist role at Meta"
- "Give me a quick cheat sheet for my Amazon interview"
"""


def run_interactive_mode(router: IntentRouter):
    """Run interactive chat mode."""
    print("\n" + "=" * 60)
    print("Interview Prep AI Assistant")
    print("=" * 60)
    print("\nHi! I'm here to help you prepare for interviews.")
    print("Tell me what you need, or type 'help' for options.")
    print("Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! Good luck with your interviews!")
            break

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "q"]:
            print("\nGoodbye! Good luck with your interviews!")
            break

        if user_input.lower() == "help":
            print(router.get_help_text())
            continue

        # Route the intent
        routed = router.classify_intent(user_input)

        print(f"\n{'─' * 60}")
        print(f"Intent: {routed.intent} (confidence: {routed.confidence:.0%})")
        if routed.company:
            print(f"Company: {routed.company}")
        if routed.role:
            print(f"Role: {routed.role}")
        print(f"{'─' * 60}")

        print(f"\nAssistant: {routed.suggested_response}")

        if routed.workflow:
            print(f"\n📋 Command to execute:")
            print(f"   {routed.workflow}")

        print()


def main():
    parser = argparse.ArgumentParser(
        description="Route user requests to interview prep workflows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python intent_router.py --input "Help me prepare for my Google PM interview"
    python intent_router.py --input "Practice interview with me" --json
    python intent_router.py --interactive
        """
    )

    parser.add_argument("--input", help="User input to route")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--interactive", action="store_true", help="Interactive chat mode")

    args = parser.parse_args()

    router = IntentRouter()

    if args.interactive:
        run_interactive_mode(router)
    elif args.input:
        routed = router.classify_intent(args.input)

        if args.json:
            print(json.dumps(asdict(routed), indent=2))
        else:
            print(f"\nIntent: {routed.intent}")
            print(f"Confidence: {routed.confidence:.0%}")
            print(f"Company: {routed.company or 'Not specified'}")
            print(f"Role: {routed.role or 'Not specified'}")
            print(f"\nResponse: {routed.suggested_response}")
            if routed.workflow:
                print(f"\nWorkflow: {routed.workflow}")
    else:
        # Default to interactive mode
        run_interactive_mode(router)


if __name__ == "__main__":
    main()
