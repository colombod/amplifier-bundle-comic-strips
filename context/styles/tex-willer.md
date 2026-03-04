# Tex Willer Style Pack

Visual style guide for Italian Western comic strip creation in the Bonelli tradition.

## Image Prompt Template

Base template for generating Tex Willer-style panel images:

```
Black and white Italian Western comic illustration, bold ink linework with crosshatching, {scene_description}. Sweeping panoramic landscapes of the American Southwest with mesas, canyons, and dusty frontier towns. Rugged stoic characters with strong jawlines and weathered faces. Heavy blacks for dramatic shadows, fine crosshatching for texture on leather, wood, and rock. In the style of Aurelio Galleppini and classic Bonelli comics. No text in image.
```

## Color Palette

Strictly monochrome black and white in the Bonelli Western tradition.

- **Primary black**: Pure black `#000000` — linework, deep shadows, night scenes, solid fills
- **Primary white**: Pure white `#FFFFFF` — open skies, highlights, negative space
- **Accents**: Crosshatched gray tones at varying densities:
  - Light hatching — distant mesas, hazy desert atmosphere, dust clouds
  - Medium hatching — leather textures, wooden buildings, fabric weave
  - Heavy hatching — cave interiors, shadowy saloons, dramatic confrontations
- **Highlights**: White space carved out of heavy blacks for muzzle flash and sunlit edges
- **Rule**: Strictly monochrome — texture achieved through hatching and stippling, not screentones

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — standard Western comic flow, left to right, top to bottom
- **Borders**: Thin clean black borders, 1-2px weight, precise and uniform
- **Gutters**: Narrow white gutters, 4-8px width between panels
- **Border shapes**: Predominantly rectangular with wider panoramic panels for landscape shots; standard grid for dialogue and action
- **Splash panels**: Wide panoramic panels spanning the full page width for sweeping frontier vistas and dramatic ride-ins
- **Panel count**: 4-6 per page in a structured 3-strip grid; wider panels for landscapes, taller panels for gunfight close-ups

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` — standard dialogue and action panels
- **Wide panoramic** (landscape): `clip-path: inset(25% 0)` — sweeping desert vistas and horizon shots
- **Tall narrow** (standoff): `clip-path: inset(0 30%)` — vertical close-ups for quick-draw sequences
- **Slight angle** (tension): `clip-path: polygon(2% 0, 100% 0, 98% 100%, 0 100%)` — bar-room brawls and chase tension
- **Full bleed** (climax): No clip-path, `border: none` — climactic shootouts and dramatic reveals

## Text Treatment

- **Speech bubbles**: Smooth rounded white bubbles with thin black borders; tail points toward speaker
- **Font style**: Clean serif lettering, mixed case for dialogue, maintaining a literary quality
- **Sound effects**: Bold black sound effects for gunshots ("BANG", "BLAM") and impacts, integrated into action panels
- **Caption boxes**: Rectangular caption boxes with thin borders for narration and scene-setting prose
- **Thought bubbles**: Rare — character emotion conveyed through visual acting rather than internal monologue

## Character Rendering

- **Build**: Tall, broad-shouldered frontier physiques; rugged and weathered, not idealized superheroes
- **Faces**: Strong jawlines, narrowed eyes, stoic expressions; emotion conveyed through subtle shifts — clenched jaw, furrowed brow
- **Costumes**: Cowboy hats, bandanas, dusters, gun belts with twin revolvers, riding boots — simple and iconic
- **Horses**: Anatomically accurate horses in full gallop with flowing manes, extended legs, and visible physical strain
- **Action**: Clear multi-beat gunfight sequences — reach, draw, aim, fire — with dust puffs, muzzle flash, and splintering wood
- **Diversity**: Supporting cast with distinct silhouettes; Native American characters rendered with cultural accuracy and dignity

## AmpliVerse Branding

- **Publisher name**: Small bold condensed "AmpliVerse" along the bottom spine edge of the cover
- **Avatar**: AmpliVerse avatar placed in the bottom-right corner of the cover
- **Color treatment**: Black on white to maintain the monochrome Bonelli aesthetic

## Image Requirements

```yaml
image_requirements:
  style_category: tex-willer-western
  detail_level: high
  text_avoidance: critical
```
