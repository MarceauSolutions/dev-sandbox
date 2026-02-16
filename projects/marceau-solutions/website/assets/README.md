# Assets Directory

This folder contains static assets for the Marceau Solutions website.

## Structure

```
assets/
├── images/       # Logo files, product photos, screenshots
├── videos/       # Demo videos, product showcases, testimonials
└── documents/    # PDFs, case studies, downloadable resources
```

## Usage

### Images
- **Logo**: Company branding, variations (light/dark, different sizes)
- **Product Photos**: Fitness equipment, software screenshots
- **Marketing**: Social media graphics, ad creative
- **Testimonials**: Client photos, before/after shots

### Videos
- **Product Demos**: Screen recordings of AI Assistant features
- **Testimonials**: Client video reviews
- **Ads**: Marketing video content
- **Tutorials**: How-to guides, feature walkthroughs

### Documents
- **Case Studies**: Client success stories (PDF)
- **Guides**: Setup instructions, user manuals
- **Marketing Materials**: One-pagers, brochures

## Best Practices

1. **File Naming**: Use descriptive, lowercase names with hyphens
   - ✅ `fitness-ai-logo-dark.png`
   - ❌ `Image1.PNG`

2. **Optimization**:
   - Images: Compress before uploading (use TinyPNG, ImageOptim)
   - Videos: Compress with H.264 codec (max 1080p for web)
   - Keep file sizes reasonable for fast loading

3. **Formats**:
   - Images: PNG (logos/graphics), JPG (photos), WebP (modern browsers)
   - Videos: MP4 (H.264), WebM (fallback)
   - Documents: PDF (universal compatibility)

4. **Accessibility**:
   - Always provide alt text for images
   - Include captions/transcripts for videos
   - Ensure documents are text-searchable

## Git LFS (Optional)

For large video files (>50MB), consider using Git LFS:
```bash
git lfs track "assets/videos/*.mp4"
git add .gitattributes
```

---

Last Updated: 2026-01-05
