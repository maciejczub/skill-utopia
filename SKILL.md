---
name: utopia
description: Build fluid, breakpoint-free responsive typography, spacing and layout grids with the Utopia methodology (utopia.fyi). Use when asked for fluid type scales, fluid space tokens, clamp() values, responsive font sizes without media queries, t-shirt spacing, fluid grids/gutters, container-query (cqi) fluid type, or when converting a Figma design with @min/@max artboards into CSS. Includes a generator script that reproduces the utopia.fyi calculators exactly.
---

# Utopia: fluid type, space and grid

Utopia (by James Gilyead and Trys Mudford, Clearleft) is a *declarative* approach to
responsive design: describe the design at two poles, a small viewport (`@min`) and a
large one (`@max`), and let the browser interpolate everything in between with CSS
`clamp()`. No breakpoints, no per-device overrides, one set of tokens that stays "in
tune" with itself on every screen.

Everything hangs off one number: the body text size (**step 0**). The type scale steps
up and down from it, the space palette multiplies it, and the grid is assembled from the
space palette.

## Core formula

Every fluid token is a linear interpolation between `(minWidth, minSize)` and
`(maxWidth, maxSize)`, expressed in rem so browser text-zoom is respected:

```
slope        = (maxSize - minSize) / (maxWidth - minWidth)      # all in rem
intersection = minSize - minWidth * slope
value        = clamp(minSize, intersection + slope * 100vw, maxSize)
```

Example, 18px → 20px between 360px and 1240px:
`clamp(1.125rem, 1.0739rem + 0.2273vw, 1.25rem)`.

Never hand-edit the middle term. Regenerate it, and keep the `/* @link https://utopia.fyi/... */`
comment that the calculators emit above the tokens so anyone can reopen the source config.

## Generate tokens: use the script, don't do the arithmetic in your head

`scripts/utopia.py` (Python 3, no dependencies) is a port of `utopia-core` and produces
output identical to the utopia.fyi CSS tab.

```bash
# Whole system from a calculator URL (the @link comment in existing CSS)
python3 scripts/utopia.py from-url "https://utopia.fyi/type/calculator?c=360,18,1.2,1240,20,1.25,5,2,&s=0.75|0.5|0.25,1.5|2|3|4|6,s-l&g=s,l,xl,12"

python3 scripts/utopia.py type  --min-width 360 --min-font 18 --min-scale 1.2 --max-width 1240 --max-font 20 --max-scale 1.25 --positive 5 --negative 2
python3 scripts/utopia.py space --min-width 360 --max-width 1240 --min-size 18 --max-size 20 --negative 0.75,0.5,0.25 --positive 1.5,2,3,4,6 --pairs s-l 2xs-xl
python3 scripts/utopia.py grid  --min-width 360 --max-width 1240 --min-size 18 --max-size 20 --gutter s-l --column xl --columns 12
python3 scripts/utopia.py clamp --min-width 320 --max-width 1240 16 48          # one ad-hoc token
python3 scripts/utopia.py clamps --min-width 320 --max-width 1240 16-48 40-18   # several, as custom properties
```

Add `--format table --at 768` to see px values at @min, @max and any viewport (useful
for mockups), `--format json` for machine-readable output, `--relative-to container`
for `cqi` (container queries) or `viewport` for `vi`, `--px` on space/clamp to detach
spacing from text zoom. In JS/SCSS/PostCSS projects prefer the official packages
(`utopia-core`, `utopia-core-scss`, `postcss-utopia`), see `references/tooling.md`.

## Workflow

1. **Set the poles.** Pick `@min` viewport (design as small as practical, 320–360px)
   and `@max` (typically where the content container stops growing, e.g. 1240px). Pick
   the body size at each pole (e.g. 18px → 20px). A small viewport is not always a
   small device (split screens), so keep @min small.
2. **Type scale.** Choose a modular ratio per pole, conservative at @min (1.2 Minor
   Third) and more dramatic at @max (1.25–1.333). Step *n* = base × ratio^n at each pole,
   then clamp between them. Tokens: `--step--2 … --step-0 … --step-5`. Generate only
   the steps you need. Check the table view: the largest steps must not overflow at @min.
