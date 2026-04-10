# Trainerize Analysis — What to Replicate for BOABFIT App

Based on Julia's screen recordings (2026-04-01).

## Admin Side (Trainer Dashboard)

### What Julia Uses Daily
1. **Activity feed** — sees all client activity in real-time (completed workouts, missed workouts, weigh-ins, food logs)
2. **Program builder** — creates "master programs" with phases/weeks
3. **Workout builder** — drag exercises from library into days, set time/reps/rest
4. **Exercise library** — pre-loaded exercise database with video thumbnails, organized by muscle group
5. **Training phases** — groups weeks together (e.g., "BOABFIT WEEKS 1-2", "WEEKS 3-4", "WEEKS 5-6")
6. **Schedule** — assign workouts to specific days for clients

### Her Current Programs (visible in sidebar)
- 14-Day Trial Program
- 20 minute Bubble
- 30-Day Ab shredder
- 8 Week Full Body
- At Home Bodyweight
- BOAB FIT 6-Week (the main one)
- BOAB FIT 20 MIN...
- BOABFIT MORN...
- BOABFIT testing
- Dad Workout
- JULIA FOR NOW...
- Julia Current Gym S...
- Mami Jami - Work...
- ON DEMAND - BO...
- QUICK & EASY
- Tags: BARBIE BODY, BOABFIT, FAMILY

### BOABFIT Weeks 1-2 Structure
5 workouts per week:
| Workout | Duration | Exercises |
|---------|----------|-----------|
| Full Body - Sculpt+Tone | 25 min | 30 exercises |
| Lower Body - Build | 25 min | 31 exercises |
| Lower Body - Sculpt | 24 min | 30 exercises |
| Upper Body - Build | 23 min | 38 exercises |
| Upper Body - Sculpt | 24 min | 14 exercises |

Each workout starts with "HEY GIRL - DISCLAIMER - There is no 'RE..."

### Exercise Builder UI
- Exercise name + thumbnail
- Time-based (e.g., 60 sec) not just rep-based
- Circuit mode toggle
- Add Rest button
- Drag-and-drop reordering
- Exercise library panel on the right with search

## Client Side (App)

### Home Screen
- "THINGS TO DO TODAY" — today's date + scheduled workout
- Calendar navigation (< today >)
- "MY PROGRESS" — customizable tiles
- "MY ACHIEVEMENTS" — auto-generated milestone badges
- Julia's avatar in bottom-right as a floating action button

### Bottom Navigation (4 tabs)
1. Activity/feed icon
2. Calendar
3. Workout/timer
4. More (ooo)

### Calendar View
- Day-by-day list showing workout name + "Complete your scheduled workout"
- Circle checkbox (empty = not done)
- Days without workouts show as rest days (Wednesday, Sunday)
- Clean, simple list format

### Workout "Press Play" Flow — THIS IS THE CORE UX
1. Exercise video plays at top (Julia doing the movement with pink dumbbells)
2. Exercise name below video ("Dumbbell Bent-Over Rows")
3. Rep/time count ("8 TOTAL")
4. Large countdown timer ("00:25")
5. "UP NEXT" preview showing next exercise thumbnail + name + reps + time
6. Bottom bar: REMAINING time (e.g., 23:25) | COMPLETED (e.g., 21%)
7. Progress bar across the bottom
8. Controls: rewind, stop, lock screen, pause/play, skip forward
9. "FULL VIDEO" button in top right corner for longer demo
10. Audio icon in top left (sound on/off for exercise audio cues)

### Key UX Details
- Timer-based exercises (30 sec per exercise, auto-advances)
- Video loops the exercise movement during the timer
- "Up Next" preview creates anticipation
- Remaining/Completed gives overall workout progress
- Lock button prevents accidental touches during workout
- Very dark/black workout screen (content-focused)

### Achievements System
- Auto-generated badges like:
  - "Heaviest weight ever! Lifted 15 lbs for Dumbbell Bench Rows"
  - "Max volume ever! Lifted 250 lbs across all reps for Dumbbell Bulgarian Split Squat"
  - "Heaviest 10RM ever! Lifted 25 lbs for Dumbbell Bulgarian Split Squat"
- Dated entries (25 Mar, 11 Mar, 10 Mar)
- Kettlebell icon for achievements

### Brand Elements Visible
- "BOABFIT" header text (clean, caps)
- Soft pink/blush background (#f5e6e0 range)
- Light grey text
- Notification bell icon
- Julia's profile photo as floating avatar

## What We MUST Replicate (Priority Order)
1. **Press Play workout flow** — this is the product. Timer, video, auto-advance, up next, progress bar.
2. **Calendar with scheduled workouts** — clients need to know what to do today
3. **Exercise library with videos** — admin uploads, client watches
4. **Program builder** — Julia builds programs with phases/weeks/days
5. **Achievement system** — auto-generated milestones keep users engaged
6. **Progress tiles** — customizable dashboard widgets
7. **Activity feed for admin** — Julia sees what all her clients are doing

## What We Can Improve Over Trainerize
- **Better UI/branding** — Trainerize is generic. BOABFIT app should feel like Julia's brand (Barbie pink, not grey)
- **Faster load times** — Trainerize can be sluggish
- **Better video playback** — fullscreen mode, higher quality
- **Push notifications that Julia controls** — not just system-generated
- **Creator presence** — Julia's weekly video messages, not just workout content
- **No Trainerize branding** — it's HER app
