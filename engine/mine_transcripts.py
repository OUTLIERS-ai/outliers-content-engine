"""
mine_transcripts.py  --  pull YOUR OWN lines out of your call transcripts, one file per month.

WHAT IT IS FOR
    Your best post ideas are positions you have already stated out loud, on calls, in your own
    words. This program does the mechanical half of finding them: it reads every transcript,
    keeps only the lines spoken by you, and writes them out month by month with the file and
    line number each came from. Deciding which lines are real positions is reading work, done
    afterwards (see prompts/mine-a-month.md). This program applies no opinion about that.

    By default the monthly files contain ONLY your own lines. If you set
    include_other_speaker_context to true, it also writes what the other person had just said
    above each of your lines, so a line wrongly labelled as yours can be spotted by eye. That
    copies their words, names and figures into the file, which is why it is off by default.

SETTINGS (config.json)
    transcript_dirs          folders to read (every .md, .txt, .vtt and .srt file inside, at any depth)
    transcript_from_date     only files whose NAME carries a date (YYYY-MM-DD) on or after this
    my_speaker_labels        every label your recorder uses for you, e.g. ["Robin", "Robin Lee"]
    mining_output_dir        where the monthly files go. Nothing is written anywhere else.
    mining_min_turn_chars    lines shorter than this ("Yeah." "Right.") are counted and dropped
    include_other_speaker_context   false (default) = your lines only; true = the other person's
                             previous line is written above each of yours

TRANSCRIPT LAYOUTS IT UNDERSTANDS
    Name: words
    [00:12:03] Name: words        00:12:03 Name: words        (00:12) Name: words
    <v Name>words</v>              (WebVTT voice tags)
    Name                           a name on its own line (optionally with a time after it),
    words on the next line(s)      with the words below it until the next name line

SET ASIDE, NOT MINED
    A transcript where one label owns 95% or more of 20+ labelled turns is set aside. That is
    almost never one person talking; it is a recording whose speaker labels collapsed, so the
    other person's words are filed under one name. Mining it would put someone else's words in
    your mouth. These files are listed in _set-aside.md for you to check by hand.

CONSENT
    Your calls contain other people's words, names and numbers. With the default setting only YOUR
    lines are written out, but your lines can still mention clients. Never quote a client's name
    or figures in a post.

Run:  python engine/mine_transcripts.py            write the monthly files
      python engine/mine_transcripts.py --stats    counts only, writes nothing
      python engine/mine_transcripts.py --help     this text, runs nothing
      python engine/mine_transcripts.py --selftest
"""

import collections
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitconfig  # noqa: E402

EXTENSIONS = (".md", ".txt", ".vtt", ".srt")
DATE_RE = re.compile(r"(20\d\d-\d\d-\d\d)")
ONE_VOICE_LIMIT = 0.95
ONE_VOICE_MIN_TURNS = 20
PLACEHOLDER_LABEL = "your name as your recorder writes it"

# A time in front of a line: [00:12:03]  00:12:03  (00:12)  0:03  00:12:03.500 -
TIME = r"[\[(]?\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?[\])]?"
TIME_PREFIX_RE = re.compile(r"^\s*" + TIME + r"\s*(?:[-|]\s*)?")
TIME_ONLY_RE = re.compile(r"^\s*" + TIME + r"\s*$")
SRT_TIMING_RE = re.compile(r"-->")
SRT_INDEX_RE = re.compile(r"^\s*\d+\s*$")
# A label: starts with a letter, up to 40 characters, at most 5 words.
LABEL = r"[^\W\d_][\w .'&()-]{0,40}?"
INLINE_RE = re.compile(r"^(" + LABEL + r")\s*:\s+(\S.*)$")
VTT_VOICE_RE = re.compile(r"^<v(?:\.[\w.-]+)?\s+([^>]+)>(.*?)(?:</v>)?\s*$")
NAME_LINE_RE = re.compile(r"^(" + LABEL + r")(?:\s+" + TIME + r")?\s*$")


def _norm(label):
    return re.sub(r"\s+", " ", label).strip().lower()


def _looks_like_label(label):
    words = label.split()
    return 0 < len(words) <= 5 and not label.rstrip().endswith((".", "?", "!", ","))


