"""
rule_tables.py  --  shared word lists and patterns the checkers use.

One definition of each table, imported by post_checks.py and batch_checks.py, so the two
checkers can never disagree about what an em dash or a markdown heading is.

The tables:
  EM_DASH_RE         em dash and en dash
  MARKDOWN_RE        bold, headings and list bullets (LinkedIn shows them as raw symbols)
  EMOJI_RE           emoji and pictograph ranges
  BLACKLIST_VOCAB    words that read as machine or corporate filler in almost any post
  TEASE_SIGNPOST     "here's the thing" style wind-ups
  AI_REVEAL_TELLS    "the part nobody tells you" style reveals, plus reveal_tells()
  vague_filler_scan  "the thing" / "stuff" used in place of the actual noun

These are starting lists, general to machine-written English, not anyone's personal taste.
Your own banned words go in your-voice/banned_words.json, which banned_words.py reads.

Run:  python engine/rule_tables.py --selftest
"""

import re
import sys

EM_DASH_RE = re.compile("[\u2014\u2013]")

# Real markdown bold (**word**), a heading (# ), or a list bullet at line start. Not censored
# swearing like f***ing, which has an odd run of asterisks and no closing pair.
MARKDOWN_RE = re.compile(r"(\*\*[^*\n]+\*\*|^#{1,6}\s|^\s*[-*]\s)", re.M)

EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\u2190-\u21ff\u2b00-\u2bff]")

# Opening wind-ups that promise a point instead of making it. Flag only: some are fine in
# casual speech, and the writer decides.
TEASE_SIGNPOST = [
    "here's what nobody", "heres what nobody", "here's the thing", "heres the thing",
    "here's the part", "heres the part", "here's my bet", "heres my bet",
    "i can tell you exactly why", "let me tell you something",
    "let that sink in", "read that again", "here's the truth about", "heres the truth about",
    "what nobody admits", "the thing nobody tells",
]

# Reveal constructions that read as machine filler anywhere in a post. Hard fail in post_checks.
AI_REVEAL_TELLS = [
    "the quiet part nobody", "quiet part nobody says", "say the quiet part",
    "the quiet part out loud", "here's the quiet part", "heres the quiet part",
    "the part nobody says out loud", "the part they don't tell you",
    "the part they dont tell you", "what they don't want you to know",
    "what they dont want you to know", "the part no one talks about",
    "the dirty little secret", "the uncomfortable truth is",
]

# The same reveal as a shape, so a reworded version is still caught:
# "the <part|bit|secret|truth> <nobody|no one|they...> <says|tells|shows...>"
AI_REVEAL_TELL_RE = re.compile(
    r"\bthe (part|bit|secret|truth)s?\b[^.!?\n]{0,24}?\b(nobody|no one|no-one|they|not many|"
    r"few people|hardly anyone)\b[^.!?\n]{0,24}?\b(say|says|said|tell|tells|told|show|shows|"
    r"showed|mention|mentions|talk|talks|admit|admits|want|wants|print|prints)\b",
    re.I,
)


def reveal_tells(text):
    """All reveal-tell hits: fixed phrases plus the general shape. Lowercased, no repeats."""
    low = text.lower()
    hits = {p for p in AI_REVEAL_TELLS if p in low}
    hits |= {m.group(0).lower().strip() for m in AI_REVEAL_TELL_RE.finditer(text)}
    return sorted(hits)


# Words that almost never appear in a person's natural post and almost always in a machine's.
# Flag only. Word-boundary matched.
BLACKLIST_VOCAB = [
    "delve", "foster", "robust", "seamless", "pivotal", "ever-evolving", "ever evolving",
    "in the realm of", "game changer", "game-changer", "synergy", "tapestry",
    "testament to", "underscore", "paradigm",
]

