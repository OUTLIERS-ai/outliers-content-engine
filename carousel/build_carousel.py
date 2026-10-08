"""build_carousel: turns a slide spec (JSON) into LinkedIn carousel slides and a PDF.

What it does, in order:
  1. Runs check/slide_checks.py on the spec. Any hard fail stops here (use --force to render anyway).
  2. Checks both logo files exist in brand/ (use --no-logo if you really want none).
  3. Renders every slide at 1080 x 1350 in a headless Chromium browser, using carousel.css and
     brand/brand.css. Stops if any text runs off the edge of a slide.
  4. Writes, into a folder next to the spec called <spec name>-output/:
        <id>-<theme>.pdf                 the file you upload to LinkedIn as a document
        <id>-<theme>.html                all slides on one page (open it in a browser)
        slides/slide-01.png ...          full-size slides (2160 x 2700, sharp on any screen)
        phone/phone-01.png ...           380 pixels wide, about the size a phone shows. LOOK AT THESE.
        phone/cover-small.png            216 pixels wide, about the size of the cover in the feed
        phone/all-slides.png             every phone-size slide on one sheet

Usage:
  python build_carousel.py specs/example-list.json
  python build_carousel.py specs/example-list.json --theme dark
  python build_carousel.py specs/my-deck.json --force        render even if the checker fails
  python build_carousel.py specs/my-deck.json --no-logo      render without a logo

The theme comes from the spec's "theme" field ("light" or "dark"). --theme overrides it.

Needs: Python 3.10+ (on Windows, Playwright will not install on 3.9 without C++ build tools),
       pip install playwright Pillow, then: python -m playwright install chromium
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import math
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRAND = HERE / "brand"
CSS = HERE / "carousel.css"
sys.path.insert(0, str(HERE / "check"))

from device_rules import DEVICES, device_for  # noqa: E402
import slide_checks  # noqa: E402

W, H = 1080, 1350


# ---------------------------------------------------------------------------------------------
# Safe writing: never overwrite a file in place. Write a temporary file, then swap it in.
# ---------------------------------------------------------------------------------------------
def _tmp_beside(path: Path) -> Path:
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    os.close(fd)
    return Path(name)


def write_bytes_safely(path: Path, data: bytes) -> None:
    tmp = _tmp_beside(path)
    try:
        with open(tmp, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def save_image_safely(img, path: Path, fmt: str, **kw) -> None:
    tmp = _tmp_beside(path)
    try:
        img.save(tmp, fmt, **kw)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def jpegs_to_pdf(jpg_paths) -> bytes:
    """A PDF with 1 page per JPEG, each JPEG copied in byte for byte (no re-compression).

    Replaces img2pdf, whose pikepdf dependency has no ready-made download for Intel Macs from
    pikepdf 10.14 on, so `pip install img2pdf` failed there. Page size matches img2pdf: the image's
    own dpi if it records one, otherwise 96 dpi (a 2160 x 2700 slide is a 1620 x 2025 pt page).
    """
    from PIL import Image

    objs = []  # objs[i] is object number i + 1

    def add(body: bytes) -> int:
        objs.append(body)
        return len(objs)

    add(b"<< /Type /Catalog /Pages 2 0 R >>")
    add(b"")  # the page tree, filled in once the pages exist
    kids = []
    for p in jpg_paths:
        data = Path(p).read_bytes()
        with Image.open(p) as im:
            if im.format != "JPEG" or im.mode not in ("RGB", "L"):
                raise ValueError(f"{p}: expected an RGB or greyscale JPEG, got {im.format} {im.mode}")
            w, h = im.size
            dpi = im.info.get("dpi") or (96, 96)
            space = b"/DeviceRGB" if im.mode == "RGB" else b"/DeviceGray"
        pw, ph = w * 72 / dpi[0], h * 72 / dpi[1]
        img = add(b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace %s "
                  b"/BitsPerComponent 8 /Filter /DCTDecode /Length %d >>\nstream\n%s\nendstream"
                  % (w, h, space, len(data), data))
        draw = b"q %.4f 0 0 %.4f 0 0 cm /Im0 Do Q" % (pw, ph)
        content = add(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(draw), draw))
        kids.append(add(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.4f %.4f] "
                        b"/Resources << /XObject << /Im0 %d 0 R >> >> /Contents %d 0 R >>"
                        % (pw, ph, img, content)))
    objs[1] = (b"<< /Type /Pages /Kids [%s] /Count %d >>"
               % (b" ".join(b"%d 0 R" % k for k in kids), len(kids)))

    out = bytearray(b"%PDF-1.3\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for n, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n%s\nendobj\n" % (n, body)
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(out)


# ---------------------------------------------------------------------------------------------
# HTML for each slide
# ---------------------------------------------------------------------------------------------
def esc(s) -> str:
    return html.escape(str(s or ""))


def rich(s) -> str:
    """Escape text but keep <b> bold spans."""
    return esc(s).replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")


def with_cue(text: str, cue, where: str) -> str:
    """Wrap the highlighted phrase in an inverted block."""
    if not text:
        return ""
    if not cue:
        return rich(text)
    plain = text.replace("<b>", "").replace("</b>", "")
    if cue not in plain:
        raise SystemExit(f"{where}: highlighted phrase {cue!r} is not in {plain[:60]!r}")
    if cue not in text:
        raise SystemExit(f"{where}: a <b> bold span crosses the edge of the highlighted phrase "
                         f"{cue!r}. Bold the whole phrase or none of it.")
    head, _, tail = text.partition(cue)
    return f'{rich(head)}<span class="cue">{esc(cue)}</span>{rich(tail)}'


def graph_svg(nodes, edges, lit) -> str:
    if len(nodes) > 7:
        raise SystemExit(f"{len(nodes)} diagram points; 7 at most")
    cx, cy, R = W / 2, 800, 240
    pts = [(cx + R * math.cos(2 * math.pi * i / len(nodes) - math.pi / 2),
            cy + R * math.sin(2 * math.pi * i / len(nodes) - math.pi / 2)) for i in range(len(nodes))]
    lit_set = {tuple(e) for e in (lit or [])} | {tuple(reversed(e)) for e in (lit or [])}
    lines = "".join(
        f'<line class="edge{" on" if tuple(pair) in lit_set else ""}" '
        f'x1="{pts[a][0]:.0f}" y1="{pts[a][1]:.0f}" x2="{pts[b][0]:.0f}" y2="{pts[b][1]:.0f}"/>'
        for pair in (edges or []) for a, b in [pair])
    dots = []
    for (x, y), name in zip(pts, nodes):
        # Labels sit OUTSIDE the ring so no line crosses them: points near the top go above,
        # near the bottom go below, and points out to the side get a label further out sideways.
        # Keep side labels short (about 14 characters); the overflow check stops the render if
        # one runs off the slide.
        if x < cx - R * 0.5:
            anchor, lx, ly = "end", x - 30, y + 12
        elif x > cx + R * 0.5:
            anchor, lx, ly = "start", x + 30, y + 12
        else:
            anchor, lx, ly = "middle", x, y + (60 if y > cy else -32)
        dots.append(f'<circle class="node" cx="{x:.0f}" cy="{y:.0f}" r="14"/>'
                    f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="{anchor}">{esc(name)}</text>')
    return f'<svg class="graph" viewBox="0 0 {W} {H}">{lines}{"".join(dots)}</svg>'


class Deck:
    def __init__(self, spec: dict, spec_dir: Path, theme: str, logos: dict):
        self.spec = spec
        self.spec_dir = spec_dir
        self.theme = theme
        self.logos = logos
        self.device = device_for(spec)
        self.css_href = ""

    def logo_html(self) -> str:
        b64 = self.logos.get(self.theme)
        return f'<img class="logo" src="data:image/png;base64,{b64}" alt="logo">' if b64 else ""

    def slide_html(self, s: dict) -> str:
        role = s.get("role", "item")
        n = s.get("n", "?")
        swipe = '<div class="swipe">swipe &rarr;</div>' if role == "cover" else ""

        if role == "cover":
            bits = []
            if s.get("kicker_top"):
                bits.append(f'<div class="kicker-top">{esc(s["kicker_top"])}</div>')
            if self.device == "split":
                bits.append(f'<div class="split-top">{esc(s.get("top", ""))}</div>')
                bits.append(f'<div class="split-bottom">{esc(s.get("bottom", ""))}</div>')
                if s.get("title"):
                    bits.append(f'<div class="title split-title">{esc(s["title"])}</div>')
            else:
                lead = f'<span class="lead">{esc(s["lead"])}</span>' if s.get("lead") else ""
                bits.append(f'<div class="title">{lead}{esc(s.get("title", ""))}</div>')
            if s.get("kicker"):
                bits.append(f'<div class="kicker">{esc(s["kicker"])}</div>')
            dev_cls = f" dev-{self.device}" if self.device != "numeral" else ""
            return (f'<div class="slide cover{dev_cls}"><div class="inner">{"".join(bits)}</div>'
                    f'{swipe}{self.logo_html()}</div>')

        if role == "graph":
            g = graph_svg(s.get("nodes") or [], s.get("edges", []), s.get("lit", []))
            idx = f'<div class="idx">{esc(s["idx"])}</div>' if s.get("idx") else ""
            inner = f'<div class="inner">{idx}<div class="title">{esc(s.get("title", ""))}</div></div>'
            return f'<div class="slide graphslide">{g}{inner}{self.logo_html()}</div>'

        shot = s.get("shot")
        num = "" if shot else (f'<div class="num">{esc(s["numeral"])}</div>' if s.get("numeral") else "")
        parts = []
        if s.get("idx"):
            parts.append(f'<div class="idx">{esc(s["idx"])}</div>')
        if s.get("title"):
            cls = "title long" if len(s["title"]) > 34 else "title"
            parts.append(f'<div class="{cls}">{esc(s["title"])}</div>')
        if s.get("does"):
            parts.append(f'<div class="does">{with_cue(s["does"], s.get("cue_does"), f"slide {n} does")}</div>')
        if shot:
            p = Path(shot)
            if not p.is_absolute():
                p = self.spec_dir / shot
            if not p.exists():
                raise SystemExit(f"slide {n}: screenshot {shot!r} not found at {p}")
            b64 = base64.b64encode(p.read_bytes()).decode()
            mime = "image/jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "image/png"
            parts.append(f'<div class="shot"><img src="data:{mime};base64,{b64}" alt="screenshot"></div>')
        if s.get("got"):
            parts.append(f'<div class="got">{with_cue(s["got"], s.get("cue"), f"slide {n} got")}</div>')
        if s.get("cta"):
            parts.append(f'<div class="does"><span class="cue">{esc(s["cta"])}</span></div>')
        if s.get("button"):
            parts.append(f'<div class="btn">{esc(s["button"])}</div>')
        if role == "summary" and s.get("lines"):
            rows = "".join(f'<div class="sumline">{esc(ln.strip())}</div>'
                           for ln in str(s["lines"]).split("\n") if ln.strip())
            parts.append(f'<div class="sumlines">{rows}</div>')
        if sum(1 for k in ("cue", "cue_does") if s.get(k)) > 1:
            raise SystemExit(f"slide {n}: two highlighted phrases. One per slide.")

        role_cls = f" {role}" if role in ("cta", "credibility", "closing", "stakes", "summary") else ""
        if shot:
            role_cls += " hasshot"
        return f'<div class="slide{role_cls}">{num}<div class="inner">{"".join(parts)}</div>{self.logo_html()}</div>'

    def document(self) -> str:
        body = "\n".join(self.slide_html(s) for s in self.spec["slides"])
        return ('<!doctype html><html data-theme="' + self.theme + '"><head><meta charset="utf-8">'
                f'<title>{esc(self.spec.get("id", "carousel"))}</title>'
                f'<link rel="stylesheet" href="{self.css_href}">'
                '<style>body{margin:0;background:#888}</style>'
                '</head><body>' + body + '</body></html>')


# ---------------------------------------------------------------------------------------------
def load_logos(no_logo: bool) -> dict:
    if no_logo:
        return {}
    logos = {}
    for theme, name in (("light", "logo-light.png"), ("dark", "logo-dark.png")):
        p = BRAND / name
        if not p.exists():
            raise SystemExit(f"logo missing: {p}\n"
                             f"Put a PNG with a transparent background there (logo-light.png is for "
                             f"light slides, so dark ink; logo-dark.png is for dark slides, so light "
                             f"ink), or run with --no-logo.")
        logos[theme] = base64.b64encode(p.read_bytes()).decode()
    return logos


def run_checker(spec: dict, force: bool) -> None:
    print("1. checking the spec (check/slide_checks.py)")
    result = slide_checks.check(json.loads(json.dumps(spec)), slide_checks.load_rules())
    for f in result["flags"]:
        print(f"   flag: {f}")
    for h in result["hard_fails"]:
        print(f"   HARD FAIL: {h}")
    if result["pass"]:
        print(f"   passed ({len(result['flags'])} flags to judge yourself)")
    elif force:
        print("   hard fails above, rendering anyway because --force was given")
    else:
        raise SystemExit("   stopped: fix the hard fails above, or re-run with --force to render anyway")


def build(spec_path: Path, theme=None, force=False, no_logo=False) -> Path:
    spec_path = spec_path.resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    theme = theme or spec.get("theme") or "light"
    if theme not in ("light", "dark"):
        raise SystemExit(f"theme must be light or dark, not {theme!r}")
    if device_for(spec) not in DEVICES:
        raise SystemExit(f"unknown cover_device {device_for(spec)!r}. Choose one of: {sorted(DEVICES)}")

    run_checker(spec, force)
    logos = load_logos(no_logo)
    for p in (CSS, BRAND / "brand.css"):
        if not p.exists():
            raise SystemExit(f"missing {p}")

    deck_id = str(spec.get("id") or spec_path.stem)
    out_dir = spec_path.parent / f"{spec_path.stem}-output"
    (out_dir / "slides").mkdir(parents=True, exist_ok=True)
    (out_dir / "phone").mkdir(parents=True, exist_ok=True)
    base = f"{deck_id}-{theme}"

    deck = Deck(spec, spec_path.parent, theme, logos)
    # link the stylesheet by a relative path, so the HTML carries no machine-specific folder names
    try:
        deck.css_href = Path(os.path.relpath(CSS, out_dir)).as_posix()
    except ValueError:  # different drive letters on Windows
        deck.css_href = CSS.as_uri()
    html_path = out_dir / f"{base}.html"
    write_bytes_safely(html_path, deck.document().encode("utf-8"))
    total = len(spec["slides"])
    print(f"2. rendering {total} slides ({theme})")

    from PIL import Image
    from playwright.sync_api import sync_playwright

    pngs = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
            page.goto(html_path.as_uri())
            page.evaluate("async () => { await document.fonts.ready; return true; }")
            page.wait_for_timeout(300)
            fonts_ok = page.evaluate("() => document.fonts.check('800 40px \"Kit Sans\"')")
            overflows = page.evaluate("""() => {
                const out = [];
                document.querySelectorAll('.slide').forEach((slide, i) => {
                    const sr = slide.getBoundingClientRect();
                    const logo = slide.querySelector('.logo');
                    const lr = logo ? logo.getBoundingClientRect() : null;
                    slide.querySelectorAll('img:not(.logo), .lead, .title, .kicker, .kicker-top, .does, .got, .idx, .sumline, .split-top, .split-bottom, .btn, .shot, .graph text, .swipe').forEach(el => {
                        if (el.closest('[data-bleed]') || el.closest('.num')) return;
                        const label = (el.textContent || el.alt || el.className || '').trim().slice(0, 50);
                        // Measure the text actually drawn. A long word spills out of its box, and the
                        // box's own size does not grow, so measuring the box misses the spill.
                        let rects;
                        if (el.tagName === 'IMG' || el.classList.contains('shot')) {
                            rects = [el.getBoundingClientRect()];
                        } else {
                            const range = document.createRange();
                            range.selectNodeContents(el);
                            rects = Array.from(range.getClientRects());
                        }
                        for (const r of rects) {
                            if (r.right > sr.right + 2 || r.left < sr.left - 2 || r.bottom > sr.bottom + 2 || r.top < sr.top - 2) {
                                out.push('slide ' + (i + 1) + ': runs off the slide: ' + label); break;
                            }
                            if (lr && r.width > 0 && r.left < lr.right && r.right > lr.left && r.top < lr.bottom && r.bottom > lr.top) {
                                out.push('slide ' + (i + 1) + ': sits on top of the logo: ' + label); break;
                            }
                        }
                    });
                });
                return out.slice(0, 10);
            }""")
            if overflows:
                raise SystemExit("LAYOUT FAULT: shorten the copy (or move the logo in brand/brand.css):\n  "
                                 + "\n  ".join(overflows))
            loc = page.locator(".slide")
            for i in range(loc.count()):
                png = out_dir / "slides" / f"slide-{i + 1:02d}.png"
                tmp = _tmp_beside(png)
                try:
                    loc.nth(i).screenshot(path=str(tmp), type="png")
                    os.replace(tmp, png)
                finally:
                    if tmp.exists():
                        tmp.unlink()
                pngs.append(png)
        finally:
            browser.close()
    if not fonts_ok:
        print("   note: the brand font did not load, a fallback font was used. Check brand/brand.css.")

    print("3. writing the PDF")
    jpgs = []
    for p in pngs:
        j = p.with_suffix(".jpg")
        save_image_safely(Image.open(p).convert("RGB"), j, "JPEG", quality=90, optimize=True, progressive=True)
        jpgs.append(str(j))
    pdf = out_dir / f"{base}.pdf"
    write_bytes_safely(pdf, jpegs_to_pdf(jpgs))

    print("4. writing phone-size copies")
    phones = []
    for i, p in enumerate(pngs, start=1):
        im = Image.open(p)
        small = im.resize((380, int(380 * im.height / im.width)), Image.LANCZOS)
        dst = out_dir / "phone" / f"phone-{i:02d}.png"
        save_image_safely(small, dst, "PNG")
        phones.append(small)
    if pngs:
        im = Image.open(pngs[0])
        save_image_safely(im.resize((216, int(216 * im.height / im.width)), Image.LANCZOS),
                          out_dir / "phone" / "cover-small.png", "PNG")
        cols = min(4, len(phones))
        rows = math.ceil(len(phones) / cols)
        pw_, ph_, gap = phones[0].width, phones[0].height, 16
        sheet = Image.new("RGB", (cols * pw_ + (cols + 1) * gap, rows * ph_ + (rows + 1) * gap), (128, 128, 128))
        for k, ph in enumerate(phones):
            sheet.paste(ph.convert("RGB"), (gap + (k % cols) * (pw_ + gap), gap + (k // cols) * (ph_ + gap)))
        save_image_safely(sheet, out_dir / "phone" / "all-slides.png", "PNG")

    size_mb = pdf.stat().st_size / 1e6
    print(f"\nDone. {total} slides.")
    print(f"  PDF:    {pdf}  ({size_mb:.1f} MB)")
    print(f"  Phone:  {out_dir / 'phone'}")
    print("  Next: open every image in the phone folder and read each slide at that size before posting.")
    return pdf


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Render a carousel spec to slides and a PDF.")
    ap.add_argument("spec", help="path to the slide spec JSON")
    ap.add_argument("--theme", choices=("light", "dark"), help="override the spec's theme")
    ap.add_argument("--force", action="store_true", help="render even if the checker finds hard fails")
    ap.add_argument("--no-logo", action="store_true", help="render with no logo")
    a = ap.parse_args(argv)
    build(Path(a.spec), a.theme, a.force, a.no_logo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
