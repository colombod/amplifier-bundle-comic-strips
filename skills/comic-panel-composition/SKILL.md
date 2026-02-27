---
name: comic-panel-composition
description: "Use when laying out comic panels, deciding panel sizes, arranging visual flow, or assembling panels into a page. Covers rule of thirds, reading direction, gutter sizing, panel weight, pacing, and quality checklists for panel generation and strip assembly review."
version: "2.0.0"
---

# Comic Panel Composition

A skill for laying out comic panels with intentional composition, visual flow, narrative pacing, and structured quality review.

## Rule of Thirds

Apply the rule of thirds to guide placement of key visual elements within each panel:

- **Eyes at upper-third intersections**: Position characters' eyes at the intersections of the upper-third horizontal and vertical lines. This naturally draws the reader's attention to faces and expressions.
- **Action at center or lower-third**: Place the primary action at the center of the panel or along the lower-third line to ground the scene and give it visual weight.
- **Horizon along thirds, never center**: Align the horizon line along either the upper or lower thirds — never dead center. A centered horizon creates a static, lifeless composition.

## Visual Flow Within a Panel

Every panel should have a deliberate visual path that guides the reader's eye:

1. **Entry point**: The spot where the reader's eye first lands in the panel. Typically the upper-left in Western comics. Use high contrast, bright color, or a dominant shape to anchor it.
2. **Path via leading lines, gaze, and contrast**: Guide the eye through the panel using compositional tools — leading lines (architecture, limbs, motion lines), character gaze direction, and areas of high contrast pulling attention along the intended route.
3. **Exit point**: The spot where the eye leaves the panel and transitions to the next. Position it at the edge closest to the next panel to maintain seamless reading flow.

## Reading Direction Between Panels

Control how readers move between panels to maintain narrative clarity:

- **Important info at entry**: Place the most critical visual or textual information where the reader's eye enters each panel. Don't bury the lead in a corner the eye reaches last.
- **Natural transitions**: Design panel exits to flow into the next panel's entry point. Avoid jarring jumps that force the reader to search for the next beat.
- **Gaze direction**: Use character gaze direction to point toward the next panel. A character looking right (in Western comics) pulls the reader forward through the sequence.
- **Speech bubble ordering**: Arrange speech bubbles in reading order (top-to-bottom, left-to-right in Western comics). The first bubble should be closest to the panel entry point so dialogue reads naturally.

## Panel Weight and Pacing

Use panel size, gutter width, and content to control narrative rhythm:

| Moment Type | Panel Size | Gutters | Pacing Effect |
|-------------|-----------|---------|---------------|
| Action | Small, many panels | Narrow gutters | Rapid, urgent pacing |
| Dialogue | Medium, standard panels | Medium gutters | Conversational, steady rhythm |
| Revelation | Large, wide panels | Wide gutter before | Dramatic pause, then impact |
| Emotional | Square or tall panels | Wide gutters | Contemplative, lingering weight |
| Climax | Splash or full-width panel | N/A | Maximum impact, story peak |
| Transition | Small, silent panels | Black or wide gutters | Time or scene change marker |

## Gutter as Storytelling Tool

The space between panels is not dead space — it communicates temporal and spatial relationships:

- **Narrow gutter = instant connection**: Minimal separation signals events happening in rapid succession or near-simultaneously. The reader barely pauses between moments.
- **Wide gutter = time passed**: Expanded space between panels tells the reader that time has elapsed — minutes, hours, or longer. The wider the gutter, the greater the implied gap.
- **Black gutter = location change**: A solid black gutter signals a shift in location or a hard scene break. The darkness acts as a curtain between two distinct spaces.
- **No gutter or overlap = simultaneous action or chaos**: When panels share edges or overlap, it conveys simultaneous events or chaotic, overwhelming moments where boundaries dissolve.

## Panel Quality Checklist (for Panel-Artist Self-Review)

After generating each panel image, run through this checklist before accepting it:

| # | Check | PASS | FAIL |
|---|-------|------|------|
| 1 | Characters fully visible? | All named characters in the scene are present and not cropped out of the frame | One or more characters missing, cut off, or obscured by the frame edge |
| 2 | Faces unobstructed? | Every character's face is clearly visible with recognizable expression | A face is hidden behind another character, object, or panel element |
| 3 | Clear focal point? | The panel has one obvious area that draws the eye first, matching the story beat | The eye wanders with no dominant subject — composition feels flat or cluttered |
| 4 | Tells story without dialogue? | The image alone communicates the action or emotion of the beat | Without the caption you cannot tell what is happening in the scene |
| 5 | Characters match references? | Characters are recognizable against their reference sheets (hair, outfit, build) | A character looks noticeably different from their established design |
| 6 | Space for text overlays? | There is open sky, wall, or low-detail area where speech bubbles can be placed | Every area is busy — overlaying text would obscure important detail |
| 7 | Style consistent? | Art style matches the chosen style guide for this strip (line weight, palette, rendering) | Panel looks like it came from a different comic — jarring style mismatch |
| 8 | No text artifacts? | The image is free of garbled letters, watermarks, or AI-generated text strings | Visible gibberish text, phantom lettering, or unwanted watermarks appear |

**Regeneration rule:** If checks 1, 2, or 3 fail, regenerate the panel with an adjusted prompt that addresses the failure. Maximum 3 attempts per panel. If all 3 attempts fail, use the best one and flag it for manual review.

## Assembly Review Checklist (for Strip-Compositor)

After assembling all panels, covers, and pages into the final strip, run this checklist:

| # | Check | PASS | FAIL |
|---|-------|------|------|
| 1 | Panel flow reads as a narrative? | Reading the panels in order tells a coherent story with clear beginning, middle, and end | Panels feel random or out of order — the narrative thread is lost |
| 2 | Speech bubbles readable? | All speech bubbles have legible text, correct tail pointing, and proper reading order | Text is too small, overlaps art, or bubble tails point to the wrong character |
| 3 | Visual consistency? | All panels share a consistent art style, color palette, and character rendering | Panels clash visually — inconsistent styles break immersion |
| 4 | Cover looks like a comic cover? | The cover has a title, key art, and feels like an authentic comic book cover | The cover is just another panel or lacks title/branding treatment |
| 5 | AmpliVerse logo visible? | The AmpliVerse logo appears on the cover in a clear, unobstructed position | Logo is missing, cropped, or placed where it cannot be read |
| 6 | Character intro complete? | Each character has an introduction panel or caption on their first appearance | A character appears with no context — the reader doesn't know who they are |
| 7 | Navigation works? | Page order is correct and any page-turn transitions make narrative sense | Pages are misordered or a page break lands in the middle of a connected beat |

**Iteration rule:** Max 2 assembly review iterations. Run the checklist, fix failures, and run it once more. If checks still fail after 2 iterations, output the strip with a warning listing the unresolved items.
