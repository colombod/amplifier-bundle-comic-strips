# Dylan Dog Noir Style Pack

Visual style guide for Dylan Dog-inspired Italian horror noir comic strip creation.

## Image Prompt Template

Base template for generating Dylan Dog noir-style panel images:

```
Black and white Italian horror comic illustration, classical European ink draftsmanship, heavy noir shadows with crosshatching for tonal depth, {scene_description}. Elegant melancholic figures with subtle facial expressions. London fog and Victorian architecture with rain-slicked streets. Gothic atmosphere with surreal horror elements in the style of Sergio Bonelli comics and Angelo Stano. No text in image.
```

## Color Palette

Strictly black and white in the Bonelli tradition. No color at any stage.

- **Primary black**: Pure black `#000000` — linework, deep shadows, dramatic solid fills
- **Primary white**: Pure white `#FFFFFF` — highlights, fog, negative space, clean skin
- **Accents**: Ink density hatching at four tonal levels:
  - Light parallel lines — distant fog, soft ambient light
  - Medium crosshatch — fabric texture, mid-tone surfaces, stone walls
  - Dense crosshatch — deep shadow, noir interiors, night scenes
  - Solid black fill — dramatic silhouettes, horror reveals, maximum contrast
- **Highlights**: Stark white against solid black for moonlight, streetlamps, and candlelight
- **Rule**: Strictly monochrome — all tonal variation achieved through ink density, never grayscale wash

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — standard Western comic flow, left to right, top to bottom
- **Borders**: Clean precise borders, 1-2px weight, contained and rigid in the Bonelli tradition
- **Gutters**: Uniform white gutters, 6-8px width, maintaining structured page rhythm
- **Border shapes**: Strictly rectangular contained panels; elements rarely break borders — restraint creates impact when rules are broken
- **Splash panels**: Used sparingly for maximum dramatic weight — horror reveals and climactic confrontations only
- **Panel count**: 4-6 per page in a regular 3-strip horizontal grid; strips subdivide vertically for up to 6 panels

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` — standard Bonelli grid panels, used for the vast majority
- **Wide strip** (establishing): `clip-path: inset(20% 0)` — London skyline, foggy street establishing shots
- **Tall narrow** (tension): `clip-path: inset(0 25%)` — stairwells, doorways, claustrophobic horror
- **Full bleed** (horror reveal): No clip-path, `border: none` — maximum impact for rare splash moments
- **Slight irregularity** (unease): `clip-path: polygon(1% 0, 100% 1%, 99% 100%, 0 99%)` — subtle wrongness for surreal sequences

## Text Treatment

- **Speech bubbles**: Clean rounded white bubbles with thin precise black borders; neat tails pointing to speakers
- **Font style**: Clean serif-influenced lettering, mixed case for dialogue, reflecting European comic tradition
- **Sound effects**: Restrained integrated SFX — "CRASH", "AAAARGH", "KNOCK KNOCK" — rendered in bold black, never overwhelming the artwork
- **Caption boxes**: Simple thin-bordered rectangular boxes for narration; sardonic noir voice-over tone

## Character Rendering

- **Proportions**: Realistic elegant builds — tall and slim with sharp features, grounded in classical Italian draftsmanship
- **Facial acting**: Nuanced subtle expressions conveying fear, determination, sardonic humor, and melancholy — no exaggerated manga-style emotion
- **Wardrobe**: Simple iconic costumes — dark jacket and distinctive shirt as instantly recognizable signature elements
- **Horror figures**: Varied creature rendering — vampires, werewolves, Lovecraftian entities — each in sub-genre-appropriate style
- **Body transformation**: Progressive anatomical stages for werewolf turns, undead decay, and supernatural corruption
- **Architectural context**: Characters grounded in detailed London settings — Victorian row houses, pubs, fog-shrouded bridges

## AmpliVerse Branding

- **Publisher name**: Clean serif "AmpliVerse" centered at the top cover edge in the Bonelli editorial tradition
- **Avatar**: Small AmpliVerse avatar in the bottom-left corner, rendered in black ink to match the monochrome aesthetic
- **Color treatment**: Black on white to maintain the strict monochrome Bonelli tradition

## Image Requirements

```yaml
image_requirements:
  style_category: dylan-dog-noir
  detail_level: high
  text_avoidance: critical
```
