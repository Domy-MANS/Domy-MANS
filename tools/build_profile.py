"""Generates the header and one animated overview block per project."""
import math
import random
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
(OUT / "assets").mkdir(parents=True, exist_ok=True)

SANS = "'Segoe UI',system-ui,-apple-system,'PingFang SC','Microsoft YaHei','Noto Sans CJK SC',sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
BG = "#0b0f17"
PANEL = "#111723"
LINE = "#263041"
TEXT = "#eef2f8"
MUTED = "#9aa7ba"
RED = "#ff5d5d"
GREEN = "#4ade80"
YELLOW = "#ffd23f"
PINK = "#ff7eb6"
BLUE = "#60a5fa"
PURPLE = "#c084fc"
GREY = "#7c889b"

W, H = 1200, 360
PX, PY, PW, PH = 690, 34, 470, 292
STYLE = f"<style>.sans{{font-family:{SANS}}}.mono{{font-family:{MONO}}}</style>"


def anim(attr, dur, values, times, spline=False):
    extra = ""
    if spline:
        extra = ' calcMode="spline" keySplines="' + ";".join([".4 0 .2 1"] * (len(values) - 1)) + '"'
    v = ";".join(str(x) for x in values)
    t = ";".join(f"{x:g}" for x in times)
    return f'<animate attributeName="{attr}" dur="{dur}s" repeatCount="indefinite" values="{v}" keyTimes="{t}"{extra}/>'


def grid(height):
    return "".join(f'<path d="M{x} 0V{height}" stroke="#141b28"/>' for x in range(0, W, 40)) + "".join(
        f'<path d="M0 {y}H{W}" stroke="#141b28"/>' for y in range(0, height, 40)
    )


def status_steps(steps, dur, color):
    out = []
    for label, a, b in steps:
        if a == 0:
            vals, times = [1, 1, 0, 0], [0, b, b + 0.001, 1]
        elif b == 1:
            vals, times = [0, 0, 1, 1], [0, a, a + 0.001, 1]
        else:
            vals, times = [0, 0, 1, 1, 0, 0], [0, a, a + 0.001, b, b + 0.001, 1]
        out.append(
            f'<text x="{PX + 16}" y="{PY + PH - 12}" class="mono" font-size="17" fill="{color}" opacity="0">{label}'
            + anim("opacity", dur, vals, times)
            + "</text>"
        )
    return "".join(out)


