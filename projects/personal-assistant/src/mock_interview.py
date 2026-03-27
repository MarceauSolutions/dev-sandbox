#!/usr/bin/env python3
"""
Mock Interview Module for Interview Prep AI Assistant

Simulates realistic interview experiences with:
- Company-specific interviewer personas
- Multiple interview types (behavioral, technical, case, cultural)
- Real-time feedback on responses
- STAR format evaluation
- Overall performance summary

Usage:
    # Start a behavioral interview
    python mock_interview.py --company "Google" --role "Product Manager" --type behavioral

    # Start with research context (uses existing research JSON)
    python mock_interview.py --company "Google" --role "Product Manager" --research .tmp/interview_research_google.json

    # Quick 5-question practice
    python mock_interview.py --company "Google" --role "Product Manager" --questions 5

    # API mode (returns JSON, for integration with chat interface)
    python mock_interview.py --api --action start --company "Google" --role "Product Manager"
    python mock_interview.py --api --action ask
    python mock_interview.py --api --action respond --response "My answer..."
    python mock_interview.py --api --action summary
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
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


class InterviewType(Enum):
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    CASE = "case"
    CULTURAL = "cultural"
    MIXED = "mixed"


@dataclass
class ResponseEvaluation:
    """Evaluation of a single response."""
    score: int  # 1-10
    star_format: dict  # {"situation": bool, "task": bool, "action": bool, "result": bool}
    strengths: list
    improvements: list
    follow_up_question: Optional[str]


@dataclass
class InterviewSession:
    """Tracks the state of a mock interview session."""
    session_id: str
    company: str
    role: str
    interview_type: InterviewType
    started_at: str
    questions: list
    responses: list
    evaluations: list
    current_question_index: int
    is_complete: bool
    research_context: Optional[dict]


class MockInterviewer:
    """Simulates an interviewer from the target company."""

    # Question banks by type
    BEHAVIORAL_QUESTIONS = [
        "Tell me about yourself and why you're interested in this role.",
        "Describe a time when you had to deal with a difficult colleague or stakeholder. How did you handle it?",
        "Tell me about a project that didn't go as planned. What happened and what did you learn?",
        "Give me an example of when you had to make a decision with incomplete information.",
        "Describe a time when you had to influence others without direct authority.",
        "Tell me about your biggest professional achievement. What made it successful?",
        "Describe a situation where you had to prioritize multiple competing deadlines.",
        "Tell me about a time you received critical feedback. How did you respond?",
        "Give an example of when you identified a problem before it became critical.",
        "Describe a time when you had to learn something new quickly to complete a project.",
    ]

    CULTURAL_QUESTIONS = [
        "Why are you interested in working at {company}?",
        "What do you know about our company culture and values?",
        "Where do you see yourself in 5 years?",
        "What motivates you in your work?",
        "How do you handle stress and pressure?",
        "What's your ideal work environment?",
        "How do you stay current with industry trends?",
        "What questions do you have for me about the team or company?",
    ]

    TECHNICAL_QUESTIONS = {
        "product manager": [
            "How would you prioritize features for a new product launch?",
            "Walk me through how you would approach defining metrics for a new feature.",
            "How do you gather and incorporate user feedback into product decisions?",
            "Describe your process for writing a product requirements document.",
            "How would you handle a situation where engineering says a feature will take 3x longer than expected?",
        ],
        "software engineer": [
            "Explain how you would design a URL shortening service.",
            "What's your approach to debugging a production issue?",
            "How do you ensure code quality in your projects?",
            "Describe a technically challenging problem you solved recently.",
            "How do you approach learning a new technology or framework?",
        ],
        "data scientist": [
            "Walk me through your approach to a new data analysis project.",
            "How do you handle missing or messy data?",
            "Explain a machine learning model you've built and its business impact.",
            "How do you communicate technical findings to non-technical stakeholders?",
            "What metrics would you use to evaluate model performance?",
        ],
        "default": [
            "Describe your approach to solving complex problems in your field.",
            "How do you stay current with developments in your area of expertise?",
            "Tell me about a technical challenge you overcame.",
            "How do you balance quality with speed of delivery?",
            "What tools or methodologies do you find most effective in your work?",
        ],
    }

    CASE_QUESTIONS = [
        "How would you approach entering a new market for {company}?",
        "If {company}'s main product saw a 20% drop in users, how would you investigate?",
        "How would you price a new subscription service?",
        "A competitor just launched a similar feature. How would you respond?",
        "How would you measure the success of a new initiative?",
    ]

    def __init__(
        self,
        company: str,
        role: str,
        interview_type: InterviewType = InterviewType.BEHAVIORAL,
        num_questions: int = 7,
        research_context: Optional[dict] = None,
    ):
        self.company = company
        self.role = role.lower()
        self.interview_type = interview_type
        self.num_questions = num_questions
        self.research_context = research_context

        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")
        self.client = Anthropic(api_key=api_key)

        # Create session
        self.session = InterviewSession(
            session_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            company=company,
            role=role,
            interview_type=interview_type,
            started_at=datetime.now().isoformat(),
            questions=[],
            responses=[],
            evaluations=[],
            current_question_index=0,
            is_complete=False,
            research_context=research_context,
        )

        # Generate questions for this session
        self._generate_questions()

    def _generate_questions(self):
        """Generate questions for the interview session."""
        questions = []

        if self.interview_type == InterviewType.BEHAVIORAL:
            questions = self.BEHAVIORAL_QUESTIONS[:self.num_questions]

        elif self.interview_type == InterviewType.CULTURAL:
            questions = [q.format(company=self.company) for q in self.CULTURAL_QUESTIONS[:self.num_questions]]

        elif self.interview_type == InterviewType.TECHNICAL:
            # Get role-specific questions or default
            role_key = self.role if self.role in self.TECHNICAL_QUESTIONS else "default"
            base_questions = self.TECHNICAL_QUESTIONS[role_key]
            questions = base_questions[:self.num_questions]

        elif self.interview_type == InterviewType.CASE:
            questions = [q.format(company=self.company) for q in self.CASE_QUESTIONS[:self.num_questions]]

        elif self.interview_type == InterviewType.MIXED:
            # Mix of all types
            questions = [
                self.BEHAVIORAL_QUESTIONS[0],  # Tell me about yourself
                self.CULTURAL_QUESTIONS[0].format(company=self.company),  # Why this company
                self.BEHAVIORAL_QUESTIONS[1],  # Difficult situation
            ]
            # Add technical if available
            role_key = self.role if self.role in self.TECHNICAL_QUESTIONS else "default"
            questions.append(self.TECHNICAL_QUESTIONS[role_key][0])
            questions.extend(self.BEHAVIORAL_QUESTIONS[2:self.num_questions-3])

        self.session.questions = questions

    def get_interviewer_intro(self) -> str:
        """Get the interviewer's introduction."""
        company_context = ""
        if self.research_context:
            culture = self.research_context.get("company_culture", {})
            values = culture.get("core_values", [])
            if values:
                company_context = f" At {self.company}, we really value {', '.join(values[:2])}."

        return f"""Hello! I'm excited to meet you today. I'm a hiring manager at {self.company} and I'll be conducting your interview for the {self.session.role} position.{company_context}

This will be a {self.interview_type.value} interview with about {len(self.session.questions)} questions. Take your time with your answers, and feel free to ask clarifying questions if needed.

Ready to begin?"""

    def get_next_question(self) -> Optional[str]:
        """Get the next question in the interview."""
        if self.session.current_question_index >= len(self.session.questions):
            self.session.is_complete = True
            return None

        question = self.session.questions[self.session.current_question_index]
        return question

    def evaluate_response(self, response: str) -> ResponseEvaluation:
        """Evaluate the user's response using Claude."""
        current_question = self.session.questions[self.session.current_question_index]

        # Build context for evaluation
        company_context = ""
        if self.research_context:
            role_info = self.research_context.get("role_analysis", {})
            skills = role_info.get("required_skills", [])
            if skills:
                company_context = f"\n\nKey skills for this role: {', '.join(skills[:5])}"

        prompt = f"""You are an expert interview coach evaluating a candidate's response.

INTERVIEW CONTEXT:
- Company: {self.company}
- Role: {self.session.role}
- Interview Type: {self.interview_type.value}{company_context}

QUESTION ASKED:
{current_question}

CANDIDATE'S RESPONSE:
{response}

Evaluate this response and provide feedback in the following JSON format:
{{
    "score": <1-10 integer>,
    "star_format": {{
        "situation": <true if clearly described context>,
        "task": <true if clearly described responsibility/goal>,
        "action": <true if clearly described specific actions taken>,
        "result": <true if clearly described outcomes/impact>
    }},
    "strengths": [<list of 2-3 specific things done well>],
    "improvements": [<list of 2-3 specific suggestions for improvement>],
    "follow_up_question": <optional follow-up question to dig deeper, or null>
}}

Be constructive and specific. Focus on interview best practices like:
- STAR format for behavioral questions
- Specificity and concrete examples
- Relevance to the role
- Quantifiable results when possible
- Appropriate length (1-2 minutes spoken)

Return ONLY the JSON, no other text."""

        try:
            response_obj = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            result = json.loads(response_obj.content[0].text)

            evaluation = ResponseEvaluation(
                score=result.get("score", 5),
                star_format=result.get("star_format", {}),
                strengths=result.get("strengths", []),
                improvements=result.get("improvements", []),
                follow_up_question=result.get("follow_up_question"),
            )
        except Exception as e:
            # Fallback evaluation
            evaluation = ResponseEvaluation(
                score=5,
                star_format={"situation": False, "task": False, "action": False, "result": False},
                strengths=["Response provided"],
                improvements=["Could not evaluate - try again"],
                follow_up_question=None,
            )

        # Store response and evaluation
        self.session.responses.append(response)
        self.session.evaluations.append(asdict(evaluation))

        # Move to next question
        self.session.current_question_index += 1

        return evaluation

    def get_summary(self) -> dict:
        """Get overall interview performance summary."""
        if not self.session.evaluations:
            return {"error": "No responses to summarize"}

        # Calculate averages
        scores = [e.get("score", 0) for e in self.session.evaluations]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Count STAR components
        star_counts = {"situation": 0, "task": 0, "action": 0, "result": 0}
        for e in self.session.evaluations:
            star = e.get("star_format", {})
            for key in star_counts:
                if star.get(key, False):
                    star_counts[key] += 1

        total_questions = len(self.session.evaluations)

        # Collect all strengths and improvements
        all_strengths = []
        all_improvements = []
        for e in self.session.evaluations:
            all_strengths.extend(e.get("strengths", []))
            all_improvements.extend(e.get("improvements", []))

        # Get top patterns
        from collections import Counter
        top_strengths = [s for s, _ in Counter(all_strengths).most_common(3)]
        top_improvements = [i for i, _ in Counter(all_improvements).most_common(3)]

        # Generate overall assessment
        if avg_score >= 8:
            overall = "Excellent"
            message = "You demonstrated strong interview skills across the board."
        elif avg_score >= 6:
            overall = "Good"
            message = "Solid performance with room for improvement in specific areas."
        elif avg_score >= 4:
            overall = "Developing"
            message = "Some good elements, but would benefit from more practice."
        else:
            overall = "Needs Practice"
            message = "Consider practicing with more mock interviews and refining your responses."

        return {
            "overall_rating": overall,
            "average_score": round(avg_score, 1),
            "total_questions": total_questions,
            "message": message,
            "star_format_usage": {
                "situation": f"{star_counts['situation']}/{total_questions}",
                "task": f"{star_counts['task']}/{total_questions}",
                "action": f"{star_counts['action']}/{total_questions}",
                "result": f"{star_counts['result']}/{total_questions}",
            },
            "top_strengths": top_strengths,
            "areas_to_improve": top_improvements,
            "session_details": {
                "company": self.company,
                "role": self.session.role,
                "interview_type": self.interview_type.value,
                "duration_questions": total_questions,
            },
        }

    def save_session(self, output_path: Optional[str] = None) -> str:
        """Save session to JSON file."""
        if output_path is None:
            output_path = f".tmp/mock_interview_{self.session.session_id}.json"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        session_data = {
            "session_id": self.session.session_id,
            "company": self.company,
            "role": self.session.role,
            "interview_type": self.interview_type.value,
            "started_at": self.session.started_at,
            "completed_at": datetime.now().isoformat(),
            "questions": self.session.questions,
            "responses": self.session.responses,
            "evaluations": self.session.evaluations,
            "summary": self.get_summary() if self.session.evaluations else None,
        }

        with open(output_path, "w") as f:
            json.dump(session_data, f, indent=2)

        return output_path


