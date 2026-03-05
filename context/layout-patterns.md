# Panel Layout Patterns Reference

A reference guide for panel layout patterns in comic strips and graphic narratives.

## Page Layout Catalog

**Design rule:** Every layout fills the entire comic page. No half-pages, no newspaper strips. Real comics use the full page height with panels tiling edge-to-edge.

**Naming convention:** `{count}p-{description}` — e.g. `2p-split` for a 2-panel top/bottom split. Legacy `NxM` names are supported as aliases.

### 1-Panel Layouts (Full-Page Splash)

| Layout ID | Description | Use |
|-----------|-------------|-----|
| `1p-splash` | Single panel fills entire page | Climax, establishing shot, title reveal |

### 2-Panel Layouts

All 2-panel layouts fill the full page. Choose based on narrative weight.

| Layout ID | Description | Use |
|-----------|-------------|-----|
| `2p-split` | Equal top / bottom halves | Balanced contrast, before/after |
| `2p-top-heavy` | Large top (2/3) + strip bottom (1/3) | Establishing shot + reaction |
| `2p-bottom-heavy` | Strip top (1/3) + large bottom (2/3) | Build-up + dramatic payoff |
| `2p-vertical` | Equal left / right halves | Confrontation, duality, parallel action |
| `2p-left-heavy` | Large left (2/3) + narrow right (1/3) | Spotlight + context |
| `2p-right-heavy` | Narrow left (1/3) + large right (2/3) | Build-up + spotlight |

### 3-Panel Layouts

All 3-panel layouts fill the full page. The most versatile panel count.

| Layout ID | Description | Use |
|-----------|-------------|-----|
| `3p-rows` | 3 equal horizontal rows | Classic manga stack, steady pacing |
| `3p-top-wide` | 1 wide top + 2 side-by-side bottom | Establishing shot + two reactions |
| `3p-bottom-wide` | 2 side-by-side top + 1 wide bottom | Two build-ups + dramatic payoff |
| `3p-columns` | 3 equal vertical columns | Triptych, parallel timelines |
| `3p-left-dominant` | Tall left (2/3 width) + 2 stacked right | Spotlight + supporting context |
| `3p-right-dominant` | 2 stacked left + tall right (2/3 width) | Build-up sequence + reveal |
| `3p-hero-top` | Large top (2/3 height) + 2 small bottom | Big moment + aftermath details |
| `3p-hero-bottom` | 2 small top + large bottom (2/3 height) | Quick setup + dramatic splash |
| `3p-cinematic` | Narrow-wide-narrow rows (1:2:1) | Cinematic bars, focused center |

### 4-Panel Layouts

| Layout ID | Description | Use |
|-----------|-------------|-----|
| `4p-grid` | Classic 2x2 grid | Balanced storytelling, Z-pattern reading |
| `4p-top-strip` | Wide top + 3-panel grid below | Establishing + sequence |
| `4p-bottom-strip` | 3-panel grid + wide bottom | Sequence + dramatic conclusion |
| `4p-stacked` | 4 equal horizontal rows | Dense manga pacing |

### 5-Panel Layouts

| Layout ID | Description | Use |
|-----------|-------------|-----|
| `5p-classic` | Wide top + 2x2 grid below | Hero intro + supporting action |
| `5p-hero-grid` | Large hero + 4-panel grid | Splash + dense action sequence |
| `5p-stacked` | 5 equal horizontal rows | Maximum vertical pacing |

### 6-Panel Layouts

| Layout ID | Description | Use |
|-----------|-------------|-----|
| `6p-classic` | 2 columns x 3 rows | Classic comic page, versatile |
| `6p-wide` | 3 columns x 2 rows | Cinematic widescreen panels |
| `6p-manga` | 2 columns x 3 rows (manga) | Manga-style dense page |
| `6p-dense` | 3 columns x 2 rows | Maximum density action |

### 7+ Panel Layouts

| Layout ID | Description |
|-----------|-------------|
| `grid_9` | 3x3 grid (Watchmen-style) |
| `stacked_wides` | 4 equal full-width rows |

## Choosing a Layout by Narrative Beat

