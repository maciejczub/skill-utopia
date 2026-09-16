#!/usr/bin/env python3
"""
Utopia fluid type / space / grid / clamp generator.

A dependency-free port of the calculations behind https://utopia.fyi
(utopia-core). Output matches the calculators' "CSS" tab.

Usage examples:

  # Single fluid value (16px -> 48px between 320px and 1240px)
  utopia.py clamp --min-width 320 --max-width 1240 16 48

  # Several clamps as custom properties
  utopia.py clamps --min-width 320 --max-width 1240 16-48 24-64 --prefix space

  # Fluid type scale (utopia.fyi defaults)
  utopia.py type --min-width 360 --min-font 18 --min-scale 1.2 \
                 --max-width 1240 --max-font 20 --max-scale 1.25 \
                 --positive 5 --negative 2

  # Fluid space palette + pairs
  utopia.py space --min-width 360 --max-width 1240 --min-size 18 --max-size 20 \
                  --negative 0.75,0.5,0.25 --positive 1.5,2,3,4,6 --pairs s-l

  # Fluid grid foundations (values taken from the space palette)
  utopia.py grid --min-width 360 --max-width 1240 --min-size 18 --max-size 20 \
                 --gutter s-l --column xl --columns 12

  # Everything at once, from a utopia.fyi calculator URL (the @link comment)
  utopia.py from-url "https://utopia.fyi/type/calculator?c=360,18,1.2,1240,20,1.25,5,2,&s=0.75|0.5|0.25,1.5|2|3|4|6,s-l&g=s,l,xl,12"

  # Container-relative tokens pinned to one wrapper (cqi + @property), see references/css-patterns.md
  utopia.py type --min-width 324 --max-width 1160 --register --container .u-container

Add --format json to any command for machine-readable output, --format table
for px values at @min / @max (and --at WIDTH for an intermediate viewport).
"""

import argparse
import json
import math
import sys
from urllib.parse import urlparse, unquote

RELATIVE_UNITS = {"viewport": "vi", "viewport-width": "vw", "container": "cqi"}
SCALE_NAMES = {
    1.067: "Minor Second", 1.125: "Major Second", 1.2: "Minor Third",
    1.25: "Major Third", 1.333: "Perfect Fourth", 1.414: "Augmented Fourth",
    1.5: "Perfect Fifth", 1.618: "Golden Ratio", 1.667: "Major Sixth",
    1.778: "Minor Seventh", 1.875: "Major Seventh", 2: "Octave",
}


def js_round(n):
    """Math.round() semantics (half away from zero for positives), not banker's."""
    return math.floor(n + 0.5)


def r4(n):
    """Round to 4 decimals like utopia-core, and print without trailing zeros."""
    v = round(n + sys.float_info.epsilon, 4)
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


# ---------------------------------------------------------------- clamp ----

def calculate_clamp(min_size, max_size, min_width, max_width,
                    use_px=False, relative_to="viewport-width"):
    """Return a CSS clamp() string. Sizes and widths are in px.

    slope        = (maxSize - minSize) / (maxWidth - minWidth)
    intersection = -minWidth * slope + minSize
    clamp(min, intersection + slope*100 * unit, max)
    Negative slopes (minSize > maxSize) are allowed: clamp() bounds are sorted.
    """
    div = 1 if use_px else 16
    unit = "px" if use_px else "rem"
    rel = RELATIVE_UNITS.get(relative_to, "vi")
    lo, hi = sorted((min_size, max_size))
    slope = ((max_size / div) - (min_size / div)) / ((max_width / div) - (min_width / div))
    intersection = (-1 * (min_width / div)) * slope + (min_size / div)
    return (f"clamp({r4(lo / div)}{unit}, {r4(intersection)}{unit} + "
            f"{r4(slope * 100)}{rel}, {r4(hi / div)}{unit})")


def value_at(min_size, max_size, min_width, max_width, width):
    """Size (px) rendered at a given viewport width, honouring the clamp."""
    if max_width == min_width:
        return min_size
    t = (width - min_width) / (max_width - min_width)
    t = min(1, max(0, t))
    return min_size + (max_size - min_size) * t


# ----------------------------------------------------------------- WCAG ----

