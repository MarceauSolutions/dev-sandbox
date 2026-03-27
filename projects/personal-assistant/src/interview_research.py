#!/usr/bin/env python3
"""
Interview Research Script
Researches a company and role to prepare interview insights.
Optionally parses resume/CV from PDF or Word documents.

Usage:
    python execution/interview_research.py --company "Apple" --role "Senior Product Manager"
    python execution/interview_research.py --company "Google" --role "Software Engineer" --resume ~/Documents/resume.pdf
    python execution/interview_research.py --company "Meta" --role "Data Scientist" --resume ~/resume.docx
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)


def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        print("Error: PyPDF2 not installed. Run: pip install PyPDF2")
        return ""

    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Warning: Could not parse PDF: {e}")
        return ""


def parse_docx(file_path: str) -> str:
    """Extract text from a Word document."""
    try:
        from docx import Document
    except ImportError:
        print("Error: python-docx not installed. Run: pip install python-docx")
        return ""

    try:
        doc = Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Warning: Could not parse Word document: {e}")
        return ""


def parse_resume(file_path: str) -> str:
    """Parse resume from PDF or Word document."""
    path = Path(file_path)

    if not path.exists():
        print(f"Warning: Resume file not found: {file_path}")
        return ""

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        print(f"📄 Parsing PDF resume: {path.name}")
        return parse_pdf(file_path)
    elif suffix in [".docx", ".doc"]:
        print(f"📄 Parsing Word resume: {path.name}")
        return parse_docx(file_path)
    elif suffix in [".txt", ".md"]:
        print(f"📄 Reading text resume: {path.name}")
        return path.read_text()
    else:
        print(f"Warning: Unsupported file format: {suffix}")
        print("Supported formats: .pdf, .docx, .doc, .txt, .md")
        return ""


class InterviewResearcher:
    """Researches companies and roles for interview preparation."""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not set.")
            print("Add it to your .env file or set it as an environment variable.")
            sys.exit(1)
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"

    def research_company(self, company: str, role: str, resume_text: str = None) -> dict:
        """
        Research a company and role for interview preparation.
        Optionally incorporates resume/experience for personalized insights.

        Returns structured data for PowerPoint generation.
        """

        # Build the prompt based on whether we have resume content
        resume_section = ""
        personalization_instructions = ""

        if resume_text:
            resume_section = f"""

**CANDIDATE'S RESUME/EXPERIENCE:**
{resume_text[:8000]}  # Truncate if too long

"""
            personalization_instructions = """

IMPORTANT - PERSONALIZATION REQUIREMENTS:
Since a resume was provided, you MUST personalize the response:
1. In "talking_points", reference SPECIFIC experiences from the resume that align with the role
2. In "interview_insights.common_questions", tailor the "strategy" to reference actual projects/skills from the resume
3. Add a new section "experience_highlights" with 5 specific experiences from the resume most relevant to this role
4. In "value_proposition", cite specific achievements and metrics from the resume
5. Make the presentation feel like it was written FOR this specific candidate, not generic advice
"""

        prompt = f"""You are an expert interview coach and business researcher. Research the following and provide comprehensive, actionable insights:
{resume_section}

**Company:** {company}
**Role:** {role}

Provide your research in the following JSON structure. Be specific, detailed, and include real information where possible:

