"""
Unified Daily Command Center

Morning dashboard showing today's calls, visits, emails, schedule, and accountability status.
"""

from datetime import datetime
from .generate_lead_lists import get_tier_1_phone_leads, get_tier_2_phone_leads, get_email_leads, get_inperson_leads
from .calendar_integration import get_todays_schedule
from .accountability_tracker import get_accountability_status
from .goal_tracker import get_goal_summary
from .unified_tracker import get_hot_leads, get_next_actions

def get_daily_command_center():
    """Get complete daily command center data."""
    from .pitch_briefer import generate_pitch_brief
    from .ab_testing import get_personalized_content

    # Today's prioritized tasks - sorted by win probability descending
    t1_calls = get_tier_1_phone_leads(5)
    t2_calls = get_tier_2_phone_leads(5)
    emails = get_email_leads(5)
    visits = get_inperson_leads(3)

    # Sort all tasks by win probability
    all_calls = t1_calls + t2_calls
    all_calls.sort(key=lambda x: x.get('win_probability', 0), reverse=True)
    t1_calls = [c for c in all_calls if c.get('tier') == 1][:5]
    t2_calls = [c for c in all_calls if c.get('tier') == 2][:5]

    # Add personalized scripts, next best actions, and A/B variants
    for call in t1_calls + t2_calls:
        if call.get('id'):
            brief = generate_pitch_brief(call)
            call['script'] = brief.get('pitch', {}).get('full_script', '')
            call['next_best_action'] = recommend_next_action(call)
            # Add A/B test info if available
            try:
                ab_content = get_personalized_content(call['id'], 'call_script')
                call['ab_variant'] = ab_content.get('variant_name', 'control')
            except:
                call['ab_variant'] = 'control'

    # Add next best actions to emails and visits
    for email in emails:
        email['next_best_action'] = recommend_next_action(email)
    for visit in visits:
        visit['next_best_action'] = recommend_next_action(visit)

    # Today's schedule
    schedule = get_todays_schedule()

    # Accountability status with streaks
    accountability = get_accountability_status()
    streaks = get_streak_data()
    accountability['streaks'] = streaks

    # Goal progress
    goal_summary = get_goal_summary()

    # Hot leads and next actions (sorted by win probability)
    hot_leads = get_hot_leads(5)
    hot_leads.sort(key=lambda x: getattr(x, 'win_probability', 0), reverse=True)
    next_actions = get_next_actions(5)

    return {
        'calls': {
            'tier_1': t1_calls,
            'tier_2': t2_calls
        },
        'emails': emails,
        'visits': visits,
        'schedule': schedule,
        'accountability': accountability,
        'goal_progress': goal_summary,
        'hot_leads': hot_leads,
        'next_actions': next_actions,
        'generated_at': datetime.now().isoformat()
    }

def recommend_next_action(deal):
    """Recommend the single best next action for a lead."""
    stage = deal.get('stage', 'Intake')
    win_prob = deal.get('win_probability', 0)
    last_contact = deal.get('last_contact_date', '')
    outreach_count = deal.get('touchpoint_count', 0)

    # High win probability leads get immediate action
    if win_prob >= 70:
        if stage in ['Intake', 'Contacted']:
            return "Call immediately - high win probability"
        elif stage == 'Qualified':
            return "Send proposal - ready to close"
        elif stage == 'Meeting Booked':
            return "Prepare for meeting - high value"

    # Medium win probability - strategic follow-up
    elif win_prob >= 40:
        if not last_contact or outreach_count < 2:
            return "Call to qualify - medium potential"
        elif stage == 'Qualified':
            return "Email proposal - building momentum"
        else:
            return "Follow-up call - nurture relationship"

    # Lower win probability - efficient touch
    else:
        if outreach_count == 0:
            return "Email introduction - test interest"
        elif outreach_count < 3:
            return "Email value-add - low effort nurture"
        else:
            return "Pause outreach - monitor for signals"

