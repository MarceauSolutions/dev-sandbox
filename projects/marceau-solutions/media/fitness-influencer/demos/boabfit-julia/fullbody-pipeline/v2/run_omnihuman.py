#!/usr/bin/env python3
"""Run OmniHuman 1.5 to generate lip-synced talking head video."""
import os, base64, time, requests, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), '.env'))

REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')
OMNIHUMAN_VERSION = '566f1b03016969ac39e242c1ae4a39034686ca8850fc3dba83dceaceb96f74b2'
API_BASE = 'https://api.replicate.com/v1'

base_dir = os.path.dirname(__file__)
headshot = os.path.join(base_dir, 'julia-v2_2.png')
audio = os.path.join(base_dir, 'julia-voiceover-v2.mp3')
output = os.path.join(base_dir, 'julia-omnihuman.mp4')

with open(headshot, 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()
with open(audio, 'rb') as f:
    audio_b64 = base64.b64encode(f.read()).decode()

print('Starting OmniHuman 1.5 via Replicate...')
print('Cost: ~$2.80 | Expected time: 3-8 minutes')

headers = {
    'Authorization': f'Bearer {REPLICATE_API_TOKEN}',
    'Content-Type': 'application/json'
}

payload = {
    'version': OMNIHUMAN_VERSION,
    'input': {
        'image': f'data:image/png;base64,{img_b64}',
        'audio': f'data:audio/mpeg;base64,{audio_b64}',
    }
}

resp = requests.post(f'{API_BASE}/predictions', headers=headers, json=payload, timeout=60)
if resp.status_code not in (200, 201):
    print(f'ERROR: {resp.status_code} - {resp.text[:300]}')
    sys.exit(1)

prediction_id = resp.json()['id']
print(f'Prediction: {prediction_id} — polling...')

for i in range(120):
    time.sleep(5)
    sr = requests.get(
        f'{API_BASE}/predictions/{prediction_id}',
        headers={'Authorization': f'Bearer {REPLICATE_API_TOKEN}'},
        timeout=30,
    )
    if sr.status_code != 200:
        continue
    status = sr.json()
    state = status.get('status')
    elapsed = (i + 1) * 5
    if state == 'succeeded':
        out = status.get('output')
        video_url = out if isinstance(out, str) else (out[0] if isinstance(out, list) else None)
        print(f'\nCompleted in {elapsed}s!')
        print('Downloading video...')
        video_data = requests.get(video_url, timeout=120).content
        with open(output, 'wb') as f:
            f.write(video_data)
        size_mb = len(video_data) / 1024 / 1024
        print(f'Saved: {output} ({size_mb:.1f} MB)')

        from moviepy import VideoFileClip
        clip = VideoFileClip(output)
        print(f'Duration: {clip.duration:.1f}s | Resolution: {clip.size[0]}x{clip.size[1]} | FPS: {clip.fps}')
        clip.close()
        print('Done!')
        sys.exit(0)
    elif state in ('failed', 'canceled'):
        print(f'\nERROR: {state}: {status.get("error", "Unknown")}')
        sys.exit(1)

    print(f'  {state} ({elapsed}s)...', end='\r')

print('\nERROR: Timed out after 10 minutes')
sys.exit(1)