{{
    "company_overview": {{
        "name": "{company}",
        "industry": "Primary industry",
        "founded": "Year founded",
        "headquarters": "Location",
        "employees": "Approximate employee count",
        "mission": "Company mission statement or core purpose",
        "key_products_services": ["Product 1", "Product 2", "Product 3"],
        "recent_news": ["Recent headline 1", "Recent headline 2", "Recent headline 3"]
    }},
    "company_culture": {{
        "core_values": ["Value 1", "Value 2", "Value 3"],
        "work_environment": "Description of work environment and culture",
        "leadership_style": "Description of leadership approach",
        "employee_reviews_summary": "Summary of common themes from employee reviews"
    }},
    "role_analysis": {{
        "title": "{role}",
        "department": "Likely department",
        "responsibilities": ["Key responsibility 1", "Key responsibility 2", "Key responsibility 3", "Key responsibility 4", "Key responsibility 5"],
        "required_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"],
        "success_metrics": ["How success is measured 1", "How success is measured 2", "How success is measured 3"],
        "growth_opportunities": "Career growth path from this role"
    }},
    "interview_insights": {{
        "common_questions": [
            {{"question": "Likely interview question 1", "strategy": "How to approach this question"}},
            {{"question": "Likely interview question 2", "strategy": "How to approach this question"}},
            {{"question": "Likely interview question 3", "strategy": "How to approach this question"}},
            {{"question": "Likely interview question 4", "strategy": "How to approach this question"}},
            {{"question": "Likely interview question 5", "strategy": "How to approach this question"}}
        ],
        "questions_to_ask": [
            "Smart question to ask interviewer 1",
            "Smart question to ask interviewer 2",
            "Smart question to ask interviewer 3",
            "Smart question to ask interviewer 4",
            "Smart question to ask interviewer 5"
        ],
        "red_flags_to_avoid": ["What NOT to do 1", "What NOT to do 2", "What NOT to do 3"],
        "differentiators": "What would make a candidate stand out for this role"
    }},
    "competitive_landscape": {{
        "main_competitors": ["Competitor 1", "Competitor 2", "Competitor 3"],
        "competitive_advantages": ["What makes {company} unique 1", "What makes {company} unique 2"],
        "industry_trends": ["Trend 1", "Trend 2", "Trend 3"]
    }},
    "preparation_checklist": [
        "Specific preparation step 1",
        "Specific preparation step 2",
        "Specific preparation step 3",
        "Specific preparation step 4",
        "Specific preparation step 5"
    ],
    "talking_points": {{
        "why_this_company": "Compelling reasons to want to work at {company}",
        "why_this_role": "Why this specific role is a great fit",
        "value_proposition": "What unique value the candidate can bring"
    }},
    "experience_highlights": [
        {{"experience": "Relevant experience from resume", "relevance": "How it applies to this role"}},
        {{"experience": "Another relevant experience", "relevance": "How it applies to this role"}},
        {{"experience": "Third relevant experience", "relevance": "How it applies to this role"}},
        {{"experience": "Fourth relevant experience", "relevance": "How it applies to this role"}},
        {{"experience": "Fifth relevant experience", "relevance": "How it applies to this role"}}
    ],
    "candidate_name": "Name from resume if available, otherwise 'Candidate'",
    "research_date": "{datetime.now().strftime('%Y-%m-%d')}"
}}
{personalization_instructions}
Return ONLY the JSON object, no additional text. Ensure all information is accurate and helpful for interview preparation."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract JSON from response
        content = response.content[0].text

        # Clean up response if needed
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        try:
            research_data = json.loads(content.strip())
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse JSON response. Error: {e}")
            print("Raw response:", content[:500])
            # Return a basic structure
            research_data = {
                "company_overview": {"name": company},
                "role_analysis": {"title": role},
                "error": "Failed to parse research data",
                "raw_response": content
            }

        return research_data


def generate_experience_images(research_data: dict, tmp_dir: Path) -> dict:
    """Generate AI images for experience highlights using Grok."""
    try:
        # Import the grok image generator
        from grok_image_gen import GrokImageGenerator
        generator = GrokImageGenerator()
    except Exception as e:
        print(f"⚠️ Could not load image generator: {e}")
        return research_data

    experiences = research_data.get("experience_highlights", [])
    if not experiences:
        return research_data

    # Generate images for each experience (max 5)
    for i, exp in enumerate(experiences[:5]):
        if isinstance(exp, dict):
            experience_text = exp.get("experience", "")
        else:
            experience_text = str(exp)

        # Create a professional prompt for the image
        prompt = f"Professional business illustration representing: {experience_text[:200]}. Clean, modern, corporate style, suitable for a presentation slide, no text, abstract visualization."

        try:
            print(f"   Generating image {i+1}/5: {experience_text[:50]}...")
            result = generator.generate_image(prompt, count=1)
            if result and len(result) > 0:
                if isinstance(exp, dict):
                    research_data["experience_highlights"][i]["image_url"] = result[0]
                else:
                    research_data["experience_highlights"][i] = {
                        "experience": experience_text,
                        "relevance": "",
                        "image_url": result[0]
                    }
        except Exception as e:
            print(f"   ⚠️ Could not generate image for experience {i+1}: {e}")

    return research_data


