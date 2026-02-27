# Panel Layout Patterns Reference

A reference guide for panel layout patterns in comic strips and graphic narratives.

## Grid Systems

### Standard Grids

- **2x2**: Four equal panels in a square arrangement. Balanced, versatile layout for short sequences and gag strips.
- **2x3**: Six panels across two rows of three. The classic comic strip format for paced storytelling.
- **3x3**: Nine-panel grid. Maximum density for detailed sequences, used famously in Watchmen.
- **Horizontal strip**: Single row of panels. Natural left-to-right flow for daily newspaper strips and web comics.

### Dynamic Grids

- **Wide establishing + grid**: Opens with a wide establishing panel spanning the full width, followed by smaller grid panels below for scene detail and dialogue.
- **Crescendo**: Panels progressively increase in size from small to large, building visual momentum toward a climactic moment.
- **Spotlight**: One dominant large panel surrounded by smaller supporting panels, drawing the reader's eye to the focal point.

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
