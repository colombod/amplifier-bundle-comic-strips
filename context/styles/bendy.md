# Bendy Style Pack

Visual style guide for 1930s cartoon horror comic strip creation inspired by Bendy and the Ink Machine.

## Image Prompt Template

Base template for generating Bendy-style panel images:

```
Sepia-toned 1930s cartoon horror illustration, corrupted rubber-hose animation style, {scene_description}. Characters with pie-cut eyes, white gloves, and simple limbs dripping with black ink. Abandoned animation studio environments with wooden floors, ink-flooded corridors, and flickering isolated light sources. Heavy ink splatter and dripping textures. Monochromatic sepia and amber palette with deep black ink as the darkest element. In the style of Bendy and the Ink Machine meets vintage Fleischer cartoons. No text in image.
```

## Color Palette

Restricted monochromatic sepia palette evoking yellowed film stock and ink-drenched decay.

- **Primary**: Core ink and shadow tones:
  - Ink black `#0A0A0A` — dripping ink, corrupted figures, deepest shadows
  - Dark sepia `#3B2F1E` — heavy shadows, aged wood, dark corridors
- **Secondary**: Warm decay tones for environment:
  - Medium sepia `#8B7355` — wooden walls, floors, studio furniture
  - Parchment `#D4C5A0` — faded posters, yellowed paper, light surfaces
- **Highlights**: Warm amber `#C4943A` — isolated light bulbs, desk lamps, the only warmth in the oppressive gloom
- **Backgrounds**: Deep murky brown-black gradients `#1E150D` to `#5C4A32` — claustrophobic abandoned interiors with no bright colors

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — standard Western comic flow, left to right, top to bottom
- **Borders**: Rough uneven black borders, 2-3px weight, with ink-drip effects bleeding past edges
- **Gutters**: Narrow dark gutters, 4-6px width, filled with dark sepia tone instead of white — no clean space
- **Border shapes**: Irregular rectangular panels with deliberately imperfect edges; borders warp and dissolve in horror moments
- **Splash panels**: Full-page reveals for Ink Demon appearances and major environmental horror set pieces
- **Panel count**: 4-6 per page in a tight claustrophobic grid; smaller panels for tension building, larger for jump scares

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rough rectangle** (default): `clip-path: polygon(1% 2%, 99% 0%, 100% 97%, 0% 100%)` — slightly uneven standard panels
- **Melting** (corruption): `clip-path: polygon(0 0, 100% 0, 100% 80%, 85% 95%, 60% 85%, 40% 100%, 15% 90%, 0 100%)` — ink dissolving the panel border
- **Vignette** (spotlight): `clip-path: ellipse(45% 42% at 50% 50%)` — isolated light source framing
- **Jagged** (terror): `clip-path: polygon(5% 0, 95% 3%, 100% 45%, 97% 100%, 3% 98%, 0 50%)` — shattered reality during horror beats
- **Full bleed** (ink flood): No clip-path, `border: none`, dark ink wash background — total ink corruption moments

## Text Treatment

- **Speech bubbles**: Off-white aged parchment bubbles with rough hand-drawn borders; slight yellowed tint
- **Font style**: Uneven hand-lettered style, mixed case, mimicking 1930s title cards with slight wobble
- **Sound effects**: Dripping, inky sound effects ("SPLORCH", "DRIIIP", "CRACK") rendered as melting black ink forms
- **Caption boxes**: Aged parchment-colored boxes with ragged edges for journal entries and audio log transcriptions
- **Scrawled text**: Wall-writing style text ("HE WILL SET US FREE") rendered as rough ink scrawls for environmental storytelling

## Character Rendering

- **Cartoon form**: Pie-cut eyes, white gloves, rubber-hose limbs, solid black bodies — faithful 1930s mascot design
- **Corrupted form**: The same designs made horrifically three-dimensional — dripping, melting, distorted grins frozen in place
- **Ink texture**: All characters drip and trail black ink; ink is alive, pooling, flowing, and corrupting everything it touches
- **Silhouette**: Both cartoon and horror forms must be instantly recognizable from silhouette alone
- **Expression**: Cartoon forms have fixed cheerful grins; horror forms have those same grins made wrong and frozen
- **Searchers**: Featureless humanoid ink figures emerging from puddles — just enough shape to be disturbing

## AmpliVerse Branding

- **Publisher name**: Aged, slightly warped "AmpliVerse" text along the bottom edge, styled as a worn studio credit
- **Avatar**: AmpliVerse avatar placed in the bottom-right corner, rendered in sepia with faint ink splatter
- **Color treatment**: Dark sepia on parchment to maintain the corrupted vintage aesthetic

## Image Requirements

```yaml
image_requirements:
  style_category: bendy-horror
  detail_level: high
  text_avoidance: critical
```
