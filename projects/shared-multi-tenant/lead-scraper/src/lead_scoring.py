#!/usr/bin/env python3
"""
Predictive Lead Scoring using Machine Learning

Uses logistic regression to predict lead response probability based on business attributes.

Features:
- category (gym, salon, restaurant, retail, ecommerce)
- review_count (numeric)
- has_website (boolean)
- location (Naples, Fort Myers, Bonita Springs)
- pain_point (no_website, few_reviews, etc)
- days_since_scrape (numeric)

Usage:
    # Train model on historical data
    python -m src.lead_scoring train

    # Score new leads
    python -m src.lead_scoring score --input scraped_leads.json --output scored_leads.json

    # Prioritize leads for a business
    python -m src.lead_scoring prioritize --business marceau-solutions --limit 100

    # Evaluate model performance
    python -m src.lead_scoring evaluate
"""

import argparse
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import pickle

# ML imports
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import roc_auc_score, precision_recall_curve, classification_report
    import numpy as np
except ImportError:
    print("ERROR: scikit-learn not installed. Install with: pip install scikit-learn numpy")
    exit(1)


@dataclass
class LeadScore:
    """Lead with predicted response score."""
    lead_id: str
    business_name: str
    phone: str
    category: str
    location: str

    # Features
    review_count: int
    has_website: bool
    pain_point: str
    days_since_scrape: int

    # Prediction
    response_probability: float  # 0-1
    lead_score: int  # 0-100 (scaled)
    priority_tier: str  # high, medium, low

    # For validation
    actual_responded: Optional[bool] = None


