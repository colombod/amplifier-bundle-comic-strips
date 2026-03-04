# One Piece Style Pack

Visual style guide for One Piece-inspired pirate adventure manga comic strip creation.

## Image Prompt Template

Base template for generating One Piece-style panel images:

```
One Piece manga illustration, bold thick outlines, wildly exaggerated character proportions, vibrant saturated colors, {scene_description}. Extreme facial expressions with manic grins and bug-eyed reactions. Geometric character foundations with diverse bizarre body types. Dense environmental detail with fantastical architecture. In the style of Eiichiro Oda. No text in image.
```

## Color Palette

Vibrant, saturated adventure palette with bold primaries and fantastical variety.

- **Primary**: Core palette for characters and high-seas action:
  - Straw Hat red `#C8102E` — Luffy's vest, action accents, passion
  - Ocean blue `#006994` — sea, sky, Marine uniforms, adventure
  - Sunny yellow `#FFD700` — straw hat, treasure, sunny optimism
- **Secondary**: World-building and grounding tones:
  - Wood brown `#8B5E3C` — ships, docks, barrels, island structures
  - Lush green `#2E8B57` — tropical islands, foliage, Zoro accents
- **Highlights**: Bright white impact bursts, golden Haki lightning `#FFAA00`, glossy black Armament Haki `#1A1A1A`
- **Backgrounds**: Vivid gradient skies over open ocean; dense colorful cityscapes for island arcs; each island has its own distinct palette

## Panel Conventions

- **Reading direction**: RIGHT-TO-LEFT — panels arranged and read from right to left, top to bottom, following traditional manga flow
- **Borders**: Thick bold black borders, 2-3px weight, giving pages a round bouncy cartoon energy
- **Gutters**: Medium white gutters, 6-10px width between panels
- **Border shapes**: Mostly rectangular; wide cinematic panels for sea vistas and battle panoramas; tall narrow panels for towering characters and vertical action
- **Splash panels**: Full-page and double-page splashes for crew reveals, island arrivals, and climactic punches
- **Panel count**: 5-9 per page in dense irregular layouts; rapid small panels for comedy beats, massive splashes for key impacts

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` -- standard dialogue and scene-setting panels
- **Wide cinematic** (adventure): Full-width panel, no clip-path -- ocean panoramas and crew group shots
- **Diagonal impact** (Gum-Gum): `clip-path: polygon(0 0, 100% 0, 100% 80%, 0 100%)` -- rubber-powered strike moments
- **Rounded burst** (comedy): `clip-path: ellipse(48% 46% at 50% 50%)` -- exaggerated reaction shots and gag panels
- **Tall tower** (scale): `clip-path: inset(0)` with 1:3 aspect ratio -- emphasizing massive characters and towering structures

## Text Treatment

- **Speech bubbles**: Large round white bubbles for normal dialogue; enormous jagged bubbles for battle cries and crew declarations; wobbly bubbles for comedic panic
- **Font style**: Bold rounded sans-serif, ALL CAPS for all dialogue; extra-large lettering for dramatic shouts
- **Sound effects**: Massive bold onomatopoeia filling entire panels — "GOMU GOMU NO!", impact SFX rendered as explosive graphic elements with debris
- **Caption boxes**: Clean rectangular caption boxes with thin borders for narration and world-building exposition

## Character Rendering

- **Proportions**: Wildly exaggerated and diverse — impossibly thin to massively muscular, tiny to enormous; each character built on distinct geometric shapes
- **Expressions**: Extreme emotional range — bug-eyed shock, waterfall tears, manic Oda grins, jaw-dropping surprise, and rage veins; comedy and drama in the same scene
- **Silhouettes**: Every character instantly recognizable by silhouette alone — hair, body shape, and outfit are maximally differentiated
- **Action**: Rubber-stretching elasticity, Haki effects as glossy black coating and dark lightning, sharp clean slash trails for swordsmanship
- **Scale variety**: Characters range from Chopper-sized to Whitebeard-sized; extreme scale contrast within single panels
- **World detail**: Dense background characters, architectural detail, signage, and environmental storytelling in every scene

## AmpliVerse Branding

- **Publisher name**: Bold rounded font spelling "AmpliVerse" across the top banner, styled like a pirate crew flag
- **Avatar**: AmpliVerse avatar placed in the top-left corner wearing a straw hat border treatment
- **Color treatment**: White text on ocean blue background with sunny yellow accent stroke

## Image Requirements

```yaml
image_requirements:
  style_category: one-piece-manga
  detail_level: high
  text_avoidance: critical
```
