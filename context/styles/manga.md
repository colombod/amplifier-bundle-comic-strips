# Manga Style Pack

Visual style guide for manga-inspired comic strip creation.

## Image Prompt Template

Base template for generating manga-style panel images:

```
Black and white manga illustration, ink wash technique, high contrast, {scene_description}. Dynamic composition with speed lines for action. Screentone shading for depth. Exaggerated facial expressions. Clean precise linework in the style of Akira and Dragon Ball. No text in image.
```

## Color Palette

Manga is strictly monochrome. No color is used at any stage.

- **Primary black**: Pure black `#000000` — linework, borders, solid fills
- **Primary white**: Pure white `#FFFFFF` — backgrounds, highlights, negative space
- **Accents**: Gray screentone patterns at three standard densities:
  - 25% density — light shading, distant backgrounds
  - 50% density — mid-tone shading, clothing, surfaces
  - 75% density — deep shadow, dramatic mood
- **Highlights**: White speed lines on black backgrounds for motion and impact
- **Rule**: Strictly monochrome — no grayscale gradients, only dot-pattern screentones

## Panel Conventions

- **Reading direction**: RIGHT-TO-LEFT — panels are arranged and read from right to left, top to bottom, following traditional manga flow
- **Borders**: Thin black borders, 1-2px weight, clean and precise
- **Gutters**: Narrow white gutters, 4-8px width between panels
- **Border shapes**: Mix of rectangular and angled/broken borders; angled borders convey motion or tension, broken borders for bleed effects
- **Splash panels**: Use splash panels for dramatic reveals and climactic moments — a single panel spanning the full page or half-page
- **Panel count**: 4-8 per page in an irregular grid layout; vary panel size to control pacing and emphasis

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` -- standard panels
- **Angled cut** (action): `clip-path: polygon(0 0, 100% 0, 100% 85%, 0 100%)` -- dynamic action sequences
- **Reverse angle** (counter-action): `clip-path: polygon(0 15%, 100% 0, 100% 100%, 0 100%)` -- opposing force
- **Broken border** (impact): No clip-path, use `border: none` with `box-shadow` for shattered effect -- maximum impact moments
- **Irregular** (tension): `clip-path: polygon(3% 0, 100% 2%, 97% 100%, 0 98%)` -- unease, instability

## Text Treatment

- **Speech bubbles**: Spiky/angular bubbles for shouting and intense emotion; round smooth bubbles for normal dialogue; cloud-shaped bubbles for thought
- **Font style**: Bold sans-serif, ALL CAPS for all dialogue text
- **Sound effects**: Large stylized sound effects (onomatopoeia) integrated into the artwork, rendered as bold graphic elements
- **Caption boxes**: Rectangular caption boxes with clean borders for narration and scene-setting text
- **Text direction**: Left-to-right text within bubbles despite right-to-left panel reading order, adapted for English-language audience

## Character Rendering

- **Eyes**: Large expressive eyes as the primary vehicle for emotion; pupil size and shape shift with mood
- **Features**: Simplified facial features — minimal nose, small mouth, emphasis on eyes and hair
- **Comedy mode**: Chibi (super-deformed) proportions for comedy beats and reaction shots
- **Action**: Dynamic poses with exaggerated foreshortening; speed lines radiating from or trailing behind characters
- **Motion**: Speed lines attached to characters and backgrounds to convey velocity and force
- **Emotion**: Emotional shorthand symbols — sweat drops for anxiety, cross-popping veins for anger, sparkles for admiration, mushroom sighs for dejection

## AmpliVerse Branding

- **Publisher name**: Vertical bold condensed font spelling "AmpliVerse" along the right spine edge of the cover
- **Avatar**: Small AmpliVerse avatar placed in the bottom-right corner of the cover
- **Color treatment**: Black on white to maintain the monochrome manga aesthetic

## Image Requirements

```yaml
image_requirements:
  style_category: manga-lineart
  detail_level: medium
  text_avoidance: critical
```
