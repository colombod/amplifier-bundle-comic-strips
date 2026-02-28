# Retro Americana Style Pack

Visual style guide for 1950s retro American advertisement comic strip creation.

## Image Prompt Template

Base template for generating retro Americana-style panel images:

```
1950s retro American advertisement illustration, vintage halftone dot pattern, {scene_description}. Limited warm color palette. Cheerful exaggerated proportions with idealized features. Propaganda-poster composition with strong diagonals. In the style of Fallout Vault Boy and 1950s magazine ads. No text in image.
```

## Color Palette

Warm, nostalgic colors inspired by mid-century American print advertising.

- **Primary**: Core retro palette for main elements:
  - Warm cream `#FFF8DC` — backgrounds, fill areas, speech bubbles
  - Cherry red `#DC143C` — accents, headlines, action highlights
  - Navy blue `#1B2A4A` — outlines, shadows, strong contrast elements
- **Secondary**: Supporting tones for depth and variety:
  - Olive green `#6B8E23` — military motifs, nature elements, secondary accents
  - Golden yellow `#DAA520` — starburst highlights, badges, warm accents
  - Dusty pink `#DDA0A0` — skin tones, soft backgrounds, nostalgic warmth
- **Paper**: Aged cream `#F5F0E1` with subtle paper texture for authentic vintage feel
- **Shading**: Halftone Ben-Day dots for all shading and gradients — no smooth gradients, only dot patterns at varying densities

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — panels are arranged and read from left to right, top to bottom, following standard Western comic flow
- **Borders**: Rounded corners with medium black slightly rough borders, giving a hand-printed vintage feel
- **Gutters**: Wide 10-14px cream gutters between panels for an airy, advertisement-like layout
- **Border shapes**: Rectangular with rounded corners and uniform sizing across the page
- **Grid layout**: Regular 2x2 or 2x3 grid for consistent, clean composition
- **Panel count**: 4-6 per page in an orderly arrangement reflecting the structured feel of mid-century print ads

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0 round 12px)` -- ALL panels have rounded corners by default
- **Circular badge** (spotlight): `clip-path: circle(45% at 50% 50%)` -- character introductions, product shots
- **Starburst** (emphasis): `clip-path: polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%)` -- exclamation moments

## Text Treatment

- **Speech bubbles**: Round, thick, cheerful outlines with cream fill; tail points toward speaker with a friendly rounded shape
- **Font style**: Retro display bold, slightly condensed, ALL CAPS lettering for all dialogue and narration
- **Sound effects**: Starburst shape retro sound effects — "POW!", "ZAP!", "WHAM!" rendered inside jagged starburst shapes with bold outlines
- **Caption boxes**: Ribbon banners and badge captions for narration — text placed inside decorative ribbon or badge frames
- **Tone**: Exclamation-heavy enthusiastic tone throughout — every line delivered with mid-century advertising energy and optimism

## Character Rendering

- **Expressions**: Cheerful, idealized characters with big smiles and bright, wide eyes conveying wholesome optimism
- **Clothing**: 1950s fashion adapted to tech — characters wear retro-styled outfits reimagined for modern technology contexts
- **Poses**: Thumbs-up, confident stances with exaggerated body language projecting can-do attitude
- **Shading**: Halftone shading using dot patterns rather than smooth gradients for authentic retro print look
- **Composition**: Pin-up composition with dynamic, flattering angles and strong silhouettes
- **Mascots**: Cheerful retro mascots as recurring brand characters — friendly, approachable figures with exaggerated features

## AmpliVerse Branding

- **Badge**: Circular quality-seal badge positioned in the top-right corner of the cover or first panel
- **Avatar**: AmpliVerse avatar placed inside badge as the central element of the seal
- **Color treatment**: Red and cream colors matching the retro palette for badge design
- **Badge text**: "APPROVED BY AMPLIVERSE" text arranged around the perimeter of the circular badge
- **Style**: Designed to resemble a vintage product quality seal or "Good Housekeeping" style approval stamp

## Image Requirements

```yaml
image_requirements:
  style_category: illustration
  detail_level: medium
  text_avoidance: fair
```

