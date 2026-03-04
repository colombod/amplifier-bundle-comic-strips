# Cuphead Style Pack

Visual style guide for Cuphead-inspired 1930s rubber-hose cartoon strip creation.

## Image Prompt Template

Base template for generating Cuphead-style panel images:

```
1930s rubber-hose cartoon illustration, hand-inked characters on watercolor painted background, {scene_description}. Tube-like limbs with no joints, pie-cut eyes, white four-fingered gloves, round organic shapes. Soft pastel watercolor backgrounds with warm vintage film grain and slight sepia desaturation. In the style of Fleischer Studios and early Disney Silly Symphonies. No text in image.
```

## Color Palette

Warm desaturated vintage palette with watercolor softness and film-aged tones.

- **Primary**: Warm vintage character tones:
  - Faded red `#C0392B` — character accents, boss anger, danger cues
  - Cream white `#F5E6CA` — gloves, highlights, speech elements
  - Warm black `#2C2416` — ink outlines, character linework, borders
- **Secondary**: Soft watercolor background palette:
  - Dusty sky blue `#89AEB2` — skies, water, calm scenes
  - Sage green `#8FBC8F` — grass, forests, natural environments
  - Warm peach `#E8B89D` — sunsets, interiors, carnival scenes
- **Highlights**: Soft yellow `#F0D58C` for sunlight, sparkles, and magical effects
- **Backgrounds**: Desaturated pastels with yellowed paper warmth `#FDF6E3` as base tone; vignette darkening `#3E2C1A` at frame edges

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — standard Western comic flow, left to right, top to bottom
- **Borders**: Rounded black borders, 2-3px weight, with slight hand-drawn wobble for vintage feel
- **Gutters**: Medium cream-colored gutters, 8-10px width, matching the aged paper tone
- **Border shapes**: Rounded rectangles and oval frames evoking vintage film title cards and cartoon iris shots
- **Splash panels**: Full-width panels for boss introductions and transformation sequences
- **Panel count**: 4-6 per page in a regular grid; occasional circular iris-in/iris-out panels for scene transitions

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rounded rectangle** (default): `clip-path: inset(2% round 12px)` -- standard vintage cartoon frame
- **Oval spotlight** (introduction): `clip-path: ellipse(48% 45% at 50% 50%)` -- boss reveals and character spotlights
- **Iris circle** (transition): `clip-path: circle(42% at 50% 50%)` -- classic cartoon iris-in/iris-out
- **Wavy border** (chaos): `clip-path: polygon(2% 5%, 50% 0%, 98% 5%, 100% 50%, 98% 95%, 50% 100%, 2% 95%, 0% 50%)` -- morphing and transformation scenes
- **Wide stage** (performance): `clip-path: inset(5% 0% 5% 0% round 8px)` -- theatrical boss encounters

## Text Treatment

- **Speech bubbles**: Round white bubbles with thick wobbly hand-drawn borders; tails curve playfully
- **Font style**: Hand-lettered vintage cartoon lettering, bold rounded uppercase with slight irregularity
- **Sound effects**: Classic cartoon onomatopoeia — "BOING", "HONK", "CRASH" — rendered in bouncy warped lettering
- **Caption boxes**: Art Deco-styled rectangular boxes with ornate geometric borders for scene-setting text
- **Title cards**: Decorative 1930s title cards with theatrical flourishes between scenes

## Character Rendering

- **Proportions**: Exaggerated rubber-hose proportions — oversized heads, tiny bodies, enormous hands and feet
- **Limbs**: Tube-like arms and legs with no elbows or knees; they bend as smooth continuous curves
- **Eyes**: Pie-cut oval eyes with triangular wedge highlight indicating gaze direction
- **Hands**: Four-fingered white gloves on every character, oversized and expressive
- **Motion**: Constant squash-and-stretch deformation; characters bounce, sway, and pulse even when idle
- **Expression**: Emotion through full-body deformation — joy inflates, fear deflates, anger enlarges

## AmpliVerse Branding

- **Publisher name**: Art Deco-styled "AmpliVerse" lettering on a decorative banner above the title
- **Avatar**: AmpliVerse avatar rendered in rubber-hose style with pie-cut eyes and white gloves
- **Color treatment**: Warm black on cream to match the vintage 1930s aesthetic

## Image Requirements

```yaml
image_requirements:
  style_category: cuphead-vintage
  detail_level: medium
  text_avoidance: good
```
