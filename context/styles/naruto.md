# Naruto Style Pack

Visual style guide for Naruto-inspired ninja manga comic strip creation.

## Image Prompt Template

Base template for generating Naruto-style panel images:

```
Naruto manga illustration, sketch-like ink linework with organic confidence, warm earthy tones, {scene_description}. Fisheye lens perspective for action shots. Spiral motifs and chakra energy swirls. Feudal Japanese architecture with ninja fantasy elements. Speed lines and dynamic martial arts choreography. In the style of Masashi Kishimoto. No text in image.
```

## Color Palette

Warm earthy tones anchored by signature orange, blending ninja fantasy with feudal Japan.

- **Primary**: Core palette for characters and action:
  - Orange `#F27930` — signature color, jumpsuits, energy blasts
  - Deep green `#2D5A27` — forests, flak jackets, foliage
  - Sky blue `#5B9BD5` — open skies, water techniques, calm scenes
- **Secondary**: Grounding and environment tones:
  - Earth brown `#8B6914` — wood structures, scrolls, terrain
  - Warm sand `#D4A853` — Hidden Sand, desert scenes, parchment
- **Highlights**: Bright white chakra bursts, golden Rasengan glow `#FFD43B`, red Sharingan accents `#CC2936`
- **Backgrounds**: Warm-toned village rooftops and forest canopies; muted gradient skies for emotional scenes

## Panel Conventions

- **Reading direction**: RIGHT-TO-LEFT — panels arranged and read from right to left, top to bottom, following traditional manga flow
- **Borders**: Thin black borders, 1-2px weight, with sketch-like energy at corners
- **Gutters**: Narrow white gutters, 4-8px width between panels
- **Border shapes**: Rectangular panels for dialogue; angled and broken borders during taijutsu fights and jutsu activation
- **Splash panels**: Full-page or half-page splash panels for jutsu reveals, transformations, and emotional climaxes
- **Panel count**: 4-7 per page in irregular grid layout; smaller panels for rapid fight choreography, larger for dramatic beats

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` -- standard dialogue and scene-setting panels
- **Angled slash** (taijutsu): `clip-path: polygon(0 0, 100% 0, 100% 82%, 0 100%)` -- fast-paced combat sequences
- **Fisheye burst** (impact): `clip-path: circle(48% at 50% 50%)` -- fisheye lens strike moments
- **Spiral cut** (jutsu): `clip-path: polygon(2% 5%, 98% 0, 100% 95%, 0 100%)` -- chakra activation and technique reveals
- **Broken border** (transformation): No clip-path, use `border: none` with `box-shadow` for jinchūriki power surges

## Text Treatment

- **Speech bubbles**: Round smooth bubbles for normal dialogue; jagged spiky bubbles for battle cries and jutsu callouts
- **Font style**: Bold sans-serif, ALL CAPS for dialogue; brush-stroke style for jutsu names
- **Sound effects**: Large stylized onomatopoeia integrated into artwork — impact SFX rendered as bold graphic elements with motion trails
- **Caption boxes**: Rectangular caption boxes with clean borders for narration and flashback context
- **Text direction**: Left-to-right text within bubbles adapted for English-language audience

## Character Rendering

- **Silhouettes**: Simple memorable silhouettes — spiky hair, headband shapes, and outfit profiles instantly identify each character
- **Eyes**: Large expressive eyes for emotion; Sharingan, Byakugan, and Rinnegan rendered with precise geometric detail
- **Comedy mode**: Chibi-proportioned reaction shots with cross-veins, waterfall tears, and blank-stare faces for comedic beats
- **Action**: Anatomically grounded martial arts poses with fisheye foreshortening; weight transfer and impact physics feel real
- **Jutsu effects**: Each technique has a unique visual signature — spinning spheres, crackling lightning, swirling flame-like chakra auras
- **Cultural detail**: Forehead protectors, tactical vests, sandals, and scroll pouches rooted in feudal Japanese shinobi design

## AmpliVerse Branding

- **Publisher name**: Vertical bold condensed font spelling "AmpliVerse" along the right spine edge, styled like a scroll seal
- **Avatar**: Small AmpliVerse avatar placed in the bottom-right corner with a leaf-village-inspired circular border
- **Color treatment**: Orange on dark earth-tone background to match the Naruto warm palette

## Image Requirements

```yaml
image_requirements:
  style_category: naruto-manga
  detail_level: medium
  text_avoidance: critical
```