3. **Space palette.** Step 0 becomes t-shirt size **S**. Multiply it: defaults
   `3xs 0.25, 2xs 0.5, xs 0.75, s 1, m 1.5, l 2, xl 3, 2xl 4, 3xl 6` (rounded to whole
   px). More options near S, fewer far out. Tokens `--space-s`, `--space-xl`…
   Each size is only *subtly* fluid (18→20px). For drama use **pairs**:
   one-up pairs (`--space-s-m`: S@min → M@max) are generated automatically; custom
   pairs (`--space-s-l`, `--space-3xs-2xl`, even reverse `--space-xl-s`) are declared explicitly.
4. **Grid.** Keep the column count constant (12 is the safe default). Gutter is a space
   pair (default `s-l`), column width @max is a space size (default `xl`).
   `max-width = columns × column@max + (columns + 1) × gutter@max` → `--grid-max-width`.
   The generated CSS is intentionally minimal: `--grid-max-width`, `--grid-gutter`,
   `--grid-columns`, `.u-container` and `.u-grid`. Build the actual layout with
   grid/flex on top of these.
5. **Apply tokens** in CSS (see patterns below). Tokens are opt-in custom properties,
   so Utopia can be retrofitted incrementally to an existing site.
6. **Validate**: text zoom to 200% (WCAG 1.4.4), negative steps that shrink on large
   screens, headings wrapping at @min. The script prints warnings for the first two.

## Applying tokens (patterns)

```css
:root { /* generated tokens go here, with the @link comment */ }

body            { font-size: var(--step-0); }
h1              { font-size: var(--step-4); }
.prose h2       { font-size: var(--step-2); }       /* "H2s are always step 2" */

.c-card         { padding: var(--space-s-m); }      /* pair: dramatic padding */
.c-card > * + * { margin-block-start: var(--space-xs); } /* size: subtle gaps */
.hero           { padding-block: var(--space-xl-3xl); }
.o-grid         { display: grid; gap: var(--space-s-l); }

/* Flow utility (Andy Bell) with fluid variants */
.u-flow > * + *      { margin-block-start: var(--flow-space, var(--space-s)); }
.u-flow--l > * + *   { margin-block-start: var(--space-l); }
.u-flow--s-m > * + * { margin-block-start: var(--space-s-m); }

/* Grid foundations */
.u-container { max-width: var(--grid-max-width); padding-inline: var(--grid-gutter); margin-inline: auto; }
.u-grid      { display: grid; gap: var(--grid-gutter); }
.u-grid--3   { grid-template-columns: repeat(3, 1fr); }
```