# VAGUE FILLER. The rule is about substitution: "the thing" or "stuff" standing where the real
# noun should be. Ordinary idiom ("the whole thing", "two things") is allowed, otherwise the
# check fires on normal English and gets ignored.
VAGUE_FILLER_RE = re.compile(r"\b(thing|things)\b", re.I)
VAGUE_FILLER_HARD_RE = re.compile(r"\b(the thing|that thing|this thing)\b", re.I)
STUFF_RE = re.compile(r"\bstuff\b", re.I)
# "the stuff I want, the stuff I don't": the clause after "stuff" names what it is.
# Allowed when stuff_carve_out is on.
STUFF_VOICE_RE = re.compile(r"\bstuff\s+(i|you|we|they|he|she|that|which|like)\b", re.I)
VAGUE_IDIOM_RE = re.compile(
    r"\b("
    r"(the )?whole thing"
    r"|(one|two|three|four|five|six|seven|eight|nine|ten|a few|several|certain|many|all|both|"
    r"these|those|more|other|two of the|the only) things?"
    r"|(the )?(same|first|last|main|real|only|hard|best|worst|right|wrong|done) thing"
    r"|(sort|kind|type) of thing"
    r"|things? like"
    r"|not a thing"
    r"|things? (went|go|goes|change|changed|got|get|stay|stayed|work|worked|break|broke)"
    r"|do(es|n't|ing)? the thing"
    r")\b",
    re.I,
)


def vague_filler_scan(body, stuff_carve_out=True):
    """Returns (hard_hits, advisory_lines).

    hard_hits      "the thing" / "that thing" / "this thing", and "stuff" (unless it is
                   followed by a clause naming it and stuff_carve_out is on)
    advisory_lines other "thing(s)" uses that are not common idiom, worth a look
    """
    hard = {m.group(0).lower() for m in VAGUE_FILLER_HARD_RE.finditer(body)}
    for m in STUFF_RE.finditer(body):
        if not (stuff_carve_out and STUFF_VOICE_RE.match(body, m.start())):
            hard.add("stuff")
    advisory = []
    for m in VAGUE_FILLER_RE.finditer(body):
        s, e = m.span()
        window = body[max(0, s - 30): min(len(body), e + 12)]
        if VAGUE_IDIOM_RE.search(window):
            continue
        if VAGUE_FILLER_HARD_RE.search(body[max(0, s - 5): e]):
            continue
        end = body.find("\n", e)
        line = body[body.rfind("\n", 0, s) + 1: end if end != -1 else len(body)]
        advisory.append(line.strip()[:90])
    return sorted(hard), sorted(set(advisory))


def selftest():
    checks = [
        ("em dash found", bool(EM_DASH_RE.search("one \u2014 two"))),
        ("plain hyphen allowed", not EM_DASH_RE.search("well-known")),
        ("markdown bold found", bool(MARKDOWN_RE.search("a **bold** word"))),
        ("censored swear not markdown", not MARKDOWN_RE.search("f***ing hard")),
        ("reveal shape found", bool(reveal_tells("It is the part nobody shows you."))),
        ("'the thing' is hard", vague_filler_scan("So the thing is the invoice.")[0] == ["the thing"]),
        ("'the whole thing' is idiom", vague_filler_scan("The whole thing took a day.") == ([], [])),
        ("scoped 'stuff I want' allowed", vague_filler_scan("The stuff I want stays.")[0] == []),
        ("scoped 'stuff' hard with carve-out off",
         vague_filler_scan("The stuff I want stays.", stuff_carve_out=False)[0] == ["stuff"]),
        ("bare 'stuff' hard", vague_filler_scan("I built some stuff.")[0] == ["stuff"]),
    ]
    out = ["%s %s" % ("pass:" if ok else "FAIL:", label) for label, ok in checks]
    good = all(ok for _, ok in checks)
    out.append("SELFTEST %s (%d checks)" % ("PASSED" if good else "FAILED", len(checks)))
    return "\n".join(out), good


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if "--selftest" in sys.argv:
        _t, _ok = selftest()
        print(_t)
        sys.exit(0 if _ok else 1)
    sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
    import kitconfig
    print(kitconfig.for_this_computer(__doc__))
