#!/usr/bin/env python3
"""
Chain/Franchise Detection - Filters out national chains from local outreach.

The Problem (Jan 2026):
We sent "you don't have a website" messages to Planet Fitness, LA Fitness,
Crunch Fitness, etc. - all national chains with major websites. This caused
high opt-out rates and reputation damage.

The Solution:
1. Maintain list of known national fitness chains
2. Fuzzy match business names against chain database
3. Flag chain locations for exclusion from "local business" outreach
4. Optionally: Different templates for chains vs independents

Usage:
    from chain_detector import ChainDetector

    detector = ChainDetector()

    # Check single business
    is_chain, chain_name, confidence = detector.is_chain("Planet Fitness Naples")
    # Returns: (True, "Planet Fitness", 0.95)

    # Filter lead list
    independent_leads = detector.filter_chains(leads)
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChainMatch:
    """Result of chain detection."""
    is_chain: bool
    chain_name: Optional[str]
    confidence: float
    reason: str


# National fitness chain database
# Format: canonical_name -> list of variations/aliases
NATIONAL_FITNESS_CHAINS = {
    # Major gym chains
    "Planet Fitness": [
        "planet fitness", "planetfitness", "planet fit"
    ],
    "LA Fitness": [
        "la fitness", "lafitness", "l.a. fitness", "la fit"
    ],
    "Gold's Gym": [
        "gold's gym", "golds gym", "gold gym", "goldsgym"
    ],
    "Anytime Fitness": [
        "anytime fitness", "anytimefitness", "anytime fit", "24/7 fitness anytime"
    ],
    "Crunch Fitness": [
        "crunch fitness", "crunch gym", "crunchfitness"
    ],
    "Orangetheory Fitness": [
        "orangetheory", "orange theory", "otf", "orangetheory fitness"
    ],
    "24 Hour Fitness": [
        "24 hour fitness", "24hour fitness", "24hr fitness", "24 hr fitness"
    ],
    "Equinox": [
        "equinox", "equinox fitness", "equinox gym"
    ],
    "Lifetime Fitness": [
        "lifetime fitness", "life time fitness", "lifetime athletic", "life time"
    ],
    "YMCA": [
        "ymca", "y.m.c.a.", "the y", "ymca of"
    ],

    # Boutique fitness chains
    "CrossFit": [
        "crossfit", "cross fit", "cf "  # Note: "cf " with space to avoid false positives
    ],
    "Pure Barre": [
        "pure barre", "purebarre"
    ],
    "Club Pilates": [
        "club pilates", "clubpilates"
    ],
    "SoulCycle": [
        "soulcycle", "soul cycle"
    ],
    "Barry's Bootcamp": [
        "barry's", "barrys bootcamp", "barry's bootcamp"
    ],
    "F45 Training": [
        "f45", "f45 training", "f 45"
    ],
    "Burn Boot Camp": [
        "burn boot camp", "burnbootcamp"
    ],
    "The Bar Method": [
        "bar method", "the bar method"
    ],
    "Barre3": [
        "barre3", "barre 3"
    ],

    # Yoga chains
    "CorePower Yoga": [
        "corepower", "core power yoga", "corepower yoga"
    ],
    "YogaWorks": [
        "yogaworks", "yoga works"
    ],
    "Hot Yoga": [  # Generic but often franchised
        "bikram yoga", "hot yoga"
    ],

    # MMA/Martial arts chains
    "UFC Gym": [
        "ufc gym", "ufcgym"
    ],
    "Title Boxing Club": [
        "title boxing", "title boxing club"
    ],
    "9Round": [
        "9round", "9 round", "nine round"
    ],

    # Personal training chains
    "Fitness Together": [
        "fitness together"
    ],
    "Snap Fitness": [
        "snap fitness", "snapfitness"
    ],

    # Recreation centers (often government-run)
    "RecPlex": [
        "recplex", "rec plex", "recreation center", "rec center"
    ],
}


# Franchise indicators in business names
FRANCHISE_INDICATORS = [
    r'\b#\d+\b',           # Store numbers: "#123"
    r'\bstore\s*\d+\b',    # "Store 45"
    r'\blocation\s*\d+\b', # "Location 12"
    r'\b-\s*\d{4,}\b',     # Long numbers often indicate franchise IDs
]


class ChainDetector:
    """Detects national fitness chains to filter from local outreach."""

    def __init__(self, custom_chains: Optional[Dict[str, List[str]]] = None):
        """
        Initialize chain detector.

        Args:
            custom_chains: Additional chains to detect (merged with defaults)
        """
        self.chains = NATIONAL_FITNESS_CHAINS.copy()
        if custom_chains:
            self.chains.update(custom_chains)

        # Build lookup index for fast matching
        self._build_index()

    def _build_index(self) -> None:
        """Build lowercase lookup index."""
        self.lookup = {}
        for canonical_name, variations in self.chains.items():
            for variation in variations:
                self.lookup[variation.lower().strip()] = canonical_name

    def _normalize(self, name: str) -> str:
        """Normalize business name for matching."""
        # Lowercase
        name = name.lower().strip()
        # Remove common suffixes
        name = re.sub(r'\b(llc|inc|corp|ltd|gym|fitness center|studio)\b', '', name)
        # Remove location indicators
        name = re.sub(r'\b(north|south|east|west|downtown|midtown|uptown)\b', '', name)
        # Remove city/state names (common ones)
        name = re.sub(r'\b(naples|miami|tampa|orlando|fort myers|bonita springs)\b', '', name)
        # Collapse whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    def is_chain(self, business_name: str) -> ChainMatch:
        """
        Check if a business is a national chain.

        Args:
            business_name: Name of the business to check

        Returns:
            ChainMatch with detection result
        """
        if not business_name:
            return ChainMatch(
                is_chain=False,
                chain_name=None,
                confidence=0.0,
                reason="Empty business name"
            )

        original_name = business_name
        normalized = self._normalize(business_name)

        # 1. Exact match in lookup
        for variation, canonical in self.lookup.items():
            if variation in normalized:
                # Calculate confidence based on match quality
                if normalized == variation:
                    confidence = 1.0
                elif normalized.startswith(variation):
                    confidence = 0.95
                else:
                    confidence = 0.85

                return ChainMatch(
                    is_chain=True,
                    chain_name=canonical,
                    confidence=confidence,
                    reason=f"Matched chain pattern: '{variation}'"
                )

        # 2. Check for franchise indicators
        for pattern in FRANCHISE_INDICATORS:
            if re.search(pattern, original_name, re.IGNORECASE):
                return ChainMatch(
                    is_chain=True,
                    chain_name=None,
                    confidence=0.6,
                    reason=f"Franchise indicator detected: {pattern}"
                )

        # 3. Not a chain
        return ChainMatch(
            is_chain=False,
            chain_name=None,
            confidence=0.9,
            reason="No chain patterns detected"
        )

    def filter_chains(
        self,
        leads: List[Dict],
        name_field: str = "business_name",
        include_chains: bool = False
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter leads into independents and chains.

        Args:
            leads: List of lead dictionaries
            name_field: Field containing business name
            include_chains: If True, return both lists; if False, only independents

        Returns:
            (independent_leads, chain_leads) if include_chains=True
            independent_leads only if include_chains=False
        """
        independents = []
        chains = []

        for lead in leads:
            name = lead.get(name_field, "")
            result = self.is_chain(name)

            # Add detection metadata
            lead_copy = lead.copy()
            lead_copy["_chain_detection"] = {
                "is_chain": result.is_chain,
                "chain_name": result.chain_name,
                "confidence": result.confidence,
                "reason": result.reason
            }

            if result.is_chain and result.confidence >= 0.7:
                chains.append(lead_copy)
                logger.debug(f"Chain detected: {name} -> {result.chain_name} ({result.confidence:.0%})")
            else:
                independents.append(lead_copy)

        logger.info(f"Filtered {len(leads)} leads: {len(independents)} independents, {len(chains)} chains")

        if include_chains:
            return independents, chains
        return independents

    def generate_report(self, leads: List[Dict], name_field: str = "business_name") -> str:
        """Generate a report of chain detection results."""
        independents, chains = self.filter_chains(leads, name_field, include_chains=True)

        lines = [
            "# Chain Detection Report",
            "",
            f"**Total Leads**: {len(leads)}",
            f"**Independent Businesses**: {len(independents)}",
            f"**National Chains**: {len(chains)}",
            "",
            "---",
            "",
        ]

        if chains:
            lines.append("## Detected Chains (Exclude from local outreach)")
            lines.append("")
            lines.append("| Business Name | Chain | Confidence |")
            lines.append("|---------------|-------|------------|")

            # Group by chain
            chain_groups = {}
            for lead in chains:
                detection = lead.get("_chain_detection", {})
                chain_name = detection.get("chain_name", "Unknown")
                if chain_name not in chain_groups:
                    chain_groups[chain_name] = []
                chain_groups[chain_name].append(lead)

            for chain_name, chain_leads in sorted(chain_groups.items()):
                for lead in chain_leads:
                    biz_name = lead.get(name_field, "Unknown")
                    confidence = lead.get("_chain_detection", {}).get("confidence", 0)
                    lines.append(f"| {biz_name} | {chain_name} | {confidence:.0%} |")

            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## Independent Businesses (Target for local outreach)")
        lines.append("")
        lines.append(f"Total: {len(independents)} businesses ready for outreach")
        lines.append("")

        return "\n".join(lines)


