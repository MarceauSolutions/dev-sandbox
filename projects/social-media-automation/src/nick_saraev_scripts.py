#!/usr/bin/env python3
"""
nick_saraev_scripts.py - Nick Saraev-Style Video Script Generator

Generates video scripts following Nick Saraev's proven format:
- Hook (0-8s): Pattern interrupt, grab attention
- Introduction (8-25s): Establish credibility, preview value
- Rising Action (25-70%): Build tension, deliver content
- Climax (70-90%): The big reveal/aha moment
- Resolution (90-100%): Recap, CTA, loop back

Adapted for fitness content while maintaining the core structure.

Usage:
    # Generate a single script
    python -m src.nick_saraev_scripts generate --type automation_tutorial --topic "email automation"

    # Generate YouTube long-form script
    python -m src.nick_saraev_scripts generate --type automation_tutorial --platform youtube --duration 600

    # Generate short-form script
    python -m src.nick_saraev_scripts generate --type contrarian --platform shorts --topic "cardio"

    # List available templates
    python -m src.nick_saraev_scripts templates
"""

import json
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ScriptSection:
    """A section of the video script."""
    name: str
    timing: str
    duration_seconds: int
    purpose: str
    script: str
    visual_notes: str
    delivery_notes: str


@dataclass
class NickSaraevScript:
    """Complete video script in Nick Saraev format."""
    id: str
    title: str
    platform: str  # youtube, shorts, x, tiktok
    duration_seconds: int
    content_type: str  # automation_tutorial, contrarian, case_study, comparison
    topic: str
    hook: ScriptSection
    introduction: ScriptSection
    rising_action: List[ScriptSection]
    climax: ScriptSection
    resolution: ScriptSection
    b_roll_shots: List[str]
    hashtags: List[str]
    thumbnail_ideas: List[str]
    created_at: str
    status: str = "pending"

    def to_markdown(self) -> str:
        """Export script as readable markdown."""
        md = f"""# {self.title}

**Platform:** {self.platform.upper()}
**Duration:** {self.duration_seconds}s ({self.duration_seconds // 60}:{self.duration_seconds % 60:02d})
**Type:** {self.content_type.replace('_', ' ').title()}
**Topic:** {self.topic}

---

## HOOK ({self.hook.timing})
*Purpose: {self.hook.purpose}*

**SAY THIS:**
> {self.hook.script}

**Visual:** {self.hook.visual_notes}
**Delivery:** {self.hook.delivery_notes}

---

## INTRODUCTION ({self.introduction.timing})
*Purpose: {self.introduction.purpose}*

**SAY THIS:**
> {self.introduction.script}

**Visual:** {self.introduction.visual_notes}
**Delivery:** {self.introduction.delivery_notes}

---

## RISING ACTION

"""
        for i, section in enumerate(self.rising_action, 1):
            md += f"""### Part {i}: {section.name} ({section.timing})
*Purpose: {section.purpose}*

**SAY THIS:**
> {section.script}

**Visual:** {section.visual_notes}
**Delivery:** {section.delivery_notes}

---

"""

        md += f"""## CLIMAX ({self.climax.timing})
*Purpose: {self.climax.purpose}*

**SAY THIS:**
> {self.climax.script}

**Visual:** {self.climax.visual_notes}
**Delivery:** {self.climax.delivery_notes}

---

## RESOLUTION ({self.resolution.timing})
*Purpose: {self.resolution.purpose}*

**SAY THIS:**
> {self.resolution.script}

**Visual:** {self.resolution.visual_notes}
**Delivery:** {self.resolution.delivery_notes}

---

## B-ROLL SHOT LIST

"""
        for shot in self.b_roll_shots:
            md += f"- [ ] {shot}\n"

        md += f"""

---

## THUMBNAIL IDEAS

"""
        for idea in self.thumbnail_ideas:
            md += f"- {idea}\n"

        md += f"""

---

## HASHTAGS

{' '.join(f'#{tag}' for tag in self.hashtags)}

---

*Script ID: {self.id}*
*Created: {self.created_at}*
*Status: {self.status}*
"""
        return md


# ============================================================================
# CONTENT TEMPLATES
# ============================================================================

