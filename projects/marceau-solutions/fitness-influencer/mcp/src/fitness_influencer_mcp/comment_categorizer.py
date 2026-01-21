#!/usr/bin/env python3
"""
Comment Auto-Categorizer Module

Automatically categorizes social media comments and DMs into actionable categories
to help fitness influencers manage engagement at scale.

Categories:
- FAQ: Common questions that can be auto-replied
- SPAM: Promotional/spam content to filter
- COLLAB_REQUEST: Collaboration/partnership inquiries
- FAN_MESSAGE: Positive fan engagement to acknowledge
- BRAND_INQUIRY: Potential sponsorship/brand deal messages
- SUPPORT: Questions requiring detailed response
- NEGATIVE: Criticism/complaints to address
"""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class CategorizedComment:
    """A categorized comment with metadata."""
    original_text: str
    category: str
    confidence: float
    suggested_action: str
    priority: int  # 1-5, 1 being highest
    auto_reply_template: Optional[str] = None


class CommentCategorizer:
    """Categorize comments and DMs for fitness influencers."""

    # Category definitions with keywords and patterns
    CATEGORIES = {
        "FAQ": {
            "keywords": [
                "how do i", "how to", "what is", "what's your", "where can i",
                "when do you", "how long", "how much", "do you have", "can you explain",
                "what equipment", "what supplements", "what diet", "meal plan",
                "workout routine", "protein", "calories", "macros", "rest day"
            ],
            "priority": 3,
            "action": "Auto-reply with FAQ response or link to FAQ content",
            "templates": {
                "workout": "Great question! Check out my free workout guide in my bio link.",
                "diet": "I cover this in my nutrition guide! Link in bio.",
                "general": "Thanks for asking! I answer this in my pinned posts/highlights."
            }
        },
        "SPAM": {
            "keywords": [
                "dm me for", "check my profile", "free followers", "make money",
                "click link", "dm for collab", "promo code", "giveaway winner",
                "congratulations you won", "earn from home", "crypto", "nft"
            ],
            "priority": 5,  # Lowest priority
            "action": "Filter/hide automatically",
            "templates": {}
        },
        "COLLAB_REQUEST": {
            "keywords": [
                "collab", "collaboration", "partner", "partnership", "feature",
                "together", "join forces", "cross promote", "shoutout exchange",
                "would love to work", "interested in working", "let's connect"
            ],
            "priority": 2,
            "action": "Review for potential partnership",
            "templates": {
                "default": "Thanks for reaching out! Please email my business inbox: [EMAIL]"
            }
        },
        "FAN_MESSAGE": {
            "keywords": [
                "love your", "amazing", "inspired", "motivation", "thank you",
                "helped me", "changed my life", "you're the best", "keep it up",
                "great content", "love this", "so helpful", "you're awesome",
                "goals", "beast mode", "crushing it"
            ],
            "priority": 3,
            "action": "Like and consider brief reply",
            "templates": {
                "default": "Thank you so much! Keep crushing it!"
            }
        },
        "BRAND_INQUIRY": {
            "keywords": [
                "brand", "sponsor", "ambassador", "represent", "paid partnership",
                "compensation", "rate card", "media kit", "pr package", "campaign",
                "product review", "affiliate", "commission", "contract", "deal"
            ],
            "priority": 1,  # Highest priority
            "action": "Respond with media kit or direct to business email",
            "templates": {
                "default": "Thanks for reaching out! Please contact [EMAIL] for business inquiries."
            }
        },
        "SUPPORT": {
            "keywords": [
                "doesn't work", "can't access", "problem with", "issue",
                "help me", "not working", "broken", "error", "refund",
                "didn't receive", "where is my", "login", "password"
            ],
            "priority": 2,
            "action": "Respond with support solution or escalate",
            "templates": {
                "default": "Sorry to hear that! Please DM me the details so I can help."
            }
        },
        "NEGATIVE": {
            "keywords": [
                "scam", "fake", "don't trust", "waste of", "doesn't work",
                "liar", "fraud", "rip off", "terrible", "worst", "hate",
                "unsubscribe", "unfollowed", "disappointed"
            ],
            "priority": 2,
            "action": "Review and respond professionally if warranted",
            "templates": {
                "default": "I'm sorry you feel that way. I'd love to understand more - please DM me."
            }
        }
    }

    def __init__(self):
        """Initialize the categorizer."""
        # Pre-compile regex patterns for efficiency
        self._compiled_patterns = {}
        for category, config in self.CATEGORIES.items():
            patterns = [re.escape(kw) for kw in config["keywords"]]
            self._compiled_patterns[category] = re.compile(
                r'\b(' + '|'.join(patterns) + r')\b',
                re.IGNORECASE
            )

    def categorize_single(self, text: str) -> CategorizedComment:
        """
        Categorize a single comment or DM.

        Args:
            text: The comment/DM text to categorize

        Returns:
            CategorizedComment with category and metadata
        """
        text_lower = text.lower()
        scores = {}

        # Score each category based on keyword matches
        for category, pattern in self._compiled_patterns.items():
            matches = pattern.findall(text_lower)
            if matches:
                # Weight by number of matches and unique keywords
                score = len(matches) + len(set(matches)) * 0.5
                scores[category] = score

        # If no matches, default to FAN_MESSAGE for positive sentiment
        # or SUPPORT for question marks
        if not scores:
            if "?" in text:
                best_category = "FAQ"
                confidence = 0.4
            else:
                best_category = "FAN_MESSAGE"
                confidence = 0.3
        else:
            # Get highest scoring category
            best_category = max(scores, key=scores.get)
            max_score = scores[best_category]
            # Normalize confidence (cap at 0.95)
            confidence = min(0.95, max_score / 5)

        config = self.CATEGORIES[best_category]

        # Get appropriate template
        auto_reply = None
        if config["templates"]:
            auto_reply = config["templates"].get(
                "default",
                list(config["templates"].values())[0] if config["templates"] else None
            )

        return CategorizedComment(
            original_text=text,
            category=best_category,
            confidence=round(confidence, 2),
            suggested_action=config["action"],
            priority=config["priority"],
            auto_reply_template=auto_reply
        )

    def categorize_batch(self, comments: list[str]) -> dict:
        """
        Categorize multiple comments and return organized results.

        Args:
            comments: List of comment/DM texts

        Returns:
            Dictionary with categorized results and statistics
        """
        results = {
            "categorized": [],
            "by_category": {},
            "by_priority": {1: [], 2: [], 3: [], 4: [], 5: []},
            "statistics": {
                "total": len(comments),
                "category_counts": {},
                "avg_confidence": 0
            }
        }

        total_confidence = 0

        for text in comments:
            categorized = self.categorize_single(text)
            results["categorized"].append({
                "text": categorized.original_text[:100] + "..." if len(categorized.original_text) > 100 else categorized.original_text,
                "category": categorized.category,
                "confidence": categorized.confidence,
                "action": categorized.suggested_action,
                "priority": categorized.priority,
                "auto_reply": categorized.auto_reply_template
            })

            # Organize by category
            if categorized.category not in results["by_category"]:
                results["by_category"][categorized.category] = []
            results["by_category"][categorized.category].append(categorized.original_text)

            # Organize by priority
            results["by_priority"][categorized.priority].append(categorized.original_text)

            # Update stats
            if categorized.category not in results["statistics"]["category_counts"]:
                results["statistics"]["category_counts"][categorized.category] = 0
            results["statistics"]["category_counts"][categorized.category] += 1
            total_confidence += categorized.confidence

        # Calculate average confidence
        if comments:
            results["statistics"]["avg_confidence"] = round(total_confidence / len(comments), 2)

        # Add action recommendations
        results["recommendations"] = self._generate_recommendations(results)

        return results

    def _generate_recommendations(self, results: dict) -> list[str]:
        """Generate action recommendations based on categorization results."""
        recommendations = []
        counts = results["statistics"]["category_counts"]

        # Brand inquiries are highest priority
        if counts.get("BRAND_INQUIRY", 0) > 0:
            recommendations.append(
                f"URGENT: {counts['BRAND_INQUIRY']} brand inquiry/inquiries detected - respond within 24h"
            )

        # Support issues need attention
        if counts.get("SUPPORT", 0) > 0:
            recommendations.append(
                f"ACTION: {counts['SUPPORT']} support request(s) need attention"
            )

        # Collab requests
        if counts.get("COLLAB_REQUEST", 0) > 0:
            recommendations.append(
                f"REVIEW: {counts['COLLAB_REQUEST']} collaboration request(s) to evaluate"
            )

        # Negative feedback
        if counts.get("NEGATIVE", 0) > 0:
            recommendations.append(
                f"MONITOR: {counts['NEGATIVE']} negative comment(s) - consider professional response"
            )

        # FAQs - opportunity for content
        if counts.get("FAQ", 0) >= 5:
            recommendations.append(
                f"CONTENT IDEA: {counts['FAQ']} similar questions - consider creating FAQ content"
            )

        # Spam volume
        spam_count = counts.get("SPAM", 0)
        total = results["statistics"]["total"]
        if total > 0 and spam_count / total > 0.2:
            recommendations.append(
                f"CLEANUP: {spam_count} spam comments ({int(spam_count/total*100)}%) - consider auto-hide"
            )

        # Fan engagement
        if counts.get("FAN_MESSAGE", 0) >= 10:
            recommendations.append(
                f"ENGAGEMENT: {counts['FAN_MESSAGE']} fan messages - batch reply to maintain community"
            )

        return recommendations


# Convenience function for direct use
def categorize_comments(comments: list[str]) -> dict:
    """
    Convenience function to categorize a list of comments.

    Args:
        comments: List of comment texts

    Returns:
        Categorization results with statistics
    """
    categorizer = CommentCategorizer()
    return categorizer.categorize_batch(comments)
