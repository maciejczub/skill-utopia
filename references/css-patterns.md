# CSS patterns for Utopian projects

Recipes that use the generated tokens. Assumes `--step-*`, `--space-*` and
`--grid-*` are defined on `:root` (with the `@link` comment).

## Minimal setup

```css
/* @link https://utopia.fyi/type/calculator?c=360,18,1.2,1240,20,1.25,5,2,&s=0.75|0.5|0.25,1.5|2|3|4|6,s-l&g=s,l,xl,12 */
:root {
  --step--2: clamp(0.7813rem, 0.7736rem + 0.0341vw, 0.8rem);
  --step--1: clamp(0.9375rem, 0.9119rem + 0.1136vw, 1rem);
  --step-0: clamp(1.125rem, 1.0739rem + 0.2273vw, 1.25rem);
  --step-1: clamp(1.35rem, 1.2631rem + 0.3864vw, 1.5625rem);
  --step-2: clamp(1.62rem, 1.4837rem + 0.6057vw, 1.9531rem);
  --step-3: clamp(1.944rem, 1.7405rem + 0.9044vw, 2.4414rem);
  --step-4: clamp(2.3328rem, 2.0387rem + 1.3072vw, 3.0518rem);
  --step-5: clamp(2.7994rem, 2.384rem + 1.8461vw, 3.8147rem);
  /* --space-* from the space calculator, --grid-* from the grid calculator */
}

body { font-size: var(--step-0); line-height: 1.5; }
h1 { font-size: var(--step-5); line-height: 1.1; }
h2 { font-size: var(--step-3); }
h3 { font-size: var(--step-2); }
small, figcaption { font-size: var(--step--1); }
```

That is the whole "fluid responsive typography" demo: no media queries. Because the
steps are abstracted from elements, several elements can share a step and a design can
say "H2s are always step 3".

## Semantic aliases

Map tokens to roles once so components never reference raw steps:

```css
:root {
  --text-body: var(--step-0);
  --text-lead: var(--step-1);
  --text-heading-1: var(--step-5);
  --gutter: var(--space-s-l);
  --section-space: var(--space-xl-3xl);
  --flow-space: var(--space-s);
}
```

## Space: sizes vs pairs

```css
.c-card {
  padding: var(--space-s-m);            /* pair: outer padding flexes 18 → 30px */
  border-radius: var(--space-2xs);
}
.c-card > * + * {
  margin-block-start: var(--space-xs);  /* size: internal rhythm 14 → 15px */
}
.c-hero {
  padding-block: var(--space-2xl-3xl);  /* one-up pair, 72 → 120px */
  padding-inline: var(--grid-gutter);
}
.c-badge { padding: var(--space-3xs) var(--space-2xs); }
.c-tight-on-desktop { gap: var(--space-l-s); }   /* reverse custom pair: declare it in the calculator */
```

## Flow (vertical rhythm) utility

```css
.u-flow > * + * { margin-block-start: var(--flow-space, var(--space-s)); }
.u-flow--xs  { --flow-space: var(--space-xs); }
.u-flow--l   { --flow-space: var(--space-l); }
.u-flow--s-m { --flow-space: var(--space-s-m); }
```

```html
<article class="c-card u-flow">
  <img src="" alt="" />
  <h2>Card title</h2>
  <p>Card description</p>
</article>
```

Kickstarter convention for prose: the prose container flows with **S** between all
items, and individual components may add their own "breathing room" above and below
(e.g. a figure adds `--space-m` block margins) rather than changing the flow value.

## Grid