def check_wcag(min_size, max_size, min_width, max_width):
    """WCAG SC 1.4.4 check ported from utopia-core (thanks to Maxwell Barvian).

    Returns (from, to) viewport range (px) where the fluid value cannot be
    zoomed to 200% in Chrome/Firefox at 500% browser zoom, or None if OK.
    """
    if min_width > max_width:
        min_width, max_width = max_width, min_width
        min_size, max_size = max_size, min_size
    slope = (max_size - min_size) / (max_width - min_width)
    if slope == 0:
        return None
    intercept = min_size - (min_width * slope)
    lh = (5 * min_size - 2 * intercept) / (2 * slope)
    rh = (5 * intercept - 2 * max_size) / (-1 * slope)
    lh2 = 3 * intercept / slope
    fail = []
    if max_width < 5 * min_width:
        if min_width < lh < max_width:
            fail += [max(lh, min_width), max_width]
        if 5 * min_size < 2 * max_size:
            fail += [max_width, 5 * min_width]
        if 5 * min_width < rh < 5 * max_width:
            fail += [5 * min_width, min(rh, 5 * max_width)]
    else:
        if min_width < lh < 5 * min_width:
            fail += [max(lh, min_width), 5 * min_width]
        if 5 * min_width < lh2 < max_width:
            fail += [max(lh2, 5 * min_width), max_width]
        if max_width < rh < 5 * max_width:
            fail += [max_width, min(rh, 5 * max_width)]
    if not fail:
        return None
    lo, hi = fail[0], fail[-1]
    if abs(hi - lo) < 0.1:
        return None
    return (round(lo), round(hi))


# ----------------------------------------------------------------- type ----

def type_label(step, style="utopia"):
    if style == "utopia":
        return str(step)
    if step < -2:
        return f"{-1 * (step + 1)}xs"
    if step == -2:
        return "xs"
    if style == "tailwind":
        return {-1: "sm", 0: "base", 1: "lg"}.get(step) or (
            "xl" if step == 2 else f"{step - 1}xl")
    if style == "tshirt":
        return {-1: "s", 0: "m", 1: "l"}.get(step) or (
            "xl" if step == 2 else f"{step - 1}xl")
    return str(step)


def calculate_type_scale(min_width, max_width, min_font, max_font,
                         min_scale, max_scale, positive=5, negative=2,
                         relative_to="viewport-width", label_style="utopia"):
    steps = []
    for step in range(-negative, positive + 1):
        lo = min_font * (min_scale ** step)
        hi = max_font * (max_scale ** step)
        steps.append({
            "step": step,
            "label": type_label(step, label_style),
            "minFontSize": round(lo, 4),
            "maxFontSize": round(hi, 4),
            "clamp": calculate_clamp(lo, hi, min_width, max_width, False, relative_to),
            "wcagViolation": check_wcag(lo, hi, min_width, max_width),
            "shrinks": hi < lo,
        })
    return steps


# ---------------------------------------------------------------- space ----

def space_label(step):
    if step == 0:
        return "s"
    if step == 1:
        return "m"
    if step == 2:
        return "l"
    if step == 3:
        return "xl"
    if step > 3:
        return f"{step - 2}xl"
    if step == -1:
        return "xs"
    return f"{abs(step)}xs"


def calculate_space_scale(min_width, max_width, min_size, max_size,
                          negative=(0.75, 0.5, 0.25), positive=(1.5, 2, 3, 4, 6),
                          custom=("s-l",), all_pairs=False,
                          relative_to="viewport-width"):
    """Sizes are rounded to whole px (as utopia-core does) before clamping."""
    def size(mult, step):
        lo = js_round(min_size * mult)
        hi = js_round(max_size * mult)
        return {
            "label": space_label(step), "multiplier": mult,
            "minSize": lo, "maxSize": hi,
            "clamp": calculate_clamp(lo, hi, min_width, max_width, False, relative_to),
            "clampPx": calculate_clamp(lo, hi, min_width, max_width, True, relative_to),
        }

    def pair(a, b):
        return {
            "label": f"{a['label']}-{b['label']}",
            "minSize": a["minSize"], "maxSize": b["maxSize"],
            "clamp": calculate_clamp(a["minSize"], b["maxSize"], min_width, max_width, False, relative_to),
            "clampPx": calculate_clamp(a["minSize"], b["maxSize"], min_width, max_width, True, relative_to),
        }

    negs = sorted(negative, reverse=True)   # 0.75, 0.5, 0.25 -> xs, 2xs, 3xs
    poss = sorted(positive)                 # 1.5, 2, 3 ... -> m, l, xl ...
    sizes = ([size(m, -(i + 1)) for i, m in enumerate(negs)][::-1]
             + [size(1, 0)]
             + [size(m, i + 1) for i, m in enumerate(poss)])
    by_label = {s["label"]: s for s in sizes}
    one_up = [pair(sizes[i], sizes[i + 1]) for i in range(len(sizes) - 1)]
    custom_pairs = []
    for c in custom:
        parts = c.split("-")
        if len(parts) == 2 and parts[0] in by_label and parts[1] in by_label:
            custom_pairs.append(pair(by_label[parts[0]], by_label[parts[1]]))
    every = []
    if all_pairs:
        for a in sizes:
            for b in sizes:
                if a is not b:
                    every.append(pair(a, b))
    return {"sizes": sizes, "oneUpPairs": one_up, "customPairs": custom_pairs,
            "allPairs": every}


