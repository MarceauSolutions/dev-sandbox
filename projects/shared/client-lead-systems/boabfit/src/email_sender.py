#!/usr/bin/env python3
"""BoabFit Email Sender - SMTP email delivery with templates"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv

# Load env
load_dotenv('/home/clawdbot/dev-sandbox/.env')

SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USERNAME')
SMTP_PASS = os.getenv('SMTP_PASSWORD')
FROM_EMAIL = os.getenv('SENDER_EMAIL', 'wmarceau@marceausolutions.com')
FROM_NAME = 'Julia from BOABFIT'

TEMPLATE_DIR = Path(__file__).parent.parent / 'email-templates'

# Email templates with subjects
TEMPLATES = {
    'welcome': {
        'subject': "🎉 You're In! Welcome to BOABFIT",
        'file': 'welcome.html'
    },
    'day1_getting_started': {
        'subject': '💪 Day 1: Let\'s Get Started!',
        'body': '''Hey {{name}}!

It's Day 1 of your Barbie Body transformation! 🎀

Quick checklist:
✅ Download the BOABFIT app (check your welcome email for the link)
✅ Find today's workout in your calendar
✅ Press play and let's GO!

Remember: I'm doing every workout WITH you. You're not alone in this!

Questions? Just reply to this email.

Let's crush it! 💪
Julia'''
    },
    'day3_checkin': {
        'subject': '📊 Day 3 Check-In: How Are You Feeling?',
        'body': '''Hey {{name}}!

Three days in! 🙌

By now you should be:
• Getting into the rhythm
• Feeling those muscles wake up
• Starting to build the habit

The first week is always the hardest. You're doing AMAZING.

Pro tip: Take a progress photo today. You'll thank yourself in 6 weeks!

Keep going! 💕
Julia

P.S. Follow me on Instagram for daily motivation and tips!'''
    },
    'day7_motivation': {
        'subject': '🏆 Week 1 DONE! You\'re Officially Crushing It',
        'body': '''{{name}}!!! 🎉

ONE WEEK DOWN!

You've completed 5 workouts. That's 5 times you showed up for yourself. That's 5 deposits in your transformation bank.

Most people quit in the first week. You didn't.

That makes you different. That makes you a BOABFIT girl.

5 more weeks to go. Let's keep this momentum! 💪

So proud of you!
Julia'''
    },
    'day14_halfway': {
        'subject': '🔥 HALFWAY! 3 Weeks Down, 3 To Go',
        'body': '''{{name}}!! We're at the HALFWAY point! 🎀

Take a moment to appreciate how far you've come:
• 15 workouts completed
• Building real strength
• Creating lasting habits

Notice any changes? More energy? Clothes fitting different? Confidence boost?

The second half is where the MAGIC happens. Your body is adapting, and the results start compounding.

Let's finish STRONG! 💪

You've got this!
Julia'''
    }
}

def get_template(template_name, first_name='there'):
    """Get email template with name substitution"""
    template = TEMPLATES.get(template_name)
    if not template:
        return None, None
    
    subject = template['subject']
    
    # Check for HTML file first
    if 'file' in template:
        html_path = TEMPLATE_DIR / template['file']
        if html_path.exists():
            body = html_path.read_text()
        else:
            body = template.get('body', '')
    else:
        body = template.get('body', '')
    
    # Replace placeholders
    body = body.replace('{{name}}', first_name)
    
    return subject, body

def send_email(to_email, subject, body, is_html=False):
    """Send an email via SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
        msg['To'] = to_email
        msg['Reply-To'] = 'julia@boabfit.com'
        
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        
        print(f"✓ Sent '{subject}' to {to_email}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to send to {to_email}: {e}")
        return False

def send_welcome_email(to_email, first_name='there'):
    """Send the welcome email"""
    subject, body = get_template('welcome', first_name)
    is_html = '<html' in body.lower()
    return send_email(to_email, subject, body, is_html)

def send_drip_email(to_email, first_name, template_name):
    """Send a drip sequence email"""
    subject, body = get_template(template_name, first_name)
    if not subject:
        print(f"Unknown template: {template_name}")
        return False
    is_html = '<html' in body.lower()
    return send_email(to_email, subject, body, is_html)

if __name__ == '__main__':
    # Test
    import sys
    if len(sys.argv) > 2:
        email = sys.argv[1]
        template = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else 'Test'
        send_drip_email(email, name, template)
    else:
        print("Usage: email_sender.py <email> <template> [name]")
        print("Templates:", list(TEMPLATES.keys()))
