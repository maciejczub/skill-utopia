# skill-utopia

An [Agent Skill](https://agentskills.io) that teaches AI coding agents (Claude Code and
other SKILL.md-compatible agents) to use the [Utopia](https://utopia.fyi) methodology:
fluid, breakpoint-free responsive typography, spacing and layout grids built on CSS
`clamp()`.

The skill condenses the utopia.fyi Type, Space, Grid and Clamp calculators and the
Utopia blog (2020–2025) into agent-ready instructions, and ships a generator script that
reproduces the calculators' output exactly.

## What's inside

```
SKILL.md                      # the skill: concepts, workflow, patterns, pitfalls (start here)
scripts/utopia.py             # dependency-free Python port of utopia-core (type/space/grid/clamp CLI)
references/formulas.md        # the maths, WCAG 1.4.4 check, calculator URL format, CSS-locks variants
references/css-patterns.md    # CSS/SCSS/PostCSS recipes: tokens, flow, grid, container queries, overrides
references/tooling.md         # utopia-core, utopia-core-scss, postcss-utopia, calculators, Figma plugins
references/design-workflow.md # designer-side process: @min/@max poles, space matrix, grid design, Figma
```

## Install

Claude Code (personal or project scope):

```bash
# personal
git clone https://github.com/maciejczub/skill-utopia ~/.claude/skills/utopia
# project
git clone https://github.com/maciejczub/skill-utopia .claude/skills/utopia
```

Or with the skills CLI:

```bash
npx skills add maciejczub/skill-utopia
```

Any other agent that reads `SKILL.md` frontmatter can point at this directory.

## Use

Ask the agent for fluid type, space or grid work and the skill activates, e.g.:

- "Set up a Utopian type scale, 18→20px body, 360→1240px, minor third to major third."
- "Turn this utopia.fyi link into CSS tokens." (the `@link` comment in existing CSS works too)
- "Give me a fluid padding token from 24px to 80px."
- "Convert these Figma @min/@max artboards into a space palette and grid."

The generator can also be used directly:

```bash
python3 scripts/utopia.py from-url "https://utopia.fyi/type/calculator?c=360,18,1.2,1240,20,1.25,5,2,&s=0.75|0.5|0.25,1.5|2|3|4|6,s-l&g=s,l,xl,12"
python3 scripts/utopia.py type --min-width 360 --min-font 18 --min-scale 1.2 --max-width 1240 --max-font 20 --max-scale 1.25 --positive 5 --negative 2 --format table --at 768
python3 scripts/utopia.py space --min-size 18 --max-size 20 --pairs s-l 2xs-xl
python3 scripts/utopia.py grid --gutter s-l --column xl --columns 12
python3 scripts/utopia.py clamp --min-width 320 --max-width 1240 16 48
```

Run `python3 scripts/utopia.py --help` for all options (`--format json|table`, `--at`,
`--relative-to container`, `--px`, `--all-pairs`, `--label-style tailwind`).

## Coverage

Techniques covered, with their sources on utopia.fyi:

| Technique | Source |
| --- | --- |
| Fluid type scales interpolated between two modular scales | Type calculator; *Designing with fluid type scales*; *CSS-only fluid modular type scales* |
| Precalculated `clamp()` and its accessibility trade-offs | Clamp calculator; *Clamp*; *Clamp calculator* |
| CSS locks with a single shared lock point; fluid custom properties ("hills") | *CSS-only fluid modular type scales*; *Fluid custom properties* |
| Tweakable per-step variables and systematic step overrides | *Utopian CSS generator, an iteration* |
| Negative steps shrinking on large screens | *Dealing with negativity in fluid type scales* |
| Fluid space palette, t-shirt sizes, one-up and custom pairs, flow utility | Space calculator; *Painting with a fluid space palette*; *Designing with a fluid space palette*; *Generate all pair permutations* |
| Fluid grid: gutters and columns from the palette, container max width | Grid calculator; *Designing a Utopian layout grid* |
| WCAG 1.4.4 check for fluid text | `utopia-core` |
| `utopia-core`, `utopia-core-scss`, `postcss-utopia` | *Utopia SCSS library*; *Readable clamp() with PostCSS Utopia* |
| Figma plugins, variables and modes, Kickstarter file | *Getting started with Utopia Figma plugins*; *Figma variables*; *Figma plugin and kickstarter V2*; *Utopian project kickstarter* |
| Type scale graphs and the introduction video | *Type scale graphs*; *A video introduction to Utopia*; *Fluid responsive typography: easy when you know how* |

## Credits

Utopia is the work of [James Gilyead](https://utopia.fyi) and
[Trys Mudford](https://trysmudford.com), supported by Clearleft. This repository only
repackages their published material for agent use; the calculators, libraries and blog
posts remain theirs.