def parse(lines, mine):
    """Return a list of turns: (line_no, label, words). Works out the layout per file."""
    inline, vtt = [], []
    for i, raw in enumerate(lines, 1):
        line = raw.strip()
        v = VTT_VOICE_RE.match(line)
        if v:
            vtt.append((i, v.group(1).strip(), re.sub(r"<[^>]+>", "", v.group(2)).strip()))
            continue
        m = INLINE_RE.match(TIME_PREFIX_RE.sub("", line, count=1))
        if m and _looks_like_label(m.group(1)) and not re.match(r"https?$", m.group(1), re.I):
            inline.append((i, m.group(1).strip(), m.group(2).strip()))
    if vtt:
        return vtt
    if len(inline) >= 3:
        return inline

    # Name-on-its-own-line layout. A candidate name line is short, has no end punctuation and
    # is followed by words. It counts as a speaker only if it recurs (2+ times) or is one of
    # your own labels, so a one-word sentence like "Okay" on its own line is not taken as a name.
    cands = []
    for i, raw in enumerate(lines, 1):
        line = TIME_PREFIX_RE.sub("", raw.strip(), count=1)
        if not line or SRT_TIMING_RE.search(line) or SRT_INDEX_RE.match(line):
            continue
        m = NAME_LINE_RE.match(line)
        if m and _looks_like_label(m.group(1)):
            cands.append((i, m.group(1).strip()))
    counts = collections.Counter(_norm(n) for _, n in cands)
    speakers = {n for n, c in counts.items() if c >= 2} | set(mine)
    starts = [(i, n) for i, n in cands if _norm(n) in speakers]
    if len(starts) < 2:
        return inline
    turns = []
    for k, (i, name) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines) + 1
        words, first = [], None
        for j in range(i + 1, end):
            t = lines[j - 1].strip()
            if not t or TIME_ONLY_RE.match(t) or SRT_TIMING_RE.search(t) or SRT_INDEX_RE.match(t):
                continue
            words.append(t)
            first = first or j
        if words:
            turns.append((first, name, " ".join(words)))
    return turns


def turns_for(path, mine, min_chars):
    """(my turns as (line_no, previous other line, words), dropped short count, set-aside reason)"""
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return [], 0, "could not be read"
    parsed = parse(lines, mine)
    labels = collections.Counter(_norm(n) for _, n, _ in parsed)
    total = sum(labels.values())
    if total >= ONE_VOICE_MIN_TURNS:
        top, top_n = labels.most_common(1)[0]
        if top_n / total >= ONE_VOICE_LIMIT:
            return [], 0, ("%d of %d turns are labelled '%s'. The speaker labels probably "
                           "collapsed, so another person's words may be filed under one name"
                           % (top_n, total, top))
    out, short, prev = [], 0, ""
    for line_no, name, said in parsed:
        if _norm(name) not in mine:
            prev = "%s: %s" % (name, said[:160])
            continue
        if len(said) < min_chars:
            short += 1
            continue
        out.append((line_no, prev, said))
    return out, short, None


def corpus(dirs, from_date):
    files, undated, missing = {}, [], []
    for d in dirs:
        root = kitconfig.resolve(d)
        if not root.exists():
            missing.append(str(root))
            continue
        for f in root.rglob("*"):
            if not f.is_file() or f.suffix.lower() not in EXTENSIONS:
                continue
            m = DATE_RE.search(f.name)
            if not m:
                undated.append(f)
            elif m.group(1) >= from_date:
                files[f.resolve()] = m.group(1)
    return sorted(files.items(), key=lambda kv: (kv[1], str(kv[0]))), undated, missing


def _safe_output_dir(out_dir):
    """Refuse an output folder that is the repo root or a folder above it."""
    out = out_dir.resolve()
    repo = kitconfig.REPO_ROOT.resolve()
    if out == repo or out in repo.parents:
        raise SystemExit("refused: mining_output_dir must be a folder of its own, not %s" % out)
    return out


