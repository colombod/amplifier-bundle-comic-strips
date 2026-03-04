# Solo Leveling Style Pack

Visual style guide for Solo Leveling manhwa-inspired comic strip creation.

## Image Prompt Template

Base template for generating Solo Leveling-style panel images:

```
Solo Leveling manhwa illustration, dark atmospheric digital art, sharp precise linework, {scene_description}. Deep blacks and charcoal shadows as base palette with explosive supernatural color bursts of electric blue and violet energy. Dramatic backlighting and rim-light silhouettes. Angular character designs with cel-shaded shadows. Cinematic composition with aggressive foreshortening. In the style of DUBU's webtoon art. No text in image.
```

## Color Palette

Dark oppressive base tones punctuated by vivid supernatural energy bursts.

- **Primary**:
  - Shadow Black `#0A0A14` — dominant base tone, dungeons, backgrounds
  - Dark Blue `#0F1B3D` — atmospheric depth, nighttime, ambient shadow
- **Secondary**:
  - Electric Blue `#3D7BFF` — power activation, aura flares, portal glow
  - Shadow Purple `#6B1FCC` — protagonist's signature shadow powers, summons
  - Ember Orange `#FF6B1A` — fire effects, enemy attacks, explosion bursts
- **Highlights**: Ethereal White `#E8E8FF` — rim lighting, flashbang power-ups, overwhelming force moments
- **Backgrounds**: Charcoal Gray `#1A1A24` — dungeon interiors, urban night, oppressive environments

## Panel Conventions

- **Reading direction**: TOP-TO-BOTTOM — vertical scroll manhwa format adapted to strip layout, read left to right within rows
- **Borders**: Thin clean black borders, 1-2px weight; panels break open during power activation and boss reveals
- **Gutters**: Narrow dark gutters, 4-8px width, nearly invisible against the dark palette
- **Border shapes**: Tall vertical panels for build-up tension; wide full-bleed panels for explosive payoff moments
- **Splash panels**: Massive full-width reveals for boss encounters, power-ups, and shadow army summons
- **Panel count**: 4-6 per page; small tension-building panels escalating to large dramatic release panels

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` -- standard narrative panels
- **Tall vertical** (tension): `clip-path: inset(0)` with 1:2.5 aspect ratio -- build-up and scrolling drama
- **Diagonal slash** (combat): `clip-path: polygon(0 10%, 100% 0, 100% 90%, 0 100%)` -- high-speed strikes
- **Shattered** (impact): `clip-path: polygon(2% 0, 55% 3%, 100% 0, 98% 52%, 100% 100%, 48% 97%, 0 100%, 3% 48%)` -- boss defeats, critical hits
- **Full bleed** (reveal): No clip-path, borderless edge-to-edge -- overwhelming power moments

## Text Treatment

- **Speech bubbles**: Sharp-cornered slightly angular white bubbles with thin borders; black inverted bubbles for shadow soldiers and monsters
- **Font style**: Clean modern sans-serif, mixed case for dialogue; bold uppercase for power activation and system prompts
- **Sound effects**: Aggressive angular Korean-manhwa-style impact text integrated into action — heavy, dark, outlined in glow color
- **Caption boxes**: Dark translucent overlay boxes with light text for narration; game-UI-styled boxes for system notifications

## Character Rendering

- **Angular precision**: Sharp jawlines, defined cheekbones, tall athletic proportions with clean digital linework
- **Power evolution**: Characters visibly transform as they gain strength — sharper features, more intense eyes, more defined build
- **Shadow soldiers**: Semi-transparent smoky dark forms with glowing eyes; ghostly blue-purple aura outlines
- **Cel-shaded lighting**: Clean hard-edged shadow shapes on characters rather than soft gradients
- **Facial intensity**: Cold composure alternating with explosive battle expressions; heavy shadow work on eyes and jaw
- **Dramatic backlighting**: Characters frequently silhouetted against glowing energy sources, portals, and explosions

## AmpliVerse Branding

- **Publisher name**: Clean modern sans-serif "AmpliVerse" glowing faintly against a dark background at the cover top
- **Avatar**: AmpliVerse avatar with a subtle blue-purple energy aura, placed in the bottom-right corner
- **Color treatment**: Electric blue text on shadow-black background matching the manhwa's supernatural palette

## Image Requirements

```yaml
image_requirements:
  style_category: solo-leveling-manhwa
  detail_level: high
  text_avoidance: critical
```