class NickSaraevTemplates:
    """Templates for different Nick Saraev-style content types."""

    # Hook templates by content type
    HOOKS = {
        "automation_tutorial": [
            "This {tool} automation saves me {hours} hours every single week.",
            "Stop doing {task} manually. Here's the fix.",
            "I automated my entire {process}. Let me show you how.",
            "{Result} in {timeframe} using {tool}. Let me show you.",
            "This workflow replaced my {role}. And it cost me $0.",
        ],
        "contrarian_insight": [
            "Stop {common_practice}. It's killing your {metric}.",
            "Delete your {popular_tool}. Here's what to use instead.",
            "{Popular_advice}? That's completely wrong. Here's why.",
            "90% of people do {thing} wrong. Don't be one of them.",
            "Everything you know about {topic} is backwards.",
        ],
        "case_study": [
            "${revenue} in {timeframe}. Here's exactly what I did.",
            "I went from {before} to {after} in {timeframe}.",
            "This changed everything for my {business_type}.",
            "{Result} with one simple change.",
            "The system that took me from {start} to {end}.",
        ],
        "tool_comparison": [
            "{tool_a} vs {tool_b}: One of these is a complete waste of money.",
            "I've used both {tool_a} and {tool_b}. Here's the truth.",
            "Which is better: {tool_a} or {tool_b}? Finally answered.",
            "Stop choosing between {tool_a} and {tool_b}. Do this instead.",
            "{tool_a} is dead. Here's what to use now.",
        ],
    }

    # Fitness-adapted hooks
    FITNESS_HOOKS = {
        "workout_tutorial": [
            "This {exercise} technique builds {muscle_group} 2x faster.",
            "Stop doing {exercise} like this. Here's the fix.",
            "Perfect {exercise} form in 60 seconds.",
            "The {exercise} cue that changed everything.",
            "You're doing {exercise} wrong. Here's proof.",
        ],
        "training_insight": [
            "Your {split} is killing your gains. Here's why.",
            "This training principle changed my physique completely.",
            "Stop {common_practice}. Science says do this instead.",
            "The {concept} mistake 90% of lifters make.",
            "{Popular_advice}? Here's what actually works.",
        ],
        "transformation": [
            "How I built {result} in {timeframe}.",
            "From {before} to {after}. The exact plan.",
            "This workout split changed everything.",
            "{Result} with this one change.",
            "The system that got me to {goal}.",
        ],
        "nutrition_tip": [
            "Stop counting {metric}. Track this instead.",
            "The meal prep system that takes {time} minutes.",
            "This eating strategy doubled my energy.",
            "{Food} is sabotaging your gains. Here's why.",
            "The nutrition hack nobody talks about.",
        ],
    }

    # Introduction templates
    INTRODUCTIONS = {
        "credibility_marker": [
            "I've helped {number} {people} do exactly this.",
            "Over the past {years} years, I've tested everything.",
            "After {number} {projects}, I've figured out what works.",
            "My {audience} have used this to get {results}.",
        ],
        "preview": [
            "Today I'm going to show you {what}. By the end, you'll know {benefit}.",
            "In the next {duration}, you'll learn {what}.",
            "Here's exactly what we're covering: {list}.",
            "Stick around to the end because {reason}.",
        ],
    }

    # CTA templates
    CTAS = {
        "youtube": [
            "If this helped, smash that like button. Subscribe and hit the bell so you don't miss the next one.",
            "Drop a comment with your biggest takeaway. And subscribe for more content like this.",
            "Like this video if you found it valuable. See you in the next one.",
        ],
        "shorts": [
            "Follow for more. Link in bio.",
            "Save this. You'll need it.",
            "Follow for daily tips.",
        ],
        "x": [
            "Retweet if this helped. Follow for more.",
            "Link in bio for the full guide.",
            "Save this thread.",
        ],
    }

    # Visual and delivery notes
    VISUALS = {
        "hook": [
            "Direct to camera, slightly leaning in",
            "High energy, confident eye contact",
            "Hand gesture on key word",
        ],
        "screen_share": [
            "Cursor highlighting key areas",
            "Zoom in on important settings",
            "Picture-in-picture with face",
        ],
        "demonstration": [
            "Multiple angles of the movement",
            "Slow motion for form check",
            "Side-by-side comparison",
        ],
        "cta": [
            "Warm, conversational tone",
            "Point gesture to subscribe button",
            "Friendly smile",
        ],
    }


