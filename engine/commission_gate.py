"""
commission_gate.py  --  checks a BRIEF before any drafting starts. It never judges a draft.

WHY IT EXISTS
    The cheapest moment to find out a post has nothing to say is before it is written. A brief
    that cannot name its reader, its source, or who will disagree with it produces a draft that
    reads as competent and says nothing, and no amount of editing fixes that afterwards.

WHAT A BRIEF MUST CARRY (frontmatter)
    grounding            path to the wave's GROUNDING.md, which must exist
    premise_source       where the position came from (a transcript and line, a post, a note)
    named_reader         the one person this is for
    grain                the reaction it should produce AND who will dislike it
    buyer_pays_for       something that reader pays for today
    buyer_loses          something that reader loses today
    buyer_cant_picture   something that reader cannot picture building
    optional: hook, scene_source, format, format_rationale, lane_justified

THE CHECKS, IN ORDER
    unfilled      no line anywhere in the brief still reads [FILL IN (the template is not filled)
    grounding     the GROUNDING.md exists on disk, not merely named
    premise       the source is a real source, not "inferred" or "assumed"
    the scroll    if a hook is given: 2 lines at most, a short first line, no sourcing shown
    one idea      a named reader
    the spike     a grain field that names who will dislike it
    the human     a scene source, or a plain statement that there is none
    the buyer     the three buyer fields, plus subjects you have banned in config.json
                  (each banned subject is a plain word or phrase, matched as whole words ignoring
                  case; an entry with "regex": true is read as a regular expression instead)
    no pitching   pitch words from config.json in the brief body
    no brackets   no word-count ranges ("200-300 words"); a drafter handed a range fills it
    lessons       the brief carries every live lesson from data/findings.jsonl, up to date

THE LESSONS BLOCK
    --stamp writes EVERY live lesson into the brief, grouped by step, between two markers, and
    records that it did. The check then refuses the brief if a lesson has been added or retired
    since, so a drafter can never start from an out-of-date brief. Re-stamp and check again.

Run:  python engine/commission_gate.py --stamp <brief.md> [...]
      python engine/commission_gate.py <brief.md> [...]      exit 0 = may be briefed
      python engine/commission_gate.py --selftest
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitconfig  # noqa: E402
import assert_not_evidence  # noqa: E402
import findings as _findings  # noqa: E402

FM_RE = re.compile(r"\A\ufeff?---\s*\n(.*?)\n---\s*\n", re.S)


def frontmatter(text: str) -> dict:
    m = FM_RE.search(text)
    if not m:
        return {}
    out, key = {}, None
    for line in m.group(1).split("\n"):
        fm = re.match(r'^([a-zA-Z_][\w-]*):\s*(.*)$', line)
        if fm:
            key = fm.group(1)
            out[key] = fm.group(2).strip().strip('"').strip("'")
        elif key and line.startswith((" ", "\t")) and out.get(key) is not None:
            out[key] = (out[key] + " " + line.strip().strip('"').strip("'")).strip()
    return out


def _missing(v) -> bool:
    return not v or v.strip().lower() in {"none", "tbd", "todo", "-", "n/a", "|", ">"}


BRACKET_RE = re.compile(
    r"\b\d{2,4}\s*[-\u2013]\s*\d{2,4}\s*(?:words?)?\b"
    r"|\bceiling\s+\d{2,4}\b|\bword band\b|\bword bracket\b", re.I)

# ---- the lessons block ----------------------------------------------------------------
STAMP_OPEN = "<!-- RETURN-PATH:BEGIN -->"
STAMP_CLOSE = "<!-- RETURN-PATH:END -->"
STAMP_RE = re.compile(re.escape(STAMP_OPEN) + r".*?" + re.escape(STAMP_CLOSE), re.S)


def _current_block() -> str:
    ids = _findings.live_ids()
    return "%s\n<!-- ids:%s -->\n\n%s\n%s" % (STAMP_OPEN, ",".join(ids), _findings.brief(), STAMP_CLOSE)


def _stamped_ids(text: str):
    m = STAMP_RE.search(text)
    if not m:
        return None
    ids = re.search(r"<!-- ids:([^>]*)-->", m.group(0))
    return [i.strip() for i in (ids.group(1).split(",") if ids else []) if i.strip()]


def stamp(path: Path) -> str:
    """Write every live lesson into the brief and record that the brief received them."""
    text = path.read_text(encoding="utf-8", errors="replace")
    block = _current_block()
    if STAMP_RE.search(text):
        new = STAMP_RE.sub(lambda _m: block, text, count=1)
        what = "refreshed"
    else:
        new = text.rstrip() + "\n\n" + block + "\n"
        what = "added"
    kitconfig.atomic_write_text(path, new)
    ids = _findings.live_ids()
    _findings.record_applied(path.stem, ids)
    return "%s the lessons block (%d lesson(s), all steps) and recorded it" % (what, len(ids))


def _resolve_grounding(g: str, brief: Path):
    """Accept an absolute path, a path from the repo root, or a path next to the brief."""
    p = Path(g)
    candidates = [p] if p.is_absolute() else [kitconfig.resolve(g), brief.parent / g]
    for c in candidates:
        if c.exists():
            return c
    return None


CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _plain_pattern(phrase: str):
    """A plain word or phrase, matched as whole words, ignoring case and extra spaces."""
    words = phrase.split()
    return re.compile(r"(?<!\w)" + r"\s+".join(re.escape(w) for w in words) + r"(?!\w)", re.I)


def _compile_subjects():
    """Each banned_subjects entry is {pattern, reason}: a plain word or phrase by default, or a
    regular expression when the entry also has "regex": true."""
    out, errors = [], []
    for i, item in enumerate(kitconfig.get("banned_subjects") or []):
        if not isinstance(item, dict) or not str(item.get("pattern") or "").strip():
            continue
        pattern = str(item["pattern"])
        reason = str(item.get("reason") or "banned subject").strip().rstrip(".")
        if CONTROL_RE.search(pattern):
            errors.append("banned_subjects[%d] pattern %r contains a hidden control character, so it "
                          "can never match. In JSON a backslash followed by b becomes one. Write the "
                          "plain word instead, for example \"crypto\"" % (i, pattern))
            continue
        if item.get("regex") is True:
            try:
                out.append((re.compile(pattern, re.I), reason))
            except re.error as exc:
                errors.append("banned_subjects[%d] pattern %r is not a valid regular expression: %s"
                              % (i, pattern, exc))
            continue
        if "\\" in pattern:
            errors.append("banned_subjects[%d] pattern %r contains a backslash, which a plain word "
                          "never needs. Write the plain word or phrase, or add \"regex\": true to "
                          "this entry if you meant a regular expression" % (i, pattern))
            continue
        out.append((_plain_pattern(pattern), reason))
    return out, errors


def unfilled_lines(text: str):
    """Line numbers (from 1) of every line that still carries a template [FILL IN marker."""
    return [n for n, line in enumerate(text.splitlines(), 1) if "[FILL IN" in line.upper()]


def check(path: Path):
    """Returns (hard, flags) for one brief."""
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = frontmatter(text)
    hard, flags = [], []
    L = lambda lens, msg: hard.append(f"[{lens}] {msg}")  # noqa: E731
    fm_match = FM_RE.search(text)
    body = text[fm_match.end():] if fm_match else text
    if not fm_match:
        L("FORMAT", "no frontmatter found. The brief must start with a --- block of fields")

    # unfilled template lines
    unfilled = unfilled_lines(text)
    if unfilled:
        L("UNFILLED", "the brief still has unfilled template lines: %d line(s) still read [FILL IN, "
                      "first at line(s) %s. Fill them in, or delete the optional ones you do not use"
                      % (len(unfilled), ", ".join(str(n) for n in unfilled[:3])))

    # grounding
    g = fm.get("grounding")
    if _missing(g):
        L("GROUNDING", "no `grounding:` field. Point it at the wave's GROUNDING.md")
    elif _resolve_grounding(g, path) is None:
        L("GROUNDING", f"`grounding:` points at {g}, which does not exist (looked from the repo "
                       "root and next to the brief)")

    # premise
    ps = fm.get("premise_source")
    refused = [w for w in (kitconfig.get("premise_source_refused_words") or []) if isinstance(w, str) and w.strip()]
    if _missing(ps):
        L("PREMISE", "no `premise_source:`. Say where the position came from: a transcript and "
                     "line, a post, a note. Reasoning about the reader is not a source")
    else:
        pm = (re.search(r"\b(?:%s)\b" % "|".join(re.escape(w) for w in refused), ps, re.I)
              if refused else None)
        if pm:
            L("PREMISE", f"`premise_source` is not a source: it says {pm.group(0)!r} "
                         f"({ps[:70]!r}). Name the file and entry the opinion was copied from")

    # the scroll
    hook = fm.get("hook") or ""
    if hook:
        lines = [x for x in re.split(r"\s*//\s*|\n", hook) if x.strip()]
        max_words = kitconfig.get("hook_first_line_max_words")
        if len(lines) > 2:
            L("SCROLL", f"the hook is {len(lines)} lines; LinkedIn shows about 2 before 'see more'")
        first = lines[0] if lines else ""
        if max_words and len(first.split()) > int(max_words):
            L("SCROLL", f"hook line 1 is {len(first.split())} words (setting: {max_words}). "
                        "It has become the body")
        if re.match(r"^\s*I\b", first):
            flags.append("[SCROLL] hook opens on 'I'. Fine for your own story; recast it if the "
                         "post is a verdict aimed at the reader")
        ah, _ = assert_not_evidence.scan(hook)
        if ah:
            L("SCROLL", f"the hook shows its sourcing: {ah[0]}")

    # one idea
    if _missing(fm.get("named_reader")):
        L("ONE IDEA", "no `named_reader:`. Name the one person this post is for")

    # the spike
    grain = fm.get("grain") or ""
    if _missing(grain):
        L("SPIKE", "no `grain:`. Name the reaction the post produces AND who will dislike it. "
                   "A post nobody could disagree with is not worth commissioning")
    else:
        if not re.search(r"dislike|disagree|argue|object|annoy|upset|angry|threat|push back|hate",
                         grain, re.I):
            L("SPIKE", "`grain:` does not say WHO WILL DISLIKE IT. Half the test is missing")
        if len(grain.split()) < 12:
            flags.append("[SPIKE] `grain:` is very short; a real one names a specific reaction")

    # the human
    scene = fm.get("scene_source") or ""
    if _missing(scene):
        flags.append("[HUMAN] no `scene_source:`. Allowed for a pure argument post, but say so "
                     "rather than leaving it blank")
    elif re.search(r"\bcandidate\b", scene, re.I) and not re.search(r"confirm|checked|approved", scene, re.I):
        L("HUMAN", "the scene is marked `candidate` with no note that you confirmed it happened")

    # the buyer
    for field, what in (("buyer_pays_for", "something the reader PAYS FOR"),
                        ("buyer_loses", "something the reader LOSES"),
                        ("buyer_cant_picture", "something the reader CANNOT PICTURE BUILDING")):
        if _missing(fm.get(field)):
            L("BUYER", f"no `{field}:`. Name {what}. A brief that cannot answer all three is "
                       "aimed at nobody")

    # banned subjects (config). Scan the frontmatter subject fields and the brief body, with
    # the brief's own plumbing removed first so it does not trip on itself: the lessons block,
    # quote callouts, inline code, file paths, and anything under a "## THE RULES" heading.
    scan_body = re.split(r"^##\s+THE RULES", body, maxsplit=1, flags=re.M)[0]
    scan_body = STAMP_RE.sub(" ", scan_body)
    scan_body = re.sub(r"<!--.*?-->", " ", scan_body, flags=re.S)
    scan_body = re.sub(r"^\s*>.*$", " ", scan_body, flags=re.M)
    scan_body = re.sub(r"`[^`]*`", " ", scan_body)
    scan_body = re.sub(r"\S*[/\\]\S*", " ", scan_body)
    subject_blob = " ".join(str(fm.get(k) or "") for k in
                            ("subject", "premise", "hook", "hook_intent")) + " " + scan_body
    subjects, errors = _compile_subjects()
    for e in errors:
        L("CONFIG", e)
    if not fm.get("lane_justified"):
        for rx, why in subjects:
            m = rx.search(subject_blob)
            if m:
                L("BUYER", f"subject is on your banned list ({m.group(0)!r}): {why}. If this post "
                           "genuinely enters through the reader's problem, say how in `lane_justified:`")

    # no pitching
    pitch = [w for w in (kitconfig.get("pitch_words") or []) if isinstance(w, str) and w.strip()]
    if pitch:
        body_no_stamp = STAMP_RE.sub(" ", body)
        rx = re.compile(r"(?<!\w)(?:%s)(?!\w)" % "|".join(
            r"\s+".join(re.escape(x) for x in w.split()) for w in pitch), re.I)
        found = sorted({m.group(0).lower() for m in rx.finditer(body_no_stamp)})
        if found:
            L("PITCH", f"pitch language in the brief: {found}. Content earns trust, it does not sell")

    # no length brackets
    for field in ("format", "format_rationale", "length"):
        m = BRACKET_RE.search(fm.get(field) or "")
        if m:
            L("LENGTH", f"`{field}:` carries a word-count range {m.group(0)!r}. A drafter handed a "
                        "range fills it. Let length come out of the content")

    # the lessons, last, so it is the final check before a drafter
    stamped = _stamped_ids(text)
    want = _findings.live_ids()
    if stamped is None:
        L("LESSONS", "carries no lessons block. Run: python engine/commission_gate.py --stamp "
                     + str(path))
    elif sorted(stamped) != want:
        missing = [i for i in want if i not in stamped]
        stale = [i for i in stamped if i not in want]
        L("LESSONS", "the lessons block is out of date (missing %s, retired but still present %s). "
                     "Re-stamp it." % (missing or "none", stale or "none"))
    return hard, flags


def selftest():
    """Runs in a temporary folder with invented briefs and lessons. Your files are untouched."""
    out = []
    real = (_findings.STORE, _findings.RUNLOG)
    brief_text = """---
grounding: GROUNDING.md
premise_source: invented-call-2025-03-04.md, lines 40-44
named_reader: a self-employed plumber who does his own quotes on a Sunday night
hook: Your quote template is costing you the job // It answers a question nobody asked
grain: plumbers who pride themselves on detailed quotes will dislike it, and some will argue that detail wins trust
buyer_pays_for: a quoting app he barely opens
buyer_loses: Sunday evenings
buyer_cant_picture: a one-page quote that goes out the same day
scene_source: invented-call-2025-03-04.md, lines 40-44, confirmed by the author
---

## The position
Long quotes lose jobs to short ones that arrive first.
"""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        _findings.STORE = tdp / "findings.jsonl"
        _findings.RUNLOG = tdp / "findings-applied.jsonl"
        kitconfig.use({"banned_subjects": [{"pattern": "how to go viral",
                                            "reason": "invented banned subject."},
                                           {"pattern": r"\bdropship\w*", "regex": True,
                                            "reason": "invented regex subject"}],
                       "pitch_words": ["buy now"]})
        try:
            (tdp / "GROUNDING.md").write_text("# invented grounding\n", encoding="utf-8")
            brief = tdp / "brief.md"
            brief.write_text(brief_text, encoding="utf-8")

            def verdict(label, want_ok, contains=None):
                hard, _ = check(brief)
                ok = (not hard) == want_ok
                if contains:
                    ok = ok and any(contains in h for h in hard)
                out.append("%s %s" % ("pass:" if ok else "FAIL:", label) + ("" if ok else "  -> %s" % hard))

            verdict("unstamped brief is refused", False, "LESSONS")
            _findings.add("Hooks that open on a date were skipped", "Open on the claim",
                          "invented", "selftest", ["hook"])
            _findings.add("Two ideas in one post were cut", "One idea per post",
                          "invented", "selftest", ["body"])
            _findings.add("A brief with no reader was cut", "Name one reader in every brief",
                          "invented", "selftest", ["brief"])
            msg = stamp(brief)
            stamped_text = brief.read_text(encoding="utf-8")
            out.append("pass: stamp carries lessons from every step (hook, body, brief)"
                       if all(i in stamped_text for i in ("F0001", "F0002", "F0003")) and "3 lesson(s)" in msg
                       else "FAIL: stamp missed lessons: %s" % msg)
            verdict("stamped complete brief may be briefed", True)
            _findings.add("A new lesson", "Check the new rule first", "invented", "selftest", ["check"])
            verdict("brief is refused once a new lesson is added", False, "out of date")
            stamp(brief)
            verdict("re-stamped brief passes again", True)
            ok = len(_findings._read(_findings.RUNLOG)) == 2
            out.append("pass: each stamp is recorded" if ok else "FAIL: stamp records")

            brief.write_text(brief_text.replace("named_reader: a self-employed plumber who does his "
                                                "own quotes on a Sunday night\n", ""), encoding="utf-8")
            stamp(brief)
            verdict("missing named_reader is refused", False, "ONE IDEA")
            brief.write_text(brief_text.replace("grounding: GROUNDING.md", "grounding: nowhere.md"),
                             encoding="utf-8")
            stamp(brief)
            verdict("grounding file that does not exist is refused", False, "GROUNDING")
            brief.write_text(brief_text.replace("premise_source: invented-call-2025-03-04.md, lines 40-44",
                                                "premise_source: inferred from the reader"), encoding="utf-8")
            stamp(brief)
            verdict("inferred premise is refused", False, "PREMISE")
            brief.write_text(brief_text + "\nTeach him how to go viral.\n", encoding="utf-8")
            stamp(brief)
            verdict("banned subject from config is refused", False, "banned list")
            hard, _ = check(brief)
            ok = any("banned list" in h and ".." not in h for h in hard)
            out.append("pass: banned subject message has no double full stop" if ok
                       else "FAIL: banned subject message -> %s" % hard)
            brief.write_text(brief_text + "\nTeach him HOW TO  GO VIRAL.\n", encoding="utf-8")
            stamp(brief)
            verdict("plain banned subject matches ignoring case and extra spaces", False, "banned list")
            brief.write_text(brief_text + "\nTeach him how to go viralish.\n", encoding="utf-8")
            stamp(brief)
            verdict("plain banned subject matches whole words only", True)
            brief.write_text(brief_text + "\nHe tried dropshipping last year.\n", encoding="utf-8")
            stamp(brief)
            verdict("banned subject with regex true is read as a regular expression", False, "dropshipping")
            kitconfig.use({"banned_subjects": [{"pattern": "\bcrypto\b", "reason": "typed with one backslash"},
                                               {"pattern": r"\bcrypto\b", "reason": "regex without regex true"}],
                           "pitch_words": ["buy now"]})
            brief.write_text(brief_text, encoding="utf-8")
            stamp(brief)
            hard, _ = check(brief)
            ok = (any("hidden control character" in h for h in hard)
                  and any("contains a backslash" in h for h in hard))
            out.append("pass: a pattern that can never match is reported, not ignored" if ok
                       else "FAIL: silent banned subject pattern -> %s" % hard)
            kitconfig.use({"banned_subjects": [], "pitch_words": ["buy now"]})
            brief.write_text(brief_text.replace("buyer_loses: Sunday evenings",
                                                "buyer_loses: \"[FILL IN: what they lose]\"")
                             + "\n| 01 | [FILL IN] | [fill in] |\n", encoding="utf-8")
            stamp(brief)
            verdict("brief with [FILL IN lines is refused", False, "unfilled template lines")
            hard, _ = check(brief)
            ok = any("first at line(s) 8, 16" in h for h in hard)
            out.append("pass: unfilled lines are named by line number" if ok
                       else "FAIL: unfilled line numbers -> %s" % hard)
            brief.write_text(brief_text + "\nEnd with buy now.\n", encoding="utf-8")
            stamp(brief)
            verdict("pitch word from config is refused", False, "PITCH")
            brief.write_text(brief_text.replace("---\n\n## The", "format: text post, 200-300 words\n---\n\n## The"),
                             encoding="utf-8")
            stamp(brief)
            verdict("word-count range is refused", False, "LENGTH")
        finally:
            _findings.STORE, _findings.RUNLOG = real
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
    if "--stamp" in argv:
        rest = [a for a in argv[1:] if a != "--stamp"]
        if not rest:
            print("--stamp needs at least one brief path")
            return 2
        for a in rest:
            p = Path(a)
            if not p.exists():
                print("%s: not found" % a)
                return 2
            print("%s: %s" % (p.name, stamp(p)))
        return 0
    worst = 0
    for a in argv[1:]:
        p = Path(a)
        if not p.exists():
            print("%s: not found" % a)
            worst = 2
            continue
        hard, flags = check(p)
        print("\n=== %s: %s" % (p.name, "MAY BE BRIEFED" if not hard else "NOT BRIEFED"))
        for h in hard:
            print("  HARD:", h)
        for f in flags:
            print("  flag:", f)
        if hard:
            worst = max(worst, 1)
    print()
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv))