def cta_button(right, cy, w, h, size, label):
    x = right - w
    ay = cy
    ax = right - 34
    return (
        f'<rect x="{x}" y="{cy - h / 2}" width="{w}" height="{h}" rx="{h / 2}" fill="{PINK}"/>'
        f'<text x="{x + 22}" y="{cy + size * 0.35:.1f}" class="sans" font-size="{size}" font-weight="600" fill="{BG}">{label}</text>'
        f'<path d="M{ax} {ay + 6}L{ax + 12} {ay - 6}M{ax + 2} {ay - 6}H{ax + 12}V{ay + 4}" fill="none" stroke="{BG}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def timeline(x, height, node_y, accent, year, plays_first):
    """Dashed rail with a node. A light travels up the lower block, then the upper one."""
    dur = 6
    a, b = (0, 0.5) if plays_first else (0.5, 1)
    label = (
        f'<text x="{x - 22}" y="{node_y + 9}" text-anchor="end" class="mono" font-size="24" font-weight="600" fill="#6f7c8f">{year}</text>'
        if year
        else ""
    )
    if plays_first:
        op_vals, op_times = [1, 1, 0, 0], [0, 0.5, 0.501, 1]
        cy_vals, cy_times = [height, 0, 0], [0, 0.5, 1]
    else:
        op_vals, op_times = [0, 0, 1, 1], [0, 0.5, 0.501, 1]
        cy_vals, cy_times = [height, height, 0], [0, 0.5, 1]
    return (
        f'<path d="M{x} 0V{height}" stroke="#6f7c8f" stroke-width="2.5" stroke-dasharray="7 7"/>'
        f'<circle cx="{x}" r="5" fill="#8a97aa" cy="{height}">'
        + anim("cy", dur, cy_vals, cy_times)
        + anim("opacity", dur, op_vals, op_times)
        + "</circle>"
        f'<circle cx="{x}" cy="{node_y}" r="10" fill="none" stroke="{accent}" stroke-width="2">'
        + anim("r", 2.4, [10, 20, 20], [0, 0.7, 1])
        + anim("opacity", 2.4, [0.8, 0, 0], [0, 0.7, 1])
        + "</circle>"
        f'<circle cx="{x}" cy="{node_y}" r="10" fill="{BG}" stroke="{accent}" stroke-width="3"/>'
        f'<circle cx="{x}" cy="{node_y}" r="4" fill="{accent}"/>'
        + label
    )


GUTTER_SHARE, CARD_SHARE = 8, 92  # percent of README width; must match README.md
RAIL_GAP = 16  # rail runs past the card so the space between cards has no link

# GitHub strips image maps, so a card with a button is cut into three rows of separately
# linked images: top, then left / button / right, then the rest. Slice widths are percents
# of README width and must match README.md. Floats are not an option because GitHub pads
# img[align=left|right]. The animated panel stays whole, below the button row, because
# each image runs its own SMIL clock and an animation cut across images would drift apart.
# A row shorter than the 24px text line would leave a gap, which sets the row heights
# and the breakpoint in README.md. Nothing may be drawn across a seam: each slice scales
# and snaps to device pixels on its own, so the two halves of a glyph would not line up.
CTA_SHARES = (74.5, 14.5, 3)  # left of button, button, right of button
MOBILE_CTA_SHARES = (54, 34, 4)
DESKTOP_ROWS = (46, 94)  # y range of the button row; button is 44 tall
MOBILE_ROWS = (56, 116)  # y range of the button row; button is 50 tall
CTA_DROP = 66  # how far the button row pushes the panel and text down on a desktop card


def write_rail(fname, card_w, height, x, node_y, accent, year, plays_first, rows=None):
    gw = round(card_w * GUTTER_SHARE / CARD_SHARE, 2)
    h = height + RAIL_GAP
    if rows:
        body = timeline(x, h, node_y, accent, year, plays_first)
        stem, top, bottom = fname[:-4], rows[0], rows[1]
        tag = "-mobile" if stem.endswith("-mobile") else ""
        stem = stem.removesuffix("-mobile")
        for part, y, part_h in [("top", 0, top), ("mid", top, bottom - top), ("bottom", bottom, h - bottom)]:
            write_crop(f"{stem}-{part}{tag}.svg", 0, y, gw, part_h, body, year or "timeline")
        return
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {gw} {h}" width="{gw}" height="{h}" role="img" aria-label="{year or 'timeline'}">
{STYLE}
{timeline(x, h, node_y, accent, year, plays_first)}
</svg>"""
    (OUT / "assets" / fname).write_text(svg, encoding="utf-8")


def write_crop(fname, x, y, w, h, body, label):
    """One slice of a card: the same drawing seen through a smaller viewBox.

    WebKit rounds an SVG image's height down to whole pixels. With the default
    preserveAspectRatio a short slice then shrinks and leaves bars at its sides, so
    slices stretch to fill their box instead; the distortion is at most one pixel.
    """
    x, y, w, h = round(x, 2), round(y, 2), round(w, 2), round(h, 2)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" preserveAspectRatio="none" width="{w}" height="{h}" role="img" aria-label="{label}">
{STYLE}
{body}
</svg>"""
    (OUT / "assets" / fname).write_text(svg, encoding="utf-8")


def write_cta_card(stem, tag, width, height, rows, shares, static, full, label, cta):
    top, bottom = rows
    unit = width / CARD_SHARE
    left, button = shares[0] * unit, shares[1] * unit
    row_h = bottom - top
    write_crop(f"{stem}-top{tag}.svg", 0, 0, width, top, static, label)
    write_crop(f"{stem}-left{tag}.svg", 0, top, left, row_h, static, label)
    write_crop(f"{stem}-button{tag}.svg", left, top, button, row_h, static, cta)
    write_crop(f"{stem}-right{tag}.svg", left + button, top, width - left - button, row_h, static, label)
    write_crop(f"{stem}-bottom{tag}.svg", 0, bottom, width, height - bottom, full, label)


def block(fname, title, subtitle, desc_lines, chips, panel, accent, label, mobile_lines, period, plays_first=False, cta=None):
    drop = CTA_DROP if cta else 0
    card_h = H + drop
    chip_svg, x = [], 58
    for c in chips:
        w = 10 * len(c) + 28
        chip_svg.append(
            f'<rect x="{x}" y="{276 + drop}" width="{w}" height="36" rx="18" fill="#182130" stroke="{LINE}"/>'
            f'<text x="{x + w / 2}" y="{300 + drop}" text-anchor="middle" class="mono" font-size="16" fill="{TEXT}">{c}</text>'
        )
        x += w + 10
    desc = "".join(
        f'<text x="58" y="{176 + drop + i * 31}" class="sans" font-size="21" fill="{MUTED}">{l}</text>'
        for i, l in enumerate(desc_lines)
    )
    brackets = "".join(
        f'<path d="M{x + 18 * sx} {y}H{x}V{y + 18 * sy}" fill="none" stroke="{accent}" stroke-width="2.5"/>'
        for x, y, sx, sy in [
            (PX, PY, 1, 1), (PX + PW, PY, -1, 1), (PX, PY + PH, 1, -1), (PX + PW, PY + PH, -1, -1),
        ]
    )
    bar_y, title_y, subtitle_y = (30, 86, 124) if cta else (44, 98, 132)
    static = f"""<rect x=".5" y=".5" width="{W - 1}" height="{card_h - 1}" rx="14" fill="{BG}" stroke="{LINE}"/>
<rect x="58" y="{bar_y}" width="52" height="5" rx="2.5" fill="{accent}"/>
<text x="58" y="{title_y}" class="sans" font-size="44" font-weight="700" fill="{TEXT}">{title}</text>
<text x="58" y="{subtitle_y}" class="sans" font-size="21" fill="{accent}">{subtitle}</text>
{cta_button(PX + PW, sum(DESKTOP_ROWS) / 2, 186, 44, 19, cta) if cta else ""}
{desc}
{''.join(chip_svg)}"""
    full = f"""{static}
<g transform="translate(0 {drop})">
<defs><clipPath id="tray"><rect x="{PX}" y="{PY}" width="{PW}" height="{PH}"/></clipPath></defs>
<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" fill="{PANEL}"/>
{panel}
<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" fill="none" stroke="{LINE}"/>
{brackets}
</g>"""
    if cta:
        write_cta_card(fname[:-4], "", W, card_h, DESKTOP_ROWS, CTA_SHARES, static, full, label, cta)
        write_rail(f"timeline-{period}.svg", W, card_h, 82, sum(DESKTOP_ROWS) // 2, accent, period, plays_first, DESKTOP_ROWS)
    else:
        write_crop(fname, 0, 0, W, card_h, full, label)
        write_rail(f"timeline-{period}.svg", W, card_h, 82, 84, accent, period, plays_first)
    mobile_block(fname.replace(".svg", "-mobile.svg"), title, subtitle, mobile_lines, chips, panel, brackets, accent, label, period, plays_first, cta)


def mobile_block(fname, title, subtitle, lines, chips, panel, brackets, accent, label, period, plays_first=False, cta=None):
    mw, scale = 600, 540 / PW
    title_y, subtitle_y, panel_top = (102, 140, 160) if cta else (88, 126, 150)
    panel_h = PH * scale
    desc_top = panel_top + panel_h + 50
    chip_y = desc_top + 36 * (len(lines) - 1) + 28
    mh = round(chip_y + 42 + 30)
    chip_svg, x = [], 30
    for c in chips:
        w = 12 * len(c) + 26
        chip_svg.append(
            f'<rect x="{x}" y="{chip_y:.0f}" width="{w}" height="42" rx="21" fill="#182130" stroke="{LINE}"/>'
            f'<text x="{x + w / 2}" y="{chip_y + 28:.0f}" text-anchor="middle" class="mono" font-size="20" fill="{TEXT}">{c}</text>'
        )
        x += w + 8
    desc = "".join(
        f'<text x="30" y="{desc_top + i * 36:.0f}" class="sans" font-size="25" fill="{MUTED}">{l}</text>'
        for i, l in enumerate(lines)
    )
    static = f"""<rect x=".5" y=".5" width="{mw - 1}" height="{mh - 1}" rx="14" fill="{BG}" stroke="{LINE}"/>
<rect x="30" y="30" width="52" height="5" rx="2.5" fill="{accent}"/>
<text x="94" y="40" class="mono" font-size="21" fill="{MUTED}">{period}</text>
<text x="30" y="{title_y}" class="sans" font-size="44" font-weight="700" fill="{TEXT}">{title}</text>
<text x="30" y="{subtitle_y}" class="sans" font-size="25" fill="{accent}">{subtitle}</text>
{cta_button(570, sum(MOBILE_ROWS) / 2, 214, 50, 23, cta) if cta else ""}"""
    full = f"""<defs><clipPath id="tray"><rect x="{PX}" y="{PY}" width="{PW}" height="{PH}"/></clipPath></defs>
{static}
<g transform="translate(30 {panel_top}) scale({scale:.4f}) translate({-PX} {-PY})">
<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" fill="{PANEL}"/>
{panel}
<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" fill="none" stroke="{LINE}"/>
{brackets}
</g>
{desc}
{''.join(chip_svg)}"""
    if cta:
        write_cta_card(fname[: -len("-mobile.svg")], "-mobile", mw, mh, MOBILE_ROWS, MOBILE_CTA_SHARES, static, full, label, cta)
        write_rail(f"timeline-{period}-mobile.svg", mw, mh, 24, sum(MOBILE_ROWS) // 2, accent, None, plays_first, MOBILE_ROWS)
    else:
        write_crop(fname, 0, 0, mw, mh, full, label)
        write_rail(f"timeline-{period}-mobile.svg", mw, mh, 24, 72, accent, None, plays_first)


def header_mobile():
    mw, h, dur = 600, 300, 9
    lines = "".join(f'<path d="M{x} 0V{h}" stroke="#141b28"/>' for x in range(0, mw, 40)) + "".join(
        f'<path d="M0 {y}H{mw}" stroke="#141b28"/>' for y in range(0, h, 40)
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {mw} {h}" width="{mw}" height="{h}" role="img" aria-label="Domy Yu: machines that see, software that connects.">
{STYLE}
<defs>
<linearGradient id="beam" x1="0" x2="1"><stop offset="0" stop-color="{YELLOW}" stop-opacity="0"/><stop offset=".5" stop-color="{YELLOW}" stop-opacity=".16"/><stop offset="1" stop-color="{YELLOW}" stop-opacity="0"/></linearGradient>
<clipPath id="c"><rect width="{mw}" height="{h}" rx="14"/></clipPath>
</defs>
<g clip-path="url(#c)">
<rect width="{mw}" height="{h}" fill="{BG}"/>
<g>{lines}</g>
<rect x="-200" width="200" height="{h}" fill="url(#beam)"><animateTransform attributeName="transform" type="translate" dur="{dur}s" repeatCount="indefinite" values="0 0;{mw + 200} 0;{mw + 200} 0" keyTimes="0;0.6;1"/></rect>
</g>
<text x="28" y="108" class="sans" font-size="84" font-weight="700" fill="{TEXT}" letter-spacing="-1">Domy Yu</text>
<text x="30" y="166" class="sans" font-size="31" fill="{TEXT}">Machines that see.</text>
<text x="30" y="206" class="sans" font-size="31" fill="{TEXT}">Software that connects.</text>
<text x="30" y="258" class="mono" font-size="22" fill="{YELLOW}">vision / automation / full-stack</text>
</svg>"""
    (OUT / "assets/header-mobile.svg").write_text(svg, encoding="utf-8")


def header():
    h, dur = 220, 9
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="Domy Yu: machines that see, software that connects.">
{STYLE}
<defs>
<linearGradient id="beam" x1="0" x2="1"><stop offset="0" stop-color="{YELLOW}" stop-opacity="0"/><stop offset=".5" stop-color="{YELLOW}" stop-opacity=".16"/><stop offset="1" stop-color="{YELLOW}" stop-opacity="0"/></linearGradient>
<clipPath id="c"><rect width="{W}" height="{h}" rx="14"/></clipPath>
</defs>
<g clip-path="url(#c)">
<rect width="{W}" height="{h}" fill="{BG}"/>
<g>{grid(h)}</g>
<rect x="-260" width="260" height="{h}" fill="url(#beam)"><animateTransform attributeName="transform" type="translate" dur="{dur}s" repeatCount="indefinite" values="0 0;{W + 260} 0;{W + 260} 0" keyTimes="0;0.6;1"/></rect>
</g>
<text x="56" y="106" class="sans" font-size="76" font-weight="700" fill="{TEXT}" letter-spacing="-1">Domy Yu</text>
<text x="58" y="152" class="sans" font-size="27" fill="{TEXT}">Machines that see. Software that connects.</text>
<text x="58" y="190" class="mono" font-size="17" fill="{YELLOW}">vision / automation / full-stack</text>
</svg>"""
    (OUT / "assets/header.svg").write_text(svg, encoding="utf-8")


# ---------- insect-frass-vision ----------
def polyline_fracs(pts):
    seg = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    cum = [0.0]
    for s in seg:
        cum.append(cum[-1] + s)
    return seg, cum, sum(seg)


def nearest_frac(p, pts):
    seg, cum, total = polyline_fracs(pts)
    best = (1e18, 0.0)
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        l2 = dx * dx + dy * dy or 1
        t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
        d = math.dist(p, (a[0] + t * dx, a[1] + t * dy))
        if d < best[0]:
            best = (d, (cum[i] + t * seg[i]) / total)
    return best[1]


def serpentine(x0, y0, x1, y1, rows):
    pts = []
    for r in range(rows):
        y = y0 + (y1 - y0) * r / (rows - 1)
        pts += [(x0, y), (x1, y)] if r % 2 == 0 else [(x1, y), (x0, y)]
    return pts


def vision_block():
    rng = random.Random(713)
    dur, start, end = 12, 0.2, 0.76
    clusters = [(PX + 130, PY + 95, 82, 50), (PX + 335, PY + 175, 86, 56)]
    route = []
    for cx, cy, rx, ry in clusters:
        route += serpentine(cx - rx, cy - ry, cx + rx, cy + ry, 5)

    frass = []
    for _ in range(95):
        x, y = rng.uniform(PX + 14, PX + PW - 14), rng.uniform(PY + 14, PY + PH - 42)
        if any(((x - c[0]) / (c[2] + 14)) ** 2 + ((y - c[1]) / (c[3] + 14)) ** 2 < 1 for c in clusters):
            continue
        frass.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rng.uniform(1.3, 2.6):.1f}"/>')

    insects = []
    for cx, cy, rx, ry in clusters:
        for _ in range(38):
            while True:
                x, y = rng.gauss(0, rx / 1.7), rng.gauss(0, ry / 1.7)
                if (x / rx) ** 2 + (y / ry) ** 2 <= 1:
                    break
            x, y = cx + x, cy + y
            t = start + nearest_frac((x, y), route) * (end - start)
            insects.append(
                f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="7.5" ry="3" transform="rotate({rng.uniform(0, 180):.0f} {x:.1f} {y:.1f})">'
                + anim("opacity", dur, [0, 0, 1, 1, 0, 0], [0, 0.07, 0.12, round(t, 3), round(t + 0.012, 3), 1])
                + "</ellipse>"
            )

    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in route)
    steps = [
        ("01 SEGMENT  insect / frass", 0.0, 0.2),
        ("02 PLAN  serpentine path", 0.2, 0.3),
        ("03 WRITE  PLC DB11", 0.3, 0.4),
        ("04 SUCTION  following path", 0.4, 0.76),
        ("05 BLOCK DONE  rescan", 0.76, 1.0),
    ]
    panel = f"""<defs><linearGradient id="scan" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{YELLOW}" stop-opacity="0"/><stop offset="1" stop-color="{YELLOW}" stop-opacity=".35"/></linearGradient></defs>
<g clip-path="url(#tray)">
<g fill="{GREEN}" opacity=".8">{''.join(frass)}</g>
<g fill="{RED}">{''.join(insects)}</g>
<path d="{d}" fill="none" stroke="{YELLOW}" stroke-width="2.5" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1">
{anim("stroke-dashoffset", dur, [1, 1, 0, 0], [0, start, end, 1])}
{anim("opacity", dur, [1, 1, 0, 0], [0, 0.9, 0.96, 1])}
</path>
<g><circle r="9" fill="none" stroke="{YELLOW}" stroke-width="2.5"/><circle r="3" fill="{YELLOW}"/>
<animateMotion dur="{dur}s" repeatCount="indefinite" path="{d}" keyPoints="0;0;1;1" keyTimes="0;{start};{end};1" calcMode="linear"/>
{anim("opacity", dur, [0, 0, 1, 1, 0, 0], [0, start - 0.01, start, end, end + 0.01, 1])}
</g>
<rect x="{PX}" y="{PY - 70}" width="{PW}" height="70" fill="url(#scan)">
<animateTransform attributeName="transform" type="translate" dur="{dur}s" repeatCount="indefinite" values="0 0;0 {PH + 70};0 {PH + 70}" keyTimes="0;0.18;1"/>
</rect>
</g>
<rect x="{PX}" y="{PY + PH - 36}" width="{PW}" height="36" fill="{BG}" opacity=".82"/>
{status_steps(steps, dur, YELLOW)}"""
    block(
        "card-vision.svg",
        "insect-frass-vision",
        "Vision-guided insect and frass separation",
        [
            "Insects cluster on their own. A camera and YOLO11n-seg",
            "find them, a suction path is planned through each cluster,",
            "and a Siemens S7 PLC drives the machine to pick them up.",
        ],
        ["YOLO11n-seg", "Snap7", "Siemens S7", "Python"],
        panel,
        YELLOW,
        "insect-frass-vision overview: insects and frass are segmented from a camera view, a serpentine suction path is planned, written to a Siemens S7 PLC, and the insects are picked up along the path.",
        [
            "Insects cluster on their own. A camera and",
            "YOLO11n-seg find them, a suction path is",
            "planned through each cluster, and a Siemens",
            "S7 PLC drives the machine to pick them up.",
        ],
        period="2026",
    )


# Pixel grid traced from the Us logo; K is the magnet's shadow.
LOGO_GRID = [
    "hhhhggK.......hhhggK................",
    "hhhhggK.......hhhggK................",
    "hhggggK.......hggggK................",
    "hhggggK.......hggggK................",
    "RRRRRRK.......BBBBBK................",
    "RRRRRRK.......BBBBBK................",
    "RRRRRRK.......BBBBBK.....SSSSSSS....",
    "RRRRRRK.......BBBBBK...SSSSSSSSSS...",
    "RRRRRRK.......BBBBBK..SSSSSS.SSSSS..",
    "RRRRRRK.......BBBBBK..SSSSS..SSSSS..",
    "RRRRRRK.......BBBBBK..SSSS.....SSS..",
    "RRRRRRK.......BBBBBK..SSSSSSSS......",
    "RRRRRRK.......BBBBBK..SSSSSSSSS.....",
    "RRRRRRK.......BBBBBK...SSSSSSSSS....",
    "RRRRRRK.......BBBBBK.....SSSSSSSS...",
    "RRRRRRRK....BBBBBBBK.........SSSSS..",
    "RRRRRRRKKKBBBBBBBBBK..........SSSS..",
    "..RRRRRRRRBBBBBBBBK...SSSS....SSSS..",
    "...RRRRRRRBBBBBBBK....SSSSSSSSSSSS..",
    "...RRRRRRRBBBBBBKK....SSSSSSSSSSSS..",
    "....RRRRRRBBBBBKK......SSSSSSSSSS...",
    "......RRRRBBBBK..........SSSSSSS....",
]
LOGO_RED = "#d92b2a"
LOGO_BLUE = "#3f75e6"
LOGO_COLORS = {"R": LOGO_RED, "B": LOGO_BLUE, "S": LOGO_BLUE, "K": "#05070b", "h": "#b9b9b9", "g": "#8c8c8c"}


def logo_pixels(x0, y0, cell, keys):
    """Pixel art as merged horizontal runs, limited to the given grid keys."""
    out = []
    for r, row in enumerate(LOGO_GRID):
        c = 0
        while c < len(row):
            k = row[c]
            e = c
            while e < len(row) and row[e] == k:
                e += 1
            if k in keys:
                out.append(
                    f'<rect x="{x0 + c * cell:.2f}" y="{y0 + r * cell:.2f}" width="{(e - c) * cell + 0.3:.2f}" '
                    f'height="{cell + 0.3:.2f}" fill="{LOGO_COLORS[k]}"/>'
                )
            c = e
    return "".join(out)


# ---------- Us ----------
def us_block():
    rng = random.Random(16)
    dur = 18
    # FindUs 0-.26, SeeU .26-.48, HelpU .48-.72, Us .72-1
    groups = [
        (PX + 100, PY + 82, BLUE, "sad / lonely"),
        (PX + 370, PY + 82, YELLOW, "happy"),
        (PX + 100, PY + 195, PURPLE, "anxious"),
    ]
    cell = 5.8
    tile_w, tile_h = 191, 176
    tile_x, tile_y = PX + (PW - tile_w) / 2, PY + 14
    art_x = tile_x + (tile_w - 36 * cell) / 2
    art_y = tile_y + (tile_h - 22 * cell) / 2
    cx, cy = round(art_x + 10 * cell), round(art_y + 11 * cell)
    letters, placed = [], []
    for gi in range(21):
        gx, gy, color, _ = groups[gi % 3]
        sx, sy = rng.uniform(PX + 24, PX + PW - 24), rng.uniform(PY + 30, PY + PH - 50)
        for _ in range(200):
            tx, ty = gx + rng.uniform(-58, 58), gy + rng.uniform(-12, 28)
            if all(math.dist((tx, ty), q) > 25 for q in placed):
                break
        placed.append((tx, ty))
        times = [0, 0.05, 0.17, 0.72, 0.82, 0.96, 1]
        letters.append(
            f'<text class="sans" font-size="{rng.randint(17, 24)}" font-weight="600" text-anchor="middle" x="{sx:.0f}" y="{sy:.0f}" fill="{GREY}">U'
            + anim("x", dur, [f"{sx:.0f}", f"{sx:.0f}", f"{tx:.0f}", f"{tx:.0f}", cx, cx, f"{sx:.0f}"], times, spline=True)
            + anim("y", dur, [f"{sy:.0f}", f"{sy:.0f}", f"{ty:.0f}", f"{ty:.0f}", cy, cy, f"{sy:.0f}"], times, spline=True)
            + anim("fill", dur, [GREY, GREY, color, color, LOGO_RED if gi % 2 else LOGO_BLUE, GREY, GREY], [0, 0.26, 0.3, 0.72, 0.78, 0.97, 1])
            + anim("opacity", dur, [1, 1, 0, 0, 1], [0, 0.8, 0.83, 0.96, 1])
            + "</text>"
        )

    labels, hearts = [], []
    for gx, gy, color, name in groups:
        labels.append(
            f'<text x="{gx}" y="{gy - 32}" text-anchor="middle" class="mono" font-size="15" fill="{color}" opacity="0">{name}'
            + anim("opacity", dur, [0, 0, 1, 1, 0, 0], [0, 0.27, 0.3, 0.71, 0.74, 1])
            + "</text>"
        )
        for k in range(6):
            t0 = 0.3 + k * 0.026 + rng.uniform(0, 0.012)
            hx, hy = gx + rng.uniform(-55, 55), gy + rng.uniform(-2, 22)
            hearts.append(
                f'<path d="M0 8C-14 -4 -8 -14 0 -6C8 -14 14 -4 0 8Z" fill="{color}" opacity="0">'
                f'<animateTransform attributeName="transform" type="translate" dur="{dur}s" repeatCount="indefinite" '
                f'values="{hx:.0f} {hy:.0f};{hx:.0f} {hy:.0f};{hx:.0f} {hy - 34:.0f};{hx:.0f} {hy - 34:.0f}" keyTimes="0;{t0:.3f};{t0 + 0.07:.3f};1"/>'
                + anim("opacity", dur, [0, 0, 1, 0, 0], [0, round(t0, 3), round(t0 + 0.015, 3), round(t0 + 0.07, 3), 1])
                + "</path>"
            )

    bx, by = PX + 370, PY + 195
    bot_op = anim("opacity", dur, [0, 0, 1, 1, 0, 0], [0, 0.48, 0.51, 0.7, 0.73, 1])
    links = []
    for i, (gx, gy, _, _) in enumerate(groups):
        ex, ey = gx + (70 if gx < bx else 0), gy + (0 if gy == by else 34)
        links.append(f'<path d="M{bx} {by}L{ex} {ey}" stroke="{PINK}" stroke-width="1.5" stroke-dasharray="4 5" fill="none"/>')
        links.append(
            f'<circle r="4" fill="{PINK}"><animateMotion dur="2.4s" begin="{i * 0.8}s" repeatCount="indefinite" path="M{bx} {by}L{ex} {ey}"/></circle>'
        )
    bot = f"""<g opacity="0">{bot_op}
{''.join(links)}
<rect x="{bx - 24}" y="{by - 22}" width="48" height="44" rx="11" fill="{PANEL}" stroke="{PINK}" stroke-width="2.5"/>
<circle cx="{bx - 9}" cy="{by - 3}" r="3.5" fill="{PINK}"/><circle cx="{bx + 9}" cy="{by - 3}" r="3.5" fill="{PINK}"/>
<path d="M{bx - 8} {by + 8}Q{bx} {by + 15} {bx + 8} {by + 8}" stroke="{PINK}" stroke-width="2.5" fill="none" stroke-linecap="round"/>
<text x="{bx}" y="{by + 42}" text-anchor="middle" class="mono" font-size="14" fill="{PINK}">UsBot</text>
<rect x="{PX + 178}" y="{PY + 208}" width="142" height="32" rx="12" fill="#232b3a" stroke="{LINE}"/>
<text x="{PX + 249}" y="{PY + 229}" text-anchor="middle" class="sans" font-size="15" fill="{TEXT}">I'm here for you.</text>
</g>"""
    tile = (
        f'<g opacity="0">' + anim("opacity", dur, [0, 0, 1, 1, 0, 0], [0, 0.71, 0.74, 0.95, 0.98, 1])
        + f'<g shape-rendering="crispEdges">{logo_pixels(art_x, art_y, cell, "RBKhg")}</g>'
        + "</g>"
    )
    arcs = []
    left_tip, right_tip = art_x + 3 * cell, art_x + 16.5 * cell
    for lift in (12, 30, 48):
        arcs.append(
            f'<path d="M{left_tip:.1f} {art_y:.1f}C{left_tip + 8:.1f} {art_y - lift:.1f} {right_tip - 8:.1f} {art_y - lift:.1f} {right_tip:.1f} {art_y:.1f}" '
            f'fill="none" stroke="#8a95a6" stroke-width="2" stroke-dasharray="5 6">'
            f'<animate attributeName="stroke-dashoffset" dur="0.9s" repeatCount="indefinite" values="22;0"/></path>'
        )
    field = (
        f'<g opacity="0">' + anim("opacity", dur, [0, 0, 1, 1, 0, 0], [0, 0.73, 0.75, 0.83, 0.86, 1])
        + "".join(arcs) + "</g>"
    )
    word = (
        f'<g opacity="0">' + anim("opacity", dur, [0, 0, 1, 1, 0, 0], [0, 0.825, 0.84, 0.95, 0.98, 1])
        + f'<g shape-rendering="crispEdges">{logo_pixels(art_x, art_y, cell, "S")}</g>'
        + f'<text x="{tile_x + tile_w / 2}" y="{tile_y + tile_h + 32}" text-anchor="middle" class="sans" font-size="19" fill="{TEXT}">Us is many U, U belong to Us</text></g>'
    )
    steps = [
        ("01 FINDU  match into groups", 0.0, 0.26),
        ("02 SEEU  share how you feel", 0.26, 0.48),
        ("03 HELPU  local AI companion", 0.48, 0.72),
        ("04 US  many U become Us", 0.72, 1.0),
    ]
    panel = f"""<g clip-path="url(#tray)">
{''.join(labels)}
{tile}
{field}
{''.join(letters)}
{''.join(hearts)}
{bot}
{word}
</g>
<rect x="{PX}" y="{PY + PH - 36}" width="{PW}" height="36" fill="{BG}" opacity=".82"/>
{status_steps(steps, dur, PINK)}"""
    block(
        "card-us.svg",
        "Us",
        "An emotional social platform",
        [
            "FindUs matches you with groups, SeeU lets you share how",
            "you feel, and HelpU offers a local AI companion.",
            "Built solo and backed by an academic paper.",
        ],
        ["JavaScript", "Node.js", "Ollama", "Research"],
        panel,
        PINK,
        "Us overview: scattered U letters are matched into groups, share emotions, get support from the UsBot AI companion, then get pulled together by a magnet-shaped U to form the Us logo.",
        [
            "FindUs matches you with groups, SeeU lets",
            "you share how you feel, and HelpU offers a",
            "local AI companion. Built solo and backed",
            "by an academic paper.",
        ],
        period="2025",
        plays_first=True,
        cta="Try Us online",
    )


header()
header_mobile()
vision_block()
us_block()
