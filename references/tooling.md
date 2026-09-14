# Utopia tooling

## 1. `scripts/utopia.py` (this skill)

Dependency-free Python 3 port of `utopia-core`. Output matches the utopia.fyi CSS tab.

| Command | What it does |
| --- | --- |
| `clamp [--min-width W] [--max-width W] MIN MAX [--px] [--relative-to viewport-width\|viewport\|container]` | one `clamp()` string |
| `clamps ... 16-48 40-18 [--prefix space] [--px]` | several custom properties, labelled `--space-16-48` |
| `type --min-width --min-font --min-scale --max-width --max-font --max-scale --positive N --negative N [--prefix step] [--label-style utopia\|tailwind\|tshirt]` | type scale, with WCAG 1.4.4 and "shrinking step" warnings |
| `space --min-width --max-width --min-size --max-size --negative 0.75,0.5,0.25 --positive 1.5,2,3,4,6 --pairs s-l 2xs-xl [--all-pairs] [--px] [--prefix space]` | sizes, one-up pairs, custom pairs |
| `grid ... --gutter s-l --column xl --columns 12` | `--grid-*` tokens plus `.u-container` / `.u-grid` |
| `from-url "<utopia.fyi URL>"` | type + space + grid from a calculator URL |

Common flags: `--format css|json|table`, `--at 768` (extra px column in table output),
`--relative-to` (default `viewport-width` = `vw`, like the website; `utopia-core`
defaults to `vi`).

Typical agent flow:

```bash
python3 scripts/utopia.py type --min-width 360 --min-font 18 --min-scale 1.2 --max-width 1240 --max-font 20 --max-scale 1.333 --positive 6 --negative 2 --format table --at 1024
# read the table, adjust ratios/steps, then emit CSS
python3 scripts/utopia.py type ... > src/styles/tokens/type.css
python3 scripts/utopia.py space ... > src/styles/tokens/space.css
python3 scripts/utopia.py grid ... > src/styles/tokens/grid.css
```

## 2. `utopia-core` (JS/TS, npm)

The calculations behind the site. Use in build scripts, design-token pipelines
(Style Dictionary, Tailwind config), or runtime generation.

```ts
import { calculateTypeScale, calculateSpaceScale, calculateClamp, calculateClamps } from 'utopia-core';

calculateTypeScale({
  minWidth: 320, maxWidth: 1240, minFontSize: 18, maxFontSize: 20,
  minTypeScale: 1.2, maxTypeScale: 1.25, positiveSteps: 5, negativeSteps: 2,
  relativeTo: 'viewport',      // 'viewport' (vi, default) | 'viewport-width' (vw) | 'container' (cqi)
  labelStyle: 'utopia',        // 'utopia' | 'tailwind' | 'tshirt'
});
// => UtopiaStep[] : { step, label, minFontSize, maxFontSize, clamp, wcagViolation: {from,to} | null }

calculateSpaceScale({
  minWidth: 320, maxWidth: 1240, minSize: 18, maxSize: 20,
  positiveSteps: [1.5, 2, 3, 4, 6], negativeSteps: [0.75, 0.5, 0.25],
  customSizes: ['s-l', '2xl-4xl'],
});
// => { sizes, oneUpPairs, customPairs } each UtopiaSize { label, minSize, maxSize, clamp, clampPx, multiplier }

calculateClamp({ minWidth: 320, maxWidth: 1240, minSize: 16, maxSize: 48, usePx?: boolean, relativeTo?: ... });
// => 'clamp(1rem, 0.3043rem + 3.4783vi, 3rem)'

calculateClamps({ minWidth: 320, maxWidth: 1240, pairs: [[16, 48], [32, 40]] });
// => [{ label: '16-48', clamp, clampPx }, ...]
```

Tailwind example (fontSize / spacing from Utopia):

```js
const { calculateTypeScale, calculateSpaceScale } = require('utopia-core');
const type = calculateTypeScale({ /* … */ , labelStyle: 'tailwind' });
const space = calculateSpaceScale({ /* … */ });
module.exports = {
  theme: {
    fontSize: Object.fromEntries(type.map(s => [s.label, s.clamp])),
    spacing: Object.fromEntries([...space.sizes, ...space.oneUpPairs, ...space.customPairs].map(s => [s.label, s.clamp])),
  },
};
```

## 3. `utopia-core-scss` (npm)

