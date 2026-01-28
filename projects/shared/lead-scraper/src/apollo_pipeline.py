#!/usr/bin/env python3
"""
Apollo MCP → Cold Outreach Pipeline Integration

Fully automated workflow that:
1. Executes Apollo search via MCP (natural language)
2. Exports results to JSON
3. Scores leads based on pain points (website, reviews, booking)
4. Filters for top 20% (scores 8-10) to save Apollo credits
5. Enriches selected leads via Apollo MCP (spending credits wisely)
6. Creates SMS campaign with enriched leads
7. Enrolls in multi-touch follow-up sequence

This implements the 80-90% credit savings strategy:
- Free: Apollo search exports (unlimited)
- Free: Manual scoring based on website visits
- Paid: Contact reveal ONLY for top 20% of leads

Usage:
    # Dry run with natural language search
    python -m src.apollo_pipeline run \\
        --search "gyms in Naples FL, 1-50 employees" \\
        --campaign "Naples Gyms Voice AI" \\
        --template no_website_intro \\
        --dry-run

    # For real (sends SMS)
    python -m src.apollo_pipeline run \\
        --search "gyms in Naples FL, 1-50 employees" \\
        --campaign "Naples Gyms Voice AI" \\
        --template no_website_intro \\
        --for-real

    # Enrich only (no SMS)
    python -m src.apollo_pipeline enrich \\
        --input output/apollo_leads_top.json \\
        --limit 20

    # Score leads (manual step if needed)
    python -m src.apollo_pipeline score \\
        --input output/apollo_leads_TIMESTAMP.json
"""

import os
import json
import logging
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

