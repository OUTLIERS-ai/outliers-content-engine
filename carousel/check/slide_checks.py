"""slide_checks: checks a carousel slide spec (JSON) before it is rendered.

It reads the spec, not the pictures. Passing it means the spec breaks none of the rules below.
It does NOT mean the deck is good. Always look at the phone-size images afterwards.

What it checks (hard fail = the render stops; flag = a warning for you to judge):
  Writing      long dashes, vague filler words, lines that tell the reader where a claim came
               from, often-repeated unverified platform statistics, calendar dates on slides,
               the "that's the whole X" closing line, your house rules (check/house_rules.json)
  Items        every item has a title / does / got, no two items say the same, the item
               lines do not all open the same way, the bold phrases do not all share one shape
  Cover        the rules for the chosen cover style (check/device_rules.py), no swipe
               instruction in the kicker
  Layout       title length, does length, one highlighted phrase per slide and it must quote the
               copy, a diagram only on the last slide with named points (7 at most),
               call-to-action placement, a declared goal
  Caption      if the spec carries a caption: house rules and the sign-off line

Usage:
  python slide_checks.py <spec.json>                 prints JSON, exit 1 on any hard fail
  python slide_checks.py <spec.json> --rules FILE    use a different house rules file
  python slide_checks.py --selftest                  runs the checker on invented specs

Standard library only. Python 3.9+. Windows and Mac.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import assert_not_evidence  # noqa: E402
from device_rules import KICKER_INSTRUCT_RE, check_body, check_cover_device  # noqa: E402

DEFAULT_RULES = HERE / "house_rules.json"

# ---- generic writing rules ------------------------------------------------------------------
LONG_DASH = re.compile(r"[—–]")  # em dash and en dash
VAGUE = re.compile(r"\b(the thing|that thing|things|stuff)\b", re.I)
SECOND_PERSON = re.compile(r"\b(you|your|you're|you've)\b", re.I)
# Platform statistics that circulate widely with no traceable source. Quoting them invites
# a correction in the comments. Add your own if you keep seeing others.
UNVERIFIED_STATS = re.compile(r"(39%|15x|15 times|6\.60%|36% completion|5x clicks|585%)", re.I)
# A three or four word slogan in bold, written to be screenshotted rather than to inform.
APHORISM = re.compile(r"^\W*\w+ \w+ (a |the )?\w+\.?\W*$")
NUMBERISH = re.compile(r"\d|\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
                       r"twenty|thirty|forty|fifty|hundred|thousand|half|double|twice)\b", re.I)
# "That's the whole X" / "This is the real Y": a tidy button line that replaces a real ending.
CRYSTALLISER_RE = re.compile(r"\b(that(?:'s| is)|this is) the (whole|entire|real|only) (\w+)\b", re.I)
# A named month, a bare year, or "last/this/next month|week|year" on a slide.
ABSOLUTE_DATE_RE = re.compile(
    r"\b(?:january|february|march|april|june|july|august|september|october|november|december)\b"
    r"|\b(?:jan|feb|apr|sept|oct|nov|dec)\b"
    r"|\b(?:last|this|next)\s+(?:month|week|year)\b"
    r"|\b(?:19|20)\d{2}\b",
    re.I,
)

TITLE_MAX_CHARS = 46   # longer titles drop below a readable headline size on a phone
DOES_MAX_CHARS = 130   # longer `does` lines drop below a readable body size on a phone
CUE_MAX_WORDS = 8
MAX_NODES = 7

TEXT_FIELDS = ("title", "does", "got", "kicker", "kicker_top", "cue", "cue_does",
               "cta", "button", "idx", "lines", "top", "bottom", "lead")

STOP = set("a an the and or but of to in on at for with is are it its i my me that this "
           "no not so as by from be been into out up".split())


# ---------------------------------------------------------------------------------------------
def load_rules(path=None) -> dict:
    p = Path(path) if path else DEFAULT_RULES
    rules = {"banned_words": [], "banned_phrases": [], "signoff_line": "", "signoff_required": False}
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        rules.update({k: v for k, v in data.items() if not k.startswith("_")})
    return rules


def words(s: str):
    return [w for w in re.findall(r"[a-z0-9']+", (s or "").lower()) if w not in STOP and len(w) > 2]


def jaccard(a, b):
    A, B = set(a), set(b)
    return len(A & B) / len(A | B) if A and B else 0.0


def does_opener(s: str) -> str:
    toks = re.findall(r"[A-Za-z']+", s or "")
    if len(toks) < 2:
        return "?"
    head = toks[0].lower()
    if head == "it":
        return "It " + ("VERB" if toks[1].lower().endswith(("s", "es")) else toks[1].lower())
    return head


def got_shape(s: str) -> str:
    plain = re.sub(r"</?b>", "", s or "")
    beats = len([x for x in re.split(r"(?<=[.!?])\s+", plain) if x.strip()])
    bolds = re.findall(r"<b>(.*?)</b>", s or "")
    if not bolds:
        return f"{beats}beat/nobold"
    tail_bold = plain.strip().rstrip(".!?").endswith(bolds[-1].strip().rstrip(".!?"))
    return f"{beats}beat/{'tailbold' if tail_bold else 'midbold'}"


def punch_shape(b: str) -> str:
    t = b.strip().lower()
    if re.match(r"^no [\w\s]+, no ", t):
        return "No X, no Y"
    if t.startswith("nobody"):
        return "Nobody ..."
    if t.startswith("i "):
        return "I ..."
    if t.startswith("it "):
        return "It ..."
    return "other"


def slide_text(s: dict) -> str:
    return " ".join(str(s.get(k) or "") for k in TEXT_FIELDS)


# ---------------------------------------------------------------------------------------------
def check_house_rules(spec: dict, rules: dict):
    hard, flags = [], []
    slides = spec.get("slides", [])
    caption = str(spec.get("caption") or "")
    for s in slides:
        text = slide_text(s)
        for w in rules.get("banned_words") or []:
            if w and re.search(r"\b" + re.escape(w) + r"\b", text, re.I):
                hard.append(f"slide {s.get('n')}: banned word {w!r} (house_rules.json)")
        for ph in rules.get("banned_phrases") or []:
            if ph and ph.lower() in text.lower():
                hard.append(f"slide {s.get('n')}: banned phrase {ph!r} (house_rules.json)")
    if caption:
        for w in rules.get("banned_words") or []:
            if w and re.search(r"\b" + re.escape(w) + r"\b", caption, re.I):
                hard.append(f"caption: banned word {w!r} (house_rules.json)")
        for ph in rules.get("banned_phrases") or []:
            if ph and ph.lower() in caption.lower():
                hard.append(f"caption: banned phrase {ph!r} (house_rules.json)")

    sign = (rules.get("signoff_line") or "").strip()
    if sign:
        for s in slides:
            if sign.lower() in slide_text(s).lower():
                hard.append(f"slide {s.get('n')}: the sign-off line is on a slide. It belongs at the "
                            f"end of the caption only.")
    if rules.get("signoff_required"):
        if not sign:
            flags.append("house_rules.json: signoff_required is true but signoff_line is empty")
        elif not caption:
            flags.append("house_rules.json requires a sign-off, but the spec has no `caption` to check")
        elif not caption.rstrip().endswith(sign):
            hard.append(f"caption does not end with the sign-off line {sign!r}")
    return hard, flags


def check_writing_and_items(spec: dict):
    hard, flags = [], []
    slides = spec["slides"]
    items = [s for s in slides if s.get("role") == "item"]

    reader_text = " ".join(slide_text(s) for s in slides)
    if LONG_DASH.search(reader_text):
        hard.append("a long dash is on a slide. Use a full stop or a comma.")
    if UNVERIFIED_STATS.search(reader_text + " " + str(spec.get("caption") or "")):
        hard.append("an often-repeated platform statistic with no traceable source is quoted. Cut it.")

    for s in slides:
        for f in ("title", "does", "got", "kicker", "cta", "lines", "top", "bottom"):
            v = str(s.get(f) or "")
            if VAGUE.search(v):
                hard.append(f"slide {s['n']} [{f}]: vague filler in {v!r}. Name the actual object.")
            # The closing call to action speaks to the reader by design, so only flag elsewhere.
            if SECOND_PERSON.search(v) and s.get("role") != "cta":
                flags.append(f"slide {s['n']} [{f}]: addresses the reader as 'you'. Fine if meant; "
                             f"most teaching slides read better in the first person.")

    # the three parts of an item slide
    for s in items:
        needed = (("title", "title"), ("does", "does")) if s.get("shot") \
            else (("title", "title"), ("does", "does"), ("got", "got"))
        missing = [b for b, k in needed if not s.get(k)]
        if missing:
            hard.append(f"slide {s['n']}: item is missing {missing}. An item needs title, does and got "
                        f"(got is optional when the slide has a screenshot).")
        for b in re.findall(r"<b>(.*?)</b>", s.get("got") or ""):
            # a short bold phrase carrying a number ("nine weeks early") is a result, not a slogan
            if NUMBERISH.search(b):
                continue
            if APHORISM.match(b) and len(b.split()) <= 4:
                flags.append(f"slide {s['n']}: bold slogan {b!r}. Land on the concrete result instead.")

    # two items that say the same
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a = words((items[i].get("title") or "") + " " + (items[i].get("does") or ""))
            b = words((items[j].get("title") or "") + " " + (items[j].get("does") or ""))
            sim = jaccard(a, b)
            if sim >= 0.34:
                hard.append(f"slides {items[i]['n']} and {items[j]['n']} look like the same item "
                            f"(word overlap {sim:.2f}). Each slide must be a different item.")

    # every item built on one sentence pattern
    if len(items) >= 4:
        openers = Counter(does_opener(s.get("does", "")) for s in items)
        top, n = openers.most_common(1)[0]
        if n / len(items) >= 0.6:
            hard.append(f"{n} of {len(items)} `does` lines open with {top!r}. Vary the openings.")
        gots = [s for s in items if s.get("got")]
        if len(gots) >= 4:
            shapes = Counter(got_shape(s["got"]) for s in gots)
            top, n = shapes.most_common(1)[0]
            if n / len(gots) >= 0.75:
                hard.append(f"{n} of {len(gots)} `got` lines share one pattern ({top}). Vary them.")
        punches = [b for s in items for b in re.findall(r"<b>(.*?)</b>", s.get("got") or "")]
        pc = Counter(punch_shape(b) for b in punches)
        repeats = {k: v for k, v in pc.items() if v >= 2 and k != "other"}
        if repeats:
            hard.append(f"bold phrases repeat one shape {repeats}. Vary them.")
    return hard, flags


def check_structure(spec: dict):
    hard, flags = [], []
    slides = spec["slides"]
    items = [s for s in slides if s.get("role") == "item"]
    cover = next((s for s in slides if s.get("role") == "cover"), None)
    ctas = [s for s in slides if s.get("role") == "cta"]

    if not cover:
        hard.append("no slide has role 'cover'")
    elif slides[0].get("role") != "cover":
        hard.append("the first slide is not the cover")

    ch, cf = check_cover_device(spec)
    hard += ch
    flags += cf
    bh, bf = check_body(spec)
    hard += bh
    flags += bf

    if cover and cover.get("kicker") and KICKER_INSTRUCT_RE.search(cover["kicker"]):
        hard.append("the cover kicker tells the reader to swipe. The cover already shows a swipe "
                    "arrow. Use the kicker for what is at stake: what it costs, replaces or saves.")

    if any(s.get("count") or s.get("page_counter") for s in slides):
        hard.append("a slide declares a page counter. Position is already shown by `idx` and the "
                    "big number, and two counts on one slide disagree.")

    for s in slides:
        blob = " ".join(str(s.get(k) or "") for k in ("title", "does", "got", "kicker", "cue", "lines", "top", "bottom"))
        m = ABSOLUTE_DATE_RE.search(blob)
        if m:
            hard.append(f"slide {s['n']} names a calendar date {m.group(0)!r}. It dates the post and "
                        f"is easy to get wrong. Use a duration ('in six weeks') instead.")
        m = CRYSTALLISER_RE.search(blob)
        if m:
            if s.get("role") in ("cta", "closing"):
                hard.append(f"slide {s['n']} ends on the stock line {m.group(0)!r}. Write a real ending.")
            else:
                flags.append(f"slide {s['n']} uses the stock line {m.group(0)!r}")

    cred = [s for s in slides if s.get("role") == "credibility"]
    if cred:
        c = cred[0]
        expected = 3 if any(s.get("role") == "stakes" for s in slides) else 2
        if c.get("n") != expected:
            flags.append(f"the credibility slide is slide {c.get('n')}; it usually sits at slide {expected}")
        blob = " ".join(str(c.get(k) or "") for k in ("title", "does", "got", "kicker"))
        ch2, cf2 = assert_not_evidence.scan(blob)
        if ch2:
            hard.append("the credibility slide only defends where the advice came from: " + ch2[0]
                        + " This slide is optional. Cut it or give it something the reader keeps.")
        flags += cf2

    if len(ctas) > 2:
        hard.append(f"{len(ctas)} call-to-action slides. Two at most (one mid-deck, one at the end).")
    if ctas and slides[-1].get("role") != "cta":
        hard.append("there is a call-to-action slide but the last slide is not one. End on the ask.")
    if any((c.get("n") or 0) <= 2 for c in ctas):
        hard.append("a call-to-action is in the first two slides. Give something first.")
    stray = [s["n"] for s in items if s.get("cta")]
    if stray:
        hard.append(f"call-to-action text on item slide(s) {stray}. Put it on a role 'cta' slide.")

    for s in items:
        t = s.get("title") or ""
        if len(t) > TITLE_MAX_CHARS:
            hard.append(f"slide {s['n']}: title is {len(t)} characters (most is {TITLE_MAX_CHARS}). "
                        f"It will be too small to read on a phone.")
        d = re.sub(r"</?b>", "", s.get("does") or "")
        if len(d) > DOES_MAX_CHARS:
            flags.append(f"slide {s['n']}: `does` is {len(d)} characters (aim for {DOES_MAX_CHARS} or "
                         f"fewer). Check it on the phone image.")

    goal = (spec.get("goal") or "").lower()
    if goal not in ("save", "reach"):
        hard.append("the spec has no `goal`. Use 'save' (a keepable reference) or 'reach' (a view "
                    "people argue with). A deck that chases both does neither.")

    theme = spec.get("theme")
    if theme is not None and theme not in ("light", "dark"):
        hard.append(f"theme {theme!r} is not 'light' or 'dark'")
    return hard, flags


def check_visual(spec: dict):
    hard, flags = [], []
    slides = spec["slides"]
    items = [x for x in slides if x.get("role") == "item"]

    for x in slides:
        for field in ("bg", "bg_kind", "bg_style", "background"):
            if x.get(field):
                hard.append(f"slide {x['n']}: `{field}` is not supported. Slides have no background "
                            f"images; a picture goes in `shot` on an item slide.")

        cues = [k for k in ("cue", "cue_does") if x.get(k)]
        if len(cues) > 1:
            hard.append(f"slide {x['n']}: {len(cues)} highlighted phrases. One per slide.")

        for k, src in (("cue", "got"), ("cue_does", "does")):
            c = x.get(k)
            if not c:
                continue
            plain = re.sub(r"</?b>", "", str(x.get(src) or ""))
            if c not in plain:
                hard.append(f"slide {x['n']}: `{k}` {c!r} is not copied exactly from `{src}`")
            n_words = len(c.split())
            if n_words > CUE_MAX_WORDS:
                hard.append(f"slide {x['n']}: highlighted phrase is {n_words} words (most is "
                            f"{CUE_MAX_WORDS}). Highlight the key phrase, not a clause.")
            elif plain and len(c) > 0.5 * len(plain):
                flags.append(f"slide {x['n']}: the highlight covers over half of `{src}`. Trim it.")

        if x.get("role") == "graph" or x.get("nodes"):
            nodes = x.get("nodes") or []
            if x["n"] != len(slides) or slides[-1] is not x:
                hard.append(f"slide {x['n']}: a diagram belongs on the last slide only")
            if len(nodes) > MAX_NODES:
                hard.append(f"slide {x['n']}: {len(nodes)} points in the diagram. {MAX_NODES} at most.")
            if len(nodes) < 2:
                hard.append(f"slide {x['n']}: a diagram needs at least 2 named points")
            if any(not str(n).strip() for n in nodes):
                hard.append(f"slide {x['n']}: a diagram point has no name")
            if len(x.get("lit") or []) != 1:
                flags.append(f"slide {x['n']}: highlight exactly one connection in `lit`")
            for pair in (x.get("edges") or []) + (x.get("lit") or []):
                if (not isinstance(pair, list) or len(pair) != 2
                        or not all(isinstance(i, int) and 0 <= i < len(nodes) for i in pair)):
                    hard.append(f"slide {x['n']}: connection {pair!r} must be two point numbers "
                                f"counting from 0")
                    break

    missing = [x["n"] for x in items if not x.get("numeral") and not x.get("shot")]
    if missing:
        flags.append(f"item slide(s) {missing} have no `numeral`")
    return hard, flags


def check(spec: dict, rules: dict = None) -> dict:
    rules = rules if rules is not None else load_rules()
    if not isinstance(spec.get("slides"), list) or not spec["slides"]:
        return {"pass": False, "hard_fails": ["the spec has no `slides` list"], "flags": [], "items": 0}
    for i, s in enumerate(spec["slides"], start=1):
        s.setdefault("n", i)
    hard, flags = [], []
    for fn in (check_writing_and_items, check_structure, check_visual):
        h, f = fn(spec)
        hard += h
        flags += f
    h, f = check_house_rules(spec, rules)
    hard += h
    flags += f
    h, f = assert_not_evidence.scan_slides(spec["slides"])
    hard += h
    flags += f
    items = sum(1 for s in spec["slides"] if s.get("role") == "item")
    return {"pass": not hard, "hard_fails": hard, "flags": flags, "items": items}


# ---------------------------------------------------------------------------------------------
# SELFTEST. Every spec below is invented. A clean spec must pass; each broken copy must fail
# for the reason named.
# ---------------------------------------------------------------------------------------------
def _clean_spec() -> dict:
    return {
        "id": "selftest-clean", "goal": "save", "cover_device": "numeral", "body": "list", "theme": "light",
        "slides": [
            {"n": 1, "role": "cover", "lead": "3", "title": "garden jobs that save a whole weekend",
             "kicker": "Each one takes under an hour."},
            {"n": 2, "role": "item", "numeral": "1", "idx": "Job 1 of 3", "title": "Mulch the beds",
             "does": "A thick layer of bark over bare soil keeps weeds down and keeps water in the ground.",
             "got": "Weeding dropped to <b>twenty minutes a month.</b>", "cue": "twenty minutes a month"},
            {"n": 3, "role": "item", "numeral": "2", "idx": "Job 2 of 3", "title": "Timer on the hose",
             "does": "A battery valve between tap and hose waters the pots at dawn with nobody standing there.",
             "got": "The pots survived a hot fortnight away.", "cue": "a hot fortnight away"},
            {"n": 4, "role": "item", "numeral": "3", "idx": "Job 3 of 3", "title": "Sharpen blades once",
             "does": "A file across the mower blade before the first cut stops grass tearing and browning.",
             "got": "The lawn stayed green <b>through the dry spell</b> without extra feed.",
             "cue": "through the dry spell"},
            {"n": 5, "role": "cta", "title": "Keep this for the first warm weekend.",
             "cta": "Save it and start with job 1."},
        ],
        "caption": "Three garden jobs.\n\nSigned, the gardener.",
    }


def _mutate(fn):
    s = _clean_spec()
    fn(s)
    return s


def selftest() -> bool:
    empty = {"banned_words": [], "banned_phrases": [], "signoff_line": "", "signoff_required": False}
    cases = [
        ("clean invented spec passes", _clean_spec(), empty, True, None),
        ("long dash fails", _mutate(lambda s: s["slides"][1].update(title="Mulch — the beds")), empty, False, "long dash"),
        ("cover count mismatch fails", _mutate(lambda s: s["slides"][0].update(lead="4")), empty, False, "promises 4"),
        ("two highlights fail", _mutate(lambda s: s["slides"][1].update(cue_does="bark")), empty, False, "highlighted phrases"),
        ("highlight not in copy fails", _mutate(lambda s: s["slides"][2].update(cue="a cold week")), empty, False, "not copied exactly"),
        ("missing goal fails", _mutate(lambda s: s.pop("goal")), empty, False, "no `goal`"),
        ("swipe kicker fails", _mutate(lambda s: s["slides"][0].update(kicker="Swipe for all three.")), empty, False, "swipe"),
        ("calendar date fails", _mutate(lambda s: s["slides"][2].update(got="The pots survived all of August.", cue="all of August")), empty, False, "calendar date"),
        ("stock closing line fails", _mutate(lambda s: s["slides"][4].update(title="That's the whole garden.")), empty, False, "stock line"),
        ("vague filler fails", _mutate(lambda s: s["slides"][1].update(does="Bark keeps the weeds and other stuff down all season long.")), empty, False, "vague filler"),
        ("sourcing clause fails", _mutate(lambda s: s["slides"][3].update(got="The lawn stayed green, verified against photos.", cue="stayed green")), empty, False, "SOURCING"),
        ("duplicate items fail", _mutate(lambda s: s["slides"][3].update(title="Mulch the beds again", does="A thick layer of bark over bare soil keeps weeds down and keeps water in.")), empty, False, "same item"),
        ("long title fails", _mutate(lambda s: s["slides"][1].update(title="Mulch every single bed in the garden before it gets warm")), empty, False, "characters"),
        ("diagram not last fails", _mutate(lambda s: s["slides"].insert(2, {"n": 3, "role": "graph", "title": "Links", "nodes": ["A", "B"], "edges": [[0, 1]], "lit": [[0, 1]]})), empty, False, "last slide only"),
        ("CTA not last fails", _mutate(lambda s: s["slides"].insert(4, s["slides"].pop(4)) or s["slides"].append({"n": 6, "role": "item", "numeral": "4", "title": "Clean the gutters", "does": "Ladder, gloves and a bucket.", "got": "No overflow in heavy rain."})), empty, False, "last slide is not"),
        ("house banned word fails", _clean_spec(), dict(empty, banned_words=["mulch"]), False, "banned word"),
        ("house banned phrase fails", _clean_spec(), dict(empty, banned_phrases=["hot fortnight"]), False, "banned phrase"),
        ("required sign-off missing fails", _clean_spec(), dict(empty, signoff_line="See you next time.", signoff_required=True), False, "does not end with"),
        ("required sign-off present passes", _clean_spec(), dict(empty, signoff_line="Signed, the gardener.", signoff_required=True), True, None),
        ("sign-off on a slide fails", _mutate(lambda s: s["slides"][4].update(title="Signed, the gardener.")), dict(empty, signoff_line="Signed, the gardener."), False, "sign-off line is on a slide"),
        ("split cover without phrases fails", _mutate(lambda s: s.update(cover_device="split")), empty, False, "split style"),
        ("verdict scold opener fails", _mutate(lambda s: (s.update(cover_device="verdict"), s["slides"][0].update(lead=None, title="Stop weeding every single weekend"))), empty, False, "lecture"),
    ]
    ok = True
    for name, spec, rules, want_pass, needle in cases:
        r = check(spec, rules)
        good = r["pass"] == want_pass
        if good and needle:
            good = any(needle.lower() in h.lower() for h in r["hard_fails"])
        ok = ok and good
        print(f"{'ok  ' if good else 'FAIL'} {name}")
        if not good:
            print("     hard_fails:", r["hard_fails"])

    # flags: a bold slogan is flagged, a bold number phrase is not
    slogan = check(_mutate(lambda s: s["slides"][1].update(got="Weeding dropped. <b>Soil does the work.</b>",
                                                         cue="Weeding dropped")), empty)
    number = check(_clean_spec(), empty)
    good = any("slogan" in f for f in slogan["flags"]) and not any("slogan" in f for f in number["flags"])
    ok = ok and good
    print(f"{'ok  ' if good else 'FAIL'} bold slogan flagged, bold number phrase not flagged")

    # the shipped examples must pass with the default (empty) house rules
    for p in sorted((HERE.parent / "specs").glob("example-*.json")):
        r = check(json.loads(p.read_text(encoding="utf-8")), empty)
        good = r["pass"]
        ok = ok and good
        print(f"{'ok  ' if good else 'FAIL'} shipped example passes: {p.name}")
        if not good:
            print("     hard_fails:", r["hard_fails"])

    print("\nassert_not_evidence:")
    ok = assert_not_evidence.selftest() and ok
    print("\nslide_checks selftest", "PASSED" if ok else "FAILED")
    return ok


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "--selftest":
        return 0 if selftest() else 1
    rules_path = None
    if "--rules" in args:
        i = args.index("--rules")
        rules_path = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1:
        print(__doc__)
        return 2
    spec = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    r = check(spec, load_rules(rules_path))
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0 if r["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
