"""
preview_linkedin.py  --  show drafts the way they will look on LinkedIn, then open the page.

WHY
    People read the feed, not a markdown file. LinkedIn cuts the post after roughly the first
    210 characters behind a "see more", and most readers never press it. A post that reads well
    in an editor can die at that fold. This renders every draft as a LinkedIn-style card with the
    real fold, so you judge the hook the way a reader meets it.

WHAT IT READS
    Every .md in the drafts folder (drafts_dir in config.json, or the folders you pass with
    --dir). Files whose name starts with "_" are skipped. Drafts without a `brief_id:` in their
    frontmatter are skipped unless you pass --all, so old notes do not mix with a live wave.
    Only the last "## Draft N" section of a file is shown, if the file has them.

    `image_path:` or `video_path:` in a draft's frontmatter is embedded under the post. A path
    can be absolute, relative to the draft file, or relative to the repo root. A declared file
    that is missing shows as a warning card, never silently.

WHAT IT SHOWS
    Your name, initials and headline from config.json. No like or comment counts: the page does
    not invent numbers.

WHERE IT WRITES
    preview_output in config.json (default preview/linkedin-preview.html). --open opens it in
    your default browser.

Run:  python engine/preview_linkedin.py --open
      python engine/preview_linkedin.py --dir <drafts folder> --open
      python engine/preview_linkedin.py --dir <folder> --commission EXAMPLE --open
      python engine/preview_linkedin.py --selftest
"""
from __future__ import annotations

import argparse
import base64
import datetime
import html
import re
import sys
import tempfile
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitconfig  # noqa: E402

FOLD_CHARS = 210
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
               ".gif": "image/gif", ".webp": "image/webp"}
VIDEO_TYPES = {".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime"}


def split_frontmatter(text: str):
    text = text.lstrip("\ufeff")
    if text.lstrip().startswith("---"):
        parts = text.lstrip().split("---", 2)
        if len(parts) >= 3:
            fm = {}
            for line in parts[1].splitlines():
                if ":" in line and not line.strip().startswith("#"):
                    k, _, v = line.partition(":")
                    fm[k.strip()] = v.strip().strip('"\'')
            return fm, parts[2]
    return {}, text


def final_draft(body: str) -> str:
    """Only the live copy: the highest-numbered '## Draft N' section, if the file has them."""
    heads = [(int(m.group(1)), m.start()) for m in re.finditer(r"^##\s+Draft\s+(\d+)\s*$", body, flags=re.M)]
    if heads:
        _, start = max(heads)
        rest = body[start:]
        rest = rest.split("\n", 1)[1] if "\n" in rest else ""
        nxt = re.search(r"^##\s+(?!Draft\s+\d)", rest, flags=re.M)
        return rest[: nxt.start()] if nxt else rest
    return body


def clean_body(body: str) -> str:
    body = final_draft(body)
    body = re.sub(r"^\s*>.*$", "", body, flags=re.M)          # quote callouts / notes
    body = re.sub(r"^#{1,6}\s.*$", "", body, flags=re.M)      # headings
    body = re.sub(r"^---\s*$", "", body, flags=re.M)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def fold_split(body: str):
    if len(body) <= FOLD_CHARS:
        return body, ""
    cut = body.rfind(" ", 0, FOLD_CHARS)
    if cut == -1:
        cut = FOLD_CHARS
    return body[:cut], body[cut:]


def paras(text: str) -> str:
    out = []
    for line in text.split("\n"):
        out.append(f"<p>{html.escape(line.strip())}</p>" if line.strip() else '<div class="gap"></div>')
    return "\n".join(out)


def _find_asset(value: str, draft: Path):
    p = Path(value)
    for c in ([p] if p.is_absolute() else [draft.parent / p, kitconfig.resolve(value)]):
        if c.exists():
            return c
    return None


def _media_html(path: Path) -> str:
    ext = path.suffix.lower()
    b64 = base64.b64encode(path.read_bytes()).decode()
    if ext in VIDEO_TYPES:
        inner = (f'<video controls loop muted playsinline preload="metadata" '
                 f'src="data:{VIDEO_TYPES[ext]};base64,{b64}"></video>')
        kind = "video"
    else:
        inner = (f'<img src="data:{IMAGE_TYPES.get(ext, "image/png")};base64,{b64}" '
                 f'alt="{html.escape(path.name)}">')
        kind = "image"
    return (f'<div class="media">{inner}<div class="docbar"><span>{html.escape(path.name)}</span>'
            f'<span>{kind}</span></div></div>')


def _missing_html(field: str, value: str) -> str:
    return ('<div class="media"><div class="norender">DECLARED FILE MISSING<br>'
            f'{html.escape(field)} does not resolve:<br>{html.escape(value)}</div></div>')