def run_interactive_interview(interviewer: MockInterviewer):
    """Run an interactive mock interview in the terminal."""
    print("\n" + "=" * 70)
    print(f"MOCK INTERVIEW: {interviewer.company} - {interviewer.session.role}")
    print(f"Type: {interviewer.interview_type.value.title()}")
    print("=" * 70)

    print(f"\n{interviewer.get_interviewer_intro()}\n")
    input("Press Enter when ready to begin...")

    question_num = 1
    while True:
        question = interviewer.get_next_question()
        if question is None:
            break

        print(f"\n{'─' * 70}")
        print(f"Question {question_num}:")
        print(f"\n  {question}\n")
        print("(Type your response, then press Enter twice to submit)")
        print("─" * 70)

        # Collect multi-line response
        lines = []
        while True:
            line = input()
            if line == "":
                if lines:
                    break
            else:
                lines.append(line)

        response = " ".join(lines)

        if response.lower() in ["quit", "exit", "q"]:
            print("\nEnding interview early...")
            break

        print("\nEvaluating your response...")
        evaluation = interviewer.evaluate_response(response)

        # Show feedback
        print(f"\n{'─' * 70}")
        print("FEEDBACK:")
        print(f"  Score: {evaluation.score}/10")
        print(f"\n  Strengths:")
        for s in evaluation.strengths:
            print(f"    + {s}")
        print(f"\n  Areas to improve:")
        for i in evaluation.improvements:
            print(f"    - {i}")

        star = evaluation.star_format
        star_check = f"S{'✓' if star.get('situation') else '○'} T{'✓' if star.get('task') else '○'} A{'✓' if star.get('action') else '○'} R{'✓' if star.get('result') else '○'}"
        print(f"\n  STAR Format: {star_check}")

        if evaluation.follow_up_question:
            print(f"\n  Follow-up to consider: {evaluation.follow_up_question}")

        question_num += 1
        input("\nPress Enter to continue...")

    # Show summary
    print("\n" + "=" * 70)
    print("INTERVIEW COMPLETE - SUMMARY")
    print("=" * 70)

    summary = interviewer.get_summary()
    print(f"\nOverall Rating: {summary['overall_rating']} ({summary['average_score']}/10)")
    print(f"\n{summary['message']}")

    print(f"\nSTAR Format Usage:")
    for component, usage in summary["star_format_usage"].items():
        print(f"  {component.title()}: {usage}")

    print(f"\nTop Strengths:")
    for s in summary["top_strengths"]:
        print(f"  + {s}")

    print(f"\nAreas to Improve:")
    for i in summary["areas_to_improve"]:
        print(f"  - {i}")

    # Save session
    output_path = interviewer.save_session()
    print(f"\nSession saved to: {output_path}")
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Mock Interview Practice for Interview Prep AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Interactive behavioral interview
    python mock_interview.py --company "Google" --role "Product Manager" --type behavioral

    # Quick 5-question practice
    python mock_interview.py --company "Apple" --role "Software Engineer" --questions 5

    # With research context
    python mock_interview.py --company "Meta" --role "Data Scientist" --research .tmp/interview_research_meta.json

    # API mode for chat integration
    python mock_interview.py --api --action start --company "Google" --role "PM"
        """
    )

    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--role", required=True, help="Role/position")
    parser.add_argument(
        "--type",
        choices=["behavioral", "technical", "case", "cultural", "mixed"],
        default="behavioral",
        help="Interview type (default: behavioral)"
    )
    parser.add_argument("--questions", type=int, default=7, help="Number of questions (default: 7)")
    parser.add_argument("--research", help="Path to research JSON for context")
    parser.add_argument("--api", action="store_true", help="API mode (returns JSON)")
    parser.add_argument("--action", choices=["start", "ask", "respond", "summary"], help="API action")
    parser.add_argument("--response", help="User response (for API respond action)")
    parser.add_argument("--session-file", help="Session file path (for API mode)")

    args = parser.parse_args()

    # Load research context if provided
    research_context = None
    if args.research and Path(args.research).exists():
        with open(args.research) as f:
            research_context = json.load(f)

    # Create interviewer
    interview_type = InterviewType(args.type)
    interviewer = MockInterviewer(
        company=args.company,
        role=args.role,
        interview_type=interview_type,
        num_questions=args.questions,
        research_context=research_context,
    )

    if args.api:
        # API mode - return JSON
        if args.action == "start":
            result = {
                "session_id": interviewer.session.session_id,
                "intro": interviewer.get_interviewer_intro(),
                "total_questions": len(interviewer.session.questions),
            }
        elif args.action == "ask":
            question = interviewer.get_next_question()
            result = {
                "question": question,
                "question_number": interviewer.session.current_question_index + 1,
                "is_complete": interviewer.session.is_complete,
            }
        elif args.action == "respond":
            if not args.response:
                result = {"error": "--response required for respond action"}
            else:
                evaluation = interviewer.evaluate_response(args.response)
                result = {
                    "evaluation": asdict(evaluation),
                    "questions_remaining": len(interviewer.session.questions) - interviewer.session.current_question_index,
                }
        elif args.action == "summary":
            result = interviewer.get_summary()
        else:
            result = {"error": "Invalid action"}

        print(json.dumps(result, indent=2))
    else:
        # Interactive mode
        run_interactive_interview(interviewer)


if __name__ == "__main__":
    main()
