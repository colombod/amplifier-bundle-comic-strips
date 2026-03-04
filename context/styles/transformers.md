# Transformers Mecha Style Pack

Visual style guide for Transformers manga-inspired mecha comic strip creation.

## Image Prompt Template

Base template for generating Transformers mecha-style panel images:

```
Transformers mecha manga illustration, giant mechanical robots with visible vehicle parts, bold metallic rendering with sharp reflective highlights, {scene_description}. Dynamic action with speed lines and impact debris. Blocky angular robot proportions with glowing eyes and faction insignias. Metallic surfaces with hard shadow edges and screentone gradients in the style of Japanese super robot manga. No text in image.
```

## Color Palette

Bold primary colors with metallic sheen and energon glow accents.

- **Primary**: Core faction and hero colors:
  - Autobot Red `#CC2936` — Optimus Prime, heroic warmth, faction insignia
  - Decepticon Purple `#6A0DAD` — Megatron, villainy, dark authority
  - Steel Blue `#4682B4` — metallic plating, neutral robot surfaces
- **Secondary**: Mechanical depth and environment:
  - Gunmetal `#2C3E50` — deep shadow on armor, interior mechanisms
  - Cybertronian Gold `#D4A017` — ancient tech, Matrix energy, regal accents
- **Highlights**: Energon Blue `#00D4FF` — glowing fluid, power cores, laser blasts
- **Backgrounds**: Metallic silver-violet for Cybertron; muted earth tones for Earth scenes

## Panel Conventions

- **Reading direction**: RIGHT-TO-LEFT — manga-style flow, panels read right to left, top to bottom
- **Borders**: Medium black borders, 2px weight, clean mechanical precision
- **Gutters**: Narrow white gutters, 6-8px width between panels
- **Border shapes**: Rectangular defaults with angled slashes for transformation sequences and combat impacts
- **Splash panels**: Full-width splash panels for transformation reveals and giant-scale battles
- **Panel count**: 4-6 per page in dynamic grid layout; large panels for mecha action, small insets for cockpit reactions

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` — standard dialogue and scene panels
- **Diagonal slash** (transformation): `clip-path: polygon(0 0, 100% 0, 100% 80%, 0 100%)` — mid-transformation sequences
- **Reverse slash** (counter-attack): `clip-path: polygon(0 20%, 100% 0, 100% 100%, 0 100%)` — opposing force clash
- **Hexagonal** (tech): `clip-path: polygon(25% 0, 75% 0, 100% 50%, 75% 100%, 25% 100%, 0 50%)` — Cybertronian tech interfaces
- **Irregular jagged** (impact): `clip-path: polygon(2% 5%, 98% 0, 100% 92%, 3% 100%)` — explosive combat moments

## Text Treatment

- **Speech bubbles**: Rounded rectangles with thin black borders for standard dialogue; angular metallic-edged bubbles for robotic speech
- **Font style**: Bold condensed sans-serif, ALL CAPS for all dialogue
- **Sound effects**: Massive stylized SFX integrated into artwork — "CHOOM", "KRAKATHOOM", "TSSSHK" rendered as explosive metallic graphic elements
- **Caption boxes**: Dark gunmetal caption boxes with light text for narration and faction identification

## Character Rendering

- **Proportions**: Blocky angular builds from geometric shapes — cubes, cylinders, wedges — not organic curves
- **Vehicle kibble**: Recognizable vehicle components (wheels, wings, grilles) visible as integrated parts of robot mode
- **Facial expression**: Emotion conveyed through eye glow color and intensity, mouth plate position, and head-crest framing
- **Scale contrast**: Characters range from human-sized to city-block-sized; include human figures for scale reference
- **Transformation states**: Mid-transformation panels show parts rotating, folding, and reconfiguring in mechanically plausible stages
- **Battle damage**: Cracked armor plating, exposed wiring, sparking joints, and leaking energon fluid

## AmpliVerse Branding

- **Publisher name**: Bold metallic-styled "AmpliVerse" across the top cover bar, angled slightly for dynamic energy
- **Avatar**: AmpliVerse avatar rendered as a faction-insignia-style emblem in the top-left corner
- **Color treatment**: Metallic silver text on dark Cybertronian purple background

## Image Requirements

```yaml
image_requirements:
  style_category: transformers-mecha
  detail_level: high
  text_avoidance: critical
```
