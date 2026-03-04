# X-Men Style Pack

Visual style guide for X-Men comic strip creation in the iconic 90s Jim Lee tradition.

## Image Prompt Template

Base template for generating X-Men-style panel images:

```
X-Men comic book illustration, Jim Lee 1990s style, hyper-detailed crosshatched ink work, bold saturated colors, {scene_description}. Muscular heroic proportions with exaggerated dynamism. Dense crosshatching for texture and shadow. Dramatic under-lighting and cinematic widescreen composition. Characters breaking panel borders with explosive mutant energy effects. No text in image.
```

## Color Palette

Bold saturated primaries with signature mutant energy colors and dramatic contrast.

- **Primary**:
  - Team Gold `#FFD700` — uniforms, insignias, Wolverine accents
  - Team Blue `#1A3A8A` — uniforms, backgrounds, heroic tones
- **Secondary**:
  - Optic Red `#FF1A1A` — Cyclops blasts, danger, intensity
  - Kinetic Magenta `#CC0066` — Gambit's charges, psychic energy, Psylocke
  - Storm White-Blue `#ADD8E6` — lightning, ice, atmospheric effects
- **Highlights**: Metallic Silver `#A8A8A8` — Wolverine's claws, Colossus skin, chrome reflections
- **Backgrounds**: Deep shadow `#0D0D1A` — night scenes, Danger Room, dramatic contrast behind bright costumes

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — standard Western comic flow, left to right, top to bottom
- **Borders**: Thick bold black outlines, 2-3px weight; characters and energy effects frequently break through borders
- **Gutters**: Medium white gutters, 8-12px width; overlapping elements bridge gutters during action
- **Border shapes**: Cinematic widescreen rectangles for team shots; angled and overlapping panels for combat sequences
- **Splash panels**: Double-page spreads for full-team compositions and climactic mutant power clashes; used liberally
- **Panel count**: 4-6 per page; mix of wide panoramic panels and tight close-ups for cinematic pacing

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Widescreen** (default): `clip-path: inset(0)` with 2.5:1 aspect ratio -- cinematic team shots
- **Diagonal action** (combat): `clip-path: polygon(0 0, 100% 0, 100% 80%, 0 100%)` -- dynamic fight sequences
- **Overlapping burst** (power): `clip-path: inset(-5%)` with `z-index` layering -- energy blasts breaking borders
- **Circular spotlight** (focus): `clip-path: circle(45% at 50% 50%)` -- character close-ups and power activation
- **V-formation** (team): `clip-path: polygon(50% 0%, 100% 100%, 0% 100%)` -- dramatic team charge compositions

## Text Treatment

- **Speech bubbles**: Bold rounded white bubbles with thick black borders; jagged burst bubbles for shouting and power activation
- **Font style**: Heavy bold uppercase comic lettering; thicker weight than standard to match the dense, detailed art
- **Sound effects**: Massive colorful 3D effect text — "SNIKT", "BAMF", "ZAP" — rendered in each character's signature power color
- **Caption boxes**: Yellow rectangular narration boxes with thin black borders for mission briefings and internal monologue

## Character Rendering

- **Proportions**: Exaggerated musculature with broad shoulders, narrow waists, and powerful builds conveying superhuman physicality
- **Costume detail**: Pouches, straps, shoulder pads, belt accessories, and tactical gear; every seam and panel rendered with crosshatching
- **Distinctive silhouettes**: Each character instantly recognizable — Wolverine's mask points, Storm's cape, Gambit's trenchcoat, Rogue's streak
- **Facial intensity**: Gritted teeth, squinted eyes, dramatic under-lighting across faces; expressions default to fierce determination
- **Hair dynamics**: Long flowing hair always in motion even in still poses — Storm, Rogue, Psylocke, Jean Grey
- **Power signatures**: Each mutant has a unique visual effect — optic beams, lightning arcs, kinetic glow, psychic waves — always in their signature color

## AmpliVerse Branding

- **Corner box**: Top-left corner box in classic Marvel style containing team insignia or character headshot
- **Avatar**: AmpliVerse avatar centered above the title on the cover
- **Color treatment**: Gold text on blue background matching the iconic X-Men team uniform palette

## Image Requirements

```yaml
image_requirements:
  style_category: x-men
  detail_level: high
  text_avoidance: good
```
