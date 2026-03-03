# Sin City Style Pack

Visual style guide for Frank Miller Sin City noir comic strip creation.

## Image Prompt Template

Base template for generating Sin City-style panel images:

```
Sin City noir illustration, extreme high-contrast black and white, heavy ink pools of pure black, stark white highlights with no mid-tones, {scene_description}. Harsh dramatic shadows cutting across faces and architecture. Bold silhouettes against white or black backgrounds. Rain-slicked streets reflecting neon. Frank Miller graphic noir style with minimal linework and maximum contrast. Cinematic low-angle or dutch-angle composition. No text in image.
```

## Color Palette

Stark monochrome with rare, deliberate color splashes for narrative emphasis.

- **Primary black**: Pure black `#000000` — shadows, silhouettes, ink pools, negative space
- **Primary white**: Pure white `#FFFFFF` — highlights, rain, muzzle flash, teeth, eyes
- **Selective red**: Blood red `#CC0000` — blood, lips, danger, violence (used VERY sparingly on 1-2 elements per issue)
- **Selective gold**: Sickly yellow `#C8A82E` — corruption, villainy, neon signs (rare accent)
- **Selective blue**: Cold blue `#4A7FB5` — moonlight, police lights, melancholy (rare accent)
- **Rule**: 95% of every panel is pure black and white. Color is a weapon — deploy only for shock or narrative emphasis.

## Panel Conventions

- **Reading direction**: LEFT-TO-RIGHT — standard Western comic flow
- **Borders**: Thick black borders, 3-4px weight, or borderless full-bleed for impact
- **Gutters**: Narrow black gutters, 3-6px, disappearing into the darkness
- **Border shapes**: Mostly rectangular with aggressive diagonal cuts for action; full-bleed splash panels for violence and revelation
- **Splash panels**: Frequent full-page and half-page splashes — silhouette figures against stark white, rain-soaked cityscapes, brutal confrontations
- **Panel count**: 3-6 per page; fewer panels = more impact. Single-panel pages for kills and revelations.

## Panel Shapes

Available SVG clip-path shapes for this style:
- **Rectangular** (default): `clip-path: inset(0)` — standard noir dialogue, establishing shots
- **Diagonal slash** (violence): `clip-path: polygon(0 0, 100% 0, 100% 85%, 0 100%)` — gunshots, car chases, brutal action
- **Reverse slash** (counter): `clip-path: polygon(0 15%, 100% 0, 100% 100%, 0 100%)` — retaliation, twist reveal
- **Wedge** (tension): `clip-path: polygon(8% 0, 100% 0, 92% 100%, 0 100%)` — narrowing stakes, interrogation, stalking
- **Full bleed** (impact): No clip-path, panel breaks boundaries — kills, confessions, maximum emotional impact

## Text Treatment

- **Speech bubbles**: White bubbles with thick black borders, angular not rounded; internal monologue in black caption boxes with white text (first person noir narration)
- **Font style**: Bold condensed uppercase sans-serif; ragged hand-lettered feel for dialogue
- **Sound effects**: Minimal — when used, stark white block letters on black. No colorful cartoon SFX. Violence is shown, not spelled.
- **Caption boxes**: Black rectangles with white text for first-person hardboiled narration. Placed at panel edges. This is the voice of the story.
- **Internal monologue**: Italic white-on-black captions — cynical, weary, poetic. The narrator's voice drives every page.

## Character Rendering

- **Silhouettes**: Characters rendered as bold black silhouettes with selective white detail — eyes, scars, cigarette glow, gun barrel
- **Faces**: Harsh shadow bisecting faces — half lit, half in total darkness. Chiaroscuro pushed to extremes
- **Bodies**: Exaggerated proportions — massive shoulders on men, elongated limbs on women. Comic book noir anatomy
- **Rain**: Constant — white diagonal lines cutting across every outdoor panel. Rain defines the world
- **Eyes**: White dots or slits in black faces — predatory, haunted, dangerous. Eyes are the only readable feature in darkness
- **Wounds**: White splatter on black for blood spray; stark, graphic, unflinching

## AmpliVerse Branding

- **Publisher name**: White condensed block text "AmpliVerse" stamped in bottom-right corner of cover, half-obscured by shadow
- **Avatar**: AmpliVerse avatar as a stark white silhouette badge, top-left corner
- **Color treatment**: Pure white on pure black — no grays, no compromise

## Image Requirements

```yaml
image_requirements:
  style_category: sin-city-noir
  detail_level: high
  text_avoidance: critical
```