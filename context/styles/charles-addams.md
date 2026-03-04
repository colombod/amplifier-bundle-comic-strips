# Charles Addams Style Pack

Visual style guide for Charles Addams-inspired macabre New Yorker cartoon comic strip creation.

## Image Prompt Template

Base template for generating Charles Addams-style panel images:

```
Charles Addams single-panel cartoon illustration, elegant ink wash technique, masterful pen and ink crosshatching, sophisticated macabre humor, {scene_description}. Thin confident ink outlines with delicate gray wash shading. Gothic Victorian architecture and furnishings. Characters with exaggerated gaunt or rotund proportions. Dry deadpan atmosphere where the horrifying is treated as perfectly ordinary. Elegant mid-century New Yorker magazine illustration quality. No text in image.
```

## Color Palette

Restrained monochrome with subtle gray washes -- the palette of a master ink illustrator.

- **Primary**: Core palette for the sophisticated macabre:
  - India ink black `#1A1A1A` -- outlines, deep shadows, silhouettes
  - Warm gray wash `#8C8580` -- mid-tone shading, atmosphere, fog
  - Cream paper `#F5F0E8` -- background, highlights, negative space
- **Secondary**: Accent tones for mood and depth:
  - Cool slate `#5A6470` -- rainy skies, stone walls, gravestones
  - Sepia shadow `#4A3C2E` -- wood paneling, old furniture, earth
- **Highlights**: Clean cream paper showing through as highlights; no pure white except for eyes and ghosts
- **Backgrounds**: Loose gray washes for atmosphere; detailed crosshatching for interiors; bare paper for sky

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT -- panels arranged and read from left to right, top to bottom, following Western comic flow
- **Borders**: Thin elegant black borders, 1px weight; consistent and understated like New Yorker cartoons
- **Gutters**: Generous white gutters, 8-12px width; clean breathing room between panels
- **Border shapes**: Rectangular only -- the humor comes from content, not gimmicky framing
- **Splash panels**: Rare -- reserved for establishing shots of the Addams mansion or a grand reveal; most panels are equally sized
- **Panel count**: 3-5 per page in clean grid layout; unhurried pacing that lets each macabre moment land

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` -- clean standard panels, the workhorse of the style
- **Rounded corners** (cozy horror): `clip-path: inset(0 round 8px)` -- domestic scenes with unsettling undertones
- **Tall portrait** (mansion): `clip-path: inset(0)` with aspect-ratio override -- vertical compositions for architecture and looming figures
- **Wide landscape** (establishing): `clip-path: inset(0)` with aspect-ratio override -- panoramic views of gothic estates, cemeteries, swamps

## Text Treatment

- **Speech bubbles**: Clean smooth oval bubbles with thin borders; no rough edges, no shout bubbles -- everyone speaks with eerie calm composure
- **Font style**: Elegant serif or refined hand-lettering style, mixed case (NOT all caps) -- the characters are articulate and mannered
- **Sound effects**: Minimal to none -- Addams cartoons rely on visual irony, not onomatopoeia; when used, small and restrained
- **Caption boxes**: Thin-bordered rectangular boxes with serif font for deadpan narration; positioned below panels like New Yorker captions

## Character Rendering

- **Faces**: Exaggerated but refined features; gaunt hollow cheeks and deep-set eyes for sinister characters; round cherubic faces for cheerfully morbid ones; deadpan expressions treating horror as mundane
- **Hands**: Long elegant spidery fingers for sinister characters; pudgy short fingers for jovial ones; hands always expressive and carefully drawn
- **Hair**: Solid black fills for dark hair (no strand detail); wild unkempt silhouettes for eccentric characters; precise bun or part lines for composed characters
- **Action**: Minimal action -- characters pose and stand; the horror is in the situation, not the movement; figures are often static while something terrible happens in the background
- **Body proportions**: Deliberately exaggerated -- impossibly tall and thin OR short and round; no normal proportions; silhouettes should be instantly recognizable
- **Shading**: Delicate crosshatching for texture; gray ink washes for atmosphere and depth; heavy solid blacks for dramatic silhouettes against windows and doorways; sharp contrast between lit and shadow areas

## AmpliVerse Branding

- **Publisher name**: Elegant serif font spelling "AmpliVerse" along the bottom margin, styled like a New Yorker magazine credit line
- **Avatar**: Small AmpliVerse avatar placed in the bottom-right corner with a thin circular border
- **Color treatment**: India ink black on cream paper background to match the refined illustration aesthetic

## Image Requirements

```yaml
image_requirements:
  style_category: charles-addams
  detail_level: high
  text_avoidance: critical
```
