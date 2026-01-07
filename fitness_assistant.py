#!/usr/bin/env python3
"""
Fitness Influencer AI Assistant
Simple menu-driven interface - NO terminal commands needed!

Just run this file and follow the menu prompts.

Usage:
    python fitness_assistant.py
"""

import os
import sys
import subprocess
from pathlib import Path


def clear_screen():
    """Clear the terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header():
    """Print the app header."""
    clear_screen()
    print("\n" + "="*70)
    print("🏋️  FITNESS INFLUENCER AI ASSISTANT")
    print("="*70 + "\n")


def print_menu():
    """Display the main menu."""
    print("What would you like to do?\n")
    print("  VIDEO CREATION:")
    print("    1. Create Video Ad (from images)")
    print("    2. Add Jump Cuts to Video (remove silences)")
    print("    3. Create Educational Graphic\n")
    
    print("  CONTENT PLANNING:")
    print("    4. Check Emails (last 24 hours)")
    print("    5. View Calendar (next 7 days)")
    print("    6. Add Calendar Reminder\n")
    
    print("  BUSINESS ANALYTICS:")
    print("    7. View Revenue Report (requires Google Sheet setup)\n")
    
    print("  SETUP:")
    print("    8. Setup Google APIs (first-time only)")
    print("    9. View Documentation")
    print("    0. Exit\n")


def create_video_ad():
    """Create a video ad from images."""
    print("\n" + "="*70)
    print("CREATE VIDEO AD")
    print("="*70 + "\n")
    
    print("This will:")
    print("  1. Generate 2 AI images from your prompt")
    print("  2. Create a professional video ad")
    print("  3. Cost: ~$0.14-0.28 per video\n")
    
    prompt = input("Enter image prompt (e.g., 'fit woman doing squats'): ").strip()
    if not prompt:
        print("❌ Prompt required!")
        return
    
    headline = input("Enter headline text (e.g., 'Transform Your Body'): ").strip()
    if not headline:
        headline = "Transform Your Body"
    
    cta = input("Enter call-to-action (e.g., 'Start Your Journey'): ").strip()
    if not cta:
        cta = "Start Your Journey"
    
    print(f"\n→ Creating video ad...")
    print(f"  Prompt: {prompt}")
    print(f"  Headline: {headline}")
    print(f"  CTA: {cta}\n")
    
    # Run the video_ads.py script
    cmd = [
        'python', 'execution/video_ads.py',
        '--prompt', prompt,
        '--headline', headline,
        '--cta', cta,
        '--count', '2'
    ]
    
    subprocess.run(cmd, cwd=Path(__file__).parent)


def add_jump_cuts():
    """Add jump cuts to a video."""
    print("\n" + "="*70)
    print("ADD JUMP CUTS")
    print("="*70 + "\n")
    
    print("This removes silent parts from your video automatically.\n")
    
    video_path = input("Enter video file path: ").strip()
    if not video_path or not os.path.exists(video_path):
        print("❌ Video file not found!")
        return
    
    output_path = input("Enter output file path (default: input_jumpcut.mp4): ").strip()
    if not output_path:
        base = os.path.splitext(video_path)[0]
        output_path = f"{base}_jumpcut.mp4"
    
    print(f"\n→ Processing video...")
    print(f"  Input: {video_path}")
    print(f"  Output: {output_path}\n")
    
    cmd = [
        'python', 'execution/video_jumpcut.py',
        video_path,
        output_path
    ]
    
    subprocess.run(cmd, cwd=Path(__file__).parent)


def create_graphic():
    """Create an educational graphic."""
    print("\n" + "="*70)
    print("CREATE EDUCATIONAL GRAPHIC")
    print("="*70 + "\n")
    
    print("This creates a branded fitness tip graphic.\n")
    
    tip_title = input("Enter tip title (e.g., 'Protein Timing'): ").strip()
    if not tip_title:
        print("❌ Title required!")
        return
    
    tip_text = input("Enter tip text (keep it short): ").strip()
    if not tip_text:
        print("❌ Tip text required!")
        return
    
    output_file = input("Enter output filename (default: fitness_tip.jpg): ").strip()
    if not output_file:
        output_file = "fitness_tip.jpg"
    
    print(f"\n→ Creating graphic...\n")
    
    cmd = [
        'python', 'execution/educational_graphics.py',
        '--tip-title', tip_title,
        '--tip-text', tip_text,
        '--output', output_file
    ]
    
    subprocess.run(cmd, cwd=Path(__file__).parent)


def check_emails():
    """Check recent emails."""
    print("\n" + "="*70)
    print("EMAIL DIGEST")
    print("="*70 + "\n")
    
    hours = input("How many hours back? (default: 24): ").strip()
    if not hours:
        hours = "24"
    
    try:
        hours = int(hours)
    except ValueError:
        print("❌ Invalid number!")
        return
    
    cmd = ['python', 'execution/gmail_monitor.py', '--hours', str(hours)]
    subprocess.run(cmd, cwd=Path(__file__).parent)


def view_calendar():
    """View upcoming calendar events."""
    print("\n" + "="*70)
    print("UPCOMING EVENTS")
    print("="*70 + "\n")
    
    cmd = ['python', 'execution/calendar_reminders.py', 'list', '--days', '7']
    subprocess.run(cmd, cwd=Path(__file__).parent)


def add_reminder():
    """Add a calendar reminder."""
    print("\n" + "="*70)
    print("ADD CALENDAR REMINDER")
    print("="*70 + "\n")
    
    print("Create a recurring reminder (e.g., 'Instagram Post' every Mon/Wed/Fri at 9am)\n")
    
    title = input("Reminder title: ").strip()
    if not title:
        print("❌ Title required!")
        return
    
    days = input("Days of week (comma-separated, e.g., Mon,Wed,Fri): ").strip()
    if not days:
        print("❌ Days required!")
        return
    
    time = input("Time (HH:MM format, e.g., 09:00): ").strip()
    if not time:
        print("❌ Time required!")
        return
    
    description = input("Description (optional): ").strip()
    
    print(f"\n→ Creating reminder...\n")
    
    cmd = [
        'python', 'execution/calendar_reminders.py', 'create',
        '--title', title,
        '--days', days,
        '--time', time
    ]
    
    if description:
        cmd.extend(['--description', description])
    
    subprocess.run(cmd, cwd=Path(__file__).parent)


def view_revenue():
    """View revenue report."""
    print("\n" + "="*70)
    print("REVENUE REPORT")
    print("="*70 + "\n")
    
    print("⚠️  This requires a Google Sheet with revenue/expense data.")
    print("See documentation for sheet setup instructions.\n")
    
    sheet_id = input("Enter Google Sheet ID: ").strip()
    if not sheet_id:
        print("❌ Sheet ID required!")
        return
    
    month = input("Month (YYYY-MM format, or press Enter for current): ").strip()
    
    cmd = ['python', 'execution/revenue_analytics.py', '--sheet-id', sheet_id]
    if month:
        cmd.extend(['--month', month])
    
    subprocess.run(cmd, cwd=Path(__file__).parent)


def setup_google_apis():
    """Setup Google APIs."""
    print("\n" + "="*70)
    print("GOOGLE API SETUP")
    print("="*70 + "\n")
    
    print("This will authenticate your Google account for:")
    print("  • Gmail (email monitoring)")
    print("  • Calendar (reminders)")
    print("  • Sheets (revenue tracking)\n")
    
    input("Press Enter to start setup...")
    
    cmd = ['python', 'execution/google_auth_setup.py']
    subprocess.run(cmd, cwd=Path(__file__).parent)


def view_docs():
    """View documentation."""
    print("\n" + "="*70)
    print("DOCUMENTATION")
    print("="*70 + "\n")
    
    print("📚 Available Documentation:\n")
    print("  1. FITNESS_INFLUENCER_QUICK_START.md - Complete guide")
    print("  2. README.md - System overview")
    print("  3. directives/fitness_influencer_operations.md - Technical details\n")
    
    doc_choice = input("Which document to view? (1-3, or Enter to skip): ").strip()
    
    docs = {
        '1': 'FITNESS_INFLUENCER_QUICK_START.md',
        '2': 'README.md',
        '3': 'directives/fitness_influencer_operations.md'
    }
    
    if doc_choice in docs:
        doc_path = Path(__file__).parent / docs[doc_choice]
        if doc_path.exists():
            # Try to open with default viewer
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['open', str(doc_path)])
            elif sys.platform == 'win32':  # Windows
                os.startfile(str(doc_path))
            else:  # Linux
                subprocess.run(['xdg-open', str(doc_path)])
            print(f"\n✓ Opened {docs[doc_choice]}")
        else:
            print(f"\n❌ Document not found: {docs[doc_choice]}")


def main():
    """Main application loop."""
    while True:
        print_header()
        print_menu()
        
        choice = input("Enter your choice (0-9): ").strip()
        
        if choice == '1':
            create_video_ad()
        elif choice == '2':
            add_jump_cuts()
        elif choice == '3':
            create_graphic()
        elif choice == '4':
            check_emails()
        elif choice == '5':
            view_calendar()
        elif choice == '6':
            add_reminder()
        elif choice == '7':
            view_revenue()
        elif choice == '8':
            setup_google_apis()
        elif choice == '9':
            view_docs()
        elif choice == '0':
            print("\n👋 Thanks for using Fitness Influencer AI Assistant!\n")
            break
        else:
            print("\n❌ Invalid choice. Please enter 0-9.")
        
        input("\nPress Enter to continue...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)