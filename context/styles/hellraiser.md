# Hellraiser Style Pack

Visual style guide for dark Gothic body horror comic strip creation inspired by Clive Barker's Hellraiser.

## Image Prompt Template

Base template for generating Hellraiser-style panel images:

```
Dark Gothic horror comic illustration, painted style with rich deep shadows, {scene_description}. Anatomically precise body horror with surgical detail — hooks, chains, and modified flesh rendered with clinical accuracy. Cenobite characters in black leather with serene composed expressions despite grotesque modifications. Deep blue-black shadows with selective amber and blood-red highlights. Impossible Labyrinth architecture blending Gothic arches with industrial steel. In the style of Clive Barker and classic Hellraiser comics. No text in image.
```

## Color Palette

Dark, murky palette dominated by deep shadows with selective warm accents for blood and firelight.

- **Primary**: Core shadow and horror tones:
  - Void black `#0D0D14` — deep shadows, Labyrinth corridors, Cenobite leather
  - Midnight blue `#1A1A2E` — cold backgrounds, Hell dimension, oppressive atmosphere
- **Secondary**: Warm horror accents:
  - Blood crimson `#8B1A1A` — blood, exposed flesh, ritual markings
  - Amber glow `#C4852A` — candlelight, Lament Configuration highlights, firelight
- **Highlights**: Pale flesh `#D4B5A0` — human skin against dark surroundings; golden gleam `#C8A84E` — the Lament Configuration's ornate surface
- **Backgrounds**: Deep blue-black gradients and murky painted washes — `#0F0F1A` to `#2A2A3E` — dimly lit with selective pools of light revealing horror

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — standard Western comic flow, left to right, top to bottom
- **Borders**: Heavy dark borders, 2-3px weight, sometimes fading into deep shadow at edges
- **Gutters**: Narrow black gutters, 4-6px width, dark-filled to maintain oppressive atmosphere between panels
- **Border shapes**: Rectangular panels with occasional irregular edges for Labyrinth sequences; borders dissolve during transformation scenes
- **Splash panels**: Full-page reveals for Cenobite appearances, Labyrinth vistas, and supreme moments of body horror
- **Panel count**: 4-6 per page; slow deliberate pacing with lingering panels for dread — small panels build tension, large panels deliver horror

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` — standard narrative panels
- **Diamond** (Leviathan): `clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)` — Hell dimension and Leviathan imagery
- **Irregular decay** (transformation): `clip-path: polygon(3% 2%, 98% 0%, 100% 96%, 0% 100%)` — reality warping during puzzle-solving and torment
- **Narrow tall** (dread): `clip-path: inset(0 25%)` — claustrophobic corridor shots and vertical reveals
- **Full bleed** (climax): No clip-path, `border: none` — Cenobite full reveals and maximum horror moments

## Text Treatment

- **Speech bubbles**: Dark-edged bubbles with pale interiors for humans; inverted dark bubbles with pale text for Cenobites
- **Font style**: Elegant serif lettering for narration; cold clean uppercase for Cenobite dialogue
- **Sound effects**: Visceral metallic sound effects ("CLANK", "TEAR", "RRRIP") rendered in dark steel-gray tones with sharp edges
- **Caption boxes**: Dark blue-black caption boxes with thin pale borders for literary narration and Barker-style prose
- **Whisper text**: Small, cramped italicized text for the Lament Configuration's seductive whispers

## Character Rendering

- **Cenobites**: Surgically precise flesh modifications — nails, pins, hooks, incisions rendered with anatomical accuracy; black leather and steel hardware
- **Expression**: Cenobites display serene, composed, almost bored calm — horror comes from their indifference, not rage
- **Humans**: Realistic proportions with warm flesh tones that contrast starkly against cold dark environments
- **Transformation**: Progressive body horror sequences — hooks entering flesh, skin separating, underlying anatomy revealed layer by layer
- **The Lament Configuration**: Ornate golden puzzle box rendered with meticulous mechanical detail, fine engravings, and supernatural golden highlights
- **Silhouettes**: Cenobites must read clearly in silhouette — Pinhead's nail grid, unique modifications for each figure

## AmpliVerse Branding

- **Publisher name**: Thin elegant serif "AmpliVerse" along the top edge of the cover in pale gold
- **Avatar**: AmpliVerse avatar placed in the top-left corner, rendered in dark steel with faint golden border
- **Color treatment**: Pale gold text on midnight blue-black background matching the Hellraiser palette

## Image Requirements

```yaml
image_requirements:
  style_category: hellraiser-horror
  detail_level: high
  text_avoidance: good
```
