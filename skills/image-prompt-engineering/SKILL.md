---
name: image-prompt-engineering
description: "Use when crafting prompts for comic panel or cover image generation. Covers the faces-visible rule, style anchoring, character consistency with reference images, camera framing, speech bubble space, avoiding common artifacts, and prompt structure for comic art."
version: "2.0.0"
---

# Image Prompt Engineering for Comics

## Rule #1: Faces MUST Be Fully Visible and Unobstructed

Every character's face must be fully visible, unobstructed, and clearly rendered in every panel. This is the single most important rule for comic art -- readers connect with characters through their faces.

**Include this directive in EVERY prompt that contains characters:**

> "characters facing the viewer with faces fully visible and unobstructed, clear detailed facial features"

If a panel has multiple characters, EVERY character's face must be visible. No exceptions. If the composition makes it impossible to show all faces, restructure the composition -- do not sacrifice face visibility.

## Prompt Structure

Every image generation prompt should follow this 7-step order:

1. **Style anchor**: Start with the style pack's image prompt template (e.g., "Manga illustration, ink wash..." or "Superhero comic, bold colors...")
2. **Scene description**: What is happening in this panel -- the action, environment, and mood
3. **Character description with face visibility**: Who is in the panel, their visual traits, and the directive that all faces are fully visible and unobstructed
4. **Composition directives**: Camera angle, framing, focal point, depth of field
5. **Space allocation**: Where to leave negative space for text overlays, speech bubbles, or title placement
6. **Technical constraints**: "No text in image", aspect ratio hints, quality markers, "anatomically correct"
7. **Reference images directive**: Attach character reference images for consistency across panels

## Camera Framing Rules

| Shot Type | Framing | When to Use | Face Rule |
|-----------|---------|-------------|-----------|
| Establishing/Wide | Full environment with characters at smaller scale | Opening scenes, location changes, showing scale | All characters' faces must still be discernible even at distance |
| Medium | Characters from waist up, balanced with environment | Dialogue scenes, character interactions | Faces fully visible and centered in frame |
| Close-up | Head and shoulders filling the frame | Emotional beats, reactions, revelations | Face is the entire focus -- every feature crisp and detailed |
| Over-shoulder | One character's back/shoulder in foreground, other character facing camera | Two-person conversations, confrontations | The facing character's face MUST be fully visible; the foreground character may show partial profile |
| Action/Dynamic | Tilted angles, motion blur, dramatic perspective | Fight scenes, chases, dramatic moments | Even in dynamic poses, faces must remain visible and unobstructed |

### NEVER Do These

- Close-ups that cut off the top of the head or the chin
- A character's face completely turned away from the viewer (facing completely away)
- A face obscured by hair, shadows, or objects
- Crowd scenes where main characters' faces are lost in the mass of people

## Leave Space for Speech Bubbles

Comic panels need room for dialogue. Always include:

> "with open negative space in the upper portion of the composition for text overlay placement"

For dialogue-heavy panels, reserve 20-30% of the panel as plain background or sky where speech bubbles can be placed without covering important art.

Guidelines:
- **Top third**: Preferred location for speech bubbles
- **Avoid faces**: Never place negative space where it would overlap a character's face
- **Multiple speakers**: Leave space near each speaker's head for their dialogue
- **Narration boxes**: Reserve a corner or edge strip for narrator captions

## Character Consistency Through Reference Images

ALWAYS include reference_images when characters are present in a panel. This is non-negotiable.

- Pass character reference sheets via the `reference_images` parameter on every image generation call
- Include `visual_traits` in the text prompt (e.g., "tall woman with short silver hair, blue jumpsuit, scar on left cheek")
- Include `distinctive_features` in the text prompt (e.g., "glowing blue eyes, mechanical right arm, always wears a red scarf")
- Never rely on text description alone -- the reference image is the ground truth for appearance
- If a character has not been illustrated yet, generate a character reference sheet FIRST, then use it for all subsequent panels

## Style Anchoring

Start EVERY prompt with the style pack's image prompt template. This anchors the visual consistency:

- Use the EXACT template wording as the first sentence of every prompt
- Replace `{scene_description}` with the panel-specific content
- Never omit the style anchor -- it prevents style drift between panels
- If the style pack provides color palette directives, include those as well
- Consistency comes from repetition: the same style anchor in every single prompt

## Avoiding Common Artifacts

| Artifact | Prevention Directive |
|----------|---------------------|
| Text/letters in image | ALWAYS include "No text in image, no words, no letters, no writing" |
| Extra fingers/limbs | Include "anatomically correct, proper hand anatomy, five fingers per hand" |
| Face distortion | "Clear detailed face, well-defined facial features, symmetrical face" |
| Style inconsistency | Always lead with the full style anchor template from the style pack |
| Busy/cluttered composition | "Clean composition, clear focal point, uncluttered background" |
| Wrong aspect ratio | Specify "wide landscape format" or "tall portrait format" as needed |
| Uncanny valley eyes | "Natural eye proportions, consistent eye direction, both eyes matching" |

## Composition Quality Checklist (for Vision-Based Self-Review)

After generating an image, evaluate it against this checklist. Use vision capabilities to inspect the result.

1. **Faces visible** -- Pass: Every character's face is fully visible, unobstructed, and clearly rendered
2. **Clear focal point** -- Pass: The viewer's eye is drawn to one primary subject or action
3. **Tells story visually** -- Pass: The panel communicates its narrative beat without needing dialogue to explain
4. **Characters match references** -- Pass: Characters are visually consistent with their reference sheets
5. **Space for text overlays** -- Pass: There is adequate negative space for speech bubbles or narration boxes
6. **Style consistent** -- Pass: The art style matches the style pack and previous panels
7. **No text artifacts** -- Pass: No unintended text, letters, or symbols appear in the image
8. **Composition balanced** -- Pass: Visual weight is distributed intentionally, no awkward empty or cramped areas

**If ANY of checks 1-3 fail, the image MUST be regenerated.** These are mandatory regeneration triggers -- no exceptions. Checks 4-8 may be addressed with prompt refinement on the next attempt.

## Panel-Specific Prompt Patterns

- **Action panel**: Emphasize dynamic poses, motion lines, dramatic angle, energy and movement -- but faces must remain visible even in motion
- **Dialogue panel**: Emphasize character expressions, clear faces, space for speech bubbles, open negative space in upper portion
- **Establishing panel**: Emphasize environment, wide angle, architectural detail, atmosphere -- characters at smaller scale but faces still discernible
- **Close-up panel**: Emphasize emotion, detailed facial features, shallow depth of field -- face fills the frame with every feature crisp
- **Silent panel**: Emphasize mood, atmosphere, environmental storytelling, visual metaphor -- character faces convey the unspoken emotion

## Cover Art Prompts

Cover prompts differ from panel prompts and must showcase the story at its most dramatic:

- Include ALL major characters together in one composition
- Use the most dramatic pose from the story -- a moment of peak tension or triumph
- Leave space in the top third for title treatment and series branding
- Compose like a movie poster -- single iconic image that sells the story
- ALL character faces must be visible and recognizable -- this is the reader's first impression
- Higher detail level than individual panels
- Include both `reference_images` and detailed `visual_traits` for every character
