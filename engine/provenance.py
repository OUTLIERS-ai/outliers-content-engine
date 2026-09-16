"""
provenance.py  --  record what a post is at the moment you decide to publish it.

WHY
    Months later you will want to know which of your posts worked and why. That question needs
    three facts per post: which brief it came from, which of your positions it used, and who
    wrote the words (you, the machine, or the machine then you). Those facts are free at the
    moment of publishing and very hard to reconstruct afterwards, because the draft files get
    edited and the published text drifts from them.

    So before you paste a post into LinkedIn, stamp it. One line goes into
    data/publish-provenance.jsonl. Nothing is ever edited; a correction is a new line.

THE KEY IS THE TEXT
    Each record is keyed by a hash of the post's words, with case, spacing, punctuation and your
    sign-off line removed first. So the same post still matches after a copy-paste round trip,
    and `reconcile` can match a row in your-voice/my-posts.csv back to its record by text alone.

FIELDS READ FROM THE DRAFT'S FRONTMATTER
    piece, wave, brief_id, author (default "machine"), premise_source, feeling, gate_override

Run:  python engine/provenance.py stamp <draft.md>
      python engine/provenance.py stamp-all [--dir <drafts folder>]     skips posts already stamped
      python engine/provenance.py audit
      python engine/provenance.py reconcile     optional: match my-posts.csv rows to records
      python engine/provenance.py --selftest
"""

import collections
import csv
import datetime
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitconfig  # noqa: E402
from post_checks import extract_body  # noqa: E402

LEDGER = kitconfig.resolve(kitconfig.PROVENANCE_FILE)
MY_POSTS = kitconfig.resolve(kitconfig.MY_POSTS_FILE)
FM_RE = re.compile(r"\A\ufeff?---\s*\n(.*?)\n---\s*\n", re.S)


def _now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def body_of(text):
    """The post as it will be sent: the same live text post_checks.py checks (frontmatter,
    notes, headings and superseded '## Draft N' sections removed)."""
    return extract_body(text).strip()


def key_of(body):
    s = body.lower().replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    signoff = str(kitconfig.get("signoff_line") or "").strip().lower().replace("\u2019", "'")
    if signoff:
        s = s.replace(signoff, "")
    s = re.sub(r"[^\w]+", " ", s).strip()
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def frontmatter(text):
    m = FM_RE.search(text)
    if not m:
        return {}
    out = {}
    for line in m.group(1).split("\n"):
        fm = re.match(r"^([a-zA-Z_][\w-]*):\s*(.*)$", line)
        if fm:
            out[fm.group(1)] = fm.group(2).strip().strip('"').strip("'")
    return out


