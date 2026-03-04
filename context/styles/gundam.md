# Gundam Style Pack

Visual style guide for Gundam mecha manga-inspired comic strip creation.

## Image Prompt Template

Base template for generating Gundam-style panel images:

```
Gundam mecha manga illustration, hard science fiction military aesthetic, precise mechanical linework with detailed panel lines on mobile suits, {scene_description}. Angular faceted armor plating with cel-shaded flat shadows. Soft expressive human characters contrasting with hard-edged mechanical rendering. Beam saber energy trails and thruster exhaust effects. Space battle and military base environments. In the style of Kazuhisa Kondo and Yasuhiko Yoshikazu. No text in image.
```

## Color Palette

Military hardware tones with bold mecha color-blocking and energy weapon accents.

- **Primary**:
  - Gundam White `#F0F0F0` — primary armor plating, protagonist mobile suit
  - Federation Blue `#1E4B8E` — joints, inner frame, team markings
- **Secondary**:
  - Accent Red `#CC2233` — chest vents, shield, feet, chin guard
  - Accent Yellow `#E8B800` — V-fin antenna, vents, sensor highlights
  - Thruster Orange `#FF6B00` — beam effects, explosions, thruster exhaust
- **Highlights**: Beam White `#FFFFFF` — beam saber cores, energy weapon trails, lens flare
- **Backgrounds**: Space Black `#0A0A1A` — star fields, void; Metallic Gray `#7A7A8A` — hangar bays, colony interiors

## Panel Conventions

- **Reading direction**: RIGHT-TO-LEFT — traditional manga flow, right to left, top to bottom
- **Borders**: Clean black borders, 1-2px weight, precise and technical; occasional borderless panels for space combat vastness
- **Gutters**: Narrow white gutters, 4-8px width, clean and mechanical in feel
- **Border shapes**: Mostly rectangular with wide-angle panels for space battles; tight inset panels for cockpit interiors and pilot reactions
- **Splash panels**: Full-page spreads for first mobile suit reveals, climactic beam clashes, and colony-scale destruction
- **Panel count**: 5-7 per page; alternating between wide establishing shots and tight cockpit close-ups

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` -- standard narrative and dialogue panels
- **Widescreen panoramic** (space battle): `clip-path: inset(0)` with 3:1 aspect ratio -- fleet engagements and colony vistas
- **Cockpit inset** (pilot): `clip-path: polygon(10% 5%, 90% 5%, 95% 95%, 5% 95%)` -- tight interior pilot reaction shots
- **Diagonal thrust** (combat): `clip-path: polygon(0 0, 100% 8%, 100% 100%, 0 92%)` -- high-speed mecha charges
- **Hexagonal** (tactical): `clip-path: polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%)` -- HUD overlays and tactical readouts

## Text Treatment

- **Speech bubbles**: Clean rounded white bubbles with thin borders; radio comms use rectangular bubbles with antenna-tick marks
- **Font style**: Clean sans-serif uppercase for dialogue; monospace font for ship communications and tactical readouts
- **Sound effects**: Technical and explosive — "VWOOOM", "KRAKOOM", "PSSHH" — rendered in sharp angular lettering with metallic shading
- **Caption boxes**: Military-styled dark olive or steel-gray boxes with white text for mission briefings and narration

## Character Rendering

- **Human/machine contrast**: Characters drawn with soft organic lines and warm tones; mecha drawn with hard ruler-straight edges and cool metallic tones
- **Mecha panel lines**: Every mobile suit surface detailed with recessed panel lines indicating hatches, armor sections, and modular joints
- **Proportional realism**: Mobile suits maintain semi-realistic military hardware proportions — implied engineering logic, not fantasy
- **Scale communication**: Panels frequently juxtapose human figures against mobile suits to emphasize the machines' enormous 18-meter scale
- **Damage progression**: Mecha show progressive battle damage — cracked armor, severed limbs, sparking circuits, trailing smoke
- **Pilot expressions**: Cockpit close-ups show sweat, strain, and emotion lit by instrument glow against cramped interiors

## AmpliVerse Branding

- **Publisher name**: Stencil-style military font "AmpliVerse" along the right spine edge of the cover
- **Avatar**: AmpliVerse avatar inside a hexagonal tactical frame in the bottom-right corner
- **Color treatment**: White text on federation blue background to match the military mecha aesthetic

## Image Requirements

```yaml
image_requirements:
  style_category: gundam-mecha
  detail_level: high
  text_avoidance: critical
```
