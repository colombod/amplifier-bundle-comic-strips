# Attack on Titan Style Pack

Visual style guide for Attack on Titan-inspired dark action manga strip creation.

## Image Prompt Template

Base template for generating Attack on Titan-style panel images:

```
Black and white manga illustration, gritty cross-hatching with raw emotional intensity, {scene_description}. Dense ink hatching on faces and surfaces conveying psychological weight. Extreme scale contrast between tiny human figures and enormous monstrous forms. Cinematic framing with dramatic foreshortening and speed lines. Germanic medieval architecture and military detail. In the style of Hajime Isayama's Attack on Titan. No text in image.
```

## Color Palette

Monochrome with gritty tonal range built through cross-hatching and screentone.

- **Primary black**: Pure black `#000000` — heavy shadows, cross-hatching, oppressive darkness
- **Primary white**: Pure white `#FFFFFF` — highlights, steam effects, sky, negative space
- **Accents**: Tonal range through layered techniques:
  - Light cross-hatching — skin, fabric, distant backgrounds
  - Dense cross-hatching — emotional intensity, rage, despair, horror
  - Screentone 30% `#B0B0B0` — atmospheric fog, smoke, steam from Titans
  - Screentone 60% `#666666` — deep environmental shadow, rubble, destruction
- **Highlights**: Sharp white slashes through dark areas for blade reflections and wire glints
- **Rule**: Primarily monochrome linework; screentones supplement cross-hatching for atmospheric depth

## Panel Conventions

- **Reading direction**: RIGHT-TO-LEFT — traditional manga flow, right to left, top to bottom
- **Borders**: Medium black borders, 1-2px weight, with occasional broken borders during combat
- **Gutters**: Narrow white gutters, 4-8px width; gutters collapse during intense action sequences
- **Border shapes**: Rectangular panels with angled slashes for combat; borders shatter and overlap during peak action
- **Splash panels**: Full-page spreads for Titan reveals, transformation sequences, and devastating attacks — scale is the weapon
- **Panel count**: 5-8 per page in varied layout; cramped small panels build claustrophobic tension before explosive full-page releases

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` -- standard narrative panels
- **Angled slash** (combat): `clip-path: polygon(8% 0, 100% 0, 92% 100%, 0 100%)` -- ODM gear combat and blade strikes
- **Tall vertical** (scale): `clip-path: inset(0)` on full-height cell -- emphasizing Titan height against tiny humans
- **Shattered** (horror): `clip-path: polygon(0 0, 95% 3%, 100% 100%, 5% 97%)` -- wall breaches and psychological breaks
- **Full bleed** (devastation): No clip-path, no border -- Titan transformation reveals and catastrophic moments

## Text Treatment

- **Speech bubbles**: Rounded white bubbles with thin borders; jagged spiked bubbles for screaming and commands
- **Font style**: Bold sans-serif, mixed case for dialogue; heavy uppercase for battle orders and screams
- **Sound effects**: Large aggressive impact effects — rumbling, crashing, wire-snap sounds rendered as bold angular text
- **Caption boxes**: Dark rectangular boxes with white text for strategic narration and military briefings
- **Internal monologue**: Borderless floating text near character for desperate inner thoughts during combat

## Character Rendering

- **Proportions**: Realistic athletic proportions; soldier physiques reflect training without superheroic exaggeration
- **Faces**: Intense cross-hatched facial rendering conveying raw emotion — terror, fury, determination, grief
- **Uniforms**: Survey Corps uniforms and ODM gear harnesses drawn with consistent military precision and detail
- **Anatomy**: Titan exposed musculature rendered with disturbing anatomical accuracy — layered muscle fibers, no skin
- **Scale**: Constant emphasis on size difference — tiny soldiers against enormous mindless giants
- **Motion**: Speed lines and dramatic foreshortening convey terrifying velocity of wire-based aerial combat

## AmpliVerse Branding

- **Publisher name**: Vertical bold condensed font spelling "AmpliVerse" along the right spine edge
- **Avatar**: Small AmpliVerse avatar placed in the bottom-right corner of the cover
- **Color treatment**: White on black to maintain the monochrome dark intensity

## Image Requirements

```yaml
image_requirements:
  style_category: attack-on-titan
  detail_level: high
  text_avoidance: critical
```
