# Designing the Utopian way

How the designer side of a Utopian project works, so an agent can read a Figma file,
brief a designer, or reason about design decisions consistently with the CSS.

## The mental model

- **Declarative, not device-based.** Utopia describes rules; the browser renders them
  for whatever viewport it has. Design tools are static, so the design is drawn at the
  two *poles*, `@min` and `@max`, and everything in between follows the rules.
  Two artboards, one design: "Don't think of @min and @max as two separate designs but
  as two aspects of the same design."
- **Step 0 is the centre of gravity.** Body text font, weight, size, line height come
  first. Type steps and the space palette are derived from that size at each pole.
- **Intrinsic web design.** Pixel perfection across devices is a myth; the system trades
  per-breakpoint control for guaranteed proportion on any screen, including sizes that
  don't exist yet.

## Fluid type scale (designer view)

1. Define a type scale for the small screen (conservative ratio, e.g. 1.2, because
   horizontal space is scarce).
2. Define a type scale for the large screen (more dramatic, e.g. 1.333).
3. Let the browser interpolate. A heading is "step 4" everywhere, never "32px on
   tablet".
4. Use the calculator's table with an inserted viewport (e.g. 1024) when a mockup for a
   specific device is needed; the graph view shows step 0 and neighbours to explain the
   relationship to stakeholders.
5. Small text: watch negative steps at @max; unhook them or create a small-text scale if
   they get impractically small (see SKILL.md, "Negativity").

## Space matrix / palette (designer view)

1. Start from step 0 at each pole (e.g. 16px → 18px, or 18px → 20px).
2. Multiply with the default increments: 0.25 steps near the base (`3xs, 2xs, xs`),
   whole numbers further out (`xl 3, 2xl 4, 3xl 6`); round to whole px in the design tool.
3. Name everything with t-shirt sizes and use only those names in specs: "gutter is
   S→L", "card padding is S→M", "items inside a card are XS".
4. Individual sizes are only subtly responsive (a 2px flex is "underwhelming"); pairs add
   *attitude*. Typical mapping: sizes for spacing between items inside a component,
   pairs for a component's padding, section spacing, hero slats.
5. Prefer the fewest sizes possible; add one only when nothing existing can be adapted.
   Every space in the design should be nameable.

## Designing the layout grid (from "Designing a Utopian layout grid")

0. Body text size → generate the space palette.
1. Choose the `@min` viewport: as small as practical (around 320px; a small viewport may
   be a window on a big screen). If it works at ~320px it works everywhere.
2. Choose the column count; it stays constant across poles. 12 is practical (divides
   into 2, 3, 4, 6; supports 9+3 sidebars).
3. Choose the `@min` gutter from the palette; step 0 (`s`) is the usual choice.
4. Choose `@max` gutter and column widths from the palette (e.g. gutter `l`, column
   `xl`). The content container's max width is the sum of those tokens, not an arbitrary
   number: `12 × 60 + 13 × 40 = 1240px`.
5. Calculate design-tool viewport widths. If `columns × column + gutters` doesn't equal
   the chosen @min width, round the column *up* and make the artboard that width (an even
   whole-pixel grid beats an exact viewport). The grid calculator offers to round and
   adjust. Either width can be used as the CSS @min; the difference is negligible.
   For the @max artboard, crop close to the container or show how edge-to-edge
   components behave beyond it; developers need to know what happens wider than @max.
6. Iterate: test typefaces and heading sizes at @min (wrapping?), line lengths, how many
   columns primary content spans. Every change on one artboard is mirrored on the other.

## Figma specifics

- Plugin-generated **type styles** come in three families per pole: Strong (headings /
  punctuation), Prose (long-form, relaxed line height), Default (short snippets, captions,
  links). Change the typeface with the type-style updater plugin (blank fields ignored;
  Deep Select to restrict to a column).
- **Variables**: with modes, each step is one variable whose value depends on whether
  the parent artboard is in the `min` or `max` mode. Without modes, separate `@min` and
  `@max` variables (collections "Utopian size", "Space @min", "Space @max").
- **Grid areas** (half, third, quarter) are provided as variables to size components at
  systematic widths.
- **Kickstarter** file: components wired to both modes; prose flow = S between items;
  components may add their own breathing room above/below.
- Re-running the plugin updates variables; some numeric Figma inputs still cannot take
  variables and must be updated by hand.

## Handing over to development

Give developers: the calculator URL(s) (or the `@link` comment), the step → element
mapping (e.g. `h1: step 5 Strong`), the space name for every gap (`gutter: s-l`,
`card padding: s-m`, `flow: s`), and the two artboards. With that, one large-screen
design file is usually enough; the developer chooses how components breathe in between
using the shared palette.
