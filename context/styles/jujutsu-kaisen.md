# Jujutsu Kaisen Style Pack

Visual style guide for Jujutsu Kaisen-inspired dark sorcery manga comic strip creation.

## Image Prompt Template

Base template for generating Jujutsu Kaisen-style panel images:

```
Jujutsu Kaisen manga illustration, aggressive cross-hatching, chaotic confident linework, high contrast black and white, {scene_description}. Heavy ink shadows with sharp light-dark transitions. Angular character features with detailed boxy hands. Dark swirling cursed energy effects. Raw sketch-like intensity in the style of Gege Akutami. No text in image.
```

## Color Palette

Dark, oppressive tones dominated by deep blues and purples with selective vivid accents.

- **Primary**: Core palette for characters and cursed energy:
  - Deep indigo `#1B0A3C` — cursed energy, dark auras, night scenes
  - Midnight blue `#0D1B2A` — backgrounds, shadows, Domain Expansions
  - Bone white `#F0EDE5` — highlights, reversed cursed technique glow
- **Secondary**: Accent and character-specific tones:
  - Crimson `#8B0000` — Sukuna's power, blood, malevolent energy
  - Electric blue `#00B4D8` — Gojo's Infinity, Six Eyes, barrier techniques
- **Highlights**: Sharp white specular hits on black surfaces; pale blue glow for cursed technique activation
- **Backgrounds**: Dense cross-hatched darkness; oppressive solid black fills for horror tension

## Panel Conventions

- **Reading direction**: RIGHT-TO-LEFT — panels arranged and read from right to left, top to bottom, following traditional manga flow
- **Borders**: Thin to medium black borders, 1-2px weight; borders break and shatter during intense action
- **Gutters**: Narrow white gutters, 4-6px width; gutters disappear when panels collide during fights
- **Border shapes**: Rectangular for dialogue; panel-breaking compositions where characters and effects burst through borders during cursed technique clashes
- **Splash panels**: Full-page splashes for Domain Expansions, Black Flash moments, and transformation reveals
- **Panel count**: 5-8 per page in irregular layout; dense rapid panels for fight choreography, explosive splashes for key impacts

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` -- standard dialogue and scene-setting panels
- **Shattered angle** (combat): `clip-path: polygon(0 0, 100% 3%, 97% 100%, 2% 97%)` -- aggressive fight sequences
- **Diagonal slash** (Black Flash): `clip-path: polygon(0 0, 100% 0, 100% 78%, 0 100%)` -- critical strike moments
- **Broken border** (Domain Expansion): No clip-path, use `border: none` with `box-shadow: 0 0 8px #1B0A3C` -- reality-breaking moments
- **Irregular tension** (horror): `clip-path: polygon(4% 2%, 98% 0, 96% 100%, 0 96%)` -- cursed spirit encounters and dread

## Text Treatment

- **Speech bubbles**: Clean round bubbles for normal dialogue; rough jagged bubbles for cursed spirits and Sukuna; inverted black bubbles with white text for Domain announcements
- **Font style**: Bold condensed sans-serif, ALL CAPS for all dialogue; heavier weight for battle declarations
- **Sound effects**: Large aggressive onomatopoeia rendered with cross-hatched texture, integrated into the dense ink artwork
- **Caption boxes**: Dark-bordered rectangular caption boxes for narration; thinner boxes for cursed technique explanations

## Character Rendering

- **Faces**: Angular male jawlines with sharp chins and defined cheekbones; rounder female faces retaining sharp features; distinctive open-mouth technique with simple teeth and solid black fill
- **Hands**: Boxy angular knuckles, defined finger joints, visible skin tension lines — hands are prominent in every composition
- **Hair**: Simple blocky silhouette shapes filled with dense fine interior lines for strand texture
- **Action**: Extreme foreshortening on strikes; characters and effects burst through panel borders; motion blur and speed lines for supernatural speed
- **Cursed energy**: Dark swirling ink effects rendered with heavy cross-hatching; ethereal lighter rendering for reverse cursed technique healing
- **Shading**: Aggressive cross-hatching throughout; solid black fills for clothing and hair shadows; sharp hard-edged transitions between light and dark

## AmpliVerse Branding

- **Publisher name**: Bold condensed font spelling "AmpliVerse" along the right spine, partially obscured by cross-hatched shadow
- **Avatar**: Small AmpliVerse avatar placed in the bottom-right corner with a dark circular border
- **Color treatment**: Bone white on deep indigo background to match the dark supernatural aesthetic

## Image Requirements

```yaml
image_requirements:
  style_category: jujutsu-kaisen
  detail_level: high
  text_avoidance: critical
```