def get_streak_data():
    """Get current streak and momentum data."""
    conn = get_db()
    today = datetime.now().strftime("%Y-%m-%d")

    # Calculate current streak (consecutive days with completed activities)
    streak_query = """
        SELECT date, COUNT(*) as completed
        FROM accountability_logs
        WHERE completed = TRUE
        GROUP BY date
        ORDER BY date DESC
    """
    daily_completions = conn.execute(streak_query).fetchall()

    current_streak = 0
    longest_streak = 0
    temp_streak = 0

    for row in daily_completions:
        if row['completed'] >= 2:  # At least 2 activities completed
            current_streak += 1
            temp_streak += 1
        else:
            longest_streak = max(longest_streak, temp_streak)
            temp_streak = 0

    longest_streak = max(longest_streak, temp_streak)

    # Momentum score (last 7 days completion rate)
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    weekly_completions = conn.execute("""
        SELECT COUNT(*) as total_activities,
               SUM(CASE WHEN completed THEN 1 ELSE 0 END) as completed_activities
        FROM accountability_logs
        WHERE date >= ?
    """, (week_ago,)).fetchone()

    momentum_score = 0
    if weekly_completions['total_activities'] > 0:
        momentum_score = (weekly_completions['completed_activities'] / weekly_completions['total_activities']) * 100

    conn.close()

    return {
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'momentum_score': round(momentum_score, 1),
        'momentum_level': 'High' if momentum_score >= 75 else 'Medium' if momentum_score >= 50 else 'Low'
    }

