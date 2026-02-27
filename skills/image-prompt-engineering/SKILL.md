---
name: image-prompt-engineering
description: "Use when crafting prompts for comic panel or cover image generation. Covers style anchoring, character consistency across panels, avoiding common artifacts, and prompt structure for comic art."
version: "1.0.0"
---

# Image Prompt Engineering for Comics

## Prompt Structure

Every image generation prompt should follow this order:

1. **Style anchor** (from style guide template): "Manga illustration, ink wash..." or "Superhero comic, bold colors..."
2. **Scene description**: What is happening in this panel
3. **Character description**: Who is in the panel and what they look like (MUST be consistent)
4. **Composition directives**: Camera angle, framing, focal point
5. **Technical constraints**: "No text in image", aspect ratio hints, quality markers

## Style Anchoring

Start EVERY prompt with the style pack's image prompt template. This anchors the visual consistency:
- Use the EXACT template wording as the first sentence
- Replace `{scene_description}` with the panel-specific content
- Never omit the style anchor -- it prevents style drift between panels

## Character Consistency

The #1 challenge in multi-panel comics. Use these techniques:

- **Character sheet**: Define each character ONCE with specific visual traits, then reference them by name in every panel
- **Trait anchoring**: Include 3-5 distinctive visual traits every time (e.g., "a tall figure with glowing blue eyes, silver armor, and a red cape")
- **Consistency keywords**: Add "same character as previous panels" or "consistent character design"
- **Avoid vague descriptions**: "the hero" is inconsistent; "a tall woman with short silver hair wearing a blue jumpsuit" is consistent

## Avoiding Common Artifacts

| Artifact | Prevention |
|----------|-----------|
| Text in image | ALWAYS include "No text in image" or "No words, no letters, no writing" |
| Extra fingers/limbs | Include "anatomically correct, proper hand anatomy" |
| Face distortion | "Clear detailed face, well-defined facial features" |
| Style inconsistency | Always lead with the full style anchor template |
| Busy/cluttered composition | "Clean composition, clear focal point, uncluttered" |
| Wrong aspect ratio | Specify "wide landscape format" or "tall portrait format" as needed |

## Panel-Specific Prompt Patterns

- **Action panel**: Emphasize dynamic poses, motion blur, speed lines, dramatic angle
- **Dialogue panel**: Emphasize character expressions, clear faces, space for speech bubbles
- **Establishing shot**: Emphasize environment, wide angle, architectural detail
- **Close-up**: Emphasize emotion, detailed features, shallow depth of field
- **Silent panel**: Emphasize mood, atmosphere, environmental storytelling

## Cover Art Prompts

Cover prompts differ from panel prompts:
- Include ALL major characters together in one composition
- Use the most dramatic/dynamic pose from the story
- Leave space for title treatment (top third typically)
- Make it a "movie poster" composition -- single iconic image
- Higher detail level than individual panels