```css
.u-container {
  max-width: var(--grid-max-width);
  padding-inline: var(--grid-gutter);
  margin-inline: auto;
}
.u-grid {
  display: grid;
  gap: var(--grid-gutter);
}

/* Build on the foundations; Utopia does not prescribe a column system */
.u-grid--12 { grid-template-columns: repeat(var(--grid-columns), minmax(0, 1fr)); }
.u-grid--auto { grid-template-columns: repeat(auto-fill, minmax(min(100%, 20rem), 1fr)); }
.l-sidebar { display: grid; grid-template-columns: minmax(0, 9fr) minmax(0, 3fr); gap: var(--grid-gutter); }

/* Common grid areas (the Figma plugin exposes the same: half, third, quarter) */
/* (grid-column needs integers, so spell them out for your column count) */
.u-span-half    { grid-column: span 6; }
.u-span-third   { grid-column: span 4; }
.u-span-quarter { grid-column: span 3; }

/* Full-bleed sections keep the same gutter as the container */
.c-band { padding-inline: var(--grid-gutter); }
```

## Container-relative tokens anchored to one wrapper (`cqi` + `@property`)

Source: Kevin Powell, "Fixing fluid typography" (2026), building on Ana Tudor's
"Using container query units relative to an outer container". Verified in Chromium.

### The three problems

1. **Squishy zone.** A `vi`/`vw` token whose @max lies beyond the wrapper's `max-width`
   keeps growing after the layout stopped (Kevin's demo: `clamp(1rem, 0.5rem + 3cqi,
   3.25rem)` tops out at ~1467px while the wrapper stops at 75rem = 1200px). Utopia's
   defaults avoid it because @max viewport = `--grid-max-width`; several wrappers or a
   mismatched @max bring it back.
2. **`cqi` without a container is `vi`.** Container units fall back to the small
   viewport unless an ancestor has `container-type`.
3. **Nested containers break consistency.** `cqi` resolves against the *nearest
   ancestor* container. Make cards containers (for `@container` layout switches) and
   the same `var(--step-2)` renders a different size in every card.

### The fix

A custom property registered with `syntax: "<length>"` is computed where it is
declared and inherited as an absolute length (unregistered ones inherit the raw token
stream and resolve at the `var()` site). Declaring the token on the wrapper's children
pins its `cqi` to the wrapper for every descendant.

```css
/* python3 scripts/utopia.py type --min-width 324 --max-width 1160 --register --container .u-container */
@property --step-2 { syntax: "<length>"; initial-value: 25.92px; inherits: true; }

:root {
  --step-2-reset: clamp(1.62rem, 1.4909rem + 0.6376cqi, 1.9531rem); /* unregistered twin: raw clamp() */
  --step-2: var(--step-2-reset);                                     /* fallback: no container → small viewport */
}

.u-container { container-type: inline-size; max-width: 77.5rem; padding-inline: var(--grid-gutter); }
.u-container > * { --step-2: var(--step-2-reset); }   /* computed against .u-container, inherited as px */

.card { container-type: inline-size; }                /* for @container queries; --step-2 unaffected */
.card__body { display: grid; gap: var(--space-s);
  @container (width > 40ch) { grid-template-columns: 5.5rem 1fr; } }

/* Opt back into card-relative sizing for one component: assign the twin on ITS children */
.card--fluid > * { --step-2: var(--step-2-reset); }