def format_command_center_html(data):
    """Format command center as HTML for email/dashboard."""
    streaks = data.get('accountability', {}).get('streaks', {})

    html = f"""
    <html>
    <head>
        <title>Daily Command Center - {datetime.now().strftime('%B %d, %Y')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
            .header {{ background: #f8f9fa; padding: 10px; margin: -15px -15px 15px -15px; border-radius: 5px 5px 0 0; }}
            .task {{ margin: 5px 0; padding: 10px; background: #fff; border-left: 3px solid #007bff; position: relative; }}
            .completed {{ background: #d4edda; border-left-color: #28a745; }}
            .script {{ background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 3px; font-size: 12px; white-space: pre-line; }}
            .copy-btn {{ position: absolute; top: 5px; right: 5px; background: #007bff; color: white; border: none; padding: 2px 5px; border-radius: 3px; cursor: pointer; }}
            .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e9ecef; border-radius: 5px; }}
            .ab-badge {{ background: #ffc107; color: #000; padding: 2px 5px; border-radius: 3px; font-size: 10px; margin-left: 5px; }}
            .win-prob {{ background: #28a745; color: white; padding: 2px 5px; border-radius: 3px; font-size: 10px; margin-left: 5px; }}
            .next-action {{ background: #17a2b8; color: white; padding: 2px 5px; border-radius: 3px; font-size: 10px; margin-left: 5px; }}
            .streak-highlight {{ background: linear-gradient(45deg, #ff6b6b, #feca57); color: white; padding: 15px; border-radius: 5px; text-align: center; margin: 10px 0; }}
        </style>
        <script>
            function copyToClipboard(text) {{
                navigator.clipboard.writeText(text);
                alert('Copied to clipboard!');
            }}
            function toggleScript(id) {{
                var script = document.getElementById(id);
                script.style.display = script.style.display === 'none' ? 'block' : 'none';
            }}
        </script>
    </head>
    <body>
        <h1>🚀 Daily Command Center</h1>
        <p><strong>{datetime.now().strftime('%A, %B %d, %Y')}</strong></p>

        <!-- Streak & Momentum Highlight -->
        <div class="streak-highlight">
            <h2>🔥 Current Streak: {streaks.get('current_streak', 0)} days | Momentum: {streaks.get('momentum_level', 'Low')} ({streaks.get('momentum_score', 0)}%)</h2>
            <p>Longest Streak: {streaks.get('longest_streak', 0)} days | Keep it going toward April 6 goal! 🎯</p>
        </div>

        <div class="section">
            <div class="header"><h2>📞 Today's Calls (Sorted by Win Probability)</h2></div>
            <h3>Tier 1 Priority:</h3>
            {"".join(f"""<div class='task'>
                <button class='copy-btn' onclick="copyToClipboard('{call.get('contact_phone', '')}')">📞</button>
                <strong>{call['company']}</strong> - {call.get('contact_name', 'Unknown')} ({call.get('contact_phone', 'No phone')})
                <span class='win-prob'>{call.get('win_probability', 0)}% win</span>
                <span class='next-action'>{call.get('next_best_action', 'Call')}</span>
                <span class='ab-badge'>A/B: {call.get('ab_variant', 'control')}</span>
                <br><small><em>{call.get('industry', 'Unknown industry')}</em></small>
                {f"<br><button onclick=\"toggleScript('script-{call.get('id', i)}')\">📜 Show Script</button><div id='script-{call.get('id', i)}' class='script' style='display:none;'>{call.get('script', '')}</div>" if call.get('script') else ""}
            </div>""" for i, call in enumerate(data['calls']['tier_1']))}
            <h3>Tier 2:</h3>
            {"".join(f"""<div class='task'>
                <button class='copy-btn' onclick="copyToClipboard('{call.get('contact_phone', '')}')">📞</button>
                <strong>{call['company']}</strong> - {call.get('contact_name', 'Unknown')} ({call.get('contact_phone', 'No phone')})
                <span class='win-prob'>{call.get('win_probability', 0)}% win</span>
                <span class='next-action'>{call.get('next_best_action', 'Call')}</span>
                <span class='ab-badge'>A/B: {call.get('ab_variant', 'control')}</span>
                <br><small><em>{call.get('industry', 'Unknown industry')}</em></small>
                {f"<br><button onclick=\"toggleScript('script-t2-{call.get('id', i)}')\">📜 Show Script</button><div id='script-t2-{call.get('id', i)}' class='script' style='display:none;'>{call.get('script', '')}</div>" if call.get('script') else ""}
            </div>""" for i, call in enumerate(data['calls']['tier_2']))}
        </div>

        <div class="section">
            <div class="header"><h2>🚗 Today's In-Person Visits</h2></div>
            {"".join(f"""<div class='task'>
                <button class='copy-btn' onclick="copyToClipboard('{visit.get('contact_phone', '')}')">📍</button>
                <strong>{visit['company']}</strong> - {visit.get('contact_name', 'Unknown')} ({visit.get('contact_phone', 'No phone')})
                <span class='win-prob'>{visit.get('win_probability', 0)}% win</span>
                <span class='next-action'>{visit.get('next_best_action', 'Visit')}</span>
                <br><small><em>{visit.get('industry', 'Unknown industry')}</em></small>
            </div>""" for visit in data['visits'])}
        </div>

        <div class="section">
            <div class="header"><h2>📧 Today's Email Queue</h2></div>
            {"".join(f"""<div class='task'>
                <button class='copy-btn' onclick="copyToClipboard('{email.get('contact_email', '')}')">✉️</button>
                <strong>{email['company']}</strong> - {email.get('contact_email', 'No email')}
                <span class='win-prob'>{email.get('win_probability', 0)}% win</span>
                <span class='next-action'>{email.get('next_best_action', 'Email')}</span>
                <br><small><em>{email.get('industry', 'Unknown industry')}</em></small>
            </div>""" for email in data['emails'])}
        </div>

        <div class="section">
            <div class="header"><h2>📅 Today's Schedule</h2></div>
            {"".join(f"<div class='task'>{event['summary']} - {event['start']['dateTime'][:16]} to {event['end']['dateTime'][:16]}</div>" for event in data['schedule'])}
        </div>

        <div class="section">
            <div class="header"><h2>✅ Accountability Status</h2></div>
            {"".join(f"<div class='task {"completed" if status["completed"] else ""}'>{activity.replace("_", " ").title()}: {"✅ Completed" if status["completed"] else "⏳ Pending"}</div>" for activity, status in data['accountability'].items() if isinstance(status, dict) and 'completed' in status)}
        </div>

        <div class="section">
            <div class="header"><h2>🎯 April 6 Goal Progress</h2></div>
            <pre>{data['goal_progress']}</pre>
        </div>

        <div class="section">
            <div class="header"><h2>🔥 Hot Leads (Sorted by Win Probability)</h2></div>
            {"".join(f"<div class='task'><strong>{getattr(lead, 'company', str(lead))}</strong> ({getattr(lead, 'win_probability', 0)}% win probability)</div>" for lead in data['hot_leads'])}
        </div>

        <div class="section">
            <div class="header"><h2>🎯 Next Actions</h2></div>
            {"".join(f"<div class='task'>{action}</div>" for action in data['next_actions'])}
        </div>
    </body>
    </html>
    """

    return html
