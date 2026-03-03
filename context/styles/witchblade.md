# Witchblade Dark Style Pack

Visual style guide for Witchblade-inspired dark supernatural comic strip creation.

## Image Prompt Template

Base template for generating Witchblade dark-style panel images:

```
Dark supernatural comic book illustration, fine detailed inking with heavy cross-hatching, dramatic warm-cool lighting contrast, {scene_description}. Elongated elegant figure proportions with flowing hair as compositional element. Organic-mechanical armor with asymmetric bladed tendrils and glowing amber gemstone nodes. Nocturnal urban atmosphere with rich shadows in the style of Michael Turner and 90s Image Comics. No text in image.
```

## Color Palette

Dark rich nocturnal tones with warm amber highlights against cool shadow depths.

- **Primary**: Core atmospheric and armor tones:
  - Midnight Blue `#0D1B2A` — night sky, deep urban shadow, base atmosphere
  - Witchblade Amber `#D4890E` — artifact glow, warm armor energy, gemstone nodes
  - Blood Crimson `#8B0000` — combat accents, violence, supernatural threat
- **Secondary**: Depth and environmental grounding:
  - Shadow Purple `#2D1B4E` — cool recessed shadows, alley darkness, mystery
  - Warm Skin `#C68642` — figure rendering under dramatic directional light
- **Highlights**: Amber-white specular glow on armor nodes and energy tendrils `#FFD07B`
- **Backgrounds**: Rain-slicked city streets, dim penthouse interiors, underground lairs in deep blue-black

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — standard Western comic flow, left to right, top to bottom
- **Borders**: Thin refined borders, 1-2px weight, elegant and precise
- **Gutters**: Narrow dark gutters, 4-6px width, maintaining nocturnal atmosphere between panels
- **Border shapes**: Flowing organic panel divisions following hair and armor tendril curves; rigid grids only for calm scenes
- **Splash panels**: Full-page and double-page spreads for transformation sequences, hero shots, and cinematic establishing shots
- **Panel count**: 3-5 per page in organic flowing layout; large dramatic panels dominate, small insets for reaction close-ups

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` — calm dialogue and interior scenes
- **Tall portrait** (hero shot): `clip-path: inset(0 20%)` — elongated figure showcase, dramatic poses
- **Organic curve** (supernatural): `clip-path: ellipse(48% 50% at 50% 50%)` — artifact activation and mystical energy
- **Diagonal dramatic** (combat): `clip-path: polygon(0 0, 100% 10%, 100% 100%, 0 90%)` — dark action sequences
- **Irregular torn** (horror): `clip-path: polygon(2% 5%, 95% 0, 100% 93%, 5% 100%)` — violent supernatural moments

## Text Treatment

- **Speech bubbles**: Slim elegant white bubbles with thin borders; sharp tails for intense speech, soft tails for whispers
- **Font style**: Refined serif-influenced lettering, mixed case for dialogue, conveying sophistication and darkness
- **Sound effects**: Dark metallic SFX with amber glow edges — "SHHRRKK", "KRNCH", "SSSKRAAAA" integrated into armor and combat art
- **Caption boxes**: Dark translucent caption boxes with warm amber text for Sara Pezzini's internal narration

## Character Rendering

- **Proportions**: Elongated statuesque figures with long limbs, narrow waists, and fashion-illustration silhouettes
- **Hair dynamics**: Flowing hair treated as a major compositional element — directing the eye, framing faces, creating visual rhythm
- **Armor design**: Asymmetric organic-mechanical armor growing from the body — metallic blades, living tendrils, amber gemstone nodes at joints
- **Facial expression**: Genuine nuanced emotion — determination, vulnerability, intensity — conveyed through subtle facial acting
- **Lighting on figures**: Strong directional warm light on skin against cool blue-purple shadow, creating cinematic depth
- **Detail gradient**: Dense intricate detail on armor and hair; clean readable rendering on skin and faces

## AmpliVerse Branding

- **Publisher name**: Elegant thin "AmpliVerse" along the bottom cover edge with subtle amber glow effect
- **Avatar**: AmpliVerse avatar rendered small in the bottom-right corner with dark translucent backing
- **Color treatment**: Amber-gold text on deep midnight blue background

## Image Requirements

```yaml
image_requirements:
  style_category: witchblade-dark
  detail_level: high
  text_avoidance: critical
```
