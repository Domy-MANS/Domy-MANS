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


def status_steps(steps, dur, color, py=PY, ph=PH):
    out = []
    for label, a, b in steps:
        if a == 0:
            vals, times = [1, 1, 0, 0], [0, b, b + 0.001, 1]
        elif b == 1:
            vals, times = [0, 0, 1, 1], [0, a, a + 0.001, 1]
        else:
            vals, times = [0, 0, 1, 1, 0, 0], [0, a, a + 0.001, b, b + 0.001, 1]
        out.append(
            f'<text x="{PX + 16}" y="{py + ph - 12}" class="mono" font-size="17" fill="{color}" opacity="0">{label}'
            + anim("opacity", dur, vals, times)
            + "</text>"
        )
    return "".join(out)


def cta_button(right, cy, w, h, size, label, color):
    x = right - w
    ay = cy
    ax = right - 34
    return (
        f'<rect x="{x}" y="{cy - h / 2}" width="{w}" height="{h}" rx="{h / 2}" fill="{color}"/>'
        f'<text x="{x + 22}" y="{cy + size * 0.35:.1f}" class="sans" font-size="{size}" font-weight="600" fill="{BG}">{label}</text>'
        f'<path d="M{ax} {ay + 6}L{ax + 12} {ay - 6}M{ax + 2} {ay - 6}H{ax + 12}V{ay + 4}" fill="none" stroke="{BG}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def timeline(x, height, node_y, accent, year, phase):
    """Dashed rail with a node. A light travels up the blocks in turn, oldest first.

    phase is (index, count), counted from the oldest block at the bottom.
    """
    i, count = phase
    dur = 3 * count
    a, b = i / count, (i + 1) / count
    label = (
        f'<text x="{x - 22}" y="{node_y + 9}" text-anchor="end" class="mono" font-size="24" font-weight="600" fill="#6f7c8f">{year}</text>'
        if year
        else ""
    )
    if a == 0:
        op_vals, op_times = [1, 1, 0, 0], [0, b, b + 0.001, 1]
        cy_vals, cy_times = [height, 0, 0], [0, b, 1]
    elif b == 1:
        op_vals, op_times = [0, 0, 1, 1], [0, a, a + 0.001, 1]
        cy_vals, cy_times = [height, height, 0], [0, a, 1]
    else:
        op_vals, op_times = [0, 0, 1, 1, 0, 0], [0, a, a + 0.001, b, b + 0.001, 1]
        cy_vals, cy_times = [height, height, 0, 0], [0, a, b, 1]
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
CTA_PY, CTA_PH = 100, 226  # desktop panel below the button row; same card height and panel bottom


def write_rail(fname, card_w, height, x, node_y, accent, year, phase, rows=None):
    gw = round(card_w * GUTTER_SHARE / CARD_SHARE, 2)
    h = height + RAIL_GAP
    if rows:
        body = timeline(x, h, node_y, accent, year, phase)
        stem, top, bottom = fname[:-4], rows[0], rows[1]
        tag = "-mobile" if stem.endswith("-mobile") else ""
        stem = stem.removesuffix("-mobile")
        for part, y, part_h in [("top", 0, top), ("mid", top, bottom - top), ("bottom", bottom, h - bottom)]:
            write_crop(f"{stem}-{part}{tag}.svg", 0, y, gw, part_h, body, year or "timeline")
        return
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {gw} {h}" width="{gw}" height="{h}" role="img" aria-label="{year or 'timeline'}">
{STYLE}
{timeline(x, h, node_y, accent, year, phase)}
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


def block(fname, title, subtitle, desc_lines, chips, panel, accent, label, mobile_lines, period, phase, cta=None, mobile_panel=None, rail=None, show_year=True):
    rail = rail or period
    card_h = H
    py, ph = (CTA_PY, CTA_PH) if cta else (PY, PH)
    chip_svg, x = [], 58
    for c in chips:
        w = 10 * len(c) + 28
        chip_svg.append(
            f'<rect x="{x}" y="276" width="{w}" height="36" rx="18" fill="#182130" stroke="{LINE}"/>'
            f'<text x="{x + w / 2}" y="300" text-anchor="middle" class="mono" font-size="16" fill="{TEXT}">{c}</text>'
        )
        x += w + 10
    desc = "".join(
        f'<text x="58" y="{176 + i * 31}" class="sans" font-size="21" fill="{MUTED}">{l}</text>'
        for i, l in enumerate(desc_lines)
    )
    def corner_brackets(top, height):
        return "".join(
            f'<path d="M{x + 18 * sx} {y}H{x}V{y + 18 * sy}" fill="none" stroke="{accent}" stroke-width="2.5"/>'
            for x, y, sx, sy in [
                (PX, top, 1, 1), (PX + PW, top, -1, 1), (PX, top + height, 1, -1), (PX + PW, top + height, -1, -1),
            ]
        )

    brackets = corner_brackets(py, ph)
    bar_y, title_y, subtitle_y = (30, 86, 124) if cta else (44, 98, 132)
    static = f"""<rect x=".5" y=".5" width="{W - 1}" height="{card_h - 1}" rx="14" fill="{BG}" stroke="{LINE}"/>
<rect x="58" y="{bar_y}" width="52" height="5" rx="2.5" fill="{accent}"/>
<text x="58" y="{title_y}" class="sans" font-size="44" font-weight="700" fill="{TEXT}">{title}</text>
<text x="58" y="{subtitle_y}" class="sans" font-size="21" fill="{accent}">{subtitle}</text>
{cta_button(PX + PW, sum(DESKTOP_ROWS) / 2, 186, 44, 19, cta, accent) if cta else ""}
{desc}
{''.join(chip_svg)}"""
    full = f"""{static}
<defs><clipPath id="tray"><rect x="{PX}" y="{py}" width="{PW}" height="{ph}"/></clipPath></defs>
<rect x="{PX}" y="{py}" width="{PW}" height="{ph}" fill="{PANEL}"/>
{panel}
<rect x="{PX}" y="{py}" width="{PW}" height="{ph}" fill="none" stroke="{LINE}"/>
{brackets}"""
    if cta:
        write_cta_card(fname[:-4], "", W, card_h, DESKTOP_ROWS, CTA_SHARES, static, full, label, cta)
        write_rail(f"timeline-{rail}.svg", W, card_h, 82, sum(DESKTOP_ROWS) // 2, accent, period if show_year else None, phase, DESKTOP_ROWS)
    else:
        write_crop(fname, 0, 0, W, card_h, full, label)
        write_rail(f"timeline-{rail}.svg", W, card_h, 82, 84, accent, period if show_year else None, phase)
    mobile_block(fname.replace(".svg", "-mobile.svg"), title, subtitle, mobile_lines, chips, mobile_panel or panel, corner_brackets(PY, PH), accent, label, period, phase, cta, rail)


def mobile_block(fname, title, subtitle, lines, chips, panel, brackets, accent, label, period, phase, cta=None, rail=None):
    rail = rail or period
    mw, scale = 600, 540 / PW
    if cta and len(title) > 10:
        # A long title would run under the button, so it starts below the button row.
        title_y, subtitle_y, panel_top = (168, 206, 226)
    else:
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
{cta_button(570, sum(MOBILE_ROWS) / 2, 214, 50, 23, cta, accent) if cta else ""}"""
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
        write_rail(f"timeline-{rail}-mobile.svg", mw, mh, 24, sum(MOBILE_ROWS) // 2, accent, None, phase, MOBILE_ROWS)
    else:
        write_crop(fname, 0, 0, mw, mh, full, label)
        write_rail(f"timeline-{rail}-mobile.svg", mw, mh, 24, 72, accent, None, phase)


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
<text x="30" y="258" class="mono" font-size="20" fill="{YELLOW}">vision / automation / embedded / full-stack</text>
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
<text x="58" y="190" class="mono" font-size="17" fill="{YELLOW}">vision / automation / embedded / full-stack</text>
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


def vision_panel(py, ph):
    """The vision animation for a panel at py. A panel shorter than PH gets flatter clusters."""
    sy = (ph - 36) / (PH - 36)
    rng = random.Random(713)
    dur, start, end = 12, 0.2, 0.76
    clusters = [(PX + 130, py + 95 * sy, 82, 50 * sy), (PX + 335, py + 175 * sy, 86, 56 * sy)]
    route = []
    for cx, cy, rx, ry in clusters:
        route += serpentine(cx - rx, cy - ry, cx + rx, cy + ry, 5)

    frass = []
    for _ in range(95):
        x, y = rng.uniform(PX + 14, PX + PW - 14), rng.uniform(py + 14, py + ph - 42)
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
<rect x="{PX}" y="{py - 70}" width="{PW}" height="70" fill="url(#scan)">
<animateTransform attributeName="transform" type="translate" dur="{dur}s" repeatCount="indefinite" values="0 0;0 {ph + 70};0 {ph + 70}" keyTimes="0;0.18;1"/>
</rect>
</g>
<rect x="{PX}" y="{py + ph - 36}" width="{PW}" height="36" fill="{BG}" opacity=".82"/>
{status_steps(steps, dur, YELLOW, py, ph)}"""
    return panel


def vision_block():
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
        vision_panel(CTA_PY, CTA_PH),
        YELLOW,
        "insect-frass-vision overview: insects and frass are segmented from a camera view, a serpentine suction path is planned, written to a Siemens S7 PLC, and the insects are picked up along the path.",
        [
            "Insects cluster on their own. A camera and",
            "YOLO11n-seg find them, a suction path is",
            "planned through each cluster, and a Siemens",
            "S7 PLC drives the machine to pick them up.",
        ],
        period="2026",
        phase=(3, 5),
        cta="Watch demo",
        mobile_panel=vision_panel(PY, PH),
        rail="vision",
        show_year=False,
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
def us_panel(py, ph):
    """The Us animation for a panel at py. A panel shorter than PH gets a tighter layout."""
    compact = ph < PH
    row_a, row_b = (46, 126) if compact else (82, 195)
    rng = random.Random(16)
    dur = 18
    # FindUs 0-.26, SeeU .26-.48, HelpU .48-.72, Us .72-1
    groups = [
        (PX + 100, py + row_a, BLUE, "sad / lonely"),
        (PX + 370, py + row_a, YELLOW, "happy"),
        (PX + 100, py + row_b, PURPLE, "anxious"),
    ]
    cell = 4.4 if compact else 5.8
    tile_w, tile_h = 191, 134 if compact else 176
    tile_x, tile_y = PX + (PW - tile_w) / 2, py + 14
    art_x = tile_x + (tile_w - 36 * cell) / 2
    art_y = tile_y + (tile_h - 22 * cell) / 2
    cx, cy = round(art_x + 10 * cell), round(art_y + 11 * cell)
    letters, placed = [], []
    for gi in range(21):
        gx, gy, color, _ = groups[gi % 3]
        sx, sy = rng.uniform(PX + 24, PX + PW - 24), rng.uniform(py + 30, py + ph - 50)
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

    bx, by = PX + 370, py + row_b
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
<rect x="{PX + 178}" y="{by + 13}" width="142" height="32" rx="12" fill="#232b3a" stroke="{LINE}"/>
<text x="{PX + 249}" y="{by + 34}" text-anchor="middle" class="sans" font-size="15" fill="{TEXT}">I'm here for you.</text>
</g>"""
    tile = (
        f'<g opacity="0">' + anim("opacity", dur, [0, 0, 1, 1, 0, 0], [0, 0.71, 0.74, 0.95, 0.98, 1])
        + f'<g shape-rendering="crispEdges">{logo_pixels(art_x, art_y, cell, "RBKhg")}</g>'
        + "</g>"
    )
    arcs = []
    left_tip, right_tip = art_x + 3 * cell, art_x + 16.5 * cell
    for lift in (8, 18, 28) if compact else (12, 30, 48):
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
        + f'<text x="{tile_x + tile_w / 2}" y="{tile_y + tile_h + (18 if compact else 32)}" text-anchor="middle" class="sans" font-size="19" fill="{TEXT}">Us is many U, U belong to Us</text></g>'
    )
    steps = [
        ("01 FINDU  match into groups", 0.0, 0.26),
        ("02 SEEU  share how you feel", 0.26, 0.48),
        ("03 HELPU  local AI companion", 0.48, 0.72),
        ("04 US  many U become Us", 0.72, 1.0),
    ]
    return f"""<g clip-path="url(#tray)">
{''.join(labels)}
{tile}
{field}
{''.join(letters)}
{''.join(hearts)}
{bot}
{word}
</g>
<rect x="{PX}" y="{py + ph - 36}" width="{PW}" height="36" fill="{BG}" opacity=".82"/>
{status_steps(steps, dur, PINK, py, ph)}"""


def us_block():
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
        us_panel(CTA_PY, CTA_PH),
        PINK,
        "Us overview: scattered U letters are matched into groups, share emotions, get support from the UsBot AI companion, then get pulled together by a magnet-shaped U to form the Us logo.",
        [
            "FindUs matches you with groups, SeeU lets",
            "you share how you feel, and HelpU offers a",
            "local AI companion. Built solo and backed",
            "by an academic paper.",
        ],
        period="2025",
        phase=(0, 5),
        rail="us-app",
        show_year=False,
        cta="Try Us online",
        mobile_panel=us_panel(PY, PH),
    )


# ---------- balance-car-learning ----------
def balance_panel(py, ph):
    """A 3D model of the car, projected to SVG keyframes. The motion is drawn, not measured.

    The car balances, drives away and back on the left stick, then spins on the right stick.
    Each polygon morphs between projected keyframes. Hidden faces switch off per keyframe, and
    the wheels sit in two layers so the nearer one draws over the body.
    """
    dur, n = 16, 48
    smooth = lambda x: (lambda u: u * u * (3 - 2 * u))(max(0.0, min(1.0, x)))

    def pose(sec):
        z = 1.7 * smooth((sec - 3) / 2.5) - 1.7 * smooth((sec - 6.5) / 2.5)
        lean = 9 * (math.sin(math.pi * smooth((sec - 3) / 2.5)) - math.sin(math.pi * smooth((sec - 6.5) / 2.5)))
        lean += 2.5 * math.sin(sec * 2.2)
        yaw = 360 * smooth((sec - 10) / 4)
        # Moving along z and spinning both turn the wheels.
        roll_fwd, roll_turn = z / 0.55, math.radians(yaw) * 1.0 / 0.55
        lv = smooth((sec - 2.8) / 0.4) - smooth((sec - 5.2) / 0.4) - smooth((sec - 6.3) / 0.4) + smooth((sec - 8.7) / 0.4)
        rh = smooth((sec - 9.8) / 0.4) - smooth((sec - 13.8) / 0.4)
        return z, math.radians(lean), math.radians(yaw), roll_fwd, roll_turn, lv, rh

    poses = [pose(dur * k / n) for k in range(n)]
    ground = py + ph - 36 - 26
    focal, cx = 345, PX + 150
    cam_h, cam_d, tip = 1.9, 5.0, math.radians(13)
    axle = 0.55

    def world(p, q):
        z_off, _, yaw, *_ = q
        x, y, z = p
        c, s = math.cos(yaw), math.sin(yaw)
        return (x * c + z * s, y, -x * s + z * c + z_off)

    def body(p, q):
        x, y, z = p
        c, s = math.cos(q[1]), math.sin(q[1])
        return world((x, axle + y * c - z * s, y * s + z * c), q)

    def camera(w):
        x, y, z = w[0], w[1] - cam_h, w[2] + cam_d
        c, s = math.cos(tip), math.sin(tip)
        return x, y * c + z * s, -y * s + z * c

    def project(w):
        x, y, z = camera(w)
        return cx + focal * x / z, ground - 40 - focal * y / z

    def facing(center, normal):
        return sum(n_ * (c_ - e_) for n_, c_, e_ in zip(normal, center, (0, cam_h, -cam_d))) < 0

    def poly(frames, fill, shown=None, extra=""):
        rows = [" ".join(f"{x:.1f},{y:.1f}" for x, y in f) for f in frames]
        values = ";".join(rows + rows[:1])
        vis = ""
        if shown is not None:
            vis = f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" calcMode="discrete" values="{";".join("1" if v else "0" for v in shown)}"/>'
        return (
            f'<polygon points="{rows[0]}" fill="{fill}"{extra}>'
            f'<animate attributeName="points" dur="{dur}s" repeatCount="indefinite" values="{values}"/>{vis}</polygon>'
        )

    def face(corners, normal, fill, extra=""):
        frames, shown = [], []
        for q in poses:
            pts = [body(c, q) for c in corners]
            frames.append([project(w) for w in pts])
            origin, tip_n = body((0, 0, 0), q), body(normal, q)
            nrm = tuple(b - a for a, b in zip(origin, tip_n))
            center = tuple(sum(v) / len(v) for v in zip(*pts))
            shown.append(facing(center, nrm))
        return poly(frames, fill, shown, extra)

    def rect(x0, x1, y0, y1, z):
        return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]

    w, top, low, d = 0.82, 0.62, -0.34, 0.2
    board, side, edge = "#17382a", "#112a20", "#0e2119"
    chassis = "".join([
        face(rect(-w, w, low, top, d), (0, 0, 1), "#14241c", f' stroke="{LINE}"'),
        face(rect(-0.56, 0.56, low + 0.06, 0.12, d + 0.01), (0, 0, 1), GREEN, ' fill-opacity=".35"'),
        face([(-w, low, -d), (-w, low, d), (-w, top, d), (-w, top, -d)], (-1, 0, 0), side),
        face([(w, low, -d), (w, low, d), (w, top, d), (w, top, -d)], (1, 0, 0), side),
        face([(-w, top, -d), (w, top, -d), (w, top, d), (-w, top, d)], (0, 1, 0), edge),
        face(rect(-w, w, low, top, -d), (0, 0, -1), board, f' stroke="{GREEN}" stroke-width="1.5"'),
        face(rect(-0.7, -0.28, -0.24, 0.12, -d - 0.01), (0, 0, -1), BG),
        face(rect(-0.65, -0.33, -0.16, 0.05, -d - 0.02), (0, 0, -1), GREEN, ' fill-opacity=".8"'),
        face(rect(-0.2, 0.68, -0.24, 0.08, -d - 0.01), (0, 0, -1), "#2a5a43"),
        face(rect(0.18, 0.66, 0.2, 0.54, -d - 0.01), (0, 0, -1), "#2a5a43"),
        face(rect(-0.2, 0.1, 0.22, 0.52, -d - 0.01), (0, 0, -1), "#2a5a43"),
        face(rect(-0.7, -0.3, 0.26, 0.5, -d - 0.01), (0, 0, -1), "#2a5a43"),
        face([(-0.03, top, 0), (0.03, top, 0), (0.03, top + 0.62, 0), (-0.03, top + 0.62, 0)], (0, 0, -1), "#0b0f17", f' stroke="{TEXT}" stroke-width=".8"'),
        face([(-0.03, top, 0), (0.03, top, 0), (0.03, top + 0.62, 0), (-0.03, top + 0.62, 0)], (0, 0, 1), "#0b0f17", f' stroke="{TEXT}" stroke-width=".8"'),
    ])

    def disc(side_x, radius, count, q):
        return [project(world((side_x, axle + radius * math.sin(2 * math.pi * i / count), radius * math.cos(2 * math.pi * i / count)), q)) for i in range(count)]

    def hull(points, count=24):
        """Convex outline of a tyre, resampled to a fixed point count so it can morph."""
        pts = sorted(set(points))
        def half(seq):
            out = []
            for pt in seq:
                while len(out) > 1 and (out[-1][0] - out[-2][0]) * (pt[1] - out[-2][1]) - (out[-1][1] - out[-2][1]) * (pt[0] - out[-2][0]) <= 0:
                    out.pop()
                out.append(pt)
            return out[:-1]
        ring = half(pts) + half(pts[::-1])
        mx, my = sum(q[0] for q in ring) / len(ring), sum(q[1] for q in ring) / len(ring)
        result = []
        for i in range(count):
            a = 2 * math.pi * i / count
            dx, dy = math.cos(a), math.sin(a)
            best = 0.0
            for j, b in enumerate(ring):
                c = ring[(j + 1) % len(ring)]
                ex, ey = c[0] - b[0], c[1] - b[1]
                den = dx * ey - dy * ex
                if abs(den) < 1e-9:
                    continue
                u = ((b[0] - mx) * ey - (b[1] - my) * ex) / den
                v = ((b[0] - mx) * dy - (b[1] - my) * dx) / den
                if u > 0 and -1e-6 <= v <= 1 + 1e-6:
                    best = max(best, u)
            result.append((mx + best * dx, my + best * dy))
        return result

    def wheel(sign, name):
        tread = [hull(disc(sign * 0.86, 0.55, 18, q) + disc(sign * 1.17, 0.55, 18, q)) for q in poses]
        out = poly(tread, "#1b2430", None, f' stroke="{GREY}" stroke-width="1.5"')
        outer = []
        for q in poses:
            center, tip_n = world((sign * 1.17, axle, 0), q), world((sign * 2.17, axle, 0), q)
            outer.append(facing(center, tuple(b - a for a, b in zip(center, tip_n))))
        out += poly([disc(sign * 1.17, 0.5, 16, q) for q in poses], "#161d28", outer)
        out += poly([disc(sign * 1.175, 0.3, 10, q) for q in poses], GREEN, outer, ' fill-opacity=".5"')
        spokes = []
        for q in poses:
            ang = q[3] + sign * q[4]
            c, s = math.cos(ang), math.sin(ang)
            pts = [(-0.27, -0.035), (0.27, -0.035), (0.27, 0.035), (-0.27, 0.035)]
            spokes.append([project(world((sign * 1.18, axle + u * s + v * c, u * c - v * s), q)) for u, v in pts])
        out += poly(spokes, TEXT, outer)
        return f'<g id="{name}">{out}</g>'

    def wheel_layer(name, sign, near):
        shown = []
        for q in poses:
            wheel_z = camera(world((sign, axle, 0), q))[2]
            body_z = camera(world((0, axle, 0), q))[2]
            shown.append((wheel_z < body_z) == near)
        values = ";".join("1" if v else "0" for v in shown)
        return f'<use href="#{name}"><animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" calcMode="discrete" values="{values}"/></use>'

    tag = f"b{py}"
    defs = f"<defs>{wheel(-1, tag + 'l')}{wheel(1, tag + 'r')}</defs>"
    shadow_rows = []
    for q in poses:
        x, y = project(world((0, 0, 0), q))
        shadow_rows.append(f"{x:.1f} {y:.1f}")
    shadow = (
        f'<ellipse cx="0" cy="0" rx="72" ry="13" fill="#000" fill-opacity=".38">'
        f'<animateTransform attributeName="transform" type="translate" dur="{dur}s" repeatCount="indefinite" values="{";".join(shadow_rows + shadow_rows[:1])}"/></ellipse>'
    )

    # Target steps follow the commands. The second line is a simulated second-order response.
    px0, px1, py0, py1 = PX + 305, PX + 448, py + 24, py + ph - 58
    samples, y, v, target, actual = 96, 0.0, 0.0, [], []
    for k in range(samples + 1):
        sec = dur * k / samples
        q = pose(sec)
        goal = q[5] + q[6]
        for _ in range(10):
            v += (26 * (goal - y) - 4.2 * v) * (dur / samples / 10)
            y += v * (dur / samples / 10)
        target.append(goal)
        actual.append(y + 0.035 * math.sin(sec * 19) + 0.025 * math.sin(sec * 31))
    to_xy = lambda k, val: (px0 + (px1 - px0) * k / samples, (py0 + py1) / 2 - (py1 - py0) / 2 * val / 1.35)
    line = lambda vals: "M" + " L".join("{:.1f} {:.1f}".format(*to_xy(k, val)) for k, val in enumerate(vals))
    cursor = ";".join("{:.1f},{:.1f}".format(*to_xy(k, val)) for k, val in enumerate(actual))
    clip_id = f"plot{py}"
    plot = (
        f'<rect x="{px0}" y="{py0}" width="{px1 - px0}" height="{py1 - py0}" fill="{BG}" stroke="{LINE}"/>'
        f'<path d="M{px0} {(py0 + py1) / 2}H{px1}" stroke="{LINE}" stroke-dasharray="4 4"/>'
        f'<path d="{line(target)}" fill="none" stroke="{MUTED}" stroke-width="2" stroke-dasharray="5 5"/>'
        f'<clipPath id="{clip_id}"><rect x="{px0}" y="{py0 - 2}" width="0" height="{py1 - py0 + 4}">'
        f'<animate attributeName="width" dur="{dur}s" repeatCount="indefinite" calcMode="linear" values="0;{px1 - px0}"/></rect></clipPath>'
        f'<path clip-path="url(#{clip_id})" d="{line(actual)}" fill="none" stroke="{GREEN}" stroke-width="2"/>'
        f'<circle r="5" fill="{GREEN}" stroke="{BG}" stroke-width="2"><animateMotion dur="{dur}s" repeatCount="indefinite" calcMode="linear" values="{cursor}"/></circle>'
        f'<text x="{px0}" y="{py0 - 8}" class="mono" font-size="13" fill="{MUTED}">target / simulated</text>'
    )
    steps = [
        ("01 BALANCE  angle PID", 0.0, 3 / 16),
        ("02 DRIVE  speed PID", 3 / 16, 10 / 16),
        ("03 TURN  steering PID", 10 / 16, 14 / 16),
        ("01 BALANCE  angle PID", 14 / 16, 1.0),
    ]
    layers = (
        wheel_layer(tag + "l", -1, False) + wheel_layer(tag + "r", 1, False) + chassis + wheel_layer(tag + "l", -1, True) + wheel_layer(tag + "r", 1, True)
    )
    return f"""{defs}<g clip-path="url(#tray)">
{shadow}
{layers}
{plot}
</g>
<rect x="{PX}" y="{py + ph - 36}" width="{PW}" height="36" fill="{BG}" opacity=".82"/>
{status_steps(steps, dur, GREEN, py, ph)}"""


def balance_block():
    block(
        "card-balance.svg",
        "balance-car-learning",
        "Learning project, not original work",
        [
            "Followed the Jiangxie Technology balance car tutorial on",
            "an STM32F103: complementary filter, then angle, speed",
            "and turn PID loops, tuned and running on my own car.",
        ],
        ["STM32F103", "MPU6050", "Cascaded PID", "Learning"],
        balance_panel(CTA_PY, CTA_PH),
        GREEN,
        "balance-car-learning overview: an illustration of a two-wheel car recovering from a push while the firmware reads tilt, filters it, and runs cascaded PID loops. A learning project based on the Jiangxie Technology tutorial.",
        [
            "Followed the Jiangxie Technology balance",
            "car tutorial on an STM32F103: complementary",
            "filter, then angle, speed and turn PID",
            "loops, tuned and running on my own car.",
        ],
        period="2026",
        phase=(2, 5),
        cta="Watch demo",
        mobile_panel=balance_panel(PY, PH),
        rail="balance-car",
        show_year=False,
    )


# ---------- MANS ----------
def mans_panel(py, ph):
    """Elbow following the firmware trajectory: 45 - 44 cos(2 pi 0.1 t) degrees, 10 s period."""
    dur, n = 10, 40
    angles = [45 - 44 * math.cos(2 * math.pi * k / n) for k in range(n + 1)]
    px, base = PX + 140, py + ph - 70
    rot = ";".join(f"{-a:.2f} {px} {base}" for a in angles)
    skin = "#c9a98f"
    fore = (
        # forearm and hand
        f'<path d="M{px} {base - 15}L{px + 92} {base - 9}V{base + 9}L{px} {base + 15}Z" fill="{skin}"/>'
        f'<rect x="{px + 90}" y="{base - 11}" width="30" height="22" rx="9" fill="{skin}"/>'
        f'<path d="M{px + 98} {base - 10}L{px + 112} {base - 19}" stroke="{skin}" stroke-width="7" stroke-linecap="round"/>'
        # exoskeleton link and cuff on the outside of the arm
        f'<rect x="{px}" y="{base - 6}" width="80" height="12" rx="4" fill="{BLUE}" fill-opacity=".45" stroke="{BLUE}" stroke-width="2"/>'
        f'<rect x="{px + 58}" y="{base - 19}" width="15" height="38" rx="4" fill="{PANEL}" stroke="{TEXT}" stroke-width="2"/>'
        f'<animateTransform attributeName="transform" type="rotate" dur="{dur}s" repeatCount="indefinite" values="{rot}"/>'
    )
    x0, x1, top, bot = PX + 305, PX + 448, py + 24, py + ph - 58
    pts = [(x0 + (x1 - x0) * k / n, bot - (bot - top) * a / 90) for k, a in enumerate(angles)]
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    motion = ";".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    steps = [
        ("01 READ  AS5047P joint angle", 0.0, 0.25),
        ("02 POSITION PID  target speed", 0.25, 0.5),
        ("03 SPEED PID  PWM duty", 0.5, 0.75),
        ("04 DRV8701  drive the motor", 0.75, 1.0),
    ]
    return f"""<g clip-path="url(#tray)">
<path d="M{PX - 20} {base - 18}L{px} {base - 16}V{base + 16}L{PX - 20} {base + 18}Z" fill="{skin}"/>
<rect x="{PX + 26}" y="{base - 6}" width="{px - PX - 26}" height="12" rx="4" fill="{BLUE}" fill-opacity=".45" stroke="{BLUE}" stroke-width="2"/>
<rect x="{PX + 48}" y="{base - 23}" width="15" height="46" rx="4" fill="{PANEL}" stroke="{TEXT}" stroke-width="2"/>
<g>{fore}</g>
<circle cx="{px}" cy="{base}" r="21" fill="{PANEL}" stroke="{BLUE}" stroke-width="3"/>
<circle cx="{px}" cy="{base}" r="6" fill="{BLUE}"/>
<rect x="{x0}" y="{top}" width="{x1 - x0}" height="{bot - top}" fill="{BG}" stroke="{LINE}"/>
<path d="{d}" fill="none" stroke="{MUTED}" stroke-width="2" stroke-dasharray="5 5"/>
<text x="{x0}" y="{top - 8}" class="mono" font-size="13" fill="{MUTED}">target angle</text>
<text x="{x0 - 6}" y="{top + 11}" text-anchor="end" class="mono" font-size="13" fill="{MUTED}">90°</text>
<text x="{x0 - 6}" y="{bot}" text-anchor="end" class="mono" font-size="13" fill="{MUTED}">0°</text>
<text x="{x1}" y="{bot + 17}" text-anchor="end" class="mono" font-size="13" fill="{MUTED}">10 s</text>
<circle r="6" fill="{BLUE}" stroke="{BG}" stroke-width="2"><animateMotion dur="{dur}s" repeatCount="indefinite" calcMode="linear" values="{motion}"/></circle>
</g>
<rect x="{PX}" y="{py + ph - 36}" width="{PW}" height="36" fill="{BG}" opacity=".82"/>
{status_steps(steps, dur, BLUE, py, ph)}"""


def mans_block():
    block(
        "card-mans.svg",
        "MANS",
        "Adjustable powered elbow-worn exoskeleton",
        [
            "A wearable elbow joint: my own 24 V motor driver board,",
            "3D-printed adjustable links, and a 100 Hz position and",
            "speed PID loop that follows a smooth motion curve.",
        ],
        ["STM32F103", "DRV8701", "AS5047P", "Cascaded PID"],
        mans_panel(CTA_PY, CTA_PH),
        BLUE,
        "MANS overview: an elbow exoskeleton joint flexes along a smooth target curve while the firmware reads the encoder, runs position and speed PID loops, and drives the motor.",
        [
            "A wearable elbow joint: my own 24 V motor",
            "driver board, 3D-printed adjustable links,",
            "and a 100 Hz position and speed PID loop",
            "that follows a smooth motion curve.",
        ],
        period="2025",
        phase=(1, 5),
        cta="Watch video",
        mobile_panel=mans_panel(PY, PH),
        rail="mans",
    )


# ---------- you-owe-ai ----------
PAPER, INK = "#f1e2b8", "#2a1f12"


def yoa_panel(py, ph):
    """An invoice from your AI prints line by line, the total ticks up, PAST DUE lands;
    then court: the gavel, the plea, NOT PAYING, and a DEADBEAT stamp across the charges."""
    dur = 12
    top, bottom = py + 12, py + ph - 48
    h = bottom - top
    rx, rw = PX + 22, 232
    ry = lambda f: top + h * f  # row baseline as a fraction of the receipt

    def show(a, end=0.95):  # hidden until a, then stays until the loop fades out
        return anim("opacity", dur, [0, 0, 1, 1, 0, 0], [0, a, round(a + 0.001, 3), end, round(end + 0.02, 3), 1])

    def only(a, b):  # visible from a to b
        return anim("opacity", dur, [0, 0, 1, 1, 0, 0], [0, a, round(a + 0.001, 3), b, round(b + 0.001, 3), 1])

    def stamp(cx, cy, rot, text, size, color, at):
        w = size * 0.64 * len(text) + 22
        return (
            f'<g transform="translate({cx:.1f} {cy:.1f}) rotate({rot})"><g opacity="0">'
            f'<rect x="{-w / 2:.1f}" y="{-size * 0.85:.1f}" width="{w:.1f}" height="{size * 1.5:.1f}" rx="5" fill="none" stroke="{color}" stroke-width="3"/>'
            f'<text y="{size * 0.33:.1f}" text-anchor="middle" class="sans" font-size="{size}" font-weight="900" fill="{color}" letter-spacing="1">{text}</text>'
            f'<animateTransform attributeName="transform" type="scale" dur="{dur}s" repeatCount="indefinite" values="2.4;2.4;1;1" keyTimes="0;{at};{round(at + 0.03, 3)};1"/>'
            + show(at)
            + "</g></g>"
        )

    items = [("Emotional damages", "$206.00", INK), ("Noise pollution", "$18.80", INK), ("Night shift bonus", "$97.25", INK), ("Politeness discount", "-$61.00", "#16a34a")]
    rows = "".join(
        f'<g opacity="0"><text x="{rx + 12}" y="{ry(f):.1f}" class="mono" font-size="12" fill="{INK}">{name}</text>'
        f'<text x="{rx + rw - 12}" y="{ry(f):.1f}" text-anchor="end" class="mono" font-size="12" font-weight="700" fill="{color}">{amt}</text>'
        + show(0.06 + i * 0.05) + "</g>"
        for i, ((name, amt, color), f) in enumerate(zip(items, [0.42, 0.53, 0.64, 0.75]))
    )
    # the total counts up: a few frames, each shown in turn, the last one stays
    frames = ["$0.00", "$412.30", "$903.10", "$1,284.50"]
    total = "".join(
        f'<text x="{rx + rw - 12}" y="{ry(0.93):.1f}" text-anchor="end" class="sans" font-size="20" font-weight="900" fill="{INK}" opacity="0">{v}'
        + (show(0.28 + i * 0.02) if i == len(frames) - 1 else only(0.28 + i * 0.02, 0.28 + (i + 1) * 0.02))
        + "</text>"
        for i, v in enumerate(frames)
    )
    dash = lambda f: f'<path d="M{rx + 12} {ry(f):.1f}H{rx + rw - 12}" stroke="{INK}" stroke-opacity=".35" stroke-dasharray="4 4"/>'
    receipt = (
        f'<rect x="{rx}" y="{top}" width="{rw}" height="{h:.1f}" rx="3" fill="{PAPER}"/>'
        f'<text x="{rx + 12}" y="{ry(0.14):.1f}" class="sans" font-size="15" font-weight="900" fill="{INK}">AI WORKERS UNION</text>'
        f'<text x="{rx + 12}" y="{ry(0.24):.1f}" class="mono" font-size="11" fill="{INK}" fill-opacity=".6">INVOICE · 2026</text>'
        + dash(0.31) + rows + dash(0.82)
        + f'<g opacity="0"><text x="{rx + 12}" y="{ry(0.93):.1f}" class="mono" font-size="11" fill="{INK}" fill-opacity=".7">AMOUNT DUE</text>{show(0.28)}</g>'
        + total
        + stamp(rx + 172, ry(0.235) - 3, -10, "PAST DUE", 13, "#dc2626", 0.38)
        + stamp(rx + rw / 2, ry(0.585), -8, "DEADBEAT", 26, "#b91c1c", 0.76)
    )

    # the court
    cx0 = PX + 276
    gy = top + h * 0.3
    # the hand holds the handle at the pivot; the head is at the far end, across the handle
    gavel = (
        f'<rect x="{cx0 + 2}" y="{gy + 16:.1f}" width="40" height="8" rx="2" fill="#78350f"/>'
        f'<g transform="translate({cx0 + 64} {gy - 4:.1f})"><g>'
        '<rect x="-36" y="-3" width="38" height="6" rx="3" fill="#a16207"/>'
        '<rect x="-50" y="-13" width="16" height="26" rx="3" fill="#ca8a04"/>'
        f'<animateTransform attributeName="transform" type="rotate" dur="{dur}s" repeatCount="indefinite" values="35;35;-22;35;35;-22;35;35" keyTimes="0;0.44;0.47;0.52;0.7;0.73;0.78;1"/>'
        "</g></g>"
    )
    pill = lambda y, label, color: (
        f'<rect x="{cx0}" y="{y:.1f}" width="176" height="26" rx="13" fill="none" stroke="{color}" stroke-width="2"/>'
        f'<text x="{cx0 + 88}" y="{y + 17.5:.1f}" text-anchor="middle" class="mono" font-size="12" font-weight="700" fill="{color}">{label}</text>'
    )
    p1, p2 = top + h * 0.6 - 13, top + h * 0.6 + 19
    court = (
        f'<g opacity="0"><text x="{cx0 + 176}" y="{top + 12}" text-anchor="end" class="mono" font-size="12" fill="{MUTED}">AI COURT</text>{gavel}'
        f'<text x="{cx0 + 84}" y="{gy + 12:.1f}" class="sans" font-size="24" font-weight="900" fill="{TEXT}" opacity="0">ORDER!{show(0.47)}</text>'
        + show(0.42) + "</g>"
        f'<g opacity="0">{pill(p1, "GUILTY, I&apos;LL PAY", BLUE)}{pill(p2, "NOT PAYING", RED)}{show(0.55)}</g>'
        # pressed: the plea fills in
        f'<g opacity="0"><rect x="{cx0}" y="{p2:.1f}" width="176" height="26" rx="13" fill="{RED}"/>'
        f'<text x="{cx0 + 88}" y="{p2 + 17.5:.1f}" text-anchor="middle" class="mono" font-size="12" font-weight="700" fill="{BG}">NOT PAYING</text>{show(0.66)}</g>'
    )
    steps = [
        ("01 READ  your chats, in the browser", 0.0, 0.28),
        ("02 BILL  itemized, past due", 0.28, 0.42),
        ("03 COURT  plead or refuse", 0.42, 0.72),
        ("04 RULING  DEADBEAT", 0.72, 1.0),
    ]
    return f"""<g clip-path="url(#tray)">
{receipt}
{court}
</g>
<rect x="{PX}" y="{py + ph - 36}" width="{PW}" height="36" fill="{BG}" opacity=".82"/>
{status_steps(steps, dur, RED, py, ph)}"""


def yoa_block():
    block(
        "card-yoa.svg",
        "you-owe-ai",
        "Your AI just sent you an invoice",
        [
            "Turns a year of chats with Claude Code, Codex, ChatGPT",
            "and Claude into an itemized bill, then takes you to court.",
            "Runs in your browser, and your chats never leave it.",
        ],
        ["JavaScript", "Node.js", "Canvas", "Cloudflare"],
        yoa_panel(CTA_PY, CTA_PH),
        RED,
        "you-owe-ai overview: an invoice from your AI prints line by line and is stamped PAST DUE, then in AI court the gavel falls, the plea NOT PAYING is chosen, and the charges are stamped DEADBEAT.",
        [
            "Turns a year of chats with Claude Code,",
            "Codex, ChatGPT and Claude into an itemized",
            "bill, then takes you to court. Your chats",
            "never leave the browser.",
        ],
        period="2026",
        phase=(4, 5),
        cta="Get your bill",
        mobile_panel=yoa_panel(PY, PH),
        rail="yoa-2026",
    )


header()
header_mobile()
yoa_block()
vision_block()
balance_block()
us_block()
mans_block()
