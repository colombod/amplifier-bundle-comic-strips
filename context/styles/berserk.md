# Berserk Style Pack

Visual style guide for Berserk-inspired dark fantasy manga strip creation.

## Image Prompt Template

Base template for generating Berserk-style panel images:

```
Black and white dark fantasy manga illustration, ultra-detailed ink hatching and cross-hatching, {scene_description}. Dense Renaissance-engraving linework with sculptural volume and dramatic chiaroscuro lighting. Gothic medieval architecture and grotesque creature design. Massive sense of scale with tiny figures against enormous structures. In the style of Kentaro Miura and Gustave Doré engravings. No text in image.
```

## Color Palette

Monochrome with extraordinary tonal range achieved through hatching density.

- **Primary black**: Pure black `#000000` — heavy shadows, solid fills, oppressive darkness
- **Primary white**: Pure white `#FFFFFF` — highlights, negative space, divine light
- **Accents**: Tonal range built entirely through hatching density:
  - Sparse hatching — skin surfaces, distant elements, soft light
  - Medium cross-hatching — fabric, stone, overcast atmosphere
  - Dense cross-hatching — deep shadow, horror, emotional intensity
- **Highlights**: Sharp white streaks against dense black for metallic reflections and moonlight
- **Rule**: Strictly monochrome — no screentones; all shading via hand-drawn hatching strokes that follow form

## Panel Conventions

- **Reading direction**: RIGHT-TO-LEFT — traditional manga flow, right to left, top to bottom
- **Borders**: Thin black borders, 1-2px weight, clean and precise
- **Gutters**: Narrow white gutters, 4-8px width between panels
- **Border shapes**: Rectangular with occasional borderless bleeds for vast landscapes and horror reveals
- **Splash panels**: Full-page and double-page spreads for monster reveals, battle panoramas, and Eclipse-level events — earned through pacing restraint
- **Panel count**: 4-7 per page in varied layout; small dense panels build tension, then release into massive spreads

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` -- standard narrative panels
- **Tall vertical** (scale): `clip-path: inset(0)` on full-height cell -- towering architecture, massive creatures
- **Diagonal slash** (combat): `clip-path: polygon(5% 0, 100% 0, 95% 100%, 0 100%)` -- sword strikes and violent action
- **Full bleed** (revelation): No clip-path, no border -- overwhelming horror and awe moments
- **Irregular jagged** (chaos): `clip-path: polygon(2% 3%, 98% 0, 100% 97%, 0 100%)` -- battlefield chaos and psychological fracture

## Text Treatment

- **Speech bubbles**: Simple rounded white bubbles with thin borders; angular jagged bubbles for demonic or anguished speech
- **Font style**: Clean sans-serif, mixed case for normal dialogue; bold uppercase for battle cries
- **Sound effects**: Minimal — large bold impact effects for sword clashes and explosions only, integrated into linework
- **Caption boxes**: Simple rectangular boxes with thin borders for narration and internal monologue
- **Whisper text**: Smaller font in bubbles with dashed outlines for quiet or sinister dialogue

## Character Rendering

- **Proportions**: Muscular but anatomically grounded; characters have realistic skeletal structure and physical weight
- **Linework**: Form-following hatching strokes that trace three-dimensional surface contours like sculpture
- **Armor and weapons**: Historically accurate medieval armor with realistic reflections, dents, and battle damage
- **Faces**: Hyper-detailed facial anatomy conveying raw emotion — rage, grief, madness — through muscle tension
- **Physicality**: Characters have mass and weight; swings feel heavy, exhaustion shows in posture
- **Creatures**: Grotesque biological detail with exposed musculature, fused anatomy, and disturbing specificity

## AmpliVerse Branding

- **Publisher name**: Vertical bold condensed font spelling "AmpliVerse" along the right spine edge
- **Avatar**: Small AmpliVerse avatar placed in the bottom-right corner of the cover
- **Color treatment**: White on black to maintain the monochrome dark fantasy aesthetic

## Image Requirements

```yaml
image_requirements:
  style_category: berserk-darkfantasy
  detail_level: very-high
  text_avoidance: critical
```