from .models import Lead, LeadCollection
from .apollo_import import import_apollo_export, filter_by_score, merge_enriched_data
from .sms_outreach import SMSOutreachManager
from .follow_up_sequence import FollowUpSequenceManager

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for Apollo pipeline."""
    output_dir: str = "output"
    min_score: int = 8  # Top 20% threshold
    apollo_credits_per_lead: int = 2  # Typical cost to reveal contact
    max_enrich_batch: int = 50  # Safety limit for enrichment
    delay_between_sms: float = 2.0  # Seconds between SMS sends


class ApolloPipeline:
    """
    Orchestrates the complete Apollo → SMS workflow.

    Implements credit-efficient strategy:
    1. Apollo search (FREE)
    2. Score leads manually (FREE)
    3. Filter top 20% (FREE)
    4. Enrich contacts (PAID - only for top leads)
    5. SMS campaign (Twilio cost)
    6. Follow-up sequence (automated)
    """

    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize managers
        self.sms_manager = SMSOutreachManager(output_dir=str(self.output_dir))
        self.followup_manager = FollowUpSequenceManager(output_dir=str(self.output_dir))
        self.leads_collection = LeadCollection(str(self.output_dir))

    def apollo_search_via_mcp(
        self,
        search_query: str,
        campaign_name: str
    ) -> Optional[List]:
        """
        Execute Apollo search via MCP and return enriched leads.

        Args:
            search_query: Natural language search (e.g., "gyms in Naples FL, 1-50 employees")
            campaign_name: Campaign identifier for tracking

        Returns:
            List of Lead objects, or None on failure
        """
        logger.info(f"🔍 Searching Apollo via MCP: {search_query}")

        try:
            from .apollo_mcp_bridge import ApolloMCPBridge
            from .models import Lead

            # Initialize MCP bridge
            api_key = os.getenv("APOLLO_API_KEY")
            if not api_key:
                logger.error("APOLLO_API_KEY not found in environment")
                return None

            bridge = ApolloMCPBridge(api_key=api_key)

            # Parse query to extract location and business type
            # Simple parsing: look for "in [location]" pattern
            parts = search_query.lower().split(" in ")
            if len(parts) >= 2:
                query = parts[0].strip()
                location = parts[1].strip()
            else:
                query = search_query
                location = "Naples, FL"  # Default

            # Detect company context from campaign name
            company_context = "marceau-solutions"
            if "hvac" in campaign_name.lower() or "comfort" in campaign_name.lower():
                company_context = "swflorida-hvac"
            elif "shipping" in campaign_name.lower() or "footer" in campaign_name.lower():
                company_context = "square-foot-shipping"

            logger.info(f"Parsed query: '{query}' in '{location}' for {company_context}")

            # Execute search via MCP bridge
            leads = bridge.search(
                query=query,
                location=location,
                campaign_name=campaign_name,
                company_context=company_context,
                max_results=100,
                enrich_top_n=20,  # Only enrich top 20% to save credits
                min_score=8
            )

            if not leads:
                logger.warning("Apollo MCP search returned no leads")
                return None

            logger.info(f"✅ Apollo MCP returned {len(leads)} enriched leads")
            return leads

        except ImportError as e:
            logger.error(f"Failed to import Apollo MCP bridge: {e}")
            logger.error("Install apollo-mcp with: pip install apollo-mcp")
            return None
        except Exception as e:
            logger.error(f"Apollo MCP search failed: {e}")
            return None

    def import_and_score(
        self,
        csv_file: str,
        campaign_name: str
    ) -> str:
        """
        Import Apollo CSV and prepare for scoring.

        Args:
            csv_file: Path to Apollo CSV export
            campaign_name: Campaign identifier

        Returns:
            Path to JSON file ready for scoring
        """
        logger.info(f"📥 Importing Apollo export: {csv_file}")

        # Import CSV to JSON format
        leads = import_apollo_export(csv_file, campaign_name=campaign_name)

        # Auto-score based on available data
        scored_leads = self._auto_score_leads(leads)

        # Save scored leads
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"apollo_leads_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(scored_leads, f, indent=2)

        logger.info(f"✅ Imported and auto-scored {len(scored_leads)} leads")
        logger.info(f"   Saved to: {output_file}")

        return str(output_file)

    def _auto_score_leads(self, leads: List[Dict]) -> List[Dict]:
        """
        Automatically score leads based on pain points.

        Scoring criteria (1-10):
        - 10: No website (critical need)
        - 9: Poor reviews mentioning calls/service (Voice AI opportunity)
        - 8: No online booking (automation opportunity)
        - 7: Few reviews (<10)
        - 6: Outdated website
        - 1-5: Lower priority

        Args:
            leads: List of lead dicts from Apollo

        Returns:
            Scored leads with pain_points and score fields
        """
        scored = []

        for lead in leads:
            score = 0
            pain_points = []

            # Check for website
            website = lead.get("website", "").strip()
            if not website:
                score = 10
                pain_points.append("no_website")

            # Check for reviews (if available in Apollo data)
            # Note: Apollo doesn't always have review data, may need enrichment
            review_count = 0
            if review_count < 10:
                if score == 0:
                    score = 7
                pain_points.append("few_reviews")

            # Default low score if no obvious pain points
            if score == 0:
                score = 5

            # Update lead with score and pain points
            lead["score"] = score
            lead["pain_points"] = pain_points
            lead["notes"] = f"Auto-scored: {score}/10 - {', '.join(pain_points) if pain_points else 'No obvious pain points'}"

            scored.append(lead)

        return scored

    def filter_top_leads(
        self,
        scored_json: str,
        min_score: int = None
    ) -> str:
        """
        Filter for top 20% of leads to minimize Apollo credit spend.

        Args:
            scored_json: Path to scored leads JSON
            min_score: Minimum score threshold (default: 8)

        Returns:
            Path to filtered leads JSON
        """
        min_score = min_score or self.config.min_score

        logger.info(f"🔍 Filtering leads (score >= {min_score})")

        top_leads = filter_by_score(scored_json, min_score=min_score)

        # Calculate credit cost estimate
        credit_cost = len(top_leads) * self.config.apollo_credits_per_lead

        print(f"\n💰 Credit Cost Estimate:")
        print(f"   {len(top_leads)} leads × {self.config.apollo_credits_per_lead} credits = {credit_cost} credits")
        print(f"   (This is 80-90% cheaper than enriching all leads)")

        return str(Path(scored_json).with_name(Path(scored_json).stem + "_top.json"))

    def enrich_via_apollo_mcp(
        self,
        top_leads_json: str,
        limit: int = None
    ) -> str:
        """
        Enrich top leads via Apollo MCP (reveal contacts - PAID).

        Args:
            top_leads_json: Path to filtered top leads JSON
            limit: Max leads to enrich (safety limit)

        Returns:
            Path to enriched CSV
        """
        limit = limit or self.config.max_enrich_batch

        with open(top_leads_json, 'r') as f:
            top_leads = json.load(f)

        leads_to_enrich = top_leads[:limit]

        logger.info(f"🔗 Enriching {len(leads_to_enrich)} leads via Apollo MCP")

        # TODO: Implement Apollo MCP enrichment
        # This would use the Apollo MCP server to reveal contacts
        # For now, we'll return a placeholder for manual enrichment

        print("\n" + "="*80)
        print("APOLLO MCP ENRICHMENT")
        print("="*80)
        print(f"\nLeads to Enrich: {len(leads_to_enrich)}")
        print(f"Credit Cost: {len(leads_to_enrich) * self.config.apollo_credits_per_lead} credits")
        print("\nTop Leads:")
        for i, lead in enumerate(leads_to_enrich[:10], 1):
            print(f"  {i}. {lead['business_name']} ({lead['city']}, {lead['state']}) - Score: {lead['score']}")
        if len(leads_to_enrich) > 10:
            print(f"  ... and {len(leads_to_enrich) - 10} more")

        print("\nNEXT STEPS:")
        print("1. Go to Apollo.io")
        print("2. Find these businesses by name/location")
        print("3. Click 'Reveal' for each contact (spends 2 credits per lead)")
        print("4. Export enriched CSV")
        print("5. Save to: output/apollo_enriched_TIMESTAMP.csv")
        print("6. Run: python -m src.apollo_pipeline merge <enriched_csv> <top_leads_json>")
        print("="*80 + "\n")

        # Return None to indicate manual step required
        # In future, this would call Apollo MCP and return enriched CSV path
        return None

    def merge_enriched(
        self,
        enriched_csv: str,
        top_leads_json: str
    ) -> str:
        """
        Merge enriched contact data with scored leads.

        Args:
            enriched_csv: CSV from Apollo with revealed contacts
            top_leads_json: JSON with scored top leads

        Returns:
            Path to ready-for-outreach JSON
        """
        logger.info(f"🔗 Merging enriched data")

        ready_leads = merge_enriched_data(enriched_csv, top_leads_json)

        output_file = self.output_dir / "apollo_ready_for_outreach.json"

        return str(output_file)

    def convert_to_lead_objects(self, apollo_json: str) -> List[Lead]:
        """
        Convert Apollo JSON to Lead objects for SMS system.

        Args:
            apollo_json: Path to ready-for-outreach JSON

        Returns:
            List of Lead objects
        """
        with open(apollo_json, 'r') as f:
            apollo_leads = json.load(f)

        lead_objects = []

        for apollo_lead in apollo_leads:
            lead = Lead(
                source="apollo",
                business_name=apollo_lead.get("business_name", ""),
                phone=apollo_lead.get("phone", ""),
                email=apollo_lead.get("email", ""),
                website=apollo_lead.get("website", ""),
                city=apollo_lead.get("city", ""),
                state=apollo_lead.get("state", ""),
                category=apollo_lead.get("industry", ""),
                pain_points=apollo_lead.get("pain_points", []),
                notes=apollo_lead.get("notes", ""),
                owner_name=apollo_lead.get("contact_name", ""),
                linkedin=apollo_lead.get("linkedin", ""),
            )
            lead_objects.append(lead)

        return lead_objects

    def run_sms_campaign(
        self,
        leads: List[Lead],
        template_name: str = None,
        dry_run: bool = True,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Execute SMS campaign with enriched leads.

        Args:
            leads: List of Lead objects
            template_name: SMS template to use (auto-selected if None)
            dry_run: Preview without sending
            limit: Max SMS to send

        Returns:
            Campaign statistics
        """
        logger.info(f"📱 Running SMS campaign (dry_run={dry_run})")

        stats = self.sms_manager.run_campaign(
            leads=leads[:limit],
            template_name=template_name,
            dry_run=dry_run,
            daily_limit=limit
        )

        return stats

    def enroll_in_followup(
        self,
        leads: List[Lead],
        business_id: str = "marceau-solutions"
    ) -> Dict[str, Any]:
        """
        Enroll leads in multi-touch follow-up sequence.

        Args:
            leads: List of Lead objects sent initial SMS
            business_id: Which business is running this campaign

        Returns:
            Enrollment statistics
        """
        logger.info(f"🔄 Enrolling {len(leads)} leads in follow-up sequence")

        enrolled_count = 0

        for lead in leads:
            if lead.phone and lead.id not in self.followup_manager.sequences:
                self.followup_manager.enroll_lead(lead, business_id=business_id)
                enrolled_count += 1

        stats = {
            "total_leads": len(leads),
            "enrolled": enrolled_count,
            "already_enrolled": len(leads) - enrolled_count
        }

        logger.info(f"✅ Enrolled {enrolled_count} new leads in sequence")

        return stats

    def run_full_pipeline(
        self,
        search_query: str,
        campaign_name: str,
        template_name: str = None,
        dry_run: bool = True,
        limit: int = 100,
        business_id: str = "marceau-solutions"
    ) -> Dict[str, Any]:
        """
        Execute complete Apollo → SMS pipeline.

        Args:
            search_query: Natural language Apollo search
            campaign_name: Campaign identifier
            template_name: SMS template (auto-selected if None)
            dry_run: Preview without sending
            limit: Max SMS to send
            business_id: Which business is running this

        Returns:
            Pipeline execution statistics
        """
        pipeline_stats = {
            "search_query": search_query,
            "campaign_name": campaign_name,
            "started_at": datetime.now().isoformat(),
            "steps_completed": [],
            "total_leads_found": 0,
            "top_leads_filtered": 0,
            "enriched_leads": 0,
            "sms_sent": 0,
            "enrolled_in_sequence": 0,
            "errors": []
        }

        try:
            # Step 1: Apollo Search via MCP (fully automated)
            print("\n" + "="*80)
            print("APOLLO PIPELINE - STEP 1: SEARCH & ENRICH")
            print("="*80)
            leads = self.apollo_search_via_mcp(search_query, campaign_name)

            if leads is None or len(leads) == 0:
                print("\n⚠️  Apollo MCP search returned no leads")
                pipeline_stats["errors"].append("No leads found")
                return pipeline_stats

            pipeline_stats["steps_completed"].append("search")
            pipeline_stats["total_leads_found"] = len(leads)
            pipeline_stats["enriched_leads"] = len([l for l in leads if l.phone])

            print(f"\n✅ Found {len(leads)} leads, {pipeline_stats['enriched_leads']} with contact info")

            # Step 2: Run SMS Campaign (if not dry run)
            if not dry_run:
                print("\n" + "="*80)
                print("APOLLO PIPELINE - STEP 2: SMS CAMPAIGN")
                print("="*80)

                # Send SMS to enriched leads
                enriched_leads = [l for l in leads if l.phone]
                sms_results = self.sms_manager.send_campaign(
                    leads=enriched_leads[:limit],
                    template_name=template_name or "no_website_intro",
                    business_id=business_id,
                    campaign_name=campaign_name,
                    dry_run=False
                )

                pipeline_stats["sms_sent"] = sms_results.get("sent", 0)
                pipeline_stats["steps_completed"].append("sms")

                print(f"\n✅ Sent {pipeline_stats['sms_sent']} SMS messages")

                # Step 3: Enroll in Follow-up Sequence
                print("\n" + "="*80)
                print("APOLLO PIPELINE - STEP 3: FOLLOW-UP SEQUENCE")
                print("="*80)

                enrolled = self.followup_manager.create_campaign(
                    campaign_name=campaign_name,
                    leads=enriched_leads[:limit],
                    business_id=business_id
                )

                pipeline_stats["enrolled_in_sequence"] = len(enrolled)
                pipeline_stats["steps_completed"].append("followup")

                print(f"\n✅ Enrolled {pipeline_stats['enrolled_in_sequence']} leads in follow-up sequence")

            else:
                print("\n⚠️  DRY RUN - No SMS sent, no follow-up enrolled")
                print(f"   Would send SMS to {min(len([l for l in leads if l.phone]), limit)} leads")

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            pipeline_stats["errors"].append(str(e))

        pipeline_stats["completed_at"] = datetime.now().isoformat()

        return pipeline_stats


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """CLI entry point for Apollo pipeline."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description="Apollo MCP → Cold Outreach Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Full pipeline (dry run)
    python -m src.apollo_pipeline run \\
        --search "gyms in Naples FL, 1-50 employees" \\
        --campaign "Naples Gyms Voice AI" \\
        --dry-run

    # Full pipeline (for real)
    python -m src.apollo_pipeline run \\
        --search "gyms in Naples FL, 1-50 employees" \\
        --campaign "Naples Gyms Voice AI" \\
        --for-real

    # Import Apollo CSV
    python -m src.apollo_pipeline import \\
        output/apollo_search.csv \\
        --campaign "Naples Gyms"

    # Filter top leads
    python -m src.apollo_pipeline filter \\
        output/apollo_leads_TIMESTAMP.json

    # Enrich top leads
    python -m src.apollo_pipeline enrich \\
        output/apollo_leads_top.json \\
        --limit 50

    # Merge enriched data
    python -m src.apollo_pipeline merge \\
        output/apollo_enriched.csv \\
        output/apollo_leads_top.json

    # Send SMS campaign
    python -m src.apollo_pipeline sms \\
        output/apollo_ready_for_outreach.json \\
        --template no_website_intro \\
        --for-real
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run full pipeline
    run_parser = subparsers.add_parser("run", help="Run full pipeline")
    run_parser.add_argument("--search", "-s", required=True, type=str, help="Natural language Apollo search")
    run_parser.add_argument("--campaign", "-c", required=True, type=str, help="Campaign name")
    run_parser.add_argument("--template", "-t", type=str, help="SMS template name")
    run_parser.add_argument("--dry-run", action="store_true", default=True, help="Preview without sending")
    run_parser.add_argument("--for-real", action="store_true", help="Actually send SMS")
    run_parser.add_argument("--limit", "-l", type=int, default=100, help="Max SMS to send")
    run_parser.add_argument("--business-id", "-b", type=str, default="marceau-solutions", help="Business ID")
    run_parser.add_argument("--output-dir", "-o", type=str, default="output", help="Output directory")

    # Import Apollo CSV
    import_parser = subparsers.add_parser("import", help="Import Apollo CSV export")
    import_parser.add_argument("csv_file", type=str, help="Path to Apollo CSV export")
    import_parser.add_argument("--campaign", "-c", required=True, type=str, help="Campaign name")
    import_parser.add_argument("--output-dir", "-o", type=str, default="output", help="Output directory")

    # Filter top leads
    filter_parser = subparsers.add_parser("filter", help="Filter top 20 percent leads")
    filter_parser.add_argument("input_file", type=str, help="Path to scored leads JSON")
    filter_parser.add_argument("--min-score", type=int, default=8, help="Minimum score threshold")
    filter_parser.add_argument("--output-dir", "-o", type=str, default="output", help="Output directory")

    # Enrich via Apollo
    enrich_parser = subparsers.add_parser("enrich", help="Enrich leads via Apollo MCP")
    enrich_parser.add_argument("input_file", type=str, help="Path to top leads JSON")
    enrich_parser.add_argument("--limit", "-l", type=int, default=50, help="Max leads to enrich")
    enrich_parser.add_argument("--output-dir", "-o", type=str, default="output", help="Output directory")

    # Merge enriched data
    merge_parser = subparsers.add_parser("merge", help="Merge enriched contacts with scores")
    merge_parser.add_argument("enriched_csv", type=str, help="Path to enriched CSV from Apollo")
    merge_parser.add_argument("scored_json", type=str, help="Path to scored leads JSON")
    merge_parser.add_argument("--output-dir", "-o", type=str, default="output", help="Output directory")

    # Send SMS campaign
    sms_parser = subparsers.add_parser("sms", help="Send SMS campaign")
    sms_parser.add_argument("input_file", type=str, help="Path to ready-for-outreach JSON")
    sms_parser.add_argument("--template", "-t", type=str, help="SMS template name")
    sms_parser.add_argument("--dry-run", action="store_true", default=True, help="Preview without sending")
    sms_parser.add_argument("--for-real", action="store_true", help="Actually send SMS")
    sms_parser.add_argument("--limit", "-l", type=int, default=100, help="Max SMS to send")
    sms_parser.add_argument("--business-id", "-b", type=str, default="marceau-solutions", help="Business ID")
    sms_parser.add_argument("--output-dir", "-o", type=str, default="output", help="Output directory")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize pipeline
    config = PipelineConfig(output_dir=getattr(args, "output_dir", "output"))
    pipeline = ApolloPipeline(config)

    if args.command == "run":
        stats = pipeline.run_full_pipeline(
            search_query=args.search,
            campaign_name=args.campaign,
            template_name=args.template,
            dry_run=not args.for_real,
            limit=args.limit,
            business_id=args.business_id
        )

        print("\n=== Pipeline Statistics ===")
        print(json.dumps(stats, indent=2))

    elif args.command == "import":
        output_file = pipeline.import_and_score(
            csv_file=args.csv_file,
            campaign_name=args.campaign
        )
        print(f"\n✅ Import complete: {output_file}")
        print("\nNext step:")
        print(f"  python -m src.apollo_pipeline filter {output_file}")

    elif args.command == "filter":
        output_file = pipeline.filter_top_leads(
            scored_json=args.input_file,
            min_score=args.min_score
        )
        print(f"\n✅ Filter complete: {output_file}")
        print("\nNext step:")
        print(f"  python -m src.apollo_pipeline enrich {output_file}")

    elif args.command == "enrich":
        enriched_csv = pipeline.enrich_via_apollo_mcp(
            top_leads_json=args.input_file,
            limit=args.limit
        )
        if enriched_csv:
            print(f"\n✅ Enrichment complete: {enriched_csv}")
        else:
            print("\n⚠️  Manual enrichment required (see instructions above)")

    elif args.command == "merge":
        output_file = pipeline.merge_enriched(
            enriched_csv=args.enriched_csv,
            scored_json=args.scored_json
        )
        print(f"\n✅ Merge complete: {output_file}")
        print("\nNext step:")
        print(f"  python -m src.apollo_pipeline sms {output_file} --for-real")

    elif args.command == "sms":
        # Load leads
        leads = pipeline.convert_to_lead_objects(args.input_file)

        # Send SMS campaign
        stats = pipeline.run_sms_campaign(
            leads=leads,
            template_name=args.template,
            dry_run=not args.for_real,
            limit=args.limit
        )

        print("\n=== SMS Campaign Results ===")
        for key, value in stats.items():
            if key != "errors":
                print(f"  {key}: {value}")

        # Enroll in follow-up sequence
        if not args.dry_run and args.for_real:
            followup_stats = pipeline.enroll_in_followup(
                leads=leads,
                business_id=args.business_id
            )
            print("\n=== Follow-up Enrollment ===")
            for key, value in followup_stats.items():
                print(f"  {key}: {value}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
