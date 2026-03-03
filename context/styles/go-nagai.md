# Go Nagai Style Pack

Visual style guide for Go Nagai-inspired classic mecha and horror manga comic strip creation.

## Image Prompt Template

Base template for generating Go Nagai-style panel images:

```
Go Nagai manga illustration, thick bold ink outlines, stark high contrast black and white, {scene_description}. Swirling psychedelic horror patterns for supernatural scenes. Bold totemic mecha silhouettes with dramatic poses. Grotesque creature designs fusing multiple biological forms. Raw visceral energy in the style of Devilman and Mazinger Z. No text in image.
```

## Color Palette

High contrast palette dominated by stark black and white with visceral accent colors.

- **Primary**: Core palette for characters and action:
  - Ink black `#0A0A0A` — heavy outlines, solid shadow fills, oppressive darkness
  - Stark white `#FAFAFA` — highlights, negative space, dramatic contrast
  - Blood crimson `#8B0000` — violence, demonic energy, transformation
- **Secondary**: Mecha and supernatural accents:
  - Mazinger blue `#1C3D7A` — super robot armor, heroic energy, pilder glow
  - Hellfire orange `#D4450B` — breast fire blasts, explosions, infernal landscapes
- **Highlights**: Bright white specular hits on mecha chrome; psychedelic swirl patterns in inverted values for horror
- **Backgrounds**: Dense solid black for horror tension; stark white voids for isolation; swirling organic patterns for supernatural dimensions

## Panel Conventions

- **Reading direction**: RIGHT-TO-LEFT — panels arranged and read from right to left, top to bottom, following traditional manga flow
- **Borders**: Thick bold black borders, 2-4px weight, heavy and graphic
- **Gutters**: Medium white gutters, 6-10px width between panels
- **Border shapes**: Large dominant panels for impact moments; characters frequently break through panel borders with fists, wings, and weapons reaching into adjacent panels
- **Splash panels**: Full-page splashes for transformation sequences, mecha reveals, and horror climaxes; wordless splash pages for maximum visual impact
- **Panel count**: 3-6 per page; fewer, larger panels than typical manga — designed for immediate visceral impact over contemplative pacing

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` -- standard scene-setting and dialogue panels
- **Massive impact** (transformation): Full-width panel, no clip-path -- Devilman transformations and mecha launches
- **Jagged shatter** (violence): `clip-path: polygon(3% 0, 100% 4%, 96% 100%, 0 97%)` -- graphic combat and body horror
- **Diagonal slash** (mecha attack): `clip-path: polygon(0 0, 100% 0, 100% 75%, 0 100%)` -- Rocket Punch and beam weapon strikes
- **Inverted circle** (horror): `clip-path: circle(44% at 50% 50%)` -- psychedelic demon reveals and surreal nightmare visions

## Text Treatment

- **Speech bubbles**: Round white bubbles for normal dialogue; thick jagged bubbles for demonic voices and battle screams; black-filled inverted bubbles for cosmic horror
- **Font style**: Heavy bold sans-serif, ALL CAPS for all dialogue; extra-bold condensed for mecha attack callouts
- **Sound effects**: Massive graphic onomatopoeia dominating panels — bold 3D effect lettering for rocket punches, explosions, and transformation sequences
- **Caption boxes**: Heavy-bordered rectangular caption boxes for narration; minimal use — Nagai lets artwork speak over text

## Character Rendering

- **Proportions**: Rounded organic character bodies with thick limbs and simplified anatomy; heroic builds for protagonists, grotesque distortion for villains
- **Mecha**: Bold simple totemic robot silhouettes — broad shoulders, narrow waists, iconic poses designed to read as powerful symbols at any size
- **Monsters**: Wildly creative biological fusions — animal, insect, plant, and human anatomy combined into impossible disturbing configurations with visible musculature
- **Transformation**: Visual contrast between gentle human forms and powerful demonic/mecha forms drives character design; progressive reveal sequences across multiple panels
- **Horror**: Surreal psychedelic distortion during supernatural encounters — swirling patterns, value inversions, and melting forms for psychological dread
- **Violence**: Graphic and consequential — dramatic blood splatters, specific injuries, unflinching visual weight to every impact

## AmpliVerse Branding

- **Publisher name**: Heavy bold condensed font spelling "AmpliVerse" along the top edge, styled like a Dynamic Production logo plate
- **Avatar**: AmpliVerse avatar placed in the bottom-right corner with a thick jagged border
- **Color treatment**: Stark white on ink black background to match the high-contrast Nagai aesthetic

## Image Requirements

```yaml
image_requirements:
  style_category: go-nagai-classic
  detail_level: high
  text_avoidance: critical
```
