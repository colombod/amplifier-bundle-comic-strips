# Spider-Man Style Pack

Visual style guide for Spider-Man comic strip creation.

## Image Prompt Template

Base template for generating Spider-Man-style panel images:

```
Spider-Man comic book illustration, dynamic extreme perspective, bold red and blue costume with intricate web pattern, {scene_description}. Dramatic foreshortening with worm's-eye and bird's-eye angles through New York City skyscrapers. Detailed webbing lines connecting architecture. Halftone dot shading with CMYK misregistration effects. Strong ink outlines in the style of Ditko, Romita, and McFarlane. No text in image.
```

## Color Palette

Classic red-and-blue heroics against gritty urban environments.

- **Primary Red**: Costume red `#CC1122` — mask, torso, boots
- **Primary Blue**: Costume blue `#1B3A6B` — legs, arms, side panels
- **Secondary**:
  - Web Silver `#C0C0C0` — webbing highlights, reflective threads
  - NYC Gray `#4A4A4A` — concrete, buildings, asphalt
- **Highlights**: Sunset Orange `#E8741A` — dramatic sky, rim lighting, warm accents
- **Backgrounds**: Urban charcoal `#2C2C2C` — nighttime rooftops, alleyways, shadowed streets

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — standard Western comic flow, left to right, top to bottom
- **Borders**: Medium black outlines, 2px weight, with occasional broken borders for web-swing sequences
- **Gutters**: Narrow white gutters, 6-10px width; webbing motifs can bridge gutters as a design element
- **Border shapes**: Mix of rectangular and dramatically tilted/angled panels; tilted panels convey vertiginous wall-crawling and mid-swing momentum
- **Splash panels**: Full-page splashes for iconic web-swinging arcs and dramatic rooftop reveals
- **Panel count**: 4-6 per page with strong vertical emphasis; exploit height to mirror Spider-Man's vertical movement

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` -- standard dialogue and establishing panels
- **Tilted vertiginous** (swinging): `clip-path: polygon(5% 0, 100% 5%, 95% 100%, 0 95%)` -- mid-swing disorientation
- **Diagonal slash** (action): `clip-path: polygon(0 0, 100% 0, 100% 75%, 0 100%)` -- rapid combat sequences
- **Tall vertical** (descent): `clip-path: inset(0)` with 1:2.5 aspect ratio -- diving between buildings
- **Web-burst** (impact): `clip-path: polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%)` -- key impact moments

## Text Treatment

- **Speech bubbles**: Smooth white rounded bubbles with thin black border; Spider-Man's quips get slightly jagged, energetic bubble edges
- **Font style**: Bold comic sans-style uppercase lettering; Peter Parker inner monologue in italicized caption text
- **Sound effects**: Dynamic onomatopoeia — "THWIP", "SPLAT", "KRASH" — rendered in angular, web-patterned lettering
- **Caption boxes**: Pale blue rectangular narration boxes for Peter Parker's internal voice

## Character Rendering

- **Costume detail**: Fine raised web-line pattern across all red sections; density varies by artist era
- **Expressive lenses**: Large white eye lenses shift shape to convey emotion — narrowed for anger, wide for surprise, squinted for suspicion
- **Silhouette strength**: Every pose must read clearly as Spider-Man in pure black silhouette
- **Signature poses**: The spider-crouch (low, limbs splayed, fingertips on surface), the web-swing arc, the upside-down perch
- **Fluid motion**: Even in still panels, convey coiled kinetic energy and potential movement through body tension
- **Web design element**: Web strands create visual flow lines connecting panels and adding texture to compositions

## AmpliVerse Branding

- **Publisher name**: Angled bold text "AmpliVerse" along a web-strand swooping across the top-right cover corner
- **Avatar**: AmpliVerse avatar placed in a small circular web-node in the bottom-right corner
- **Color treatment**: White text on deep blue background to complement the Spider-Man red-and-blue palette

## Image Requirements

```yaml
image_requirements:
  style_category: spider-man
  detail_level: high
  text_avoidance: critical
```
