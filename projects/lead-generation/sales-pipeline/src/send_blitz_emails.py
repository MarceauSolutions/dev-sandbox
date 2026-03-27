#!/usr/bin/env python3
"""Send cold call follow-up emails for phone blitz leads."""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv('/Users/williammarceaujr./dev-sandbox/.env')

SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USERNAME')
SMTP_PASS = os.getenv('SMTP_PASSWORD')
FROM_EMAIL = 'wmarceau@marceausolutions.com'
FROM_NAME = 'William Marceau'
CALENDLY = 'https://calendly.com/wmarceau/ai-services-discovery-call'
WEBSITE = 'https://marceausolutions.com/ai-automation'

emails = [
    {
        'to': 'goldenplumbingfl@gmail.com',
        'name': 'Dawn',
        'company': 'Golden Plumbing',
        'subject': 'Following up -- AI systems for Golden Plumbing',
        'body': f"""Hi Dawn,

Really enjoyed speaking with you earlier today. As promised, here's a bit more on what we do.

We build AI-powered intake systems for plumbing companies -- so your phone never goes unanswered, even at 11pm when someone's basement is flooding on a Sunday.

For a company with Golden Plumbing's reputation, the biggest risk isn't getting leads -- it's losing them to a competitor who picks up when you can't. The average emergency plumbing job is $400-$800. Every missed after-hours call is a job you never knew you lost.

Here's what we'd set up for you:
- AI voice receptionist that answers, qualifies the job, and routes urgent calls to you directly
- Automatic appointment booking for non-emergency calls
- SMS follow-up for anyone who called and didn't reach you

Everything gets built during a free 2-week onboarding -- no cost, no commitment. We talk through exactly what you need on a discovery call, scope the build specifically for your business, and go from there.

Book a free 15-minute discovery call here:
{CALENDLY}

Or just reply to this email and we'll find a time.

Best,
William Marceau
Marceau Solutions | (239) 398-5676
{WEBSITE}"""
    },
    {
        'to': 'alexandra@prosplumbing.com',
        'name': 'Alexandra',
        'company': 'Pros Plumbing',
        'subject': 'Great speaking with you -- Pros Plumbing + AI systems',
        'body': f"""Hi Alexandra,

Thanks for taking my call earlier. You mentioned things are busy -- that's exactly the situation where this tends to help most.

We help plumbing companies handle the volume overflow that falls through the cracks: after-hours calls, missed follow-ups, appointment scheduling when your team is heads-down on jobs.

When a new caller can't get through, they usually just call the next plumber on Google. An AI intake layer means they get answered, qualified, and booked -- without pulling anyone off a job.

I'd love to learn more about how Pros Plumbing operates before suggesting anything specific. A free 15-minute discovery call is the right first step -- no pitch, just a conversation about where the gaps are.

Book here:
{CALENDLY}

William Marceau
Marceau Solutions | (239) 398-5676
{WEBSITE}"""
    },
    {
        'to': 'zach.johnson@plumbingpro.pro',
        'name': 'Zach',
        'company': 'PlumbingPro Naples',
        'subject': 'Quick question for you, Zach -- re: call intake at PlumbingPro',
        'body': f"""Hi Zach,

I spoke briefly with someone at PlumbingPro Naples earlier today -- they mentioned you'd be the right person to connect with on this.

I run Marceau Solutions and we help local service companies capture more jobs without adding headcount. An AI-powered intake system that handles calls 24/7 -- books appointments, qualifies jobs, routes urgent calls to the right person -- so your team isn't buried in phone intake during peak hours or missing calls after 5pm.

I'd want to learn more about your current setup before suggesting anything specific. A free 15-minute discovery call is the best first step.

Book here:
{CALENDLY}

Or reply and we'll find a time that works.

Best,
William Marceau | (239) 398-5676
{WEBSITE}"""
    },
    {
        'to': 'jessica@truglowmedspa.com',
        'name': 'Jessica',
        'company': 'Tru Glo Medspa',
        'subject': 'Information you requested -- AI systems for Tru Glo',
        'body': f"""Hi Jessica,

Thanks for the conversation earlier and for taking the time. You mentioned you might be exploring this in the coming months -- I want to make sure you have everything you need when the time is right.

Here's what we typically solve for medspas:

After-hours lead capture. Anyone who finds you on Instagram or Google after 3pm on a Friday has nowhere to go -- they either book blind online or call someone else Monday. An AI layer answers their questions, captures the lead, and books the consult automatically.

Review velocity. An automated post-visit follow-up via SMS asking happy clients for a Google review can significantly increase your review count -- which is the #1 driver of new medspa clients finding you.

Consultation follow-up. High-consideration treatments like fillers and body contouring often require multiple touchpoints before someone books. Without an automated sequence, those leads go cold.

Every build is scoped specifically to what you actually need -- I'd want to learn more about how Tru Glo operates before suggesting anything specific. Whenever the timing is right, a free 15-minute discovery call is the best first step.

Book here whenever you're ready:
{CALENDLY}

William Marceau
Marceau Solutions | (239) 398-5676
{WEBSITE}"""
    },
    {
        'to': 'cloud9medspanaples@gmail.com',
        'name': '',
        'company': 'Cloud 9 Med Spa',
        'subject': 'Re: AI systems -- addressing your concern directly',
        'body': f"""Hi,

Thank you for the honest pushback on the call today -- it's the most important thing anyone's said to me during this entire outreach.

You're right. Clients don't come to Cloud 9 for a spa. Based on your reviews, they come for Carrie specifically -- people describe leaving "renewed emotionally," feeling "completely at ease," cared for as an individual. That's not something AI can or should replace.

Here's what we actually do: we protect that experience by handling everything that happens when Carrie isn't in the room.

When someone finds Cloud 9 at 9pm on a Sunday after seeing an Instagram post and wants to ask whether CryoSlimming is right for them -- right now, that question sits unanswered until Monday. An AI layer answers that question, books the consult, and Carrie closes it in person the way only she can.

The goal isn't to replace the human touch. It's to make sure no one who's looking for it ever hits a voicemail.

If you'd ever want to see exactly how it works without changing anything about how you run your practice, I'd love to show you. Free 15-minute call, no commitment.

Book here:
{CALENDLY}

William Marceau
Marceau Solutions | (239) 398-5676
{WEBSITE}"""
    },
]

def send_email(to, subject, body, name, company):
    msg = MIMEMultipart('alternative')
    msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
    msg['To'] = to
    msg['Subject'] = subject
    msg['Reply-To'] = FROM_EMAIL
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(FROM_EMAIL, to, msg.as_string())

results = []
for e in emails:
    try:
        send_email(e['to'], e['subject'], e['body'], e['name'], e['company'])
        results.append(f"  SENT   {e['company']} -> {e['to']}")
    except Exception as ex:
        results.append(f"  FAILED {e['company']} -> {e['to']} | {ex}")

print('\n'.join(results))