# ----------------------------------------------------------------- grid ----

def calculate_grid(space, gutter="s-l", column="xl", columns=12):
    """Grid max width = columns * column@max + (columns + 1) * gutter@max.

    `gutter` is "min-max" space labels (e.g. s-l) or a single label (s).
    `column` is the space label used for the column width @max.
    """
    by_label = {s["label"]: s for s in space["sizes"]}
    g = gutter.split("-")
    g_min, g_max = (g[0], g[-1])
    for label in (g_min, g_max, column):
        if label not in by_label:
            sys.exit(f"grid: space size '{label}' does not exist in this palette "
                     f"(available: {', '.join(by_label)}). Adjust --gutter/--column or the multipliers.")
    gutter_min = by_label[g_min]["minSize"]
    gutter_max = by_label[g_max]["maxSize"]
    col_max = by_label[column]["maxSize"]
    max_width = columns * col_max + (columns + 1) * gutter_max
    gutter_label = f"{g_min}-{g_max}" if g_min != g_max else g_min
    gutter_clamp = calculate_clamp(gutter_min, gutter_max,
                                   space["_minWidth"], space["_maxWidth"])
    return {
        "columns": columns, "gutterLabel": gutter_label,
        "gutterMin": gutter_min, "gutterMax": gutter_max,
        "columnMax": col_max, "maxWidthPx": max_width,
        "maxWidthRem": round(max_width / 16, 4),
        "gutterClamp": gutter_clamp,
        # Column width @min, useful for design-tool artboards
        "columnMin": (space["_minWidth"] - (columns + 1) * gutter_min) / columns,
    }


# ------------------------------------------------------------- URL parse ----

def parse_url(url):
    """Parse a utopia.fyi calculator URL (?c=...&s=...&g=... or ?a=...)."""
    q = urlparse(url).query or url.lstrip("?")
    parts = q.split("&")
    cfg = dict(minWidth=360, minFontSize=18, minScale=1.2, maxWidth=1240,
               maxFontSize=20, maxScale=1.25, positiveSteps=5, negativeSteps=2,
               viewports=[], negativeSizes=[0.75, 0.5, 0.25],
               positiveSizes=[1.5, 2, 3, 4, 6], customSizes=["s-l"],
               minGridGutter="s", maxGridGutter="l", maxGridColumn="xl",
               maxGridColumnCount=12)

    def pick(arr, i, default, fn=float):
        return fn(arr[i]) if i < len(arr) and arr[i] != "" else default

    for p in parts:
        if p.startswith("c="):
            c = unquote(p[2:]).split(",")
            cfg.update(minWidth=pick(c, 0, 360), minFontSize=pick(c, 1, 18),
                       minScale=pick(c, 2, 1.2), maxWidth=pick(c, 3, 1240),
                       maxFontSize=pick(c, 4, 20), maxScale=pick(c, 5, 1.25),
                       positiveSteps=int(pick(c, 6, 5)), negativeSteps=int(pick(c, 7, 2)),
                       viewports=[float(v) for v in pick(c, 8, "", str).split("-") if v])
        elif p.startswith("a="):
            a = unquote(p[2:]).split(",")
            cfg.update(minWidth=pick(a, 0, 360), maxWidth=pick(a, 1, 1240))
        elif p.startswith("s="):
            s = unquote(p[2:]).split(",")
            cfg.update(
                negativeSizes=[float(v) for v in pick(s, 0, "0.75|0.5|0.25", str).split("|") if v],
                positiveSizes=[float(v) for v in pick(s, 1, "1.5|2|3|4|6", str).split("|") if v],
                customSizes=[v.strip() for v in pick(s, 2, "s-l", str).split("|") if v.strip()])
        elif p.startswith("g="):
            g = unquote(p[2:]).split(",")
            cfg.update(minGridGutter=pick(g, 0, "s", str), maxGridGutter=pick(g, 1, "l", str),
                       maxGridColumn=pick(g, 2, "xl", str), maxGridColumnCount=int(pick(g, 3, 12)))
    return cfg