Rules of thumb:
- **Use sizes for internal rhythm, pairs for outer padding/section spacing** ("the space
  between a card's items is a size; the card's padding is a pair").
- **Pick the attitude, not the number.** Tight on mobile, generous on desktop → steep
  pair (`3xs-xl`). Similar everywhere → single size. Shrinking on desktop → reverse pair.
- **Before adding a size, try to adapt the design to an existing one.** Keep the
  palette small; that is what makes it a shared language between design and code.
- Tokens work for anything accepting a length: margin, padding, gap, border-width,
  border-radius, clip-path, transform, inset. Not everything must be fluid: a prose
  measure such as `max-width: 65ch` is fine left static.
- Prefer `rem` (default). Use `--px` / `usePx: true` only for space you deliberately want
  independent of the user's text-size preference.
- Fluid tokens relative to a **container** (`cqi`) let text and space scale with the
  wrapper they live in instead of the viewport. See the next section before using them.
- Utopia sets *values*, not usage. Which element gets which step is a design decision;
  document the mapping (e.g. `h1 → step 4`) in the project.

## Container-relative tokens (optional profile)

Use when the viewport is a poor proxy for the space text lives in: several wrappers of
different widths, components reused in sidebars/modals/embeds, design systems rendered
in Storybook or micro-frontends, or a token whose @max exceeds the wrapper's `max-width`
(text keeps growing after the layout stopped). With one wrapper whose max width equals
the @max viewport, the default `vw` tokens already behave; skip this.

Naive `cqi` has a trap: units resolve against the *nearest ancestor* query container,
so once cards become containers for `@container` queries, the same `var(--step-2)`
renders a different size in every card. Fix (Kevin Powell, after Ana Tudor): register
the token with `@property` so it is computed where declared and inherited as a length,
then declare it on the wrapper's children.

```bash
python3 scripts/utopia.py type --min-width 324 --max-width 1160 --register --container .u-container
python3 scripts/utopia.py from-url "<utopia.fyi url>" --register   # type + space tokens
```

Rules the output follows, and you must keep when hand-writing it:
- `@property --step-N { syntax: "<length>"; initial-value: <px>; inherits: true; }`.
  **`initial-value` must be px.** `rem`/`em` are not "computationally independent";
  Chrome and Firefox then drop the whole `@property` silently and the inconsistency
  comes back.
- Keep an unregistered twin (`--step-N-reset`) holding the raw `clamp(... cqi ...)`;
  assign `--step-N: var(--step-N-reset)` on `:root` (fallback, resolves against the
  small viewport) and on `.u-container > *`.
- **Declare on the container's children, never on the container itself.** An element is
  not its own query container; declared on `.card`, a token still measures the wrapper.
  To scale a token to a nested container, assign the `-reset` twin on `.card > *`.
- `cqi` measures the container's **content box**. Pass @min/@max as content widths
  (viewport minus gutters, e.g. 360 − 2×18 = 324 and 1240 − 2×40 = 1160), or make the
  container an element without inline padding.
- `container-type: inline-size` on the wrapper is required; naming it is optional.
  The WCAG 1.4.4 check still applies, with the container widths as @min/@max.

## Pitfalls and how to handle them

- **Negativity.** Steps below 0 shrink faster with a larger @max ratio; small text can end
  up *smaller* on desktop than on mobile (the script marks these). Fixes: fewer negative
  steps, unhook small text from the scale (or a separate small-text scale), build the
  scale around the smallest text instead of body copy, or use more steps and skip some.
- **Oversized headings at @min.** A step that is 79px @max may be 68px @min. Override a
  single step's @min systematically rather than arbitrarily, e.g. start step 7 where
  step 5 starts (`--f-7-min: var(--f-5-min)`), accepting that the rhythm changes for that
  step. See `references/formulas.md` for the tweakable-variable variant.
- **Accessibility of `clamp()`.** Fluid values can cap the effect of browser text zoom
  (Adrian Roselli's warning). Steep slopes fail WCAG 1.4.4 (200% resize); the script's
  WCAG check reports the viewport range where a step fails. Keep min/max ratios moderate
  (roughly under 2.5×) and test with browser zoom, not just DevTools resizing.
- **Rounding in design tools.** Space values are rounded to whole px. If `columns ×
  column + gutters` doesn't equal the @min viewport, round the column up and make the
  artboard that width; whole-pixel grids beat an exact viewport number.
- **Too many tokens.** `allPairs` (SCSS) or `--all-pairs` (script) generate every
  permutation; purge unused custom properties at build time.
- **@min and @max are two views of one design**, not two designs. Every change on one
  artboard is mirrored (scaled) on the other.

## Defaults worth remembering (utopia.fyi calculator defaults)

| Setting | @min | @max |
| --- | --- | --- |
| Viewport | 360px | 1240px |
| Body (step 0) | 18px | 20px |
| Ratio | 1.2 (Minor Third) | 1.25 (Major Third) |
| Steps | 2 negative, 5 positive | |
| Space multipliers | 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 6 | |
| Grid | gutter s-l, column xl, 12 columns → 77.5rem (1240px) | |

Ratio presets: 1.067, 1.125, 1.2, 1.25, 1.333, 1.414, 1.5, 1.618, 1.667, 1.778, 1.875, 2.

## Reference files

- `references/formulas.md`: the maths for clamp, type, space, grid, the WCAG check,
  calculator URL format, and the older CSS-locks / "fluid custom properties" variants.
- `references/css-patterns.md`: fuller CSS recipes (flow, grid areas, prose spacing,
  container-relative tokens with `@property`, step overrides, SCSS/PostCSS snippets).
- `references/tooling.md`: script CLI, `utopia-core` (JS/TS), `utopia-core-scss`,
  `postcss-utopia`, Figma plugins and the Kickstarter file.
- `references/design-workflow.md`: designer-side process (choosing poles, grid design
  in Figma, variables and modes, Strong/Prose/Default type styles).