h2 { font-size: var(--step-2); }                      /* identical in every card */
```

Measured in Chromium (wrapper content 720px → all three h2 = 28.45px; naive `cqi`
gave 25.92px in the cards; the opt-in card re-evaluates to 25.92px).

### Rules

- `initial-value` **in px**. `1rem` looks harmless but is not computationally
  independent; Chromium and Firefox discard the entire `@property` rule silently and the
  token silently degrades to naive `cqi`. The script uses the token's @min px value.
- Declare on `.wrapper > *`, never on `.wrapper`: an element is never its own query
  container, so a declaration on the wrapper itself would measure the wrapper's ancestor.
  The same applies to the reset: `.card > *`, not `.card`.
- Keep the `:root` fallback; outside any container a registered property would
  otherwise be its `initial-value`.
- `cqi` is 1% of the container's **content box**. Feed the script content widths
  (viewport − 2 × gutter at each pole) or give the container no inline padding.
- Registering ~26 tokens (8 steps, 9 sizes, 9 pairs) is fine; purge unused ones.
- `inherits: true` is what makes the pinned value reach nested components. Naming the
  container (`container: wrapper / inline-size`) is optional for units; don't reuse the
  same name on nested containers if you also write named `@container` queries.
- Accessibility: a container capped in rem behaves like the viewport under text zoom
  until it hits `max-width`; run the WCAG check with the container widths as @min/@max.
- Baseline: `@property` and container units are widely available since 2024.

## Overriding a step systematically

When the largest heading is too big at @min, adjust that one step rather than the
whole scale. With precalculated `clamp()` regenerate the step as a custom clamp:

```bash
python3 scripts/utopia.py clamp --min-width 360 --max-width 1240 44.79 78.83
```

With the tweakable (CSS-locks) output, feed one step's value into another:

```css
--f-7-min: var(--f-5-min);   /* step 7 starts where step 5 starts */
--f-7-min: var(--f-4-max);   /* or at step 4's end point */
```

Either way the rhythm between steps changes for that step; document it.

## Handling small text ("negativity")

```css
/* Option A: unhook small text from the fluid scale */
:root { --text-small: 0.875rem; }
/* Option B: a separate, gentler small-text scale */
:root { --small-1: clamp(0.8125rem, 0.7841rem + 0.1263vw, 0.875rem); }
/* Option C: build the main scale around the smallest text size instead of body copy */
```

## SCSS

```scss
@use 'node_modules/utopia-core-scss/src/utopia' as utopia;

:root {
  @include utopia.generateTypeScale((
    "minWidth": 360, "maxWidth": 1240,
    "minFontSize": 18, "maxFontSize": 20,
    "minTypeScale": 1.2, "maxTypeScale": 1.25,
    "positiveSteps": 5, "negativeSteps": 2,
    "relativeTo": "viewport",      // vi (default) | viewport-width (vw) | container (cqi)
    "prefix": "step-",
  ));
  @include utopia.generateSpaceScale((
    "minWidth": 360, "maxWidth": 1240,
    "minSize": 18, "maxSize": 20,
    "positiveSteps": (1.5, 2, 3, 4, 6),
    "negativeSteps": (0.75, 0.5, 0.25),
    "customSizes": ("s-l", "2xs-xl"),
    "usePx": false,
    "allPairs": false,              // true: every permutation (purge unused!)
  ));
  @include utopia.generateClamp(("minWidth": 360, "maxWidth": 1240, "minSize": 16, "maxSize": 48, "prefix": "measure-"));
}

.c-hero { padding-block: utopia.calculateClamp(("minWidth": 360, "maxWidth": 1240, "minSize": 40, "maxSize": 200)); }
```

## PostCSS

```js
// postcss.config.js
module.exports = { plugins: { 'postcss-utopia': { minWidth: 360, maxWidth: 1240 } } };
```

```css
:root {
  @utopia typeScale({ minFontSize: 18, maxFontSize: 20, minTypeScale: 1.2, maxTypeScale: 1.25, positiveSteps: 5, negativeSteps: 2 });
  @utopia spaceScale({ minSize: 18, maxSize: 20, positiveSteps: [1.5, 2, 3, 4, 6], negativeSteps: [0.75, 0.5, 0.25], customSizes: ['s-l'] });
  @utopia clamps({ pairs: [[16, 40], [24, 64]], prefix: 'fluid' });
}
.c-hero { padding-block: utopia.clamp(40, 200); }          /* readable clamp, compiled to clamp(...) */
.c-note { margin-block-end: utopia.clamp(16, 24, 320, 1080); } /* explicit viewports */
```

## Checklist before shipping

- `@link` comment present above each generated block.
- Only tokens that are used are generated (or unused ones are purged).
- Headings checked at @min for wrapping/overflow; largest steps overridden if needed.
- Small text checked at @max (no shrinking below @min size unless intended).
- Browser zoom 200% tested on body and headings (WCAG 1.4.4).
- Space usage documented: which pair is the gutter, which size is the flow default.
