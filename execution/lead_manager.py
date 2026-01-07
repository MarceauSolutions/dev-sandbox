#!/usr/bin/env python3
"""
lead_manager.py - Comprehensive Lead Management System

WHAT: Capture, route, and nurture leads from forms to CRM to conversion
WHY: Automate lead capture, ClickUp CRM routing, and personalized follow-up sequences
INPUT: Form submission data (name, email, phone, project type, etc.)
OUTPUT: ClickUp task, welcome email, SMS, and scheduled nurture sequence

QUICK USAGE:
  python lead_manager.py --process-lead --name "John Smith" --email "john@example.com" --phone "+15551234567" --project "fitness-ai"
  python lead_manager.py --list-leads
  python lead_manager.py --nurture-sequence --lead-id TASK_ID

CAPABILITIES:
  • Form submission processing
  • ClickUp CRM task creation with custom fields
  • Welcome email automation
  • SMS opt-in and welcome messages
  • Lead research via web scraping (social profiles, website)
  • Personalized nurture sequences
  • Lead scoring and prioritization

INTEGRATIONS:
  • ClickUp CRM (task management)
  • SMTP Email (Gmail)
  • Twilio SMS
  • Web scraping (lead research)
"""

import os
import sys
import json
import argparse
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Import our tools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from clickup_api import (
        create_task, get_task, update_task, list_tasks, 
        list_spaces, list_lists, get_headers, CLICKUP_API_BASE
    )
except ImportError:
    print("Warning: clickup_api not available")

try:
    from twilio_sms import TwilioSMS
except ImportError:
    TwilioSMS = None
    print("Warning: twilio_sms not available")