def build_url(cfg):
    c = [cfg["minWidth"], cfg["minFontSize"], cfg["minScale"], cfg["maxWidth"],
         cfg["maxFontSize"], cfg["maxScale"], cfg["positiveSteps"], cfg["negativeSteps"],
         "-".join(str(v) for v in cfg.get("viewports", []))]
    s = ["|".join(num(v) for v in cfg["negativeSizes"]),
         "|".join(num(v) for v in cfg["positiveSizes"]),
         "|".join(cfg["customSizes"])]
    g = [cfg["minGridGutter"], cfg["maxGridGutter"], cfg["maxGridColumn"], cfg["maxGridColumnCount"]]
    return ("https://utopia.fyi/type/calculator?c=" + ",".join(num(v) for v in c)
            + "&s=" + ",".join(s) + "&g=" + ",".join(num(v) for v in g))


def num(v):
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


# --------------------------------------------------------------- output ----

def css_type(steps, prefix="step", link=None):
    out = []
    if link:
        out.append(f"/* @link {link} */\n")
    out.append(":root {")
    for s in steps:
        out.append(f"  --{prefix}-{s['label']}: {s['clamp']};")
    out.append("}")
    shrink = [s for s in steps if s["shrinks"]]
    warn = [s for s in steps if s["wcagViolation"]]
    if shrink or warn:
        out.append("")
        for s in shrink:
            out.append(f"/* Note: --{prefix}-{s['label']} is smaller @max ({s['maxFontSize']}px) than @min "
                       f"({s['minFontSize']}px). Consider unhooking small text from the scale. */")
        for s in warn:
            f, t = s["wcagViolation"]
            out.append(f"/* WCAG 1.4.4 warning: --{prefix}-{s['label']} cannot be zoomed to 200% "
                       f"between {f}px and {t}px viewports. Reduce the slope (min/max size ratio). */")
    return "\n".join(out)


def css_space(space, prefix="space", use_px=False, link=None, all_pairs=False):
    key = "clampPx" if use_px else "clamp"
    out = []
    if link:
        out.append(f"/* @link {link} */\n")
    out.append(":root {")
    for s in space["sizes"]:
        out.append(f"  --{prefix}-{s['label']}: {s[key]};")
    if all_pairs and space["allPairs"]:
        out.append("\n  /* All pairs */")
        for s in space["allPairs"]:
            out.append(f"  --{prefix}-{s['label']}: {s[key]};")
    else:
        out.append("\n  /* One-up pairs */")
        for s in space["oneUpPairs"]:
            out.append(f"  --{prefix}-{s['label']}: {s[key]};")
        if space["customPairs"]:
            out.append("\n  /* Custom pairs */")
            for s in space["customPairs"]:
                out.append(f"  --{prefix}-{s['label']}: {s[key]};")
    out.append("}")
    return "\n".join(out)


def css_grid(grid, prefix="space", link=None):
    out = []
    if link:
        out.append(f"/* @link {link} */\n")
    out += [
        ":root {",
        f"  --grid-max-width: {grid['maxWidthRem']:.2f}rem;",
        f"  --grid-gutter: var(--{prefix}-{grid['gutterLabel']}, {grid['gutterClamp']});",
        f"  --grid-columns: {grid['columns']};",
        "}",
        "",
        ".u-container {",
        "  max-width: var(--grid-max-width);",
        "  padding-inline: var(--grid-gutter);",
        "  margin-inline: auto;",
        "}",
        "",
        ".u-grid {",
        "  display: grid;",
        "  gap: var(--grid-gutter);",
        "}",
    ]
    return "\n".join(out)