def main():
    """CLI for chain detection."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Chain Detection Tool")
    parser.add_argument("command", choices=["check", "filter", "report"],
                       help="Command to run")
    parser.add_argument("--name", type=str, help="Business name to check")
    parser.add_argument("--file", type=str, help="JSON file with leads")
    parser.add_argument("--field", type=str, default="business_name",
                       help="Field containing business name")
    parser.add_argument("--output", type=str, help="Output file")

    args = parser.parse_args()

    detector = ChainDetector()

    if args.command == "check":
        if not args.name:
            print("Error: --name required for check command")
            return

        result = detector.is_chain(args.name)
        print(f"\nBusiness: {args.name}")
        print(f"Is Chain: {result.is_chain}")
        print(f"Chain Name: {result.chain_name or 'N/A'}")
        print(f"Confidence: {result.confidence:.0%}")
        print(f"Reason: {result.reason}")

    elif args.command in ["filter", "report"]:
        if not args.file:
            print("Error: --file required for filter/report command")
            return

        with open(args.file, 'r') as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, list):
            leads = data
        elif isinstance(data, dict):
            leads = data.get("leads", data.get("records", data.get("sequences", [])))
        else:
            leads = []

        if args.command == "filter":
            independents, chains = detector.filter_chains(leads, args.field, include_chains=True)

            print(f"\n📊 CHAIN DETECTION RESULTS")
            print(f"=" * 50)
            print(f"Total Leads: {len(leads)}")
            print(f"Independent: {len(independents)}")
            print(f"Chains: {len(chains)}")

            if args.output:
                output_data = {
                    "independents": independents,
                    "chains": chains,
                    "summary": {
                        "total": len(leads),
                        "independent_count": len(independents),
                        "chain_count": len(chains)
                    }
                }
                with open(args.output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                print(f"\nSaved to: {args.output}")

        else:  # report
            report = detector.generate_report(leads, args.field)
            print(report)

            if args.output:
                with open(args.output, 'w') as f:
                    f.write(report)
                print(f"\nSaved to: {args.output}")


if __name__ == "__main__":
    main()