def post_card(label: str, body: str, extra: str, idx: int, who: dict) -> str:
    head, tail = fold_split(body)
    tail_html = ""
    if tail.strip():
        tail_html = ('<span class="ellipsis">&hellip;</span><button class="seemore">see more</button>'
                     f'<div class="tail">{paras(tail)}</div>')
    return f"""
<article class="post">
  <div class="devmeta"><b>#{idx}</b> &nbsp;&middot;&nbsp; {html.escape(label)}</div>
  <div class="card">
    <header>
      <div class="avatar">{html.escape(who['initials'])}</div>
      <div class="who">
        <div class="name">{html.escape(who['name'])}</div>
        <div class="headline">{html.escape(who['headline'])}</div>
        <div class="time">now</div>
      </div>
    </header>
    <div class="body"><div class="head">{paras(head)}</div>{tail_html}</div>
    {extra}
    <div class="social"><div class="actions"><span>Like</span><span>Comment</span><span>Repost</span><span>Send</span></div></div>
  </div>
</article>"""


def build(dirs, include_all=False, commission=None, echo=print) -> str:
    who = {"name": str(kitconfig.get("author_name") or ""),
           "initials": str(kitconfig.get("author_initials") or "")[:3],
           "headline": str(kitconfig.get("author_headline") or "")}
    prefixes = [c.strip().upper() for c in commission.split(",")] if commission else []
    cards, skipped, missing, notfound = [], [], [], []
    for folder in dirs:
        if not folder.exists():
            notfound.append(str(folder))
            continue
        for f in sorted(folder.glob("*.md")):
            if f.name.startswith("_"):
                continue
            fm, body = split_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
            body = clean_body(body)
            if not body:
                continue
            bid = (fm.get("brief_id") or "").split()[0] if fm.get("brief_id") else ""
            if not include_all and not bid:
                skipped.append(f.name)
                continue
            if prefixes and not any(bid.upper().startswith(p) for p in prefixes):
                skipped.append("%s (not %s)" % (f.name, commission))
                continue
            extra = ""
            for field in ("image_path", "video_path"):
                value = fm.get(field) or ""
                if value.strip().lower() in ("", "none", "null", "~", "-"):
                    continue
                found = _find_asset(value, f)
                if found:
                    extra += _media_html(found)
                else:
                    missing.append("%s: %s -> %s" % (f.name, field, value))
                    extra += _missing_html(field, value)
            age = datetime.date.fromtimestamp(f.stat().st_mtime).isoformat()
            label = "%s \u00b7 %s \u00b7 %s" % (bid or "no brief_id", age, f.stem)
            cards.append(post_card(label, body, extra, len(cards) + 1, who))
    for nf in notfound:
        echo("  folder not found: %s" % nf)
    if missing:
        echo("  %d declared file(s) missing, shown as warning cards:" % len(missing))
        for m in missing:
            echo("     " + m)
    if skipped:
        echo("  skipped %d file(s): %s" % (len(skipped), ", ".join(skipped)))
        echo("  (drafts need `brief_id:` in frontmatter; pass --all to include everything)")

    title = "LinkedIn preview: %s" % who["name"]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
  :root {{ --bg:#f4f2ee; --card:#fff; --line:#e0dfdc; --ink:#000000e6; --dim:#00000099; --blue:#0a66c2; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; color:var(--ink); }}
  .wrap {{ max-width:555px; margin:0 auto; padding:24px 12px 80px; }}
  .top {{ position:sticky; top:0; background:var(--bg); padding:14px 0 10px; z-index:5; border-bottom:1px solid var(--line); margin-bottom:16px; }}
  .top h1 {{ font-size:16px; margin:0 0 4px; }}
  .top p {{ margin:0; font-size:12.5px; color:var(--dim); }}
  .devmeta {{ font:12px ui-monospace,Consolas,monospace; color:#6b6b6b; margin:0 0 6px 2px; }}
  .post {{ margin-bottom:26px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:8px; overflow:hidden; }}
  header {{ display:flex; align-items:flex-start; gap:8px; padding:12px 16px 0; }}
  .avatar {{ width:48px; height:48px; border-radius:50%; background:#1a1a1a; color:#fff; display:grid; place-items:center; font-weight:700; font-size:15px; flex:none; }}
  .who {{ flex:1; min-width:0; line-height:1.25; }}
  .name {{ font-weight:600; font-size:14px; }}
  .headline, .time {{ font-size:12px; color:var(--dim); margin-top:1px; }}
  .body {{ padding:10px 16px 0; font-size:14px; line-height:1.45; overflow-wrap:anywhere; }}
  .body p {{ margin:0; }}
  .gap {{ height:14px; }}
  .tail {{ display:none; }}
  .tail.open {{ display:block; }}
  .seemore {{ background:none; border:0; color:var(--dim); font:inherit; font-size:14px; cursor:pointer; padding:0 0 0 2px; }}
  .seemore:hover {{ color:var(--blue); text-decoration:underline; }}
  .media {{ margin-top:12px; background:#000; }}
  .media img, .media video {{ width:100%; display:block; }}
  .docbar {{ display:flex; justify-content:space-between; padding:8px 12px; background:#f3f2ef; font-size:12px; color:var(--dim); }}
  .norender {{ color:#b00020; background:#fff4f4; padding:40px 16px; text-align:center; font-size:13px; overflow-wrap:anywhere; }}
  .social {{ margin-top:8px; padding:0 16px 6px; border-top:1px solid var(--line); }}
  .actions {{ display:flex; justify-content:space-between; padding:4px 0; }}
  .actions span {{ font-size:13px; color:var(--dim); font-weight:600; padding:8px 10px; }}
</style></head>
<body>
<div class="wrap">
  <div class="top">
    <h1>{html.escape(title)}</h1>
    <p>{len(cards)} draft(s). The body is cut at the real fold; click <b>see more</b> to expand, as a reader must. Refer to a draft by its <b>#</b> when you give feedback.</p>
  </div>
  {''.join(cards) if cards else '<p>No drafts found. Check the folder and that each draft has <code>brief_id:</code> in its frontmatter.</p>'}
</div>
<script>
document.querySelectorAll('.seemore').forEach(b => b.addEventListener('click', () => {{
  const tail = b.parentElement.querySelector('.tail');
  const open = tail.classList.toggle('open');
  b.textContent = open ? 'see less' : 'see more';
  b.previousElementSibling.style.display = open ? 'none' : 'inline';
}}));
</script>
</body></html>"""


def selftest():
    out = []
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        drafts = tdp / "drafts"
        drafts.mkdir()
        long_body = " ".join(["Word%d" % i for i in range(80)])
        (drafts / "one.md").write_text(
            "---\ntype: social-post\napproved: false\nbrief_id: EXAMPLE-01\n---\n\n"
            "## Draft 1\n\nOld version.\n\n## Draft 2\n\n" + long_body + "\n", encoding="utf-8")
        (drafts / "two.md").write_text(
            "---\ntype: social-post\nbrief_id: EXAMPLE-02\nimage_path: missing.png\n---\n\nShort post.\n",
            encoding="utf-8")
        (drafts / "notes.md").write_text("No frontmatter here.\n", encoding="utf-8")
        kitconfig.use({"author_name": "Robin Example", "author_initials": "RE",
                       "author_headline": "Invented headline for a test"})
        try:
            page = build([drafts], echo=lambda *_: None)
        finally:
            kitconfig.use(None)
        checks = [
            ("author name and initials come from config", "Robin Example" in page and ">RE<" in page),
            ("headline comes from config", "Invented headline for a test" in page),
            ("only the last draft section is shown", "Old version." not in page and "Word79" in page),
            ("long body is cut at the fold", "see more</button>" in page),
            ("missing image shows a warning card", "DECLARED FILE MISSING" in page),
            ("draft without brief_id is skipped", "No frontmatter here" not in page),
            ("no invented like or comment counts", not re.search(r"\d+\s+comments", page)),
        ]
        out += ["%s %s" % ("pass:" if ok else "FAIL:", label) for label, ok in checks]
        target = tdp / "preview" / "page.html"
        kitconfig.atomic_write_text(target, page)
        out.append("pass: page written" if target.exists() else "FAIL: page not written")
    good = not any(x.startswith("FAIL") for x in out)
    out.append("SELFTEST %s (%d checks)" % ("PASSED" if good else "FAILED", len(out)))
    return "\n".join(out), good


def main():
    kitconfig.utf8_console()
    ap = argparse.ArgumentParser(description="Render drafts as LinkedIn cards.")
    ap.add_argument("--dir", action="append", default=None,
                    help="a drafts folder (repeatable). Default: drafts_dir in config.json")
    ap.add_argument("--open", action="store_true", help="open the page in your default browser")
    ap.add_argument("--all", action="store_true", help="include drafts without a brief_id")
    ap.add_argument("--commission", default=None,
                    help="only drafts whose brief_id starts with this (comma-separate several)")
    ap.add_argument("--out", default=None, help="where to write the page (default: the preview_output setting in config.json, "
                         "which ships as preview/linkedin-preview.html)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        text, good = selftest()
        print(text)
        return 0 if good else 1
    dirs = [kitconfig.cli_path(d) for d in args.dir] if args.dir else [kitconfig.path("drafts_dir")]
    out = kitconfig.cli_path(args.out) if args.out else kitconfig.path("preview_output")
    kitconfig.atomic_write_text(out, build(dirs, include_all=args.all, commission=args.commission))
    print("preview -> %s" % out)
    if args.open:
        if webbrowser.open(out.resolve().as_uri()):
            print("opened in your default browser")
        else:
            print("could not open a browser; open the file above by hand")
    return 0


if __name__ == "__main__":
    sys.exit(main())