def registered_tokens(steps=None, space=None, clamps=None, type_prefix="step", space_prefix="space", use_px=False):
    tokens = []
    for st in steps or []:
        tokens.append({"name": f"--{type_prefix}-{st['label']}", "clamp": st["clamp"], "minPx": st["minFontSize"]})
    if space:
        key = "clampPx" if use_px else "clamp"
        for sz in space["sizes"] + space["oneUpPairs"] + space["customPairs"]:
            tokens.append({"name": f"--{space_prefix}-{sz['label']}", "clamp": sz[key], "minPx": sz["minSize"]})
    for c in clamps or []:
        tokens.append({"name": f"--{space_prefix}-{c['label']}", "clamp": c["clamp"], "minPx": c["minPx"]})
    return tokens


def css_registered(tokens, container=".u-container", link=None):
    """Container-relative tokens anchored to ONE query container via @property.

    tokens: list of {"name": "--step-2", "clamp": "clamp(... cqi ...)", "minPx": 25.92}
    Technique: Kevin Powell, "Fixing fluid typography" (2026), after Ana Tudor.
    A registered <length> custom property is computed where it is declared and
    inherited as an absolute length, so declaring it on the container's children
    pins the cqi units to that container even inside nested query containers.
    """
    out = []
    if link:
        out.append(f"/* @link {link} */\n")
    out += [
        "/* Container-relative tokens (cqi) anchored to one query container.",
        f"   {container} must be a query container; cqi measures its CONTENT box,",
        "   so @min/@max must be the container's content widths, not the viewport.",
        "   initial-value must be px: rem/em make browsers drop the whole @property. */",
        "",
    ]
    for t in tokens:
        out.append(f"@property {t['name']} {{ syntax: \"<length>\"; initial-value: {r4(t['minPx'])}px; inherits: true; }}")
    out += ["", ":root {", "  /* Unregistered copies keep the raw clamp() and re-evaluate wherever they are assigned */"]
    for t in tokens:
        out.append(f"  {t['name']}-reset: {t['clamp']};")
    out.append("")
    out.append("  /* Fallback outside any query container: cqi resolves against the small viewport */")
    for t in tokens:
        out.append(f"  {t['name']}: var({t['name']}-reset);")
    out += ["}", "", f"{container} {{", "  container-type: inline-size;", "}", "",
            "/* Declared on the container's CHILDREN: an element is never its own query container.",
            f"   Computed once against {container}, then inherited as a length by every descendant,",
            "   regardless of nested containers (cards, sidebars) on the way. */",
            f"{container} > * {{"]
    for t in tokens:
        out.append(f"  {t['name']}: var({t['name']}-reset);")
    out += ["}", "",
            "/* To re-evaluate a token against a nested container, assign the -reset copy on ITS children:",
            f"   .card {{ container-type: inline-size; }}  .card > * {{ {tokens[0]['name']}: var({tokens[0]['name']}-reset); }} */"]
    return "\n".join(out)


def table(rows, min_width, max_width, at=None):
    hdr = ["label", "@min", "@max"] + ([f"@{num(at)}"] if at else [])
    lines = [" | ".join(hdr)]
    for r in rows:
        lo, hi = r.get("minFontSize", r.get("minSize")), r.get("maxFontSize", r.get("maxSize"))
        cells = [r["label"], f"{lo:.2f}px", f"{hi:.2f}px"]
        if at:
            cells.append(f"{value_at(lo, hi, min_width, max_width, at):.2f}px")
        if r.get("wcagViolation"):
            cells.append(f"WCAG 1.4.4 fails {r['wcagViolation'][0]}-{r['wcagViolation'][1]}px")
        lines.append(" | ".join(cells))
    return "\n".join(lines)


# ----------------------------------------------------------------- CLI ----

def floats(s):
    return [float(v) for v in s.split(",") if v.strip()]


def add_register(p):
    p.add_argument("--register", action="store_true",
                   help="container-relative tokens anchored to one container via @property (implies cqi)")
    p.add_argument("--container", default=".u-container",
                   help="query container selector for --register (default .u-container)")


def add_widths(p):
    p.add_argument("--min-width", type=float, default=360, help="min viewport px (default 360)")
    p.add_argument("--max-width", type=float, default=1240, help="max viewport px (default 1240)")
    p.add_argument("--relative-to", choices=list(RELATIVE_UNITS), default="viewport-width",
                   help="vw (default, matches utopia.fyi), vi (utopia-core default) or cqi")
    p.add_argument("--format", choices=["css", "json", "table"], default="css")
    p.add_argument("--at", type=float, help="viewport px for an extra column in table output")