def run(stats_only=False, echo=print):
    labels = [x for x in (kitconfig.get("my_speaker_labels") or []) if isinstance(x, str) and x.strip()]
    if not labels:
        raise SystemExit("my_speaker_labels is empty in config.json. Add every label your "
                         "recorder uses for you, exactly as it appears in the transcripts.")
    if any(_norm(x) == PLACEHOLDER_LABEL for x in labels):
        raise SystemExit("my_speaker_labels still holds the placeholder from config.example.json. "
                         "Copy it to config.json and put in the label your recorder uses for you.")
    mine = {_norm(x) for x in labels}
    dirs = kitconfig.get("transcript_dirs") or []
    if not dirs:
        raise SystemExit("transcript_dirs is empty in config.json. Add the folder(s) your transcripts are in.")
    from_date = str(kitconfig.get("transcript_from_date") or "1900-01-01")
    min_chars = int(kitconfig.get("mining_min_turn_chars") or 0)
    out_dir = _safe_output_dir(kitconfig.path("mining_output_dir"))

    files, undated, missing = corpus(dirs, from_date)
    for m in missing:
        echo("folder not found: %s" % m)
    by_month = collections.defaultdict(list)
    totals = collections.Counter()
    setaside = []
    for path, date in files:
        t, short, reason = turns_for(path, mine, min_chars)
        totals["files"] += 1
        if reason:
            totals["set_aside"] += 1
            setaside.append((date, path, reason))
            continue
        totals["turns"] += len(t)
        totals["short"] += short
        totals["chars"] += sum(len(x[2]) for x in t)
        if not t:
            totals["none_of_yours"] += 1
        by_month[date[:7]].append((path, date, t))

    echo("transcripts dated %s or later: %d" % (from_date, totals["files"]))
    echo("  skipped, no YYYY-MM-DD date in the file name: %d" % len(undated))
    echo("  set aside, speaker labels collapsed: %d" % totals["set_aside"])
    echo("  with none of your lines in them: %d" % totals["none_of_yours"])
    echo("your lines long enough to carry a sentence: %d" % totals["turns"])
    echo("  dropped as too short (under %d characters): %d" % (min_chars, totals["short"]))
    echo("your words: %.2f MB" % (totals["chars"] / 1e6))
    echo("")
    echo("%-9s %7s %9s" % ("month", "files", "lines"))
    for month in sorted(by_month):
        echo("%-9s %7d %9d" % (month, len(by_month[month]), sum(len(p[2]) for p in by_month[month])))
    if totals["files"] and not totals["turns"] and not stats_only:
        echo("\nNo lines matched your labels %s. Open one transcript and copy your label exactly." % labels)
    if stats_only:
        return totals, out_dir

    written = []
    if setaside:
        lines = ["# Transcripts set aside: speaker labels collapsed", "",
                 "Not mined. In each one a single label owns %.0f%% or more of the turns, so "
                 "someone else's words are probably filed under one name. Check them by hand." % (ONE_VOICE_LIMIT * 100), ""]
        for date, path, reason in sorted(setaside):
            lines += ["- **%s** `%s`" % (date, path.name), "  - %s" % reason]
        kitconfig.atomic_write_text(out_dir / "_set-aside.md", "\n".join(lines) + "\n")
        written.append("_set-aside.md")

    with_context = kitconfig.get("include_other_speaker_context") is True
    if with_context:
        note = ("> Word for word. `L<n>` is the line in the source file. The italic line above each "
                "of yours is what the other person had just said (include_other_speaker_context is "
                "true), so a wrongly labelled line can be spotted. It carries their words, names and "
                "figures: never copy it.")
    else:
        note = ("> Word for word. `L<n>` is the line in the source file. Only your own lines are "
                "here (include_other_speaker_context is false). If a line might not be yours, open "
                "the source file at that line and check who was speaking.")
    index = []
    for month in sorted(by_month):
        lines = ["# Your own lines: %s" % month, "", note, ""]
        n = 0
        for path, date, t in by_month[month]:
            if not t:
                continue
            lines += ["", "## %s" % path.name, "`%s`" % kitconfig.rel(path), ""]
            for line_no, prev, said in t:
                if with_context:
                    if prev:
                        lines.append("- _%s_" % prev.replace("_", ""))
                    lines.append("  **L%d** %s" % (line_no, said))
                else:
                    lines.append("- **L%d** %s" % (line_no, said))
                n += 1
        name = "%s.md" % month
        kitconfig.atomic_write_text(out_dir / name, "\n".join(lines) + "\n")
        written.append(name)
        index.append({"month": month, "file": name, "lines": n,
                      "transcripts": len([p for p in by_month[month] if p[2]])})
    kitconfig.atomic_write_text(out_dir / "_index.json",
                                json.dumps({"from_date": from_date, "labels": labels, "packs": index}, indent=2) + "\n")
    written.append("_index.json")
    echo("\nwrote %d file(s) to %s" % (len(written), out_dir))
    return totals, out_dir


