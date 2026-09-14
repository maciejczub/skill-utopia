# Utopia formulas

All maths behind utopia.fyi, in the order the calculators apply it. Widths and sizes are
px unless stated; the generated CSS converts to rem by dividing by 16.

## 1. Single fluid value (`clamp()`)

Given `minWidth`, `maxWidth`, `minSize`, `maxSize` (px), convert each to rem, then:

```
slope        = (maxSize - minSize) / (maxWidth - minWidth)
intersection = -minWidth * slope + minSize
clamp(minSize rem, intersection rem + (slope * 100) vw, maxSize rem)
```

Worked example (Pedro Rodriguez's derivation): 1rem → 2rem between 320px (20rem) and
1440px (90rem): slope = 1/70 = 0.014286, intersection = 1 − 20 × 0.014286 = 0.7143 →
`clamp(1rem, 0.7143rem + 1.4286vw, 2rem)`.

Notes:
- Values are rounded to 4 decimals (`utopia-core` `roundValue`).
- If `minSize > maxSize` the slope is negative and the `clamp()` bounds are sorted
  (`clamp(smaller, a + −b vw, larger)`); the value *shrinks* as the viewport grows.
- Unit choices: `vw` (utopia.fyi CSS output), `vi` (inline-size, the `utopia-core`
  default, identical to `vw` in horizontal writing modes), `cqi` (container inline size,
  needs an ancestor with `container-type: inline-size`).
- `usePx: true` keeps px instead of rem: the value then ignores the user's text-size
  preference. Reserve for space you explicitly want fixed relative to the layout.
- Value at an arbitrary viewport `w`: `minSize + (maxSize − minSize) × clamp01((w − minWidth)/(maxWidth − minWidth))`.

## 2. Fluid type scale

Inputs: `minWidth, minFontSize, minTypeScale, maxWidth, maxFontSize, maxTypeScale,
positiveSteps, negativeSteps`.

```
size@min(step) = minFontSize × minTypeScale ^ step
size@max(step) = maxFontSize × maxTypeScale ^ step
--step-{n} = clamp(size@min(n), size@max(n))      # via formula 1
```

Default 360/18/1.2 → 1240/20/1.25, steps −2…5:

| step | @min px | @max px | token |
| --- | --- | --- | --- |
| −2 | 12.50 | 12.80 | `clamp(0.7813rem, 0.7736rem + 0.0341vw, 0.8rem)` |
| −1 | 15.00 | 16.00 | `clamp(0.9375rem, 0.9119rem + 0.1136vw, 1rem)` |
| 0 | 18.00 | 20.00 | `clamp(1.125rem, 1.0739rem + 0.2273vw, 1.25rem)` |
| 1 | 21.60 | 25.00 | `clamp(1.35rem, 1.2631rem + 0.3864vw, 1.5625rem)` |
| 2 | 25.92 | 31.25 | `clamp(1.62rem, 1.4837rem + 0.6057vw, 1.9531rem)` |
| 3 | 31.10 | 39.06 | `clamp(1.944rem, 1.7405rem + 0.9044vw, 2.4414rem)` |
| 4 | 37.32 | 48.83 | `clamp(2.3328rem, 2.0387rem + 1.3072vw, 3.0518rem)` |
| 5 | 44.79 | 61.04 | `clamp(2.7994rem, 2.384rem + 1.8461vw, 3.8147rem)` |

Label styles (`utopia-core` `labelStyle`): `utopia` (`--step--1, --step-0, --step-1`),
`tailwind` (`xs, sm, base, lg, xl, 2xl…`), `tshirt` (`xs, s, m, l, xl, 2xl…`).
Negative-step token names carry a double dash: `--step--1`.

Modular scale ratios: 1.067 Minor Second, 1.125 Major Second, 1.2 Minor Third,
1.25 Major Third, 1.333 Perfect Fourth, 1.414 Augmented Fourth, 1.5 Perfect Fifth,
1.618 Golden Ratio, 1.667 Major Sixth, 1.778 Minor Seventh, 1.875 Major Seventh, 2 Octave.

Negativity: because step −n = base / ratio^n, a larger @max ratio pulls the small steps
*down* at @max. With a static 16px body and ratios 1.2 → 2, step −2 is 11.1px @min but
only 4px @max, so small text shrinks as the screen grows. With 1.2 → 1.333 the effect is
small but present; always check the table for steps below 0.

## 3. Fluid space palette

Inputs: `minWidth, maxWidth, minSize, maxSize` (= step 0 at each pole), multipliers
`negativeSteps` (below S) and `positiveSteps` (above S), `customSizes` (pairs).

```
size@min(label) = round(minSize × multiplier)     # whole px, JS Math.round
size@max(label) = round(maxSize × multiplier)
--space-{label}      = clamp(size@min, size@max)
--space-{a}-{b}      = clamp(size@min(a), size@max(b))   # pairs
```

Labels: multipliers < 1 → `xs, 2xs, 3xs…` (largest multiplier is `xs`); 1 → `s`;
> 1 → `m, l, xl, 2xl, 3xl…` in ascending order.

Default palette (18 → 20px):

| label | × | @min | @max | one-up pair | pair @min → @max |
| --- | --- | --- | --- | --- | --- |
| 3xs | 0.25 | 5 | 5 | 3xs-2xs | 5 → 10 |
| 2xs | 0.5 | 9 | 10 | 2xs-xs | 9 → 15 |
| xs | 0.75 | 14 | 15 | xs-s | 14 → 20 |
| s | 1 | 18 | 20 | s-m | 18 → 30 |
| m | 1.5 | 27 | 30 | m-l | 27 → 40 |
| l | 2 | 36 | 40 | l-xl | 36 → 60 |
| xl | 3 | 54 | 60 | xl-2xl | 54 → 80 |
| 2xl | 4 | 72 | 80 | 2xl-3xl | 72 → 120 |
| 3xl | 6 | 108 | 120 | custom s-l | 18 → 40 |

Pairs are the "attitude" control: a single size moves by ~10%, a one-up pair by ~60%,
a custom pair (`3xs-3xl`) by 24×, and a reverse pair (`xl-s`) gets smaller on wide screens.
`allPairs` generates every ordered permutation (n × (n−1) tokens); purge unused ones.

## 4. Fluid grid

Inputs: space palette, `minGridGutter` (label @min, default `s`), `maxGridGutter`
(label @max, default `l`), `maxGridColumn` (label for column width @max, default `xl`),
`columns` (default 12).

```
--grid-gutter    = var(--space-{min}-{max}, clamp(...))     # e.g. --space-s-l
--grid-max-width = (columns × column@max + (columns + 1) × gutter@max) / 16 rem
                 = (12 × 60 + 13 × 40) / 16 = 77.5rem (1240px) with defaults
column@min       = (minWidth − (columns + 1) × gutter@min) / columns
                 = (360 − 13 × 18) / 12 = 10.5px  → round up and adjust the artboard
```

Generated CSS (intentionally minimal):

```css
:root {
  --grid-max-width: 77.50rem;
  --grid-gutter: var(--space-s-l, clamp(1.125rem, 0.5625rem + 2.5vw, 2.5rem));
  --grid-columns: 12;
}
.u-container { max-width: var(--grid-max-width); padding-inline: var(--grid-gutter); margin-inline: auto; }
.u-grid { display: grid; gap: var(--grid-gutter); }
```

The container is the sum of the tokens you chose, not an arbitrary number; below
`--grid-max-width` gutters and columns stay in tune automatically.

## 5. WCAG 1.4.4 check (from `utopia-core`, by Maxwell Barvian)

Text must remain resizable to 200%. Browser zoom scales rem but also shrinks the CSS
viewport, so a steep `vw` term can cancel part of the zoom. The check compares the
size at 500% browser zoom (`z5`) with twice the size at 100% (`2·z1`) and reports the
viewport range where `z5 < 2·z1`. With `slope = (max−min)/(maxW−minW)`,
`intercept = min − minW·slope`:

```
lh  = (5·min − 2·intercept) / (2·slope)
rh  = (5·intercept − 2·max) / (−slope)
lh2 = 3·intercept / slope
if maxW < 5·minW:
    fails on [max(lh,minW), maxW]     if minW < lh < maxW
    fails on [maxW, 5·minW]           if 5·min < 2·max
    fails on [5·minW, min(rh,5·maxW)] if 5·minW < rh < 5·maxW
else:
    fails on [max(lh,minW), 5·minW]   if minW < lh < 5·minW
    fails on [max(lh2,5·minW), maxW]  if 5·minW < lh2 < maxW
    fails on [maxW, min(rh,5·maxW)]   if maxW < rh < 5·maxW
```

Practical reading: the default scale passes; 16 → 48px over 320–1240px fails between
roughly 1010px and 2060px. Keep `max/min` ratios moderate for text, and always test
real browser zoom.

## 6. Calculator URL format (the `@link` comment)

```
https://utopia.fyi/type/calculator?c=<minW>,<minFont>,<minScale>,<maxW>,<maxFont>,<maxScale>,<positiveSteps>,<negativeSteps>,<extraViewports a-b-c>
                                 &s=<negative multipliers a|b|c>,<positive multipliers a|b|c>,<custom pairs s-l|2xs-xl>
                                 &g=<minGutterLabel>,<maxGutterLabel>,<maxColumnLabel>,<columns>
https://utopia.fyi/clamp/calculator?a=<minW>,<maxW>
```

`/type/`, `/space/` and `/grid/` share the same query. Always keep this comment in the
generated CSS; `clamp()` cannot be reverse-engineered by eye, and the URL is the only
practical way to tweak the system later. `scripts/utopia.py from-url <url>` regenerates
type, space and grid from it.

## 7. Older / alternative implementations

### CSS locks (Mike Riethmuller) with a shared lock point

The pre-`clamp()` approach. A lock interpolates with `calc()` and needs a media query
to stop growing. Utopia's trick: extract `100vw` into a custom property and override it
once at the max breakpoint, so *one* media query locks every fluid value:

```css
:root {
  --fluid-min-width: 320;  --fluid-max-width: 1500;
  --fluid-screen: 100vw;
  --fluid-bp: calc((var(--fluid-screen) - ((var(--fluid-min-width) / 16) * 1rem))
              / ((var(--fluid-max-width) / 16) - (var(--fluid-min-width) / 16)));
}
@media screen and (min-width: 1500px) {
  :root { --fluid-screen: calc(var(--fluid-max-width) * 1px); }
}
:root {
  --f-0-min: 18; --f-0-max: 20;
  --step-0: calc(((var(--f-0-min) / 16) * 1rem) + (var(--f-0-max) - var(--f-0-min)) * var(--fluid-bp));
}
```

Advantages: parameters stay readable and tweakable in the CSS; a step's @min can be
tied to another step (`--f-7-min: var(--f-5-min)` or `var(--f-4-max)`); powers are not
available in CSS so each step is spelled out. Disadvantages: verbose. The calculators
still offer "CSS locks" as an output option; `clamp()` is the default.

### Fluid custom properties ("hills")

A generalisation: store a *gradient* (e.g. 1.25:1, 2:1, 5:1 between 320px and a summit)
as a tiny custom property and multiply it by the px value wanted at 320px:

```css
:root {
  --f-summit: 1200;
  --f-screen: 100vw;
  --f-foot: 1 / 16;
  --f-hill: (var(--f-screen) - 20rem) / (var(--f-summit) / 16 - 20) + var(--f-foot) * 1rem;
  --f-1-25: ((1.25 / 16 - var(--f-foot)) * var(--f-hill));
  --f-2:    ((2 / 16 - var(--f-foot)) * var(--f-hill));
  --f-5:    ((5 / 16 - var(--f-foot)) * var(--f-hill));
}
@media screen and (min-width: 1200px) { :root { --f-screen: calc(var(--f-summit) * 1px); } }

body  { font-size: calc(var(--f-1-25) * 16); }   /* 16px → 20px */
.hero { padding: calc(var(--f-5) * 40) 0; }       /* 40px → 200px */
```

Steep gradient × small number = tight on mobile, ample on desktop; shallow gradient ×
large number = similar everywhere; negative gradients shrink. This is the conceptual
ancestor of space pairs.

### In-CSS clamp calculation

The clamp formula itself can live in CSS custom properties (`--f-0-slope`,
`--f-0-intersection`) to keep min/max editable, at the cost of readability. Precalculated
`clamp()` is what Utopia ships by default.