class LeadManager:
    """
    Comprehensive lead management system.
    
    Workflow:
    1. Receive form submission
    2. Create ClickUp task with lead data
    3. Send welcome email
    4. Send welcome SMS (if opted in)
    5. Research lead (social profiles, website)
    6. Update ClickUp task with research
    7. Schedule nurture sequence
    """
    
    # Project type to ClickUp list mapping
    PROJECT_LISTS = {
        "fitness-ai": {
            "name": "Fitness Influencer AI Leads",
            "folder": "AI Assistants",
            "tags": ["fitness", "ai-assistant", "subscription"]
        },
        "custom-ai": {
            "name": "Custom AI Project Leads", 
            "folder": "AI Assistants",
            "tags": ["custom", "ai-assistant", "project"]
        },
        "amazon-seller": {
            "name": "Amazon Seller Leads",
            "folder": "AI Assistants", 
            "tags": ["amazon", "ecommerce", "subscription"]
        },
        "general": {
            "name": "General Inquiries",
            "folder": "Leads",
            "tags": ["inquiry", "general"]
        }
    }
    
    # Lead scoring criteria
    SCORING_CRITERIA = {
        "has_website": 10,
        "has_social_media": 15,
        "large_following": 20,  # >10k followers
        "business_email": 5,   # Non-gmail/yahoo
        "phone_provided": 10,
        "sms_opted_in": 5,
        "complete_profile": 10
    }
    
    def __init__(self):
        """Initialize lead manager with all integrations."""
        # Email config
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USERNAME')
        self.smtp_pass = os.getenv('SMTP_PASSWORD')
        self.sender_name = os.getenv('SENDER_NAME', 'Marceau Solutions')
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.calendly_url = os.getenv('CALENDLY_URL', 'https://calendly.com/wmarceau/30min')
        
        # ClickUp config  
        self.clickup_token = os.getenv('CLICKUP_API_TOKEN')
        self.clickup_workspace = os.getenv('CLICKUP_WORKSPACE_ID')
        self.clickup_space = os.getenv('CLICKUP_SPACE_NAME', 'Template Creative Agency')
        
        # Twilio SMS
        self.sms_client = None
        if TwilioSMS:
            try:
                self.sms_client = TwilioSMS()
            except:
                pass
        
        # Leads database (JSONL file)
        self.leads_dir = Path(".tmp/leads")
        self.leads_dir.mkdir(parents=True, exist_ok=True)
        self.leads_file = self.leads_dir / "leads.jsonl"
    
    def process_lead(
        self,
        name: str,
        email: str,
        phone: str = None,
        project_type: str = "general",
        business_name: str = None,
        website: str = None,
        social_handles: Dict[str, str] = None,
        message: str = None,
        sms_opt_in: bool = False,
        email_opt_in: bool = True,
        source: str = "website",
        branding: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process a new lead from form submission.
        
        Args:
            name: Lead's full name
            email: Lead's email address
            phone: Lead's phone number (optional)
            project_type: Type of project (fitness-ai, custom-ai, amazon-seller, general)
            business_name: Business/brand name (optional)
            website: Website URL (optional)
            social_handles: Dict of social media handles
            message: Additional message/notes
            sms_opt_in: Whether lead opted into SMS
            email_opt_in: Whether lead opted into email
            source: Lead source (website, referral, etc.)
            branding: Brand colors and logo info
            
        Returns:
            Dict with lead_id, task_url, and status
        """
        print(f"\n{'='*70}")
        print("PROCESSING NEW LEAD")
        print(f"{'='*70}")
        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"Project: {project_type}")
        print(f"SMS Opt-in: {sms_opt_in}")
        
        # Generate lead ID
        lead_id = f"lead_{datetime.now().strftime('%Y%m%d%H%M%S')}_{email.split('@')[0]}"
        
        result = {
            "lead_id": lead_id,
            "success": True,
            "actions": []
        }
        
        # Step 1: Create ClickUp task
        print(f"\n→ Step 1: Creating ClickUp task...")
        clickup_result = self._create_clickup_task(
            name=name,
            email=email,
            phone=phone,
            project_type=project_type,
            business_name=business_name,
            website=website,
            social_handles=social_handles,
            message=message,
            branding=branding
        )
        
        if clickup_result.get("success"):
            result["clickup_task_id"] = clickup_result.get("task_id")
            result["clickup_task_url"] = clickup_result.get("task_url")
            result["actions"].append("clickup_task_created")
            print(f"  ✓ ClickUp task created: {clickup_result.get('task_url')}")
        else:
            print(f"  ✗ ClickUp task failed: {clickup_result.get('error')}")
        
        # Step 2: Send welcome email
        if email_opt_in:
            print(f"\n→ Step 2: Sending welcome email...")
            email_result = self._send_welcome_email(
                name=name,
                email=email,
                project_type=project_type,
                business_name=business_name
            )
            
            if email_result.get("success"):
                result["actions"].append("welcome_email_sent")
                print(f"  ✓ Welcome email sent")
            else:
                print(f"  ✗ Email failed: {email_result.get('error')}")
        
        # Step 3: Send welcome SMS
        if sms_opt_in and phone and self.sms_client:
            print(f"\n→ Step 3: Sending welcome SMS...")
            sms_result = self.sms_client.send_message(
                to=phone,
                template="welcome",
                template_vars={"name": name.split()[0]}
            )
            
            if sms_result.get("success"):
                result["actions"].append("welcome_sms_sent")
                print(f"  ✓ Welcome SMS sent")
            else:
                print(f"  ✗ SMS failed: {sms_result.get('error')}")
        
        # Step 4: Research lead (async in production)
        print(f"\n→ Step 4: Researching lead...")
        research = self._research_lead(
            email=email,
            website=website,
            social_handles=social_handles
        )
        result["research"] = research
        
        # Step 5: Calculate lead score
        lead_score = self._calculate_lead_score(
            phone=phone,
            website=website,
            social_handles=social_handles,
            sms_opt_in=sms_opt_in,
            research=research
        )
        result["lead_score"] = lead_score
        print(f"  Lead Score: {lead_score}/100")
        
        # Step 6: Save lead to local database
        lead_record = {
            "lead_id": lead_id,
            "timestamp": datetime.now().isoformat(),
            "name": name,
            "email": email,
            "phone": phone,
            "project_type": project_type,
            "business_name": business_name,
            "website": website,
            "social_handles": social_handles,
            "message": message,
            "sms_opt_in": sms_opt_in,
            "email_opt_in": email_opt_in,
            "source": source,
            "branding": branding,
            "lead_score": lead_score,
            "research": research,
            "clickup_task_id": result.get("clickup_task_id"),
            "nurture_stage": 0,
            "status": "new"
        }
        
        self._save_lead(lead_record)
        result["actions"].append("lead_saved")
        
        print(f"\n{'='*70}")
        print(f"LEAD PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"Lead ID: {lead_id}")
        print(f"Score: {lead_score}/100")
        print(f"Actions: {', '.join(result['actions'])}")
        
        return result
    
    def _create_clickup_task(
        self,
        name: str,
        email: str,
        phone: str = None,
        project_type: str = "general",
        business_name: str = None,
        website: str = None,
        social_handles: Dict[str, str] = None,
        message: str = None,
        branding: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a ClickUp task for the lead."""
        if not self.clickup_token:
            return {"success": False, "error": "ClickUp not configured"}
        
        # Get project config
        project_config = self.PROJECT_LISTS.get(project_type, self.PROJECT_LISTS["general"])
        
        # Build task description
        description = f"""
## Lead Information

**Name:** {name}
**Email:** {email}
**Phone:** {phone or 'Not provided'}
**Business:** {business_name or 'Not provided'}
**Website:** {website or 'Not provided'}
**Project Type:** {project_type}

### Social Media
"""
        if social_handles:
            for platform, handle in social_handles.items():
                if handle:
                    description += f"- **{platform.title()}:** @{handle}\n"
        else:
            description += "Not provided\n"
        
        if branding:
            description += f"""
### Branding
- **Primary Color:** {branding.get('colors', {}).get('primary', 'Not set')}
- **Secondary Color:** {branding.get('colors', {}).get('secondary', 'Not set')}
- **Accent Color:** {branding.get('colors', {}).get('accent', 'Not set')}
- **Logo:** {'Uploaded' if branding.get('hasLogo') else 'Not uploaded'}
- **Tagline:** {branding.get('tagline', 'Not set')}
"""
        
        if message:
            description += f"""
### Message
{message}
"""
        
        description += f"""
---
*Lead captured on {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
        
        # First, get the list ID for this project type
        # For now, we'll use the first list we find
        try:
            headers = {
                "Authorization": self.clickup_token,
                "Content-Type": "application/json"
            }
            
            # Get spaces
            spaces_url = f"https://api.clickup.com/api/v2/team/{self.clickup_workspace}/space"
            spaces_resp = requests.get(spaces_url, headers=headers)
            spaces = spaces_resp.json().get('spaces', [])
            
            # Find our space
            space_id = None
            for space in spaces:
                if space['name'].lower() == self.clickup_space.lower():
                    space_id = space['id']
                    break
            
            if not space_id and spaces:
                space_id = spaces[0]['id']
            
            if not space_id:
                return {"success": False, "error": "No ClickUp space found"}
            
            # Get folderless lists in space
            lists_url = f"https://api.clickup.com/api/v2/space/{space_id}/list"
            lists_resp = requests.get(lists_url, headers=headers)
            all_lists = lists_resp.json().get('lists', [])
            
            # Also get lists from folders (Sales Pipeline, etc.)
            folders_url = f"https://api.clickup.com/api/v2/space/{space_id}/folder"
            folders_resp = requests.get(folders_url, headers=headers)
            folders = folders_resp.json().get('folders', [])
            
            for folder in folders:
                all_lists.extend(folder.get('lists', []))
            
            # Find appropriate list for leads (prefer "Intake" or "Leads")
            list_id = None
            intake_keywords = ['intake', 'lead', 'new', 'incoming']
            
            for lst in all_lists:
                lst_name = lst['name'].lower()
                for keyword in intake_keywords:
                    if keyword in lst_name:
                        list_id = lst['id']
                        break
                if list_id:
                    break
            
            # Fallback to first list
            if not list_id and all_lists:
                list_id = all_lists[0]['id']
            
            if not list_id:
                return {"success": False, "error": "No ClickUp list found"}
            
            # Create task
            task_name = f"Lead: {name} - {project_type.replace('-', ' ').title()}"
            if business_name:
                task_name = f"Lead: {business_name} ({name})"
            
            task_data = {
                "name": task_name,
                "description": description,
                "tags": project_config.get("tags", []),
                "priority": 2 if project_type in ["fitness-ai", "custom-ai"] else 3
            }
            
            create_url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
            create_resp = requests.post(create_url, headers=headers, json=task_data)
            
            if create_resp.status_code == 200:
                task = create_resp.json()
                return {
                    "success": True,
                    "task_id": task['id'],
                    "task_url": task['url']
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {create_resp.status_code} - {create_resp.text}"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _send_welcome_email(
        self,
        name: str,
        email: str,
        project_type: str,
        business_name: str = None
    ) -> Dict[str, Any]:
        """Send welcome email to new lead."""
        if not self.smtp_user or not self.smtp_pass:
            return {"success": False, "error": "SMTP not configured"}
        
        # Email subject based on project type
        subjects = {
            "fitness-ai": "Welcome to Fitness Influencer AI! 🎯",
            "custom-ai": "Your Custom AI Project Inquiry - Marceau Solutions",
            "amazon-seller": "Amazon Seller AI - Let's Get Started!",
            "general": "Thanks for Reaching Out - Marceau Solutions"
        }
        
        subject = subjects.get(project_type, subjects["general"])
        first_name = name.split()[0]
        
        # HTML email body
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
        .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 12px 12px; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
        .feature {{ background: white; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #667eea; }}
        .footer {{ text-align: center; color: #6b7280; font-size: 14px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Welcome, {first_name}!</h1>
            <p>We're excited to help you grow your business with AI</p>
        </div>
        <div class="content">
            <p>Hi {first_name},</p>
            
            <p>Thank you for your interest in <strong>Marceau Solutions</strong>! We've received your information and our team is reviewing it now.</p>
            
            <h3>What Happens Next?</h3>
            
            <div class="feature">
                <strong>📋 Step 1:</strong> Our team reviews your requirements (usually within 24 hours)
            </div>
            <div class="feature">
                <strong>📞 Step 2:</strong> We'll reach out to schedule a brief discovery call
            </div>
            <div class="feature">
                <strong>🚀 Step 3:</strong> Get personalized recommendations for your AI solution
            </div>
            
            <p style="text-align: center;">
                <a href="{self.calendly_url}" class="button">Schedule a Call Now →</a>
            </p>
            
            <p>Want to skip ahead? Click the button above to book a 30-minute call with our team.</p>
            
            <p>In the meantime, feel free to reply to this email with any questions!</p>
            
            <p>Best regards,<br>
            <strong>William Marceau</strong><br>
            Founder, Marceau Solutions</p>
        </div>
        <div class="footer">
            <p>Marceau Solutions LLC | AI-Powered Business Growth</p>
            <p><a href="https://marceausolutions.com">marceausolutions.com</a></p>
        </div>
    </div>
</body>
</html>
"""
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = email
            
            # Plain text version
            text_body = f"""
Hi {first_name},

Thank you for your interest in Marceau Solutions! We've received your information and our team is reviewing it now.

What Happens Next?

1. Our team reviews your requirements (usually within 24 hours)
2. We'll reach out to schedule a brief discovery call
3. Get personalized recommendations for your AI solution

Want to skip ahead? Book a call: {self.calendly_url}

Feel free to reply to this email with any questions!

Best regards,
William Marceau
Founder, Marceau Solutions

---
Marceau Solutions LLC | AI-Powered Business Growth
https://marceausolutions.com
"""
            
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _research_lead(
        self,
        email: str,
        website: str = None,
        social_handles: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Research lead from available information.
        
        In production, this would:
        - Scrape social media profiles for follower counts
        - Check website for business info
        - Look up company info via APIs
        - Enrich data with Clearbit or similar
        """
        research = {
            "email_domain": email.split("@")[1] if "@" in email else None,
            "is_business_email": False,
            "website_status": None,
            "social_profiles_found": [],
            "estimated_following": 0
        }
        
        # Check if business email
        free_email_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"]
        if research["email_domain"] and research["email_domain"].lower() not in free_email_domains:
            research["is_business_email"] = True
        
        # Check website (basic)
        if website:
            try:
                resp = requests.head(website, timeout=5, allow_redirects=True)
                research["website_status"] = "active" if resp.status_code == 200 else "error"
            except:
                research["website_status"] = "unreachable"
        
        # Note which social profiles were provided
        if social_handles:
            for platform, handle in social_handles.items():
                if handle:
                    research["social_profiles_found"].append(platform)
        
        return research
    
    def _calculate_lead_score(
        self,
        phone: str = None,
        website: str = None,
        social_handles: Dict[str, str] = None,
        sms_opt_in: bool = False,
        research: Dict[str, Any] = None
    ) -> int:
        """Calculate lead score from 0-100."""
        score = 0
        
        # Base score for submitting
        score += 10
        
        # Phone provided
        if phone:
            score += self.SCORING_CRITERIA["phone_provided"]
        
        # SMS opt-in
        if sms_opt_in:
            score += self.SCORING_CRITERIA["sms_opted_in"]
        
        # Website provided
        if website:
            score += self.SCORING_CRITERIA["has_website"]
        
        # Social media presence
        if social_handles:
            profiles = [h for h in social_handles.values() if h]
            if len(profiles) >= 1:
                score += self.SCORING_CRITERIA["has_social_media"]
            if len(profiles) >= 3:
                score += 10  # Bonus for multiple platforms
        
        # Research-based scoring
        if research:
            if research.get("is_business_email"):
                score += self.SCORING_CRITERIA["business_email"]
            if research.get("website_status") == "active":
                score += 5
        
        return min(score, 100)
    
    def _save_lead(self, lead_record: Dict[str, Any]):
        """Save lead to local JSONL database."""
        with open(self.leads_file, 'a') as f:
            f.write(json.dumps(lead_record) + '\n')
    
    def list_leads(self, status: str = None, project_type: str = None) -> List[Dict[str, Any]]:
        """List all leads from local database."""
        leads = []
        
        if not self.leads_file.exists():
            return leads
        
        with open(self.leads_file, 'r') as f:
            for line in f:
                try:
                    lead = json.loads(line.strip())
                    
                    # Filter by status
                    if status and lead.get("status") != status:
                        continue
                    
                    # Filter by project type
                    if project_type and lead.get("project_type") != project_type:
                        continue
                    
                    leads.append(lead)
                except:
                    continue
        
        return leads
    
    def send_nurture_message(
        self,
        lead_id: str,
        stage: int = None
    ) -> Dict[str, Any]:
        """
        Send nurture message based on lead's current stage.
        
        Nurture sequence:
        Stage 0: Welcome (sent on signup)
        Stage 1: Feature highlight (Day 2)
        Stage 2: Check-in (Day 4)
        Stage 3: Value prop (Day 7)
        Stage 4: Call-to-action (Day 14)
        """
        # Find lead
        leads = self.list_leads()
        lead = None
        for l in leads:
            if l.get("lead_id") == lead_id:
                lead = l
                break
        
        if not lead:
            return {"success": False, "error": f"Lead not found: {lead_id}"}
        
        current_stage = stage if stage is not None else lead.get("nurture_stage", 0)
        first_name = lead["name"].split()[0]
        
        # Define nurture messages
        nurture_stages = {
            1: {
                "email_subject": "Quick tip for your AI assistant 💡",
                "sms_template": "followup_1",
                "email_body": f"Hi {first_name}, just wanted to share a quick tip..."
            },
            2: {
                "email_subject": "How's it going, {first_name}?",
                "sms_template": "followup_2",
                "email_body": f"Hi {first_name}, checking in to see how you're doing..."
            },
            3: {
                "email_subject": "Did you know? 🎬",
                "sms_template": "feature_highlight",
                "email_body": f"Hi {first_name}, here's a feature you might love..."
            }
        }
        
        if current_stage not in nurture_stages:
            return {"success": False, "error": f"Invalid nurture stage: {current_stage}"}
        
        stage_config = nurture_stages[current_stage]
        result = {"success": True, "stage": current_stage, "actions": []}
        
        # Send SMS if opted in
        if lead.get("sms_opt_in") and lead.get("phone") and self.sms_client:
            sms_result = self.sms_client.send_message(
                to=lead["phone"],
                template=stage_config["sms_template"],
                template_vars={"name": first_name}
            )
            if sms_result.get("success"):
                result["actions"].append("sms_sent")
        
        # TODO: Send email for this stage
        
        return result
    
    def get_lead_stats(self) -> Dict[str, Any]:
        """Get statistics about all leads."""
        leads = self.list_leads()
        
        stats = {
            "total_leads": len(leads),
            "by_project_type": {},
            "by_status": {},
            "average_score": 0,
            "sms_opted_in": 0,
            "with_phone": 0
        }
        
        if not leads:
            return stats
        
        total_score = 0
        
        for lead in leads:
            # By project type
            ptype = lead.get("project_type", "unknown")
            stats["by_project_type"][ptype] = stats["by_project_type"].get(ptype, 0) + 1
            
            # By status
            status = lead.get("status", "unknown")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Score
            total_score += lead.get("lead_score", 0)
            
            # Opt-ins
            if lead.get("sms_opt_in"):
                stats["sms_opted_in"] += 1
            if lead.get("phone"):
                stats["with_phone"] += 1
        
        stats["average_score"] = total_score / len(leads) if leads else 0
        
        return stats


def main():
    """CLI for lead manager."""
    parser = argparse.ArgumentParser(description="Lead management system")
    
    parser.add_argument('--process-lead', action='store_true', help='Process a new lead')
    parser.add_argument('--name', help='Lead name')
    parser.add_argument('--email', help='Lead email')
    parser.add_argument('--phone', help='Lead phone')
    parser.add_argument('--project', default='general', help='Project type')
    parser.add_argument('--business', help='Business name')
    parser.add_argument('--website', help='Website URL')
    parser.add_argument('--sms-opt-in', action='store_true', help='SMS opt-in')
    parser.add_argument('--message', help='Additional message')
    
    parser.add_argument('--list-leads', action='store_true', help='List all leads')
    parser.add_argument('--stats', action='store_true', help='Show lead statistics')
    parser.add_argument('--nurture-sequence', action='store_true', help='Send nurture message')
    parser.add_argument('--lead-id', help='Lead ID for nurture sequence')
    parser.add_argument('--stage', type=int, help='Nurture stage to send')
    
    args = parser.parse_args()
    
    manager = LeadManager()
    
    if args.process_lead:
        if not args.name or not args.email:
            print("Error: --name and --email required")
            sys.exit(1)
        
        result = manager.process_lead(
            name=args.name,
            email=args.email,
            phone=args.phone,
            project_type=args.project,
            business_name=args.business,
            website=args.website,
            sms_opt_in=args.sms_opt_in,
            message=args.message
        )
        
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("success") else 1)
    
    elif args.list_leads:
        leads = manager.list_leads()
        print(f"\n{'='*70}")
        print(f"LEADS DATABASE ({len(leads)} total)")
        print(f"{'='*70}\n")
        
        for lead in leads:
            print(f"📋 {lead.get('name', 'Unknown')} ({lead.get('email')})")
            print(f"   Project: {lead.get('project_type')} | Score: {lead.get('lead_score', 0)}")
            print(f"   Status: {lead.get('status')} | SMS: {'✓' if lead.get('sms_opt_in') else '✗'}")
            print()
        
        sys.exit(0)
    
    elif args.stats:
        stats = manager.get_lead_stats()
        print(json.dumps(stats, indent=2))
        sys.exit(0)
    
    elif args.nurture_sequence:
        if not args.lead_id:
            print("Error: --lead-id required")
            sys.exit(1)
        
        result = manager.send_nurture_message(args.lead_id, args.stage)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("success") else 1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
