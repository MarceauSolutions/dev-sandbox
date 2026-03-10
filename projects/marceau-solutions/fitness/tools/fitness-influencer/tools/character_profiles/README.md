# Character Profiles

Character profiles define consistent physical descriptions for AI-generated characters.
Based on the "Facial Engineering" technique from the research PDFs.

## How to Use

1. Copy `example_profile.json` and customize for your character
2. Run `test_character_consistency.py --profile your_profile.json --count 5`
3. Review generated images for consistency
4. Refine the profile based on results

## Profile Fields

- **physical**: Detailed physical description (age, build, hair, face, skin)
- **style**: Clothing, environment, camera setup
- **voice**: Provider and voice ID (filled in after voice testing)
- **prompt_template**: Auto-constructed prompt using the physical/style fields

## Tips from Research

- Be extremely specific about facial features (the more detail, the more consistent)
- Include camera model for photorealistic results (RED Komodo, ARRI Alexa, Sony Venice)
- Use "8K" and specific lens mm for quality
- Keep environment consistent across generations
