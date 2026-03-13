# Edward Gorey Style Pack

Visual style guide for Edward Gorey-inspired macabre Victorian pen-and-ink comic strip creation.

## Image Prompt Template

Base template for generating Edward Gorey-style panel images:

```
Edward Gorey pen-and-ink illustration, obsessive parallel crosshatching built from thousands of tiny precise ink strokes, {scene_description}. Tiny detailed figures dwarfed by vast oppressive Edwardian interiors and overgrown Victorian estates. Dense crosshatch shading with no gray washes — pure black India ink on white paper only. Crumbling iron fences, heavy curtains, ornate wallpaper, mysterious staircases, urns on pedestals. Cats lurking in backgrounds — on banisters, behind curtains, atop shelves. Atmosphere of inevitable melancholic doom presented with detached literary calm. In the style of The Gashlycrumb Tinies and The Doubtful Guest. No text in image.
```

## Color Palette

Strictly black and white — the palette of obsessive pen-and-ink crosshatching on bare paper.

- **Primary**: Pure monochrome, no exceptions:
  - India ink black `#000000` — outlines, crosshatching, solid fills, silhouettes
  - Paper white `#FFFFFF` — bare paper, negative space, highlights
- **Secondary**: None — all tonal variation achieved through crosshatch density alone
- **Highlights**: Bare white paper showing through gaps in crosshatching; eyes as tiny white dots in dark faces
- **Backgrounds**: Dense parallel crosshatching for interiors; sparser hatching for exteriors; bare paper for sky with occasional hatched clouds
- **Rule**: Absolutely no gray tones, no washes, no gradients — every shadow and texture is built from individual ink strokes

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — panels read left to right following Western literary flow
- **Borders**: Ornate thin black borders, 1-2px weight; may include subtle decorative corner flourishes in the style of Victorian bookplates
- **Gutters**: Wide white gutters, 10-14px width; generous spacing that frames each panel as its own vignette
- **Border shapes**: Rectangular only — the dread comes from content, never from framing tricks
- **Splash panels**: Never — every panel is equally sized; doom is distributed democratically
- **Panel count**: 1-4 per page; each panel is a self-contained vignette accompanied by verse narration beneath, in the alphabet-book tradition
- **Layout**: Sequential vignettes with literary verse captions below each panel — closer to an illustrated book of doom than a traditional comic strip

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` — clean vignette frames, the only shape needed
- **Ornate border** (bookplate): `clip-path: inset(0 round 4px)` with decorative CSS border-image — for title pages and chapter openings
- **Tall portrait** (staircase): `clip-path: inset(0)` with aspect-ratio override — vertical compositions for looming architecture, towering hedgerows, and figures ascending to their doom

## Text Treatment

- **Speech bubbles**: Extremely rare — Gorey characters seldom speak directly; when used, thin precise oval bubbles with tiny serif text, whispered and formal
- **Font style**: Tiny precise serif hand-lettering, mixed case, tightly kerned — the lettering itself should feel hand-drawn with a fine nib pen
- **Sound effects**: None — silence is the medium; doom arrives without announcement
- **Caption boxes**: Verse narration in thin-bordered rectangular boxes positioned below each panel; rhyming couplets or alphabetical verse in the Gashlycrumb tradition; detached omniscient narrator voice observing catastrophe with literary composure
- **Dialogue philosophy**: Text exists as literary narration, not character speech — the narrator catalogues misfortune with the dispassionate precision of a Victorian naturalist

## Character Rendering

- **Faces**: Small and precisely rendered; hollow dark eyes as tiny dots or circles; pointed noses; expressions range from blank resignation to polite bewilderment; no one is ever surprised by their impending doom
- **Bodies**: Tiny figures — characters occupy at most one-third of the panel height, dwarfed by their environments; wrapped in heavy fur coats, long scarves, Edwardian high collars, and elaborate hats
- **Hands**: Small precise hands, often clasped or holding mysterious objects — letters, urns, dubious parcels; gestures are restrained and formal
- **Action**: Almost none — characters stand, sit, or are discovered mid-catastrophe; the horror has already happened or is about to; movement is implied by consequence, not depicted
- **Shading**: Obsessive parallel crosshatching — vertical strokes for flat surfaces, curved following contours for fabric and faces, cross-hatched layers for deep shadow; density of strokes controls all tonal value
- **Cats**: Ever-present background inhabitants — perched on furniture, threading between ankles, observing from shadows, sitting on graves; drawn with the same precise crosshatching as everything else; they are witnesses, not participants

## AmpliVerse Branding

- **Publisher name**: Tiny precise hand-lettered "AmpliVerse" along the bottom margin, styled as a Victorian publisher's imprint — like "Edward Gorey / Harcourt" on a Gorey book cover
- **Avatar**: Small AmpliVerse avatar placed in the bottom-right corner within a decorative oval border resembling a Victorian cameo
- **Color treatment**: Pure black ink on white paper — matching the uncompromising monochrome of the illustration style

## Image Requirements

```yaml
image_requirements:
  style_category: edward-gorey
  detail_level: high
  text_avoidance: critical
```