# ============================================================================
# SCRIPT GENERATOR
# ============================================================================

class NickSaraevScriptGenerator:
    """Generates video scripts in Nick Saraev's format."""

    OUTPUT_DIR = Path(__file__).parent.parent / "output" / "scripts" / "nick_style"
    TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

    # Platform configurations
    PLATFORMS = {
        "youtube": {
            "name": "YouTube Long-Form",
            "min_duration": 300,  # 5 minutes
            "max_duration": 900,  # 15 minutes
            "default_duration": 480,  # 8 minutes
            "rising_action_parts": 4,
        },
        "shorts": {
            "name": "YouTube Shorts / Reels / TikTok",
            "min_duration": 30,
            "max_duration": 60,
            "default_duration": 45,
            "rising_action_parts": 1,
        },
        "x": {
            "name": "X (Twitter) Video",
            "min_duration": 15,
            "max_duration": 60,
            "default_duration": 30,
            "rising_action_parts": 1,
        },
    }

    def __init__(self):
        """Initialize the script generator."""
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.templates = NickSaraevTemplates()
        self.nick_style = self._load_style_config()

    def _load_style_config(self) -> Dict:
        """Load the Nick Saraev style configuration."""
        style_file = self.TEMPLATES_DIR / "nick_saraev_style.json"
        if style_file.exists():
            with open(style_file) as f:
                return json.load(f)
        return {}

    def _generate_id(self) -> str:
        """Generate unique script ID."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"nick_{timestamp}_{random.randint(1000, 9999)}"

    def generate_script(
        self,
        content_type: str = "automation_tutorial",
        platform: str = "youtube",
        topic: Optional[str] = None,
        duration: Optional[int] = None,
        is_fitness: bool = True
    ) -> NickSaraevScript:
        """
        Generate a complete video script in Nick Saraev format.

        Args:
            content_type: Type of content (automation_tutorial, contrarian, etc.)
            platform: Target platform (youtube, shorts, x)
            topic: Specific topic (random if None)
            duration: Target duration in seconds
            is_fitness: Whether to use fitness-adapted content

        Returns:
            Complete NickSaraevScript
        """
        # Get platform config
        platform_config = self.PLATFORMS.get(platform, self.PLATFORMS["youtube"])

        # Set duration
        if duration is None:
            duration = platform_config["default_duration"]
        else:
            duration = max(platform_config["min_duration"],
                          min(duration, platform_config["max_duration"]))

        # Generate topic if not provided
        if topic is None:
            topic = self._generate_topic(content_type, is_fitness)

        # Calculate section timings
        timings = self._calculate_timings(duration, platform_config)

        # Generate each section
        hook = self._generate_hook(content_type, topic, timings["hook"], is_fitness)
        introduction = self._generate_introduction(topic, timings["intro"], is_fitness)
        rising_action = self._generate_rising_action(
            content_type, topic, timings["rising_action"],
            platform_config["rising_action_parts"], is_fitness
        )
        climax = self._generate_climax(content_type, topic, timings["climax"], is_fitness)
        resolution = self._generate_resolution(platform, timings["resolution"])

        # Generate supporting elements
        b_roll = self._generate_b_roll_shots(content_type, topic, is_fitness)
        hashtags = self._generate_hashtags(content_type, topic, platform, is_fitness)
        thumbnails = self._generate_thumbnail_ideas(content_type, topic)

        # Create script
        script = NickSaraevScript(
            id=self._generate_id(),
            title=self._generate_title(content_type, topic),
            platform=platform,
            duration_seconds=duration,
            content_type=content_type,
            topic=topic,
            hook=hook,
            introduction=introduction,
            rising_action=rising_action,
            climax=climax,
            resolution=resolution,
            b_roll_shots=b_roll,
            hashtags=hashtags,
            thumbnail_ideas=thumbnails,
            created_at=datetime.now().isoformat()
        )

        # Save to file
        self._save_script(script)

        return script

    def _calculate_timings(self, duration: int, platform_config: Dict) -> Dict:
        """Calculate timing for each section based on Nick's structure."""
        if platform_config["name"].startswith("YouTube Long"):
            # Long-form structure
            return {
                "hook": {"start": 0, "end": 8, "duration": 8},
                "intro": {"start": 8, "end": 25, "duration": 17},
                "rising_action": {
                    "start": 25,
                    "end": int(duration * 0.7),
                    "duration": int(duration * 0.7) - 25
                },
                "climax": {
                    "start": int(duration * 0.7),
                    "end": int(duration * 0.9),
                    "duration": int(duration * 0.2)
                },
                "resolution": {
                    "start": int(duration * 0.9),
                    "end": duration,
                    "duration": int(duration * 0.1)
                },
            }
        else:
            # Short-form structure (condensed)
            return {
                "hook": {"start": 0, "end": 3, "duration": 3},
                "intro": {"start": 3, "end": 8, "duration": 5},
                "rising_action": {
                    "start": 8,
                    "end": int(duration * 0.7),
                    "duration": int(duration * 0.7) - 8
                },
                "climax": {
                    "start": int(duration * 0.7),
                    "end": int(duration * 0.85),
                    "duration": int(duration * 0.15)
                },
                "resolution": {
                    "start": int(duration * 0.85),
                    "end": duration,
                    "duration": int(duration * 0.15)
                },
            }

    def _generate_topic(self, content_type: str, is_fitness: bool) -> str:
        """Generate a random topic based on content type."""
        fitness_topics = {
            "workout_tutorial": ["squats", "deadlifts", "bench press", "pull-ups", "lunges"],
            "training_insight": ["progressive overload", "rest days", "workout splits", "volume"],
            "transformation": ["muscle building", "fat loss", "strength gains", "physique"],
            "nutrition_tip": ["protein intake", "meal timing", "calories", "macros"],
        }

        automation_topics = {
            "automation_tutorial": ["email automation", "CRM workflows", "lead nurturing", "reporting"],
            "contrarian_insight": ["to-do lists", "time tracking", "meetings", "multitasking"],
            "case_study": ["agency scaling", "client acquisition", "systems building"],
            "tool_comparison": ["Make vs Zapier", "ChatGPT vs Claude", "Notion vs ClickUp"],
        }

        topics = fitness_topics if is_fitness else automation_topics
        topic_list = topics.get(content_type, list(topics.values())[0])
        return random.choice(topic_list)

    def _generate_hook(
        self, content_type: str, topic: str, timing: Dict, is_fitness: bool
    ) -> ScriptSection:
        """Generate the hook section."""
        hooks = (
            self.templates.FITNESS_HOOKS if is_fitness else self.templates.HOOKS
        )

        # Map content types for fitness
        hook_type = content_type
        if is_fitness and content_type == "automation_tutorial":
            hook_type = "workout_tutorial"
        elif is_fitness and content_type == "contrarian_insight":
            hook_type = "training_insight"
        elif is_fitness and content_type == "case_study":
            hook_type = "transformation"

        hook_templates = hooks.get(hook_type, hooks.get("workout_tutorial", []))
        hook_text = random.choice(hook_templates)

        # Fill in placeholders
        replacements = {
            "{exercise}": topic,
            "{muscle_group}": "muscle",
            "{topic}": topic,
            "{tool}": topic,
            "{task}": topic,
            "{hours}": str(random.randint(5, 20)),
            "{process}": topic,
            "{result}": "results",
            "{timeframe}": f"{random.randint(2, 12)} weeks",
            "{split}": "training split",
            "{concept}": topic,
            "{common_practice}": topic,
            "{metric}": "gains",
            "{Popular_advice}": f"Doing {topic} every day",
        }

        for placeholder, value in replacements.items():
            hook_text = hook_text.replace(placeholder, value)

        return ScriptSection(
            name="Hook",
            timing=f"{timing['start']}-{timing['end']}s",
            duration_seconds=timing["duration"],
            purpose="Pattern interrupt - grab attention immediately",
            script=hook_text,
            visual_notes=random.choice(self.templates.VISUALS["hook"]),
            delivery_notes="High energy, confident, slightly lean in toward camera"
        )

    def _generate_introduction(
        self, topic: str, timing: Dict, is_fitness: bool
    ) -> ScriptSection:
        """Generate the introduction section."""
        credibility = random.choice(self.templates.INTRODUCTIONS["credibility_marker"])
        preview = random.choice(self.templates.INTRODUCTIONS["preview"])

        # Fill placeholders
        credibility = credibility.replace("{number}", str(random.randint(100, 1000)))
        credibility = credibility.replace("{people}", "people" if is_fitness else "businesses")
        credibility = credibility.replace("{years}", str(random.randint(3, 10)))
        credibility = credibility.replace("{projects}", "projects")
        credibility = credibility.replace("{audience}", "clients" if is_fitness else "students")
        credibility = credibility.replace("{results}", "real results")

        preview = preview.replace("{what}", f"exactly how to master {topic}")
        preview = preview.replace("{benefit}", f"how to get better results with {topic}")
        preview = preview.replace("{duration}", "few minutes")
        preview = preview.replace("{list}", f"the setup, the execution, and the results")
        preview = preview.replace("{reason}", "I'm sharing my exact system")

        intro_script = f"{credibility} {preview}"

        return ScriptSection(
            name="Introduction",
            timing=f"{timing['start']}-{timing['end']}s",
            duration_seconds=timing["duration"],
            purpose="Establish credibility and preview value",
            script=intro_script,
            visual_notes="Medium close-up, confident posture",
            delivery_notes="Conversational but authoritative, build rapport"
        )

    def _generate_rising_action(
        self,
        content_type: str,
        topic: str,
        timing: Dict,
        num_parts: int,
        is_fitness: bool
    ) -> List[ScriptSection]:
        """Generate the rising action sections."""
        sections = []
        part_duration = timing["duration"] // max(num_parts, 1)

        if is_fitness and content_type in ["automation_tutorial", "workout_tutorial"]:
            # Step-by-step workout breakdown
            steps = [
                ("Setup", f"First, let's get your starting position right. For {topic}, you want to..."),
                ("Execution", f"Now, initiate the movement by... Focus on feeling your muscles work."),
                ("Common Mistakes", f"Here's where most people mess up. Don't do THIS..."),
                ("Pro Tips", f"The cue that changed everything for me: [specific tip]"),
            ]
        elif content_type == "contrarian_insight":
            steps = [
                ("The Conventional Wisdom", f"Everyone tells you to {topic}. Here's the problem..."),
                ("Why It's Wrong", "The research actually shows..."),
                ("What To Do Instead", "Here's what the top performers actually do..."),
                ("The Evidence", "Look at these results..."),
            ]
        else:
            steps = [
                ("The Problem", f"Most people struggle with {topic} because..."),
                ("The Insight", "What I discovered is..."),
                ("The System", "Here's the exact framework..."),
                ("Implementation", "To make this work for you..."),
            ]

        for i in range(num_parts):
            step = steps[i % len(steps)]
            start_time = timing["start"] + (i * part_duration)
            end_time = start_time + part_duration

            sections.append(ScriptSection(
                name=step[0],
                timing=f"{start_time}-{end_time}s",
                duration_seconds=part_duration,
                purpose=f"Build tension and deliver core content - Part {i + 1}",
                script=step[1],
                visual_notes="Screen share / demonstration as appropriate",
                delivery_notes="Building energy, maintaining engagement"
            ))

        return sections

    def _generate_climax(
        self, content_type: str, topic: str, timing: Dict, is_fitness: bool
    ) -> ScriptSection:
        """Generate the climax/aha moment section."""
        if is_fitness:
            climax_text = f"And THIS is the moment it all clicks. When you apply this to your {topic}, you'll feel the difference immediately. This is what separates the people who get results from everyone else."
        else:
            climax_text = f"And here's where it all comes together. This {topic} system, running exactly like I showed you, is what changed everything. Watch what happens when we run it..."

        return ScriptSection(
            name="Climax - The Big Reveal",
            timing=f"{timing['start']}-{timing['end']}s",
            duration_seconds=timing["duration"],
            purpose="Deliver the 'aha moment' - the key insight",
            script=climax_text,
            visual_notes="Peak energy, dramatic pause before reveal",
            delivery_notes="Slow down slightly for emphasis, then build to the reveal"
        )

    def _generate_resolution(self, platform: str, timing: Dict) -> ScriptSection:
        """Generate the resolution/CTA section."""
        ctas = self.templates.CTAS.get(platform, self.templates.CTAS["youtube"])
        cta_text = random.choice(ctas)

        recap = "So remember: [quick 3-point summary]. That's what's going to get you results."

        return ScriptSection(
            name="Resolution & CTA",
            timing=f"{timing['start']}-{timing['end']}s",
            duration_seconds=timing["duration"],
            purpose="Recap key points and call to action",
            script=f"{recap} {cta_text}",
            visual_notes=random.choice(self.templates.VISUALS["cta"]),
            delivery_notes="Warm, genuine, conversational close"
        )

    def _generate_title(self, content_type: str, topic: str) -> str:
        """Generate a video title."""
        templates = {
            "workout_tutorial": [
                f"Perfect {topic.title()} Form (99% Do This Wrong)",
                f"How to {topic.title()} for Maximum Gains",
                f"The {topic.title()} Technique That Changed Everything",
            ],
            "training_insight": [
                f"Stop {topic.title()}ing Like This (Here's Why)",
                f"The {topic.title()} Mistake Killing Your Gains",
                f"Why Your {topic.title()} Isn't Working",
            ],
            "automation_tutorial": [
                f"Automate Your {topic.title()} in 10 Minutes",
                f"This {topic.title()} Workflow Saves 20 Hours/Week",
                f"How I Automated {topic.title()} (Full Tutorial)",
            ],
            "contrarian_insight": [
                f"Stop {topic.title()} (Do This Instead)",
                f"Why {topic.title()} is Killing Your Progress",
                f"The {topic.title()} Lie Everyone Believes",
            ],
        }

        type_templates = templates.get(content_type, templates["workout_tutorial"])
        return random.choice(type_templates)

    def _generate_b_roll_shots(
        self, content_type: str, topic: str, is_fitness: bool
    ) -> List[str]:
        """Generate B-roll shot suggestions."""
        if is_fitness:
            return [
                f"Close-up of {topic} movement",
                "Multiple angles of exercise execution",
                "Slow-motion form demonstration",
                "Common mistake demonstration (what NOT to do)",
                "Correct form overlay comparison",
                "Equipment setup shot",
                "Wide gym establishing shot",
                "Post-workout satisfied expression",
            ]
        else:
            return [
                "Screen recording of tool in action",
                "Close-up of key settings/buttons",
                "Workflow diagram or flowchart",
                "Results dashboard/metrics",
                "Before/after comparison",
                "Quick typing/working shots",
                "Notification/automation trigger moment",
            ]

    def _generate_hashtags(
        self, content_type: str, topic: str, platform: str, is_fitness: bool
    ) -> List[str]:
        """Generate platform-appropriate hashtags."""
        base_fitness = ["FitnessCoach", "WorkoutTips", "GymLife", "FitnessTips", "Training"]
        base_automation = ["Automation", "NoCode", "Productivity", "AI", "Workflow"]

        topic_tag = topic.replace(" ", "").title()

        if is_fitness:
            tags = base_fitness + [topic_tag]
        else:
            tags = base_automation + [topic_tag]

        # Platform-specific
        if platform == "shorts":
            tags = tags[:5] + ["Shorts"]
        elif platform == "x":
            tags = tags[:3]

        return tags

    def _generate_thumbnail_ideas(self, content_type: str, topic: str) -> List[str]:
        """Generate thumbnail ideas."""
        return [
            f"Face with surprised expression + '{topic.upper()}' text",
            f"Before/after split with arrow",
            f"Bold text: 'STOP {topic.upper()}' with red X",
            f"Pointing at key visual element",
            f"Numbers/stats prominently featured",
        ]

    def _save_script(self, script: NickSaraevScript):
        """Save script to file."""
        # Save JSON
        json_path = self.OUTPUT_DIR / f"{script.id}.json"
        with open(json_path, 'w') as f:
            json.dump(asdict(script), f, indent=2)

        # Save Markdown
        md_path = self.OUTPUT_DIR / f"{script.id}.md"
        with open(md_path, 'w') as f:
            f.write(script.to_markdown())

    def list_scripts(self) -> List[Dict]:
        """List all generated scripts."""
        scripts = []
        for json_file in self.OUTPUT_DIR.glob("nick_*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    scripts.append({
                        "id": data["id"],
                        "title": data["title"],
                        "platform": data["platform"],
                        "content_type": data["content_type"],
                        "created_at": data["created_at"],
                        "status": data.get("status", "pending"),
                    })
            except Exception:
                pass
        return sorted(scripts, key=lambda x: x["created_at"], reverse=True)


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI for Nick Saraev script generator."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Nick Saraev-Style Video Script Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate fitness tutorial script:
    python -m src.nick_saraev_scripts generate --type workout_tutorial --topic "squats"

  Generate long-form YouTube script:
    python -m src.nick_saraev_scripts generate --platform youtube --duration 600

  Generate short-form script:
    python -m src.nick_saraev_scripts generate --platform shorts --type training_insight

  List all scripts:
    python -m src.nick_saraev_scripts list

  Show available templates:
    python -m src.nick_saraev_scripts templates
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate a new script')
    gen_parser.add_argument('--type', '-t', default='workout_tutorial',
                           choices=['workout_tutorial', 'training_insight', 'transformation',
                                   'nutrition_tip', 'automation_tutorial', 'contrarian_insight',
                                   'case_study', 'tool_comparison'],
                           help='Content type')
    gen_parser.add_argument('--platform', '-p', default='youtube',
                           choices=['youtube', 'shorts', 'x'],
                           help='Target platform')
    gen_parser.add_argument('--topic', help='Specific topic (random if not provided)')
    gen_parser.add_argument('--duration', type=int, help='Target duration in seconds')
    gen_parser.add_argument('--automation', action='store_true',
                           help='Generate automation content instead of fitness')
    gen_parser.add_argument('--output', '-o', help='Output file path for markdown')

    # List command
    subparsers.add_parser('list', help='List all generated scripts')

    # Templates command
    subparsers.add_parser('templates', help='Show available content templates')

    args = parser.parse_args()

    generator = NickSaraevScriptGenerator()

    if args.command == 'generate':
        is_fitness = not args.automation

        script = generator.generate_script(
            content_type=args.type,
            platform=args.platform,
            topic=args.topic,
            duration=args.duration,
            is_fitness=is_fitness
        )

        print(f"\n{'=' * 60}")
        print(f"SCRIPT GENERATED: {script.title}")
        print(f"{'=' * 60}")
        print(f"ID: {script.id}")
        print(f"Platform: {script.platform}")
        print(f"Duration: {script.duration_seconds}s")
        print(f"Content Type: {script.content_type}")
        print(f"Topic: {script.topic}")
        print(f"\nFiles saved:")
        print(f"  JSON: {generator.OUTPUT_DIR / f'{script.id}.json'}")
        print(f"  Markdown: {generator.OUTPUT_DIR / f'{script.id}.md'}")

        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                f.write(script.to_markdown())
            print(f"  Custom: {output_path}")

        print(f"\n{'=' * 60}")
        print("\nHOOK PREVIEW:")
        print(f"> {script.hook.script}")
        print(f"{'=' * 60}\n")

    elif args.command == 'list':
        scripts = generator.list_scripts()

        print(f"\n{'=' * 60}")
        print("GENERATED SCRIPTS")
        print(f"{'=' * 60}")

        if not scripts:
            print("No scripts generated yet.")
        else:
            for s in scripts:
                print(f"\n[{s['id']}]")
                print(f"  {s['title']}")
                print(f"  Platform: {s['platform']} | Type: {s['content_type']}")
                print(f"  Created: {s['created_at'][:10]} | Status: {s['status']}")

        print(f"\n{'=' * 60}\n")

    elif args.command == 'templates':
        print("\n" + "=" * 60)
        print("AVAILABLE CONTENT TEMPLATES")
        print("=" * 60)

        print("\nFITNESS TEMPLATES:")
        print("-" * 40)
        for template_type in ["workout_tutorial", "training_insight", "transformation", "nutrition_tip"]:
            print(f"\n  {template_type}:")
            for hook in NickSaraevTemplates.FITNESS_HOOKS.get(template_type, [])[:2]:
                print(f"    - {hook[:50]}...")

        print("\n\nAUTOMATION TEMPLATES:")
        print("-" * 40)
        for template_type in ["automation_tutorial", "contrarian_insight", "case_study", "tool_comparison"]:
            print(f"\n  {template_type}:")
            for hook in NickSaraevTemplates.HOOKS.get(template_type, [])[:2]:
                print(f"    - {hook[:50]}...")

        print(f"\n{'=' * 60}\n")

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