def main():
    parser = argparse.ArgumentParser(
        description="Research a company and role for interview preparation"
    )
    parser.add_argument(
        "--company", "-c",
        required=True,
        help="Company name to research"
    )
    parser.add_argument(
        "--role", "-r",
        required=True,
        help="Role/position to research"
    )
    parser.add_argument(
        "--resume",
        default=None,
        help="Path to resume file (PDF, DOCX, or TXT) for personalized insights"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path (default: .tmp/interview_research_{company}.json)"
    )
    parser.add_argument(
        "--generate-images",
        action="store_true",
        help="Generate AI images for experience highlights (requires XAI_API_KEY)"
    )

    args = parser.parse_args()

    # Ensure .tmp directory exists
    tmp_dir = Path(__file__).parent.parent / ".tmp"
    tmp_dir.mkdir(exist_ok=True)

    # Set default output path
    if args.output is None:
        safe_company = args.company.lower().replace(" ", "_").replace("/", "_")
        args.output = str(tmp_dir / f"interview_research_{safe_company}.json")

    # Parse resume if provided
    resume_text = None
    if args.resume:
        resume_text = parse_resume(args.resume)
        if resume_text:
            print(f"✅ Resume parsed: {len(resume_text)} characters extracted")
        else:
            print("⚠️ Could not parse resume, proceeding without personalization")

    print(f"\n🔍 Researching {args.company} for {args.role} position...")
    if resume_text:
        print("📋 Including personalized insights based on your resume")
    print()

    researcher = InterviewResearcher()

    try:
        research_data = researcher.research_company(args.company, args.role, resume_text)

        # Save to file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(research_data, f, indent=2)

        print(f"✅ Research complete!")
        print(f"📄 Saved to: {output_path}")
        print()

        # Print summary
        if "company_overview" in research_data:
            overview = research_data["company_overview"]
            print(f"📊 Company: {overview.get('name', args.company)}")
            print(f"   Industry: {overview.get('industry', 'N/A')}")
            print(f"   Mission: {overview.get('mission', 'N/A')[:100]}...")

        if "role_analysis" in research_data:
            role_info = research_data["role_analysis"]
            print(f"\n💼 Role: {role_info.get('title', args.role)}")
            skills = role_info.get("required_skills", [])[:3]
            print(f"   Key Skills: {', '.join(skills)}")

        if "interview_insights" in research_data:
            questions = research_data["interview_insights"].get("common_questions", [])
            print(f"\n❓ Common Questions: {len(questions)} identified")

        # Generate images for experience highlights if requested
        if args.generate_images and "experience_highlights" in research_data:
            print("\n🎨 Generating images for experience highlights...")
            research_data = generate_experience_images(research_data, tmp_dir)

            # Re-save with image URLs
            with open(output_path, "w") as f:
                json.dump(research_data, f, indent=2)
            print("✅ Images generated and saved to research data")

        # Print personalization summary if resume was used
        if resume_text and "experience_highlights" in research_data:
            highlights = research_data.get("experience_highlights", [])
            print(f"\n🎯 Experience Highlights: {len(highlights)} relevant experiences identified")
            candidate = research_data.get("candidate_name", "Candidate")
            if candidate != "Candidate":
                print(f"👤 Personalized for: {candidate}")

        print(f"\n→ Next: Run pptx_generator.py with this research file to create PowerPoint")

        return 0

    except Exception as e:
        print(f"❌ Error during research: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