def selftest():
    out = []
    long_a = "I think most quotes are far too long and nobody reads past the first page of them."
    long_b = "Send the price first, then the detail, because the price is what they open it for."
    other = "That makes sense, we have always sent eight pages."
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        tr = tdp / "transcripts"
        (tr / "zoom").mkdir(parents=True)
        (tr / "2025-03-04 call with a plumber.txt").write_text(
            "Jo Client: %s\nRobin Lee: %s\nJo Client: Okay.\nRobin Lee: Yeah.\nRobin Lee: %s\n"
            % (other, long_a, long_b), encoding="utf-8")
        (tr / "zoom" / "2025-03-20-meeting.txt").write_text(
            "[00:00:05] Jo Client: %s\n00:00:09 Robin: %s\n(00:12) Jo Client: Right.\n" % (other, long_b),
            encoding="utf-8")
        (tr / "2025-04-02 otter export.txt").write_text(
            "Jo Client  0:03\n%s\n\nRobin Lee  0:10\n%s\nand a second line of it.\n\n"
            "Jo Client  0:20\nOkay\n\nRobin Lee  0:25\n%s\n" % (other, long_a, long_b), encoding="utf-8")
        (tr / "2025-04-10 captions.vtt").write_text(
            "WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<v Robin Lee>%s</v>\n" % long_b, encoding="utf-8")
        (tr / "2025-05-01 collapsed.txt").write_text(
            "".join("Robin Lee: line number %d of a call where every label is the same person.\n" % i
                    for i in range(25)), encoding="utf-8")
        (tr / "2024-12-01 too old.txt").write_text("Robin Lee: %s\n" % long_a, encoding="utf-8")
        (tr / "no date in name.txt").write_text("Robin Lee: %s\n" % long_a, encoding="utf-8")
        kitconfig.use({"transcript_dirs": [str(tr)], "transcript_from_date": "2025-01-01",
                       "my_speaker_labels": ["Robin Lee", "Robin"],
                       "mining_output_dir": str(tdp / "mined"), "mining_min_turn_chars": 45})
        try:
            before = sorted(str(p) for p in tr.rglob("*"))
            totals, out_dir = run(echo=lambda *_: None)
            march = (out_dir / "2025-03.md").read_text(encoding="utf-8")
            april = (out_dir / "2025-04.md").read_text(encoding="utf-8")
            checks = [
                ("'Name: words' layout", long_a in march and "**L2**" in march),
                ("'[00:00:05] Name:' and '00:00:09 Name:' layouts", "2025-03-20-meeting.txt" in march),
                ("by default only your own lines are written (no other speaker's words or name)",
                 other not in march + april and "Jo Client" not in march + april
                 and "include_other_speaker_context is false" in march),
                ("short lines dropped and counted", "Yeah." not in march and totals["short"] >= 1),
                ("name-on-its-own-line layout, lines joined",
                 (long_a + " and a second line of it.") in april),
                ("WebVTT voice tags", "2025-04-10 captions.vtt" in april),
                ("collapsed-label file set aside",
                 totals["set_aside"] == 1 and "collapsed.txt" in (out_dir / "_set-aside.md").read_text(encoding="utf-8")),
                ("files before the start date skipped", "too old" not in march + april),
                ("output written only inside mining_output_dir",
                 sorted(p.name for p in out_dir.iterdir()) == ["2025-03.md", "2025-04.md", "_index.json", "_set-aside.md"]
                 and sorted(str(p) for p in tr.rglob("*")) == before),
            ]
            out += ["%s %s" % ("pass:" if ok else "FAIL:", label) for label, ok in checks]
            kitconfig.use({"transcript_dirs": [str(tr)], "transcript_from_date": "2025-01-01",
                           "my_speaker_labels": ["Robin Lee", "Robin"],
                           "mining_output_dir": str(tdp / "mined-context"), "mining_min_turn_chars": 45,
                           "include_other_speaker_context": True})
            _, ctx_dir = run(echo=lambda *_: None)
            march_ctx = (ctx_dir / "2025-03.md").read_text(encoding="utf-8")
            ok = "_Jo Client: %s_" % other in march_ctx and long_a in march_ctx
            out.append("%s include_other_speaker_context true keeps the other person's previous line"
                       % ("pass:" if ok else "FAIL:"))
            try:
                kitconfig.use({"my_speaker_labels": [], "transcript_dirs": [str(tr)]})
                run(echo=lambda *_: None)
                out.append("FAIL: ran with no speaker labels")
            except SystemExit:
                out.append("pass: refuses to run with no speaker labels")
            try:
                kitconfig.use({"my_speaker_labels": ["Robin"], "transcript_dirs": [str(tr)],
                               "mining_output_dir": str(kitconfig.REPO_ROOT)})
                run(echo=lambda *_: None)
                out.append("FAIL: wrote into the repo root")
            except SystemExit:
                out.append("pass: refuses the repo root as the output folder")
        finally:
            kitconfig.use(None)
    good = not any(x.startswith("FAIL") for x in out)
    out.append("SELFTEST %s (%d checks)" % ("PASSED" if good else "FAILED", len(out)))
    return "\n".join(out), good


def main():
    kitconfig.utf8_console()
    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        print(__doc__)
        return 0
    unknown = [a for a in args if a not in ("--selftest", "--stats")]
    if unknown:
        print("refused: unknown option(s) %s. Nothing was read or written.\n"
              "Valid options: --stats, --selftest, --help" % unknown)
        return 2
    if "--selftest" in args:
        text, good = selftest()
        print(text)
        return 0 if good else 1
    run(stats_only="--stats" in args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
