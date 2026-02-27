# Superhero Style Pack

Visual style guide for superhero comic book strip creation.

## Image Prompt Template

Base template for generating superhero-style panel images:

```
Superhero comic book illustration, bold saturated colors, dramatic perspective, {scene_description}. Dynamic poses with muscular proportions. Detailed ink outlines with cel-shading. Dramatic lighting with strong shadows. In the style of classic Marvel and DC comics. No text in image.
```

## Color Palette

Bold, saturated colors with high contrast and dramatic lighting.

- **Primary**: Bold saturated core colors for heroes and action:
  - Red `#E63946` — costumes, capes, energy blasts
  - Blue `#1D3557` — skies, suits, heroic tones
  - Yellow `#FFD60A` — accents, power effects, insignias
- **Secondary**: Depth and grounding tones:
  - Deep shadows `#1A1A2E` — nighttime scenes, dark silhouettes, dramatic contrast
  - Midtone grays `#6C757D` — buildings, concrete, metallic surfaces
- **Highlights**: White specular reflections and lens flare effects for power and energy
- **Backgrounds**: Gradient skies for outdoor scenes; urban cityscapes for street-level action

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — panels are arranged and read from left to right, top to bottom, following standard Western comic flow
- **Borders**: Thick black outlines, 2-3px weight, bold and prominent
- **Gutters**: Medium white gutters, 8-12px width between panels
- **Border shapes**: Mostly rectangular panels with angled action panels for dynamic fight sequences and intense moments
- **Splash panels**: Full-page splash panels for dramatic reveals, power-ups, and climactic confrontations
- **Panel count**: 4-6 per page in a regular grid layout; vary for pacing with occasional wide or tall panels

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` -- standard panels
- **Diagonal splash** (action): `clip-path: polygon(0 0, 100% 0, 100% 80%, 0 100%)` -- dynamic action
- **Wide splash** (climax): Full-width panel, no clip-path -- maximum impact
- **Overlapping** (intensity): `clip-path: inset(-5%)` with `z-index` layering -- panels bleeding into each other
- **Circular** (focus): `clip-path: circle(45% at 50% 50%)` -- character spotlight

## Text Treatment

- **Speech bubbles**: Smooth rounded white bubbles with thin black border; tail points toward speaker
- **Font style**: Comic Sans equivalent bold rounded uppercase lettering for all dialogue
- **Sound effects**: Large bold colorful 3D sound effects integrated into the artwork — "BOOM", "CRACK", "WHOOSH" rendered as explosive graphic elements
- **Caption boxes**: Yellow/cream caption boxes with thin borders for narration and scene-setting
- **Thought bubbles**: Cloud-shaped thought bubbles with small circular trail leading to the thinker

## Character Rendering

- **Proportions**: Heroic proportions with broad shoulders, narrow waist, and powerful builds
- **Perspective**: Dramatic foreshortening on punches, leaps, and flying poses for maximum impact
- **Costumes**: Capes flowing with motion, detailed costume textures, emblems, and accessories
- **Powers**: Power effects rendered as glowing energy, lightning, fire, or force fields radiating from characters
- **Identity**: Distinctive costumes and colors for each character — every hero instantly recognizable by silhouette and palette
- **Silhouettes**: Strong silhouettes that read clearly at any size — iconic poses and shapes

## AmpliVerse Branding

- **Corner box**: Top-left corner box in classic Marvel-style containing character headshot or icon
- **Avatar**: AmpliVerse avatar placed above title on the cover
- **Color treatment**: White text on colored background matching the issue's primary hero color
