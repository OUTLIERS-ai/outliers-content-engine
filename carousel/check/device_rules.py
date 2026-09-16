"""device_rules: the cover styles and body shapes, written as data.

Both the renderer (build_carousel.py) and the checker (slide_checks.py) import this one file, so
the two can never disagree about what a cover style needs.

A cover style ("cover_device" in the spec) decides what makes the first slide readable in under a
second: a giant number, a giant word, a flat statement, two contrasting phrases, and so on.
A body shape ("body" in the spec) decides which slide roles the deck uses.

Standard library only. Python 3.9+.
"""
from __future__ import annotations

import re

# A cover that opens with a telling-off ("Stop ...", "Don't ...") reads as a lecture.
SCOLD_RE = re.compile(r"^\s*(stop|don't|dont|quit)\b", re.I)
# The renderer already prints a swipe arrow on the cover, so the kicker must not repeat it.
KICKER_INSTRUCT_RE = re.compile(r"\b(swipe|scroll|read on|keep going|slide through)\b", re.I)

# Words too general to count as a concrete shared subject between a cover and its item titles.
ANCHOR_STOPLIST = {"business", "work", "working", "build", "built", "building", "system",
                   "systems", "better", "faster", "own", "owner", "solo", "person", "people",
                   "money", "time", "day", "week", "everything", "nothing"}

# Cover elements that each count as one "unit" the eye has to read. More than 3 is too many
# for a slide seen for under a second. The small label above the title does not count.
COVER_UNIT_FIELDS = ("lead", "shot", "title", "kicker", "top", "bottom")
COVER_FURNITURE = ("kicker_top",)
COVER_MAX_UNITS = 3

# ---------------------------------------------------------------------------
# THE 7 COVER STYLES
# word_band:   (min, max) words allowed in the cover title
# count_match: a number in the title must equal the number of item slides
# lead:        what the big "lead" slot contains: "digit" | "word" | "glyph" | "token" | None
# ---------------------------------------------------------------------------
DEVICES = {
    "numeral": dict(
        stop="a giant number", hook="a specific count the reader wants",
        lead="digit", word_band=(6, 10), count_match=True,
        note="the number must equal the item count",
    ),
    "word": dict(
        stop="one giant word", hook="the word is the picture",
        lead="word", word_band=(3, 10), count_match=False,
        lead_max_solid=6, lead_max_spaced=7,
        note="a longer lead word runs off the slide; there is no automatic shrinking",
    ),
    "question": dict(
        stop="a large question", hook="a question tied to a named subject",
        lead="glyph", word_band=(6, 12), count_match=False,
        anchor_overlap=True,
        note="the title must share a concrete word with the item titles, so it is not pure teasing",
    ),
    "verdict": dict(
        stop="one flat statement at maximum size", hook="a claim the reader may disagree with",
        lead=None, word_band=(4, 12), count_match=False,
        no_scold=True,
        note="no Stop / Don't / Quit openers",
    ),
    "split": dict(
        stop="two contrasting phrases, the second inverted", hook="before and after",
        lead=None, word_band=(0, 12), count_match=False,
        requires=("top", "bottom"),
        note="needs `top` and `bottom` on the cover slide",
    ),
    "endstate": dict(
        stop="the result, large", hook="the result shown, the method kept back",
        lead="token", word_band=(5, 12), count_match=False,
        anchor_overlap=True,
        note="the result word must also appear in an item title",
    ),
    "masthead": dict(
        stop="one dominant line", hook="a magazine-style headline",
        lead=None, word_band=(4, 10), count_match=False,
        note="one big line and one quiet line; the sizes are fixed in carousel.css",
    ),
}

# ---------------------------------------------------------------------------
# BODY SHAPES
# roles: the expected order. "?" means optional, "*" means one or more.
# ---------------------------------------------------------------------------
BODIES = {
    "list":        dict(tier="A", roles=("cover", "credibility?", "item*", "cta")),
    "casestudy":   dict(tier="A", roles=("cover", "credibility?", "item*", "cta"),
                        note="items run problem -> action -> result"),
    "beforeafter": dict(tier="A", roles=("cover", "credibility?", "item*", "cta"),
                        note="state A -> changes -> state B, with numbers at both ends"),
    "datastory":   dict(tier="A", roles=("cover", "credibility?", "item*", "cta"),
                        number_source_required=True,
                        note="spec must carry number_source: 'author' or a source URL and date"),
    "stakes_tldr": dict(tier="B", roles=("cover", "stakes", "credibility?", "item*", "summary", "cta"),
                        note="summary slide repeats the item titles word for word, nothing new"),
}