def add_space_args(p):
    p.add_argument("--min-size", type=float, default=18, help="base (S / step 0) px @min")
    p.add_argument("--max-size", type=float, default=20, help="base (S / step 0) px @max")
    p.add_argument("--negative", type=floats, default=[0.75, 0.5, 0.25],
                   help="multipliers below S, comma separated (default 0.75,0.5,0.25)")
    p.add_argument("--positive", type=floats, default=[1.5, 2, 3, 4, 6],
                   help="multipliers above S, comma separated (default 1.5,2,3,4,6)")
    p.add_argument("--pairs", nargs="*", default=["s-l"], help="custom pairs, e.g. s-l 2xs-xl")
    p.add_argument("--all-pairs", action="store_true", help="emit every size pair")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("clamp", help="single clamp() value")
    add_widths(p)
    p.add_argument("min_size", type=float)
    p.add_argument("max_size", type=float)
    p.add_argument("--px", action="store_true", help="output px instead of rem")

    p = sub.add_parser("clamps", help="several clamp() custom properties")
    add_widths(p)
    p.add_argument("pairs", nargs="+", help="min-max px pairs, e.g. 16-48 40-18")
    p.add_argument("--px", action="store_true")
    p.add_argument("--prefix", default="space")
    add_register(p)

    p = sub.add_parser("type", help="fluid type scale")
    add_widths(p)
    p.add_argument("--min-font", type=float, default=18)
    p.add_argument("--max-font", type=float, default=20)
    p.add_argument("--min-scale", type=float, default=1.2)
    p.add_argument("--max-scale", type=float, default=1.25)
    p.add_argument("--positive", type=int, default=5)
    p.add_argument("--negative", type=int, default=2)
    p.add_argument("--prefix", default="step")
    p.add_argument("--label-style", choices=["utopia", "tailwind", "tshirt"], default="utopia")
    add_register(p)

    p = sub.add_parser("space", help="fluid space palette and pairs")
    add_widths(p)
    add_space_args(p)
    p.add_argument("--px", action="store_true", help="px output (detach from text zoom)")
    p.add_argument("--prefix", default="space")
    add_register(p)

    p = sub.add_parser("grid", help="fluid grid foundations from the space palette")
    add_widths(p)
    add_space_args(p)
    p.add_argument("--gutter", default="s-l", help="gutter space labels @min-@max (default s-l)")
    p.add_argument("--column", default="xl", help="column width label @max (default xl)")
    p.add_argument("--columns", type=int, default=12)
    p.add_argument("--prefix", default="space")

    p = sub.add_parser("from-url", help="type + space + grid CSS from a utopia.fyi URL")
    p.add_argument("url")
    p.add_argument("--format", choices=["css", "json", "table"], default="css")
    p.add_argument("--relative-to", choices=list(RELATIVE_UNITS), default="viewport-width")
    p.add_argument("--at", type=float)
    add_register(p)

    a = ap.parse_args(argv)
    if getattr(a, "register", False):
        a.relative_to = "container"

    if a.cmd == "clamp":
        print(calculate_clamp(a.min_size, a.max_size, a.min_width, a.max_width, a.px, a.relative_to))
        return

    if a.cmd == "clamps":
        rows = []
        for pr in a.pairs:
            lo, hi = (float(v) for v in pr.split("-"))
            rows.append({"label": f"{num(lo)}-{num(hi)}", "minPx": lo,
                         "clamp": calculate_clamp(lo, hi, a.min_width, a.max_width, a.px, a.relative_to)})
        if a.format == "json":
            print(json.dumps(rows, indent=2))
        elif a.register:
            print(css_registered(registered_tokens(clamps=rows, space_prefix=a.prefix), a.container))
        else:
            print(":root {")
            for r in rows:
                print(f"  --{a.prefix}-{r['label']}: {r['clamp']};")
            print("}")
        return

    if a.cmd == "type":
        steps = calculate_type_scale(a.min_width, a.max_width, a.min_font, a.max_font,
                                     a.min_scale, a.max_scale, a.positive, a.negative,
                                     a.relative_to, a.label_style)
        link = build_url(dict(minWidth=a.min_width, minFontSize=a.min_font, minScale=a.min_scale,
                              maxWidth=a.max_width, maxFontSize=a.max_font, maxScale=a.max_scale,
                              positiveSteps=a.positive, negativeSteps=a.negative,
                              negativeSizes=[0.75, 0.5, 0.25], positiveSizes=[1.5, 2, 3, 4, 6],
                              customSizes=["s-l"], minGridGutter="s", maxGridGutter="l",
                              maxGridColumn="xl", maxGridColumnCount=12))
        if a.format == "json":
            print(json.dumps(steps, indent=2))
        elif a.format == "table":
            print(table(steps, a.min_width, a.max_width, a.at))
        elif a.register:
            print(css_registered(registered_tokens(steps=steps, type_prefix=a.prefix), a.container, link))
        else:
            print(css_type(steps, a.prefix, link))
        return

    if a.cmd in ("space", "grid"):
        space = calculate_space_scale(a.min_width, a.max_width, a.min_size, a.max_size,
                                      a.negative, a.positive, a.pairs, a.all_pairs, a.relative_to)
        space["_minWidth"], space["_maxWidth"] = a.min_width, a.max_width
        if a.cmd == "space":
            if a.format == "json":
                print(json.dumps({k: v for k, v in space.items() if not k.startswith("_")}, indent=2))
            elif a.format == "table":
                print(table(space["sizes"] + space["oneUpPairs"] + space["customPairs"],
                            a.min_width, a.max_width, a.at))
            elif a.register:
                print(css_registered(registered_tokens(space=space, space_prefix=a.prefix, use_px=a.px), a.container))
            else:
                print(css_space(space, a.prefix, a.px, None, a.all_pairs))
        else:
            grid = calculate_grid(space, a.gutter, a.column, a.columns)
            if a.format == "json":
                print(json.dumps(grid, indent=2))
            elif a.format == "table":
                print(f"columns: {grid['columns']}\ngutter: {grid['gutterMin']}px -> {grid['gutterMax']}px "
                      f"({grid['gutterLabel']})\ncolumn: {grid['columnMin']:.2f}px @min -> {grid['columnMax']}px @max"
                      f"\nmax width: {grid['maxWidthPx']}px ({grid['maxWidthRem']}rem)")
            else:
                print(css_grid(grid, a.prefix))
        return

    if a.cmd == "from-url":
        cfg = parse_url(a.url)
        steps = calculate_type_scale(cfg["minWidth"], cfg["maxWidth"], cfg["minFontSize"],
                                     cfg["maxFontSize"], cfg["minScale"], cfg["maxScale"],
                                     cfg["positiveSteps"], cfg["negativeSteps"], a.relative_to)
        space = calculate_space_scale(cfg["minWidth"], cfg["maxWidth"], cfg["minFontSize"],
                                      cfg["maxFontSize"], cfg["negativeSizes"], cfg["positiveSizes"],
                                      cfg["customSizes"], False, a.relative_to)
        space["_minWidth"], space["_maxWidth"] = cfg["minWidth"], cfg["maxWidth"]
        gutter = f"{cfg['minGridGutter']}-{cfg['maxGridGutter']}"
        grid = calculate_grid(space, gutter, cfg["maxGridColumn"], cfg["maxGridColumnCount"])
        link = build_url(cfg)
        if a.format == "json":
            print(json.dumps({"config": cfg, "type": steps,
                              "space": {k: v for k, v in space.items() if not k.startswith("_")},
                              "grid": grid}, indent=2))
        elif a.format == "table":
            print("TYPE\n" + table(steps, cfg["minWidth"], cfg["maxWidth"], a.at))
            print("\nSPACE\n" + table(space["sizes"] + space["oneUpPairs"] + space["customPairs"],
                                      cfg["minWidth"], cfg["maxWidth"], a.at))
            print(f"\nGRID\ncolumns: {grid['columns']}, gutter {grid['gutterLabel']}, "
                  f"max width {grid['maxWidthPx']}px ({grid['maxWidthRem']}rem)")
        elif a.register:
            print(css_registered(registered_tokens(steps=steps, space=space), a.container, link))
            print()
            print(css_grid(grid, "space"))
        else:
            print(css_type(steps, "step", link))
            print()
            print(css_space(space, "space"))
            print()
            print(css_grid(grid, "space"))
        return


if __name__ == "__main__":
    main()
