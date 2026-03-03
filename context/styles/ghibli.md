# Ghibli Style Pack

Visual style guide for Studio Ghibli-inspired watercolor illustration strip creation.

## Image Prompt Template

Base template for generating Ghibli-style panel images:

```
Studio Ghibli watercolor illustration, hand-painted backgrounds with soft earthy natural palette, {scene_description}. Lush botanical detail with dappled golden-hour sunlight filtering through trees. Gentle rounded character designs with expressive simplicity. Atmospheric perspective with layered transparent washes. Magical realism where fantasy feels organic and natural. In the style of Hayao Miyazaki and Kazuo Oga background art. No text in image.
```

## Color Palette

Earthy natural tones with watercolor warmth and atmospheric depth.

- **Primary**: Nature-derived foundation colors:
  - Forest green `#5B8C5A` — trees, grass, living nature, magical vitality
  - Sky blue `#87CEEB` — open skies, water, peaceful moments
  - Warm brown `#A0522D` — earth, wood, architecture, grounding elements
- **Secondary**: Emotional and atmospheric accents:
  - Golden hour amber `#DAA520` — sunlight, warmth, home, nostalgia
  - Twilight lavender `#9B7EC8` — dusk, mystery, quiet magic
  - Sunrise pink `#E8A0BF` — dawn, wonder, gentle fantasy
- **Highlights**: White gouache `#FEFEFE` for water reflections, bright flowers, and window light
- **Backgrounds**: Layered watercolor washes from pale sky `#E8F4FD` to warm earth `#D2B48C`; atmospheric fade to soft blue `#B0C4DE` in distance

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — adapted Western flow for international audience, left to right, top to bottom
- **Borders**: Soft thin borders, 1px weight, in warm gray `#8B8682` rather than harsh black
- **Gutters**: Wide white gutters, 10-14px width, giving each panel breathing room
- **Border shapes**: Soft rectangles with very slight rounded corners; occasional borderless panels for landscape vistas
- **Splash panels**: Panoramic wide panels for sweeping landscapes, flying sequences, and moments of natural wonder
- **Panel count**: 4-6 per page in a relaxed grid; generous panel sizing to let the watercolor art breathe

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Soft rectangle** (default): `clip-path: inset(0 round 4px)` -- standard panels with gentle corners
- **Wide panoramic** (landscape): `clip-path: inset(15% 0% 15% 0% round 4px)` -- sweeping vistas and flying scenes
- **Borderless** (wonder): No clip-path, no border — full bleed for moments of awe and magical discovery
- **Tall vertical** (growth): `clip-path: inset(0% 20% 0% 20% round 4px)` -- towering trees, spirits, ascending moments
- **Oval vignette** (memory): `clip-path: ellipse(48% 46% at 50% 50%)` -- flashbacks, dreams, and nostalgic moments

## Text Treatment

- **Speech bubbles**: Soft rounded white bubbles with thin warm-gray borders; tails gently curve toward speaker
- **Font style**: Clean rounded sans-serif, mixed case, warm and approachable tone
- **Sound effects**: Subtle and sparse — soft naturalistic sounds like wind and rain rendered as delicate stylized text
- **Caption boxes**: Semi-transparent boxes with soft edges for narration, letting background art show through
- **Whisper text**: Smaller italic text in bubbles with faded borders for quiet, intimate dialogue

## Character Rendering

- **Proportions**: Gentle, naturalistic proportions; children look like children, elderly show realistic aging
- **Faces**: Round open faces with large but not exaggerated eyes; emotion through subtle shifts in shape and position
- **Hair and clothing**: Constantly interacting with environment — wind-blown hair, rustling clothes, rain-splashed fabric
- **Body language**: Authentic human gesture — the way a child runs, an old person sits, someone clutches a hat in wind
- **Physicality**: Characters show effort and fatigue; flying is joyous but climbing is hard work
- **Creatures**: Nature-based spirit designs with believable weight and texture; mysterious but never threatening

## AmpliVerse Branding

- **Publisher name**: Gentle horizontal text "AmpliVerse" in warm brown along the bottom edge of cover
- **Avatar**: AmpliVerse avatar placed in bottom-right corner, softened to match the watercolor aesthetic
- **Color treatment**: Warm brown on cream background to harmonize with the earthy natural palette

## Image Requirements

```yaml
image_requirements:
  style_category: ghibli-watercolor
  detail_level: high
  text_avoidance: good
```
