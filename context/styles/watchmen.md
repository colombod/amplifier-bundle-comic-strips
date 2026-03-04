# Watchmen Style Pack

Visual style guide for Watchmen-inspired graphic novel strip creation.

## Image Prompt Template

Base template for generating Watchmen-style panel images:

```
Graphic novel illustration, muted secondary color palette of purples greens and oranges, flat European-style coloring, {scene_description}. Rigid formal composition with uniform thin linework and clinical precision. Grounded realistic proportions with no idealized anatomy. Film noir lighting with deep shadows. Symbolic visual density in the style of Dave Gibbons and Watchmen. No text in image.
```

## Color Palette

Muted secondary colors with flat fills and deliberate emotional shifts.

- **Primary**: Moody secondary tones for atmosphere and symbolism:
  - Deep purple `#5B2C6F` — night scenes, moral ambiguity, psychological weight
  - Olive green `#6B8E23` — urban grime, institutional decay, military tones
  - Burnt orange `#CC7722` — tension, warmth, nostalgic flashbacks
- **Secondary**: Symbolic and narrative accent colors:
  - Blood red `#8B0000` — the smiley-face badge, violence, consequence
  - Cold cyan `#4A90D9` — Dr. Manhattan's glow, detachment, cosmic scale
  - Sickly yellow `#D4AA00` — Ozymandias, corruption, false utopia
- **Highlights**: Sparse white specular highlights for metallic and wet surfaces
- **Backgrounds**: Flat color fills with no gradients — urban grays `#4F4F4F`, midnight blues `#1B2631`

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — standard Western comic flow, left to right, top to bottom
- **Borders**: Thin uniform black borders, 1px weight, precise and clinical
- **Gutters**: Consistent narrow white gutters, 4-6px width between all panels
- **Border shapes**: Strictly rectangular — the rigid grid is the signature; deviations are rare and narratively earned
- **Splash panels**: Extremely rare — reserved only for catastrophic narrative events to maximize impact
- **Panel count**: 9 per page in a strict 3×3 grid; variations (merging cells) only at key dramatic beats

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` -- strict 3×3 grid cell, the signature layout
- **Wide horizontal** (revelation): `clip-path: inset(0)` on a double-width cell -- spanning two grid columns for slow reveals
- **Full-width strip** (transition): `clip-path: inset(0)` on a triple-width cell -- spanning full row for scene transitions
- **Tall vertical** (isolation): `clip-path: inset(0)` on a double-height cell -- character isolation and introspection
- **Full-page** (catastrophe): No clip-path, full bleed -- reserved for singular devastating moments

## Text Treatment

- **Speech bubbles**: Simple rounded white bubbles with thin black borders; no stylistic embellishment
- **Font style**: Clean serif lettering, mixed case, understated and literary in tone
- **Sound effects**: None — no onomatopoeia rendered as stylized text; all sound is implied through art
- **Caption boxes**: Rectangular boxes with flat color backgrounds matching the character's motif for narration
- **Thought bubbles**: None — inner monologue delivered through journal-entry caption boxes only

## Character Rendering

- **Proportions**: Realistic, non-idealized human proportions — no exaggerated muscles or impossible poses
- **Linework**: Uniform line weight with hard stiff pen; controlled, clinical, deliberately non-expressive
- **Faces**: Detailed but restrained; emotion conveyed through subtle anatomical shifts, not exaggeration
- **Costumes**: Functional and unglamorous — these are real people in costumes, not icons
- **Physicality**: Characters show age, weight, and physical limitation; bodies are believably flawed
- **Silhouettes**: Strong recognizable silhouettes through costume design, not heroic posing

## AmpliVerse Branding

- **Publisher name**: Small horizontal text "AmpliVerse" along bottom edge, matching the understated formalism
- **Avatar**: AmpliVerse avatar placed in bottom-left corner of cover, integrated into the grid structure
- **Color treatment**: Muted purple text on dark background to maintain the sober Watchmen aesthetic

## Image Requirements

```yaml
image_requirements:
  style_category: watchmen-noir
  detail_level: high
  text_avoidance: critical
```