def _read_ledger():
    if not LEDGER.exists():
        return []
    out = []
    with open(LEDGER, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def stamp(path):
    p = kitconfig.cli_path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    fm = frontmatter(text)
    body = body_of(text)
    if not body:
        raise SystemExit("refused: no post text in %s" % path)
    rec = {
        "key": key_of(body),
        "stamped_at": _now(),
        "source_file": kitconfig.rel(p),
        "piece": fm.get("piece") or p.stem,
        "wave": fm.get("wave") or "",
        "brief_id": fm.get("brief_id") or "",
        "author": fm.get("author") or "machine",
        "premise_source": fm.get("premise_source") or "",
        "feeling": fm.get("feeling") or "",
        "gate_override": fm.get("gate_override") or "",
        "chars": len(body),
        "shipped_text": body,
    }
    kitconfig.append_jsonl(LEDGER, rec)
    return rec


def stamp_all(folder):
    seen = {r["key"] for r in _read_ledger()}
    done, skipped = [], 0
    for f in sorted(Path(folder).glob("*.md")):
        if f.name.startswith("_"):
            continue
        b = body_of(f.read_text(encoding="utf-8", errors="replace"))
        if not b:
            continue
        if key_of(b) in seen:
            skipped += 1
            continue
        done.append(stamp(str(f)))
        seen.add(key_of(b))
    return done, skipped


def reconcile():
    """Match the posts in your-voice/my-posts.csv (column `text`) to stamped records."""
    led = {r["key"]: r for r in _read_ledger()}
    if not MY_POSTS.exists():
        return "no %s to reconcile against (this step is optional)" % kitconfig.rel(MY_POSTS)
    with open(MY_POSTS, encoding="utf-8-sig", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if (r.get("text") or "").strip()]
    hit = [r for r in rows if key_of(r["text"]) in led]
    miss = [r for r in rows if key_of(r["text"]) not in led]
    L = ["RECONCILE  (%s)" % _now()[:10], "=" * 58,
         "stamped records        %d" % len(led),
         "posts in my-posts.csv  %d" % len(rows),
         "matched to a record    %d" % len(hit),
         "no record              %d" % len(miss), ""]
    for r in hit:
        p = led[key_of(r["text"])]
        L.append("  %-10s %-12s %-10s %s" % ((r.get("date") or "?")[:10], p["piece"][:12],
                                            p["author"][:10], p["premise_source"][:40]))
    if miss:
        L += ["", "published but not stamped (usually posts from before you started stamping):"]
        for r in miss[:8]:
            L.append("  %-10s %s" % ((r.get("date") or "?")[:10], r["text"].strip().split("\n")[0][:60]))
        if len(miss) > 8:
            L.append("  ... and %d more" % (len(miss) - 8))
    return "\n".join(L)


def audit():
    led = _read_ledger()
    L = ["PROVENANCE AUDIT  (%s)" % _now()[:10], "=" * 58, "stamped records  %d" % len(led)]
    if not led:
        L += ["", "  Nothing stamped yet. Before you publish a post, run:",
              "    python engine/provenance.py stamp <draft.md>"]
        return "\n".join(L)
    L.append("by author        %s" % dict(collections.Counter(r.get("author", "?") for r in led)))
    L.append("by wave          %s" % dict(collections.Counter(r.get("wave", "?") for r in led)))
    nosrc = [r for r in led if not r.get("premise_source")]
    L.append("no premise_source %d" % len(nosrc))
    for r in nosrc:
        L.append("   %s  %s" % (r.get("piece"), r.get("source_file")))
    return "\n".join(L)


def selftest():
    global LEDGER, MY_POSTS
    real = (LEDGER, MY_POSTS)
    out = []
    kitconfig.use({"signoff_line": "See you Monday."})
    try:
        a = "Hello there.\n\nSee you Monday."
        b = "hello   there!\n\nSee you Monday."
        c = "Hello there."
        out.append("pass: spacing, case and punctuation do not change the key"
                   if key_of(a) == key_of(b) else "FAIL: round trip")
        out.append("pass: the sign-off line is not part of the key"
                   if key_of(a) == key_of(c) else "FAIL: sign-off in key")
        out.append("pass: different posts differ" if key_of(a) != key_of("Something else.")
                   else "FAIL: collision")
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            LEDGER = tdp / "publish-provenance.jsonl"
            MY_POSTS = tdp / "my-posts.csv"
            drafts = tdp / "drafts"
            drafts.mkdir()
            (drafts / "EX-01.md").write_text(
                "---\ntype: social-post\npiece: EX-01\nwave: EX\nauthor: me\n"
                "premise_source: invented-call.md, line 12\n---\n\nInvoices on Friday.\n\nSee you Monday.\n",
                encoding="utf-8")
            (drafts / "EX-02.md").write_text("---\npiece: EX-02\n---\n\nQuotes on Monday.\n", encoding="utf-8")
            done, skipped = stamp_all(drafts)
            out.append("pass: stamp-all stamps each draft" if len(done) == 2 else "FAIL: stamp-all")
            done2, skipped2 = stamp_all(drafts)
            out.append("pass: already-stamped drafts are skipped" if not done2 and skipped2 == 2
                       else "FAIL: re-stamp")
            led = _read_ledger()
            out.append("pass: author read from frontmatter, default 'machine'"
                       if led[0]["author"] == "me" and led[1]["author"] == "machine"
                       else "FAIL: author")
            MY_POSTS.write_text("date,text,impressions,comments,author\n"
                                "2025-05-01,\"invoices on friday.\",100,2,me\n"
                                "2025-05-02,An older post,50,1,me\n", encoding="utf-8")
            rec = reconcile()
            out.append("pass: reconcile matches by text" if "matched to a record    1" in rec
                       else "FAIL: reconcile\n" + rec)
    finally:
        LEDGER, MY_POSTS = real
        kitconfig.use(None)
    good = not any(x.startswith("FAIL") for x in out)
    out.append("SELFTEST %s (%d checks)" % ("PASSED" if good else "FAILED", len(out)))
    return "\n".join(out), good


def main(argv):
    kitconfig.utf8_console()
    if "--selftest" in argv:
        text, good = selftest()
        print(text)
        return 0 if good else 1
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "stamp":
        if len(argv) < 3:
            print("stamp needs a draft path")
            return 2
        r = stamp(argv[2])
        print("stamped %s  author=%s  key=%s" % (r["piece"], r["author"], r["key"]))
    elif cmd == "stamp-all":
        folder = kitconfig.cli_path(argv[argv.index("--dir") + 1]) if "--dir" in argv \
            else kitconfig.path("drafts_dir")
        done, skipped = stamp_all(folder)
        print("stamped %d, already on file %d" % (len(done), skipped))
        for r in done:
            print("  %-12s %-10s %s" % (r["piece"], r["author"], r["source_file"]))
    elif cmd == "reconcile":
        print(reconcile())
    elif cmd == "audit":
        print(audit())
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
