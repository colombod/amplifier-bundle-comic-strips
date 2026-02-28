# Ligne Claire Style Pack

Visual style guide for ligne claire comic strip creation.

## Image Prompt Template

Base template for generating ligne claire panel images:

```
Ligne claire comic illustration, clean uniform line weight, flat bright colors, {scene_description}. Highly detailed backgrounds with architectural precision. No hatching or cross-hatching. Clear distinct outlines on every element. In the style of Herge's Tintin and Moebius. European album format. No text in image.
```

## Color Palette

Clean, precise palette with flat bright fills on uniform black outlines.

- **Primary**: Clean uniform black outlines `#000000` — every element defined by identical-weight ink lines with no variation
- **Fill**: Flat bright colors for vivid, unshaded coloring:
  - Sky blue `#4ECDC4` — skies, water, open spaces
  - Warm orange `#FF6B35` — clothing, accents, warm elements
  - Leaf green `#2ECC71` — vegetation, nature, environmental detail
- **Rule**: No gradients, no shading, flat fills only — color exists purely within outlines as solid, uniform areas

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — panels are arranged and read from left to right, following European album page flow
- **Borders**: Uniform thin 1.5px black borders around every panel — same weight as art lines for seamless visual consistency
- **Gutters**: Consistent medium 8px white gutters between panels — balanced spacing for clear panel separation
- **Border shapes**: Rectangular regular grid with occasional wide establishing panels — structured layouts that open up for scenic moments
- **Format**: European album format with larger panels than American comics — generous space for detailed backgrounds and precise linework
- **Panel count**: 4-8 per page across 2-3 rows — flexible grid allowing narrative pacing within a structured framework

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` -- standard panels
- **Wide rectangular** (establishing): Full-width panel, `clip-path: inset(0)` -- establishing shots and landscapes
- **Rounded rectangular** (soft): `clip-path: inset(0 round 8px)` -- gentle moments, character close-ups

## Text Treatment

- **Speech bubbles**: Clean round white bubbles with uniform outline matching art weight — seamless integration with the linework
- **Font style**: Clean rounded sans-serif sentence case lettering — legible and unobtrusive within the precise aesthetic
- **Sound effects**: Rare integrated sound effects — used sparingly and drawn to match the clean line style rather than disrupting it
- **Caption boxes**: Clean rectangular thin border captions — precise boxes for narration matching the overall geometric precision
- **Dialogue philosophy**: Dialogue-driven storytelling — conversations and character interaction carry the narrative forward

## Character Rendering

- **Line quality**: Clean uniform line weight with no thick/thin variation — the defining characteristic of ligne claire, every line identical weight
- **Faces**: Slightly simplified expressive faces — readable emotions through clean, economical linework
- **Clothing**: Detailed clothing and accessories — precise rendering of garments, gear, and personal items
- **Depth**: Equal detail in foreground and background — no atmospheric perspective or detail falloff, everything rendered with the same precision
- **Proportions**: Natural proportions — realistic body ratios without exaggeration or stylized distortion
- **Archetypes**: Adventurer-type characters — curious, resourceful agents exploring detailed worlds

## AmpliVerse Branding

- **Placement**: Clean banner positioned top center of the page — a precise title area anchoring the composition
- **Avatar**: AmpliVerse avatar placed left of title within the banner — small and neatly integrated
- **Color treatment**: Clean black on white for all branding elements — matching the precise aesthetic of the ligne claire style

## Image Requirements

```yaml
image_requirements:
  style_category: ligne-claire
  detail_level: high
  text_avoidance: excellent
```