| Narrative Beat | Recommended Layouts |
|---------------|-------------------|
| Opening / establishing | `2p-top-heavy`, `3p-top-wide`, `3p-hero-top` |
| Dialogue / conversation | `3p-rows`, `4p-grid`, `6p-classic` |
| Action / confrontation | `3p-columns`, `4p-grid`, `3p-left-dominant` |
| Build-up + reveal | `2p-bottom-heavy`, `3p-bottom-wide`, `3p-hero-bottom` |
| Climax / splash | `1p-splash`, `2p-split`, `3p-cinematic` |
| Duality / confrontation | `2p-vertical`, `3p-columns` |
| Resolution / aftermath | `3p-bottom-wide`, `2p-top-heavy` |

## Panel Sizing

| Type | Aspect Ratio | Use Case |
|------|-------------|----------|
| Wide | 2:1 | Establishing shots and landscapes |
| Standard | 3:2 | Dialogue scenes and general use |
| Tall | 1:2 | Reveals and dramatic moments |
| Square | 1:1 | Portraits and emotional beats |
| Splash | Full page | Climaxes and major story turning points |

## Gutter Conventions

- **Narrow (4-8px)**: Tight spacing for fast pacing and rapid action sequences.
- **Medium (8-12px)**: Standard gutter width for normal narrative flow.
- **Wide (12-20px)**: Expanded spacing for contemplative moments and scene pauses.
- **Black gutters**: Solid black separation indicating time jumps or shifts between scenes.
- **No gutter/bleed**: Panels merge with zero separation for maximum intensity and immersion.

## Reading Flow

- **Left-to-right, top-to-bottom**: Standard Western comic reading convention.
- **Right-to-left**: Manga convention, panels and pages read in reverse horizontal order.
- **Z-pattern**: Natural eye movement across a 2x2 grid — top-left to top-right, then down to bottom-left to bottom-right.
- **Spiral**: Inward-focusing path used in spotlight layouts, guiding the eye from outer panels toward the central dominant panel.

## Panel Weight and Pacing

- **Larger panels = slower pacing**: Big panels make the reader linger, slowing the narrative tempo.
- **Smaller panels = faster pacing**: Small panels accelerate the reading speed and sense of urgency.
- **Many panels = dense storytelling**: High panel counts pack more information and detail into a page.
- **Few panels = dramatic emphasis**: Fewer panels per page give each moment more weight and significance.
- **Silent panels = emotional resonance**: Wordless panels let artwork carry the emotional beat without dialogue.
- **Full-bleed panels = breaking the fourth wall**: Borderless panels that extend to page edges shatter the narrative frame, creating direct impact.

## SVG Clip-Path Panel Shapes

Panel images are always generated as standard rectangles. The strip-compositor applies SVG clip-paths to create non-rectangular visible shapes. The style guide's Panel Shapes section defines which shapes are available.

### Shape Reference

| Shape | CSS | Use For |
|-------|-----|---------| 
| **Rectangular** | `clip-path: inset(0)` | Default, dialogue, general scenes |
| **Rounded** | `clip-path: inset(0 round 12px)` | Soft moments, retro styles |
| **Diagonal** | `clip-path: polygon(0 0, 100% 0, 100% 85%, 0 100%)` | Action, dynamic energy |
| **Circular** | `clip-path: circle(45% at 50% 50%)` | Character focus, portraits |
| **Elliptical** | `clip-path: ellipse(48% 45% at 50% 50%)` | Intimate, vignette framing |
| **Irregular** | `clip-path: polygon(3% 0, 100% 2%, 97% 100%, 0 98%)` | Tension, instability |
| **Borderless bleed** | No clip-path, negative margin | Atmospheric, establishing |

### Applying Shapes

The strip-compositor reads the style guide's Panel Shapes section and applies the appropriate clip-path based on the panel's `emotional_beat` from the storyboard:

| Emotional Beat | Suggested Shape |
|---------------|----------------|
| setup / establishing | Wide rectangular or borderless bleed |
| dialogue / conversation | Rectangular (default) |
| action / conflict | Diagonal or angled |
| revelation / climax | Wide splash or circular |
| emotional / intimate | Elliptical or rounded |
| tension / unease | Irregular or torn edge |
| impact / maximum | Full-width splash or broken border |

### Implementation Notes

- Clip-paths are applied to the panel's container `<div>`, not to the `<img>` directly
- Speech bubbles and text overlays are positioned OUTSIDE the clip-path area so they're never clipped
- The base image should be slightly larger than the panel container to avoid white edges at clip boundaries
- Transitions between panel shapes create visual rhythm across the page
