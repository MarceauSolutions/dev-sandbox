Export photos from macOS Photos.app, resize/compress to a max file size, and save to a folder.

Run this as an interactive guided flow using AskUserQuestion at each step. Do NOT show the user any bash commands — just run them behind the scenes.

## Step 1: Selection Mode

Use AskUserQuestion to ask how the user wants to select photos:
- **"Pick from recent photos"** — Show their recent photos in a numbered list and let them pick. Maps to `--browse`.
- **"Choose an album"** — List their albums and let them pick one, then export the whole album. Maps to `--album "<name>"`.
- **"Most recent N photos"** — Ask how many, export all of them. Maps to `--recent <N>`.

### If "Pick from recent photos":
Run the command silently to get recent photo filenames:
```
cd /Users/williammarceaujr./dev-sandbox/projects/shared/photo-processor && python -c "
from src.photo_exporter import PhotoExporter
photos = PhotoExporter().get_recent_photos(30)
for i, p in enumerate(photos, 1):
    date = p.date.strftime('%Y-%m-%d') if p.date else 'unknown'
    print(f'{i}. {p.filename} ({date})')
"
```
Show the list to the user and use AskUserQuestion to ask which ones they want (e.g., "1-5", "1,3,7", "all"). Then run `--recent 30` with the browse flow, passing the user's selection as stdin.

**Simpler alternative:** Just tell the user the command will show a numbered list in terminal and they can pick from there, then run: `python -m src --browse --output <FOLDER> --max-size <SIZE> --verbose`

### If "Choose an album":
Run this command silently to get album names:
```
cd /Users/williammarceaujr./dev-sandbox/projects/shared/photo-processor && python -c "
from src.photo_exporter import PhotoExporter
for a in PhotoExporter().list_albums():
    print(a)
"
```
Then use AskUserQuestion to present the albums as options (pick up to 4 that seem most relevant, plus "Other" lets them type any name).

### If "Most recent N photos":
Use AskUserQuestion to ask how many: "5", "10", "20", "50".

## Step 2: Output Folder

Use AskUserQuestion:
- "~/Desktop/exported-photos/ (Recommended)"
- "~/Downloads/exported-photos/"
(User can type a custom path via "Other")

## Step 3: Max File Size

Use AskUserQuestion:
- "5 MB (Recommended)"
- "2 MB"
- "1 MB"
(User can type a custom size via "Other")

## Step 4: Execute

Build and run the command with collected parameters. Always add `--verbose`.

```
cd /Users/williammarceaujr./dev-sandbox/projects/shared/photo-processor && python -m src <FLAGS> --output <FOLDER> --max-size <SIZE> --verbose
```

For `--browse` mode, the tool shows a numbered list in terminal — the user picks interactively there.

## Step 5: Results

Show a clean summary of what was exported. Mention the output folder path so they can find their photos.

## Important
- Never show raw bash commands to the user
- Always use AskUserQuestion for choices (not text prompts)
- If $ARGUMENTS is provided, try to parse the intent (e.g., "from Gym album to desktop") and skip redundant questions