TEXT_ROLES = ("item", "stakes", "summary", "credibility")


def device_for(spec: dict) -> str:
    """The spec's cover style. Missing means the numeral style."""
    return (spec.get("cover_device") or "numeral").lower()


def body_for(spec: dict) -> str:
    return (spec.get("body") or "list").lower()


def _words(s: str):
    stop = set("a an the and or but of to in on at for with is are it its i my me that this "
               "no not so as by from be been into out up".split())
    return {w for w in re.findall(r"[a-z0-9']+", (s or "").lower()) if w not in stop and len(w) > 2}


def check_cover_device(spec: dict):
    """Cover checks that depend on the cover style. Returns (hard_fails, flags)."""
    hard, flags = [], []
    dev_name = device_for(spec)
    dev = DEVICES.get(dev_name)
    if dev is None:
        return [f"unknown cover_device {dev_name!r}. Choose one of: {sorted(DEVICES)}"], []

    slides = spec.get("slides", [])
    cover = next((s for s in slides if s.get("role") == "cover"), None)
    items = [s for s in slides if s.get("role") == "item"]
    if not cover:
        return hard, flags

    title = cover.get("title") or ""
    w = len(title.split())
    lo, hi = dev["word_band"]
    if title and not (lo <= w <= hi):
        flags.append(f"cover title is {w} words; the {dev_name} style allows {lo} to {hi}")

    if dev["count_match"]:
        nums = [int(x) for x in re.findall(r"([0-9]{1,2})", str(cover.get("lead") or "") + " " + title)]
        if nums and nums[0] != len(items):
            hard.append(f"cover promises {nums[0]} items but the deck has {len(items)} item slides")

    if dev_name == "word":
        lead = str(cover.get("lead") or "")
        if not lead:
            hard.append("word style: the cover needs a `lead` word")
        else:
            limit = dev["lead_max_spaced"] if " " in lead else dev["lead_max_solid"]
            if len(lead.replace(" ", "")) > limit:
                hard.append(f"word style: lead {lead!r} is longer than {limit} letters and will run "
                            f"off the slide. Use a shorter word.")

    for f in dev.get("requires", ()):
        if not cover.get(f):
            hard.append(f"split style: the cover needs `{f}` (two short phrases)")

    if dev.get("no_scold") and SCOLD_RE.search(title):
        hard.append(f"verdict style: the title opens with {title.split()[0]!r}, which reads as a lecture")

    if dev.get("anchor_overlap") and items:
        pool = set().union(*(_words(s.get("title")) for s in items)) - ANCHOR_STOPLIST
        probe = _words(title) | _words(str(cover.get("lead") or ""))
        if not (probe & pool):
            hard.append(f"{dev_name} style: the cover shares no concrete word with the item titles. "
                        f"Name the subject on the cover.")

    units = [f for f in COVER_UNIT_FIELDS if cover.get(f)]
    if "top" in units and "bottom" in units:
        units.remove("bottom")
        units[units.index("top")] = "top+bottom"
    if len(units) > COVER_MAX_UNITS:
        hard.append(f"cover has {len(units)} elements {units}; the most is {COVER_MAX_UNITS}. "
                    f"Delete the weakest one.")
    return hard, flags


def check_body(spec: dict):
    """Checks that depend on the body shape. Returns (hard_fails, flags)."""
    hard, flags = [], []
    body_name = body_for(spec)
    body = BODIES.get(body_name)
    if body is None:
        return [f"unknown body {body_name!r}. Choose one of: {sorted(BODIES)}"], []

    slides = spec.get("slides", [])
    items = [s for s in slides if s.get("role") == "item"]

    if body.get("number_source_required"):
        src = str(spec.get("number_source") or "").strip().lower()
        if src in ("", "assumed", "[assumed]"):
            hard.append("datastory body: `number_source` must be 'author' (your own figure) or a "
                        "source URL and date. An invented number is not allowed.")

    for s in slides:
        if s.get("role") != "summary":
            continue
        titles = {(i.get("title") or "").strip() for i in items}
        lines = [ln.strip() for ln in str(s.get("lines") or s.get("does") or "").split("\n") if ln.strip()]
        if not lines:
            hard.append(f"slide {s.get('n')}: summary slide has no lines")
        for ln in lines:
            if ln not in titles:
                hard.append(f"slide {s.get('n')}: summary line {ln!r} is not an item title word for word")
    if sum(1 for s in slides if s.get("role") == "summary") > 1:
        hard.append("two summary slides; one per deck")
    return hard, flags
