# Disney Classic Style Pack

Visual style guide for classic Disney rubber-hose cartoon comic strip creation.

## Image Prompt Template

Base template for generating Disney classic-style panel images:

```
Classic 1930s Disney cartoon illustration, rubber-hose animation style, bold clean outlines, {scene_description}. Round shapes and smooth curves on all characters with oversized heads, pie-cut eyes, white gloves, and exaggerated squash-and-stretch poses. Bright primary colors with soft watercolor pastel backgrounds. Cheerful, energetic, and always in motion. In the style of early Mickey Mouse and Silly Symphonies cartoons. No text in image.
```

## Color Palette

Bright primary colors with high contrast and soft pastel backgrounds.

- **Primary**: Bold character colors for instant recognition:
  - Black `#1A1A1A` — character bodies, outlines, ears
  - Red `#E12C2C` — shorts, bows, costume accents
  - Yellow `#F5C842` — shoes, buttons, warm highlights
- **Secondary**: Supporting tones for depth:
  - Cream `#FFF5E1` — skin tones, face, gloves
  - White `#FFFFFF` — gloves, buttons, eye whites
- **Highlights**: Bright white specular spots on eyes and glossy surfaces for lively appeal
- **Backgrounds**: Soft watercolor pastels — sky blue `#A8D8EA`, gentle green `#B5E8B5`, warm pink `#F4C2C2` — never competing with bold character design

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — standard Western comic flow, left to right, top to bottom
- **Borders**: Medium-weight rounded black borders, 2px weight, smooth and friendly
- **Gutters**: Wide white gutters, 10-14px width between panels for an open, airy layout
- **Border shapes**: Rounded rectangular panels with soft corners; occasional circular or oval panels for comedic beats
- **Splash panels**: Large panels for slapstick payoffs, musical numbers, and grand reveals
- **Panel count**: 4-6 per page in a clean regular grid; generous spacing to maintain a cheerful, uncluttered feel

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rounded rectangle** (default): `clip-path: inset(0 round 12px)` — standard friendly panels
- **Circle** (gag): `clip-path: circle(45% at 50% 50%)` — comedic spotlight and reaction shots
- **Oval** (whimsy): `clip-path: ellipse(48% 42% at 50% 50%)` — dreamy or musical moments
- **Wavy** (chaos): `clip-path: polygon(2% 5%, 50% 0%, 98% 5%, 100% 50%, 98% 95%, 50% 100%, 2% 95%, 0% 50%)` — slapstick chaos and explosions
- **Wide rounded** (scene): `clip-path: inset(20% 0 round 12px)` — establishing shots and wide gags

## Text Treatment

- **Speech bubbles**: Smooth round white bubbles with medium black borders; bubbly and inviting
- **Font style**: Friendly rounded bold lettering, mixed case, warm and approachable
- **Sound effects**: Bouncy, colorful sound effects ("BONK", "SPLASH", "ZOOM") with playful 3D styling and bright fills
- **Caption boxes**: Rounded cream-colored caption boxes for narrator asides and storybook framing
- **Thought bubbles**: Puffy cloud-shaped thought bubbles with small circular trail, used for daydreaming sequences

## Character Rendering

- **Construction**: Three-circle head construction (head + two round ears); all shapes based on circles and ovals, zero sharp angles
- **Proportions**: Large heads relative to bodies; oversized hands and feet for expressive gestures and comedic weight
- **Limbs**: Rubber-hose style — smooth, flexible tube-like arms and legs that bend without visible joints
- **Expression**: Mouth is the primary emotional vehicle, stretching across the entire face; full-body posture conveys mood
- **Motion**: Constant implied movement — squash-and-stretch deformation, dynamic action lines, and exaggerated follow-through
- **Simplicity**: Minimal internal detail; character strength comes from bold silhouette and what is left out

## AmpliVerse Branding

- **Publisher name**: Rounded friendly "AmpliVerse" text centered above the title on the cover
- **Avatar**: AmpliVerse avatar placed in the top-right corner with a circular frame
- **Color treatment**: White text on red background matching the classic Disney primary palette

## Image Requirements

```yaml
image_requirements:
  style_category: disney-classic
  detail_level: medium
  text_avoidance: critical
```
