"""
batch_checks.py  --  checks a whole wave of drafts together, for sameness.

WHY
    post_checks.py judges one post at a time. But a batch of individually decent drafts can
    still read as one writer on one setting: the same ending shape, the same reframe, the same
    clause, the same idea reworded. Nobody reading a single post can see that. This reads them
    all at once and reports what only shows up across the batch.

THE CHECKS
    shared crystalliser   2+ posts land on "that's the whole X"                       HARD
    reframe engine        2+ posts use "not X, it's Y" more than once each             HARD
    repeated sentences    near-identical sentences in two posts                        HARD
    shared clause         the same run of 6+ words inside different sentences          HARD
    one idea              5+ content words shared by 60% of posts                      HARD
    sign-off              only when signoff_rule is "required": a post missing it      HARD
    opening length        every post opens on a sentence of about the same length      flag
    landing length        every post ends on a line of about the same length           flag
    length variety        lengths too similar, or no short / no long post in the wave  flag

Settings used from config.json: signoff_line, signoff_rule, batch_length_short,
batch_length_long, drafts_dir (when no folder is given). The sign-off line itself is removed
before comparing posts, so a sign-off every post shares is never reported as a repeated clause.

Run:  python engine/batch_checks.py --dir <drafts folder> [--glob "*.md"]
      python engine/batch_checks.py <draft.md> <draft.md> [...]
      python engine/batch_checks.py --selftest
Exit 1 if any HARD finding. Needs at least 2 posts.
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitconfig  # noqa: E402
from post_checks import extract_body, NEGATION_COUPLET_RE  # noqa: E402

CRYSTALLISER_RE = re.compile(r"\b(that(?:'s| is)|this is) the (whole|entire|real|only) (\w+)\b", re.I)

STOPWORDS = set(
    "a an the and or but of to in on at for with is are was were it its it's i i'd i've you your "
    "that this then so my me he she they we not no as if by from be been being do does did".split()
)

# Words that recur in any batch by one author without carrying an idea: function words,
# degree and time words, pronouns. Only words that are function words by grammar belong here.
# Never add a word because it happens to recur in your own batch; that tunes the check until
# it agrees with you.
FUNCTION_WORDS = set(
    "every got out them there what when where which who how why all can cant can't will wont "
    "won't dont don't its into about over under after before because while now only some most "
    "any other same own off up down again once here very too also both each few such nor get "
    "gets getting make makes making made goes going gone went come comes came back still just "
    "even really never always more much than one two three four five six seven eight nine ten "
    "first last next thing things stuff way ways lot bit "
    "day days week weeks month months year years hour hours minute minutes morning evening "
    "night nights time times today tomorrow yesterday "
    "his hers mine yours ours theirs "
    "nobody anybody somebody everybody noone "
    "nothing anything something everything "
    "anyone someone everyone people person "
    "else another whether".split()
)


def _signoff():
    return str(kitconfig.get("signoff_line") or "").strip()


def _sentences(text: str):
    for s in re.split(r"(?<=[.!?])\s+", text):
        s = s.strip()
        if s:
            yield s


def _content_words(s: str):
    return [w for w in re.findall(r"[a-z0-9']+", s.lower()) if w not in STOPWORDS and len(w) > 2]


def _shingle(s: str, n: int = 4):
    w = _content_words(s)
    return {tuple(w[i: i + n]) for i in range(max(0, len(w) - n + 1))}


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def _strip_signoff(body: str) -> str:
    s = _signoff()
    return body.replace(s, "").strip() if s else body


def load(paths):
    """{file name: (live post with sign-off removed, last non-blank line of the live post)}"""
    posts, last_lines = {}, {}
    for p in paths:
        body = extract_body(Path(p).read_text(encoding="utf-8", errors="replace")).strip()
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
        last_lines[Path(p).name] = lines[-1] if lines else ""
        posts[Path(p).name] = _strip_signoff(body)
    return posts, last_lines


def check_signoff(last_lines):
    rule = str(kitconfig.get("signoff_rule") or "off").strip().lower()
    if rule != "required":
        return False, []
    s = _signoff()
    if not s:
        return True, ["signoff_rule is 'required' but signoff_line is empty in config.json"]
    missing = [n for n, last in last_lines.items() if last != s]
    if not missing:
        return False, []
    return True, ["%d post(s) do not end on your sign-off line %r: %s" % (len(missing), s, ", ".join(missing))]


def check_crystalliser(posts):
    hits = {}
    for name, body in posts.items():
        for m in CRYSTALLISER_RE.finditer(body):
            hits.setdefault(name, []).append(m.group(0).strip())
    if len(hits) >= 2:
        f = ["SHARED ENDING SHAPE in %d/%d posts, the same 'that's the whole X' landing:" % (len(hits), len(posts))]
        f += ["    %s: %s" % (n, h) for n, h in hits.items()]
        f.append("    Give each post its own way to land, or none.")
        return True, f
    return False, (["crystalliser in 1 post only (fine): %s" % hits] if hits else [])


def check_negation_engine(posts):
    counts = {name: len(NEGATION_COUPLET_RE.findall(body)) for name, body in posts.items()}
    over = {k: v for k, v in counts.items() if v > 1}
    if len(over) >= 2:
        f = ["'NOT X, IT'S Y' used more than once in %d/%d posts:" % (len(over), len(posts))]
        f += ["    %s: %d" % (k, v) for k, v in sorted(over.items(), key=lambda x: -x[1])]
        f.append("    One post may lean on the reframe. A batch may not.")
        return True, f
    return False, (["reframe over the limit in 1 post: %s" % over] if over else [])


def check_repeated_sentences(posts, threshold=0.55):
    names = list(posts)
    seen = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            for sa in _sentences(posts[a]):
                if len(_content_words(sa)) < 5:
                    continue
                for sb in _sentences(posts[b]):
                    if len(_content_words(sb)) < 5:
                        continue
                    sim = _jaccard(_shingle(sa), _shingle(sb))
                    if sim >= threshold:
                        seen.append((sim, a, b, sa[:90], sb[:90]))
    if not seen:
        return False, []
    f = ["REPEATED SENTENCES across posts (%d pair(s), overlap >= %.2f):" % (len(seen), threshold)]
    for sim, a, b, sa, sb in sorted(seen, key=lambda x: -x[0])[:8]:
        f.append("    [%.2f] %s: \"%s\"" % (sim, a, sa))
        f.append("           %s: \"%s\"" % (b, sb))
    f.append("    A batch that reuses a sentence reads as one template with the nouns swapped.")
    return True, f


def check_shared_clause(posts, min_words=6, min_posts=2):
    """The same run of words inside two different sentences. Whole-sentence comparison misses
    this, because the words around the clause dilute the overlap. It is exactly how a line
    written into a brief spreads: each drafter wraps it in a sentence of their own."""
    grams = {}
    for name, body in posts.items():
        words = re.findall(r"[a-z0-9']+", body.lower())
        for n in range(min_words, min(len(words), 14) + 1):
            for i in range(len(words) - n + 1):
                grams.setdefault(" ".join(words[i:i + n]), set()).add(name)
    shared = {g: names for g, names in grams.items() if len(names) >= min_posts}
    maximal = []
    for g, names in sorted(shared.items(), key=lambda kv: -len(kv[0])):
        if not any(g in bigger and names <= bignames for bigger, bignames in maximal):
            maximal.append((g, names))
    if not maximal:
        return False, []
    f = ["SHARED CLAUSE across posts (%d run(s) of %d+ words, word for word):" % (len(maximal), min_words)]
    for g, names in sorted(maximal, key=lambda kv: -len(kv[0].split()))[:8]:
        f.append("    [%d words in %d] \"%s\"" % (len(g.split()), len(names), g))
        f.append("           %s" % ", ".join(sorted(names)))
    f.append("    A sentence handed down in the brief ends up in every post. Brief the move, not the line.")
    return True, f


def _lemma(w: str) -> str:
    w = w.rstrip("'")
    if w.endswith("'s"):
        w = w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    return w


def check_idea_diversity(posts):
    """A batch can share no sentences and still be one idea reworded. The shared noun field
    shows it: different ideas live in different vocabularies."""
    if len(posts) < 3:
        return False, []
    vocab = {name: {_lemma(w) for w in re.findall(r"[a-z0-9']+", body.lower())
                    if w not in STOPWORDS and w not in FUNCTION_WORDS and len(w) > 2}
             for name, body in posts.items()}
    need = max(2, -(-len(posts) * 3 // 5))  # 60% of posts, rounded up
    counts = Counter(w for words in vocab.values() for w in words)
    shared = sorted(w for w, c in counts.items() if c >= need)
    if len(shared) >= 5:
        return True, ["ONE-IDEA BATCH: %d content words appear in %d+ of %d posts: %s"
                      % (len(shared), need, len(posts), shared),
                      "    Commission different ideas, not different wording."]
    if len(shared) >= 3:
        return False, ["shared words %s appear in %d+ of %d posts: check these are different ideas"
                       % (shared, need, len(posts))]
    return False, []


def check_opening_shape(posts):
    shapes = {name: len(next(_sentences(body), "").split()) for name, body in posts.items()}
    if len(shapes) >= 3 and max(shapes.values()) - min(shapes.values()) <= 3:
        return False, ["every post opens on a %d-%d word sentence. Vary the entry. %s"
                       % (min(shapes.values()), max(shapes.values()), shapes)]
    return False, []


def check_landing_shape(posts):
    lands = {}
    for name, body in posts.items():
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
        if lines:
            lands[name] = len(lines[-1].split())
    if len(lands) >= 3 and max(lands.values()) - min(lands.values()) <= 3:
        return False, ["every post ends on a %d-%d word line. One flat verdict per batch is plenty. %s"
                       % (min(lands.values()), max(lands.values()), lands)]
    return False, []


def check_length_variance(posts):
    """Length is judged across the wave, never as a per-post ceiling: a fixed ceiling produces
    exactly the uniform lengths this check exists to catch."""
    lengths = {name: len(body.split()) for name, body in posts.items()}
    if len(lengths) < 3:
        return False, []
    vals = sorted(lengths.values())
    spread, mean = vals[-1] - vals[0], sum(vals) / len(vals)
    f = []
    if spread < 0.35 * mean:
        f.append("lengths are uniform: %d-%d words (spread %d, mean %.0f). Mix short and long. %s"
                 % (vals[0], vals[-1], spread, mean, lengths))
    short, long_ = kitconfig.get("batch_length_short"), kitconfig.get("batch_length_long")
    if short and not any(v <= short for v in vals):
        f.append("no short post in the wave (shortest is %d words; setting batch_length_short is %s)"
                 % (vals[0], short))
    if long_ and not any(v >= long_ for v in vals):
        f.append("no long post in the wave (longest is %d words; setting batch_length_long is %s)"
                 % (vals[-1], long_))
    return False, f


CHECKS = (check_crystalliser, check_negation_engine, check_repeated_sentences,
          check_shared_clause, check_idea_diversity, check_opening_shape,
          check_landing_shape, check_length_variance)


def run(paths, echo=print):
    posts, last_lines = load(paths)
    echo("BATCH SWEEP: %d posts: %s\n" % (len(posts), ", ".join(posts)))
    hard_any = False
    results = [("check_signoff", check_signoff(last_lines))] + [(fn.__name__, fn(posts)) for fn in CHECKS]
    for name, (hard, findings) in results:
        hard_any = hard_any or hard
        if findings:
            echo("[%s] %s" % ("HARD" if hard else "flag", name))
            for f in findings:
                echo("  " + f)
            echo("")
    echo("BATCH FAILS: fix the HARD findings above." if hard_any else "No HARD batch findings.")
    return hard_any, results


def selftest():
    out = []
    shared = "Nobody reads a quote that arrives after the competitor has already been booked in."
    distinct = [
        "Plumbers lose jobs on Sunday nights.\n\nThe quote goes out on Tuesday.\n\n" + shared,
        "My accountant charges by the hour and hates it.\n\nFixed fees changed her year.\n\n" + shared,
        "Three weeks of invoices sat in a drawer.\n\nThe drawer is now a calendar reminder at 4pm.",
    ]
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        paths = []
        for i, text in enumerate(distinct):
            p = tdp / ("draft-%d.md" % i)
            p.write_text("---\ntype: social-post\n---\n\n" + text + "\n\nSee you Monday.\n", encoding="utf-8")
            paths.append(p)
        try:
            kitconfig.use({"signoff_line": "See you Monday.", "signoff_rule": "off"})
            hard, results = run(paths, echo=lambda *_: None)
            r = dict(results)
            out.append("pass: shared clause is caught" if r["check_shared_clause"][0]
                       else "FAIL: shared clause missed")
            clause_text = " ".join(r["check_shared_clause"][1]).lower()
            out.append("pass: the shared sign-off is not reported as a clause"
                       if "see you monday" not in clause_text else "FAIL: sign-off counted as clause")
            out.append("pass: sign-off not checked when rule is off" if not r["check_signoff"][0]
                       else "FAIL: sign-off checked while off")
            kitconfig.use({"signoff_line": "See you Monday.", "signoff_rule": "required"})
            _, results = run(paths, echo=lambda *_: None)
            out.append("pass: required sign-off present passes" if not dict(results)["check_signoff"][0]
                       else "FAIL: sign-off present but reported")
            paths[2].write_text("---\ntype: social-post\n---\n\n" + distinct[2] + "\n", encoding="utf-8")
            _, results = run(paths, echo=lambda *_: None)
            out.append("pass: required sign-off missing is HARD" if dict(results)["check_signoff"][0]
                       else "FAIL: missing sign-off not caught")
            kitconfig.use({"batch_length_short": 5, "batch_length_long": 500})
            _, results = run(paths, echo=lambda *_: None)
            lv = " ".join(dict(results)["check_length_variance"][1])
            out.append("pass: length settings from config are used"
                       if "batch_length_short" in lv and "batch_length_long" in lv
                       else "FAIL: length settings ignored: %s" % lv)
            same = []
            for i in range(3):
                p = tdp / ("same-%d.md" % i)
                p.write_text("Draft %d.\n\nThe invoice was late again. That's the whole problem.\n" % i,
                             encoding="utf-8")
                same.append(p)
            kitconfig.use({})
            hard, results = run(same, echo=lambda *_: None)
            out.append("pass: shared ending shape is caught" if dict(results)["check_crystalliser"][0]
                       else "FAIL: crystalliser missed")
        finally:
            kitconfig.use(None)
    good = not any(x.startswith("FAIL") for x in out)
    out.append("SELFTEST %s (%d checks)" % ("PASSED" if good else "FAILED", len(out)))
    return "\n".join(out), good


def main():
    kitconfig.utf8_console()
    ap = argparse.ArgumentParser(description="Sameness checks across a wave of drafts.")
    ap.add_argument("paths", nargs="*", help="draft .md files")
    ap.add_argument("--dir", help="a drafts folder (default: drafts_dir from config.json)")
    ap.add_argument("--glob", default="*.md")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        text, good = selftest()
        print(text)
        return 0 if good else 1
    paths = list(args.paths)
    if args.dir or not paths:
        folder = kitconfig.cli_path(args.dir) if args.dir else kitconfig.path("drafts_dir")
        if not folder.exists():
            raise SystemExit("drafts folder not found: %s" % folder)
        paths += [str(p) for p in sorted(folder.glob(args.glob)) if not p.name.startswith("_")]
    if len(paths) < 2:
        raise SystemExit("batch_checks needs at least 2 posts. Sameness is a property of a batch.")
    hard, _ = run(paths)
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
