# Tatsunoko Classic Style Pack

Visual style guide for Tatsunoko Production-inspired retro anime comic strip creation.

## Image Prompt Template

Base template for generating Tatsunoko classic-style panel images:

```
Retro 1970s Japanese anime illustration, sharp precise linework, bold saturated cel-shaded colors, {scene_description}. Heroic athletic figures with angular features and elaborate helmet designs. Sleek aerodynamic vehicles and mecha. Color-coded team uniforms with warm organic cel animation quality in the style of Gatchaman and Speed Racer. No text in image.
```

## Color Palette

Bold saturated primary colors with warm cel-animation quality and team color-coding.

- **Primary**: Team-coded hero colors:
  - Gatchaman White `#F0F0F0` — team leader, purity, command
  - Action Red `#D72638` — second-in-command, passion, combat
  - Sky Blue `#2E86DE` — flight, speed, open skies
- **Secondary**: Environmental and tonal depth:
  - Hero Gold `#F5A623` — insignias, accents, warm highlights
  - Deep Navy `#1B2A4A` — night skies, dramatic shadow, villain bases
- **Highlights**: Warm white specular glints on helmets, visors, and vehicle surfaces
- **Backgrounds**: Painterly atmospheric gradients — sunlit cityscapes, mountain vistas, space nebulae

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — Western comic flow adapted for international audience, left to right, top to bottom
- **Borders**: Clean black borders, 2px weight, precise and sharp
- **Gutters**: Medium white gutters, 8-10px width between panels
- **Border shapes**: Primarily rectangular with diagonal cuts for high-speed chase sequences and aerial combat
- **Splash panels**: Wide cinematic panels for vehicle reveals, team group poses, and combination sequences
- **Panel count**: 4-6 per page in clean grid layout; wide panels for vehicle action, tight panels for helmet close-ups

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` — standard dialogue and scene panels
- **Diagonal speed** (chase): `clip-path: polygon(0 0, 100% 0, 100% 85%, 0 100%)` — high-speed pursuit sequences
- **Wide cinematic** (reveal): `clip-path: inset(15% 0)` — panoramic vehicle and team reveals
- **Diamond** (emblem): `clip-path: polygon(50% 0, 100% 50%, 50% 100%, 0 50%)` — hero spotlight and transformation focus
- **Angled bracket** (combat): `clip-path: polygon(5% 0, 100% 0, 95% 100%, 0 100%)` — dynamic fight choreography

## Text Treatment

- **Speech bubbles**: Smooth rounded white bubbles with clean black borders; tail points toward speaker
- **Font style**: Bold rounded sans-serif, ALL CAPS for dialogue, conveying retro anime energy
- **Sound effects**: Colorful bold SFX with motion streaks — "WHOOOM", "ZAAAP", "CRASH" rendered in bright primary colors
- **Caption boxes**: Cream-colored caption boxes with thin borders for narration and episode-style scene transitions

## Character Rendering

- **Proportions**: Tall athletic heroic builds with clean angular features — Western superhero influence filtered through Japanese sensibility
- **Helmets and masks**: Elaborate distinctive headgear — bird-shaped helmets, streamlined visors, iconic crests as signature design elements
- **Facial style**: Sharp precise features with defined jawlines; expressive eyes beneath visors convey determination and emotion
- **Team identity**: Each team member instantly identifiable by unique color, helmet shape, and body silhouette
- **Vehicles**: Sleek aerodynamic designs that look fast even when stationary — wedge shapes, low profiles, integrated gadgetry
- **Comedy mode**: Simplified deformed proportions with large heads and rubbery expressions for comedic relief beats

## AmpliVerse Branding

- **Publisher name**: Bold retro-styled "AmpliVerse" in a horizontal banner across the top cover edge
- **Avatar**: AmpliVerse avatar placed inside a team-emblem-style circular badge on the cover
- **Color treatment**: White text on bold primary-colored background matching the lead hero's team color

## Image Requirements

```yaml
image_requirements:
  style_category: tatsunoko-classic
  detail_level: medium
  text_avoidance: good
```