class LeadScoringModel:
    """ML-based lead scoring system."""

    def __init__(self, model_path: str = "output/lead_scoring_model.pkl"):
        self.model_path = Path(model_path)
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.category_map = {}
        self.location_map = {}
        self.pain_point_map = {}

    def _encode_features(self, leads: List[Dict]) -> np.ndarray:
        """
        Convert lead dicts to numeric feature matrix.

        Features (11 total):
        - category_gym, category_salon, category_restaurant, category_retail, category_ecommerce (5 one-hot)
        - review_count (1 numeric)
        - has_website (1 binary)
        - location_naples, location_fort_myers, location_bonita (3 one-hot)
        - days_since_scrape (1 numeric)
        """
        features = []

        for lead in leads:
            feature_vector = []

            # Category (one-hot encoding)
            category = lead.get("category", "unknown").lower()
            feature_vector.append(1 if "gym" in category or "fitness" in category else 0)
            feature_vector.append(1 if "salon" in category or "spa" in category or "beauty" in category else 0)
            feature_vector.append(1 if "restaurant" in category or "cafe" in category or "food" in category else 0)
            feature_vector.append(1 if "retail" in category or "store" in category else 0)
            feature_vector.append(1 if "ecommerce" in category or "online" in category else 0)

            # Review count (numeric)
            feature_vector.append(float(lead.get("review_count", 0)))

            # Has website (binary)
            feature_vector.append(1 if lead.get("has_website", False) else 0)

            # Location (one-hot encoding)
            business_name = lead.get("business_name", "").lower()
            feature_vector.append(1 if "naples" in business_name else 0)
            feature_vector.append(1 if "fort myers" in business_name or "ft myers" in business_name else 0)
            feature_vector.append(1 if "bonita" in business_name else 0)

            # Days since scrape (numeric)
            scrape_date = lead.get("scrape_date", lead.get("created_at", ""))
            if scrape_date:
                try:
                    scrape_dt = datetime.fromisoformat(scrape_date.replace("Z", "+00:00"))
                    days_ago = (datetime.now().astimezone() - scrape_dt).days
                    feature_vector.append(float(days_ago))
                except:
                    feature_vector.append(0.0)
            else:
                feature_vector.append(0.0)

            features.append(feature_vector)

        self.feature_names = [
            "category_gym", "category_salon", "category_restaurant", "category_retail", "category_ecommerce",
            "review_count", "has_website",
            "location_naples", "location_fort_myers", "location_bonita",
            "days_since_scrape"
        ]

        return np.array(features)

    def train(self, campaign_data_path: str = "output/campaign_analytics.json"):
        """
        Train logistic regression model on historical campaign data.

        Returns:
            Dict with training metrics (AUC, precision, recall)
        """
        print("Loading historical campaign data...")

        # Load campaign analytics
        with open(campaign_data_path, 'r') as f:
            analytics = json.load(f)

        # Extract leads with known outcomes
        training_leads = []
        labels = []

        for lead_id, lead_data in analytics.get("leads", {}).items():
            # Skip leads without enough history
            if lead_data.get("total_touches", 0) == 0:
                continue

            # Extract features
            lead_dict = {
                "lead_id": lead_id,
                "business_name": lead_data.get("business_name", ""),
                "category": lead_data.get("category", "unknown"),
                "review_count": lead_data.get("review_count", 0),
                "has_website": lead_data.get("has_website", False),
                "location": lead_data.get("location", "unknown"),
                "pain_point": lead_data.get("pain_point", "unknown"),
                "scrape_date": lead_data.get("first_contact_date", ""),
                "created_at": lead_data.get("first_contact_date", "")
            }

            # Label: did they respond?
            responded = lead_data.get("has_responded", False)

            training_leads.append(lead_dict)
            labels.append(1 if responded else 0)

        if len(training_leads) < 50:
            print(f"WARNING: Only {len(training_leads)} training examples. Need at least 50 for reliable model.")
            print("Run more campaigns first, then retrain.")
            return None

        print(f"Training on {len(training_leads)} leads ({sum(labels)} responders, {len(labels) - sum(labels)} non-responders)")

        # Encode features
        X = self._encode_features(training_leads)
        y = np.array(labels)

        # Split train/test (80/20)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train logistic regression
        print("Training logistic regression model...")
        self.model = LogisticRegression(max_iter=1000, random_state=42)
        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_proba = self.model.predict_proba(X_test_scaled)[:, 1]

        auc = roc_auc_score(y_test, y_proba)
        report = classification_report(y_test, y_pred, output_dict=True)

        print(f"\n✅ Model trained successfully!")
        print(f"   AUC-ROC: {auc:.3f}")
        print(f"   Precision: {report['1']['precision']:.3f}")
        print(f"   Recall: {report['1']['recall']:.3f}")

        # Feature importances
        print(f"\n📊 Most Important Features:")
        feature_importance = list(zip(self.feature_names, self.model.coef_[0]))
        feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)

        for feat, coef in feature_importance[:5]:
            direction = "increases" if coef > 0 else "decreases"
            print(f"   {feat}: {coef:+.3f} ({direction} response probability)")

        # Save model
        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "auc": auc,
            "precision": report['1']['precision'],
            "recall": report['1']['recall'],
            "trained_at": datetime.now().isoformat()
        }

        self.model_path.parent.mkdir(exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"\n💾 Model saved to: {self.model_path}")

        return {
            "auc": auc,
            "precision": report['1']['precision'],
            "recall": report['1']['recall'],
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }

    def load_model(self):
        """Load trained model from disk."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}. Run 'train' first.")

        with open(self.model_path, 'rb') as f:
            model_data = pickle.load(f)

        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.feature_names = model_data["feature_names"]

        print(f"✅ Model loaded from {self.model_path}")
        print(f"   Trained: {model_data.get('trained_at', 'unknown')}")
        print(f"   AUC: {model_data.get('auc', 0):.3f}")

    def score_leads(self, leads: List[Dict]) -> List[LeadScore]:
        """
        Score a list of leads.

        Args:
            leads: List of lead dicts with business_name, category, review_count, etc

        Returns:
            List of LeadScore objects with predictions
        """
        if self.model is None:
            self.load_model()

        # Encode features
        X = self._encode_features(leads)
        X_scaled = self.scaler.transform(X)

        # Predict probabilities
        probabilities = self.model.predict_proba(X_scaled)[:, 1]

        # Create scored leads
        scored_leads = []
        for lead, prob in zip(leads, probabilities):
            # Scale to 0-100
            score = int(prob * 100)

            # Priority tier
            if prob >= 0.15:  # Top 15% likely to respond
                tier = "high"
            elif prob >= 0.08:  # Middle 8-15%
                tier = "medium"
            else:
                tier = "low"

            scored_leads.append(LeadScore(
                lead_id=lead.get("lead_id", lead.get("phone", "unknown")),
                business_name=lead.get("business_name", ""),
                phone=lead.get("phone", ""),
                category=lead.get("category", "unknown"),
                location=lead.get("location", "unknown"),
                review_count=lead.get("review_count", 0),
                has_website=lead.get("has_website", False),
                pain_point=lead.get("pain_point", "unknown"),
                days_since_scrape=0,  # Calculate if needed
                response_probability=prob,
                lead_score=score,
                priority_tier=tier
            ))

        return scored_leads

    def prioritize_leads(self, business_id: str, limit: int = 100, scraped_leads_path: str = "output/scraped_leads.json") -> List[LeadScore]:
        """
        Get top N leads for a business, sorted by predicted response probability.

        Args:
            business_id: Business to filter for
            limit: Max leads to return
            scraped_leads_path: Path to scraped leads file

        Returns:
            Top N scored leads
        """
        # Load scraped leads
        with open(scraped_leads_path, 'r') as f:
            all_leads = json.load(f)

        # Filter by business (would need business-specific targeting logic)
        # For now, return top N across all leads

        # Score all leads
        scored = self.score_leads(all_leads)

        # Sort by score descending
        scored.sort(key=lambda x: x.response_probability, reverse=True)

        return scored[:limit]


def main():
    parser = argparse.ArgumentParser(description="Predictive Lead Scoring")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Train command
    train_parser = subparsers.add_parser("train", help="Train model on historical data")
    train_parser.add_argument("--data", default="output/campaign_analytics.json", help="Campaign data path")

    # Score command
    score_parser = subparsers.add_parser("score", help="Score leads")
    score_parser.add_argument("--input", required=True, help="Input leads file (JSON)")
    score_parser.add_argument("--output", default="output/scored_leads.json", help="Output scored leads file")

    # Prioritize command
    prioritize_parser = subparsers.add_parser("prioritize", help="Get top N leads for a business")
    prioritize_parser.add_argument("--business", required=True, help="Business ID")
    prioritize_parser.add_argument("--limit", type=int, default=100, help="Number of leads to return")
    prioritize_parser.add_argument("--input", default="output/scraped_leads.json", help="Scraped leads file")

    # Evaluate command
    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate model performance")

    args = parser.parse_args()

    # Change to project directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    scorer = LeadScoringModel()

    if args.command == "train":
        metrics = scorer.train(args.data)
        if metrics:
            print(f"\n✅ Training complete. Metrics: {json.dumps(metrics, indent=2)}")

    elif args.command == "score":
        # Load input leads
        with open(args.input, 'r') as f:
            leads = json.load(f)

        # Score
        scored = scorer.score_leads(leads)

        # Save
        output_path = Path(args.output)
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump([asdict(s) for s in scored], f, indent=2)

        print(f"✅ Scored {len(scored)} leads")
        print(f"   High priority: {sum(1 for s in scored if s.priority_tier == 'high')}")
        print(f"   Medium priority: {sum(1 for s in scored if s.priority_tier == 'medium')}")
        print(f"   Low priority: {sum(1 for s in scored if s.priority_tier == 'low')}")
        print(f"\n💾 Saved to: {output_path}")

    elif args.command == "prioritize":
        top_leads = scorer.prioritize_leads(args.business, args.limit, args.input)

        print(f"=" * 80)
        print(f"TOP {args.limit} LEADS FOR {args.business.upper()}")
        print(f"=" * 80)
        print(f"\n{'Rank':<6} {'Business':<30} {'Score':>7} {'Tier':>10} {'Category':<15}")
        print("-" * 80)

        for rank, lead in enumerate(top_leads, 1):
            tier_icon = "🔥" if lead.priority_tier == "high" else "⚡" if lead.priority_tier == "medium" else "💤"
            print(f"{rank:<6} {lead.business_name[:28]:<30} {lead.lead_score:>7} {tier_icon} {lead.priority_tier:>8} {lead.category:<15}")

        print(f"\n✅ Top {len(top_leads)} leads prioritized by ML model")
        print(f"   Average score: {sum(l.lead_score for l in top_leads) / len(top_leads):.1f}/100")

    elif args.command == "evaluate":
        # Load model and show performance
        scorer.load_model()
        print("\n✅ Model loaded successfully")
        print("   Run 'train' to retrain with latest data")

    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    exit(main())