```bash
npm install utopia-core-scss
```

```scss
@use 'node_modules/utopia-core-scss/src/utopia' as utopia;
```

Mixins emit custom properties; functions return raw values with identical parameters.

| Mixin | Function | Purpose |
| --- | --- | --- |
| `generateTypeScale()` | `calculateTypeScale()` | type scale (`prefix` default `step-`) |
| `generateSpaceScale()` | `calculateSpaceScale()` | sizes + one-up pairs + custom pairs (`prefix` default `space-`, `usePx`, `allPairs`) |
| `generateClamps()` | `calculateClamps()` | several clamps from `pairs: ((16, 48), (40, 18))` |
| `generateClamp()` | `calculateClamp()` | one clamp |

All accept `relativeTo`: `viewport` (`vi`, default), `viewport-width` (`vw`), `container` (`cqi`).
`allPairs: true` (v1.3.0+) generates every permutation and makes `customSizes` unnecessary;
combine with PurgeCSS. `calculateSpaceScale` also returns an `allPairs` list.

## 4. `postcss-utopia` (npm)

```js
// postcss.config.js
module.exports = { plugins: { 'postcss-utopia': { minWidth: 320, maxWidth: 1240 } } };
```

- Declaration method: `utopia.clamp(16, 24)` or `utopia.clamp(16, 24, 320, 1080)` →
  readable clamp compiled to `clamp(1rem, 0.7895rem + 1.0526vi, 1.5rem)`.
- At-rules inside `:root`: `@utopia typeScale({...})`, `@utopia spaceScale({...})`,
  `@utopia clamps({ pairs: [[16, 40]] })`. Any `utopia-core` config is valid
  (`relativeTo`, `usePx`, `prefix`); `minWidth`/`maxWidth` default to the plugin config.
- The calculators' "PostCSS" tab exports the matching config object.

## 5. utopia.fyi calculators

- `/type/calculator`: min/max viewport, font size, ratio; steps table, graph (step 0 and
  neighbours at both poles), visualiser; "insert a viewport width" column for mockups;
  add steps up/down; output CSS / SCSS / PostCSS; `clamp()` or CSS locks; relative to
  viewport or container.
- `/space/calculator`: same base values; editable multipliers and t-shirt sizes; one-up
  pairs; custom pairs; `rem` or `px`.
- `/grid/calculator`: gutter @min/@max and column @max from the space palette, column
  count; offers to round the @min column and adjust the viewport; emits `--grid-*`,
  `.u-container`, `.u-grid`.
- `/clamp/calculator`: any number of ad-hoc tokens between one min/max viewport; rem or px;
  viewport or container; custom prefix. The middle ground between single-token
  calculators (e.g. 9elements' min-max) and a full Utopian system, ideal for retrofitting.

Every export starts with an `@link` URL back to the exact configuration. Keep it.

## 6. Figma

- **Utopia Fluid Type + Space Calculator plugin** (Figma Community): paste a calculator
  URL or enter values; generates artboards: Settings (source of truth, re-read on
  re-run), Space @min / @max (layout-grid based components, toggle with Shift+G),
  Type @min / @max with three style sets: *Strong* (headings), *Prose* (long-form,
  looser line height), *Default* (captions, links, snippets). Default typeface Inter.
- **V2 (June 2024)**: generates variable collections that drive the artboards (artboards
  become disposable: delete and re-run). With a paid plan, one variable per step with
  `min` and `max` **modes**; otherwise separate min/max variables. Also generates space
  pairs, grid-area variables (half, third, quarter…), optional artboards per section,
  separate min/max base sizes for space (e.g. keep an 8px space system while type stays
  Utopian), dark mode. Earlier (Sept 2023) collections: "Utopian size" (raw px),
  "Space @min", "Space @max".
- **Type style updater plugin**: bulk-change family/style/line-height/letter-spacing/
  size/paragraph spacing on the generated styles; blank fields are ignored; use
  Deep Select (Cmd/Ctrl-drag) to target one column such as all Strong styles.
- **Utopia Kickstarter** (Figma Community file): project starting point with min/max
  modes wired into every component, a prose flow-spacing convention (S between items,
  optional per-component breathing room) and a page mockup. Compatible with the plugin.
- Video walkthroughs exist on the Utopia YouTube channel (introduction talk from UX
  Ghent, Kickstarter walkthrough); a longer written introduction is on Smashing Magazine.
