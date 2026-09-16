"""
post_checks.py  --  mechanical checks on one finished draft. No AI judges anything here.

WHAT IT IS FOR
    A cheap first pass that runs before any person reads a draft. It catches the defects a rule
    can count (em dashes, markdown, stock machine phrases, your banned words, uncontracted
    English) so human attention goes on what a rule cannot judge: is it any good.

HARD FAILS AND FLAGS
    hard_fails  the draft is not shown to anyone until these are fixed (exit code 1)
    flags       worth a look, never block

WHICH RULES ARE YOURS TO SET
    Every taste threshold is in config.json with a note. They are starting defaults that came
    from one person's rejected drafts, not laws. Each can be switched off there.

    sign-off line            signoff_rule: required / optional / off (default off)
    uncontracted negatives   uncontracted_negative_hard_at (default 2 in one post)
    "you" in every sentence  you_density_hard / you_density_flag
    one long sentence        long_sentence_words, applies over long_sentence_applies_over_words
    phrases you never use    banned_phrases
    em dash                  em_dash_rule: hard / flag / off
    "the thing" / "stuff"    vague_filler_rule: hard / flag / off
    your banned words        your-voice/banned_words.json (see banned_words.py)

Checks that always apply: markdown, stock reveal phrases ("the part nobody tells you"), the
"it's not X, it's Y" reframe, and sourcing shown to the reader (assert_not_evidence.py).

Run:  python engine/post_checks.py <draft.md>
      python engine/post_checks.py --text "full post text..."
      python engine/post_checks.py --selftest
Prints JSON: {pass, hard_fails, flags, body_words}.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitconfig  # noqa: E402
import assert_not_evidence  # noqa: E402
import banned_words  # noqa: E402
import unicode_scrub  # noqa: E402
from rule_tables import (  # noqa: E402
    EM_DASH_RE, MARKDOWN_RE, EMOJI_RE, BLACKLIST_VOCAB, TEASE_SIGNPOST,
    reveal_tells, vague_filler_scan,
)

# THE "IT'S NOT X, IT'S Y" REFRAME. A same-paragraph construction: the beat is [.,;] plus at
# most one space, so two separate paragraphs are never read as one couplet. Defined here, the
# lower-level module, and imported by batch_checks.py, so there is one definition.
NEGATION_COUPLET_RE = re.compile(
    r"\b(?:isn't|is not|wasn't|was never|were never|won't be|not)\b"
    r"[^.!?\n]{0,70}?"
    r"[.,;]\s?"
    r"(?:it(?:'s| is)|that(?:'s| is)|they(?:'re| are))\b",
    re.I,
)

# The "not just X, but Y" variant.
NOT_JUST_RE = re.compile(
    r"\bnot (?:just|merely|simply|only)\b[^.!?\n]{0,70}?[,;]?\s*"
    r"(?:but|it(?:'s| is)|they(?:'re| are))\b", re.I)

LINK_RE = re.compile(r"https?://|www\.", re.I)

# Uncontracted English. Negatives ("does not", "cannot") read as robotic fastest, so they carry
# the configurable hard threshold. The be/have forms ("it is", "you are") are only flagged.
# Nothing here demands contractions; plenty of people write posts with none.
UNCONTRACTED_NEG_RE = re.compile(
    r"\b(?:does not|do not|did not|is not|are not|was not|were not|has not|have not|had not"
    r"|cannot|can not|could not|would not|should not|will not|shall not|must not)\b", re.I)
UNCONTRACTED_BE_RE = re.compile(
    r"\b(?:it is|that is|there is|here is|you are|they are|we are|I am"
    r"|I will|you will|we will|they will|I would|you would|it will)\b", re.I)
UNCONTRACTED_BE_FLAG_AT = 5

# Signs a post is anchored in something that happened. Advisory only.
TEMPORAL_RE = re.compile(
    r"\b(yesterday|tonight|this (morning|afternoon|evening|week|weekend|month|year)|"
    r"last (night|week|weekend|month|year|summer|winter)|(the )?last [\w-]+ (days|weeks|months|years|hours)|"
    r"the day before|the other (day|night|week)|"
    r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"[\w-]+ (days|weeks|months|years|hours|minutes) ago|"
    r"since (six|seven|eight|nine|ten|eleven|twelve|\d))\b", re.I)
MONTH_RE = re.compile(  # case-sensitive, so "may" and "march" as verbs do not count
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b")
SCENE_RE = re.compile(
    r"\bI (stood|sat|watched|walked|drove|spent|caught|opened|built|made|wrote|found|stopped)\b"
    r"|\bI've been\b|\bI was (in|at|on|up)\b|\bI'm (in|at|on) the\b", re.I)
SURVEY_MARKERS = [
    "some people say", "some say", "some argue", "others argue", "others say", "others believe",
    "both sides", "on the one hand", "on the other hand", "it depends", "pros and cons",
    "trade-offs", "trade offs", "finding the balance", "a balance to strike", "the right balance",
    "no right answer", "there's no one answer", "only time will tell", "what works for one",
]
STANCE_RE = re.compile(
    r"\bI (think|reckon|believe|bet|refuse|refused|disagree|stopped|won't|wouldn't|would never|never|don't buy)\b"
    r"|\bmy (rule|bet|take|view|answer|advice)\b|\bthe answer is\b"
    r"|\b(better|worse|wrong|nonsense|a lie|a trap)\b", re.I)
NUMBER_RE = re.compile(
    r"[\u00a3$\u20ac%]|\b\d[\d,]*\b|\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|dozen|grand)\b",
    re.I)

# A declared list structure makes a run of short lines the form, not a fault.
LIST_STRUCTURE_WORDS = ("list",)
VALID_RULES = ("hard", "flag", "off")


def sentences(body):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", body.replace("\n", " ")) if s.strip()]


def paragraphs(body):
    return [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]


def named_entities(body):
    """Capitalised words mid-sentence. Crude on purpose: a false hit only silences a flag."""
    ents = []
    for s in sentences(body):
        for tok in s.split()[1:]:
            w = tok.strip("\"'\u201c\u201d\u2018\u2019().,!?;:")
            if re.fullmatch(r"[A-Z][a-z]{2,}", w):
                ents.append(w)
    return ents


def extract_body(text):
    """The live post from a draft file: frontmatter removed, the last '## Draft N' section if
    there is one, and headings, quote callouts, rules and [bracketed notes] dropped."""
    lines = text.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and lines[0].strip() == "---":
        closed = False
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                del lines[:j + 1]
                closed = True
                break
        if not closed:
            break
    draft_idxs = [k for k, ln in enumerate(lines) if re.match(r"^#{1,6}\s*Draft\s*\d", ln.strip(), re.I)]
    if draft_idxs:
        lines = lines[draft_idxs[-1] + 1:]
    body = []
    for ln in lines:
        s = ln.strip()
        if s.startswith(">") or s.startswith("#") or s == "---":
            continue
        if s.startswith("[") and s.endswith("]"):
            continue
        body.append(ln)
    return "\n".join(body).strip()


def declared_structure(text):
    m = re.search(r"^structure:\s*(.+)$", text, flags=re.M)
    return m.group(1).strip().strip('"\'').lower() if m else ""


def _rule(cfg_key):
    v = str(kitconfig.get(cfg_key) or "off").strip().lower()
    return v if v in VALID_RULES else "hard"


def _num(cfg_key):
    """A numeric setting; None, 0, false or blank means switched off."""
    v = kitconfig.get(cfg_key)
    if v in (None, "", False) or v == 0:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _place(level, msg, hard, flags):
    if level == "hard":
        hard.append(msg)
    elif level == "flag":
        flags.append(msg)


def check_post(text):
    body = extract_body(text)
    hard, flags = [], []
    nonblank = [ln.strip() for ln in body.splitlines() if ln.strip()]
    signoff = str(kitconfig.get("signoff_line") or "").strip()
    signoff_rule = str(kitconfig.get("signoff_rule") or "off").strip().lower()

    # --- sign-off line: required / optional / off --------------------------------------
    if signoff_rule == "required":
        if not signoff:
            hard.append("config says signoff_rule is 'required' but signoff_line is empty. "
                        "Set the line in config.json, or set signoff_rule to 'off'")
        elif not nonblank or nonblank[-1] != signoff:
            hard.append("final line is not your sign-off line exactly: %r" % signoff)
    body_no_signoff = body.replace(signoff, "") if signoff else body

    # --- opening word "I": flag only ----------------------------------------------------
    if nonblank:
        m = re.match(r"i(?:'(?:m|ve|d|ll))?\b", nonblank[0].lower())
        if m:
            flags.append("opens with '%s'. Fine when the post is your own account; recast it if "
                         "the post is a verdict aimed at the reader" % m.group(0))

    # --- vague filler -------------------------------------------------------------------
    vf_level = _rule("vague_filler_rule")
    if vf_level != "off":
        vf_hard, vf_adv = vague_filler_scan(body, stuff_carve_out=True)
        if vf_hard:
            _place(vf_level, "vague filler %s: name the actual noun" % vf_hard, hard, flags)
        for ln in vf_adv:
            flags.append("'thing(s)' outside common idiom, check it: \"%s\"" % ln)

    # --- your banned phrases (config) -----------------------------------------------------
    for phrase in kitconfig.get("banned_phrases") or []:
        if not isinstance(phrase, str) or not phrase.strip():
            continue
        rx = re.compile(r"(?<!\w)" + r"\s+".join(re.escape(w) for w in phrase.split()) + r"(?!\w)", re.I)
        m = rx.search(body)
        if m:
            hard.append("banned phrase from config: %r" % m.group(0))

    # --- second-person density ----------------------------------------------------------
    sents = sentences(body_no_signoff)
    you_hard, you_flag = _num("you_density_hard"), _num("you_density_flag")
    if len(sents) >= 6 and (you_hard or you_flag):
        you_any = [s for s in sents if re.search(r"\b(you|your|you're|you've|yours|you'd)\b", s, re.I)]
        ratio = len(you_any) / len(sents)
        if you_hard and ratio >= you_hard:
            hard.append("%d of %d sentences (%.0f%%) speak to 'you'. A post that tells a stranger "
                        "about their own week reads as presumptuous; tell it from your side"
                        % (len(you_any), len(sents), ratio * 100))
        elif you_flag and ratio >= you_flag:
            flags.append("'you' in %d of %d sentences (%.0f%%): thin it"
                         % (len(you_any), len(sents), ratio * 100))

    # --- em dash ------------------------------------------------------------------------
    if EM_DASH_RE.search(body):
        _place(_rule("em_dash_rule"), "em dash or en dash present", hard, flags)

    # --- "it's not X, it's Y" -----------------------------------------------------------
    for m in list(NEGATION_COUPLET_RE.finditer(body)) + list(NOT_JUST_RE.finditer(body)):
        hard.append("'not X, it's Y' reframe: %r. Cut the negated half and say the claim straight"
                    % m.group(0)[:60].strip())

    # --- your banned words (your-voice/banned_words.json) --------------------------------
    bw_hard, bw_soft = banned_words.scan(body)
    hard.extend(bw_hard)
    flags.extend(bw_soft)

    # --- uncontracted English -----------------------------------------------------------
    neg_at = _num("uncontracted_negative_hard_at")
    unc = [m.group(0) for m in UNCONTRACTED_NEG_RE.finditer(body)]
    if neg_at and len(unc) >= neg_at:
        hard.append("%d uncontracted negatives (%s). Contract them: doesn't, don't, isn't, can't, "
                    "won't" % (len(unc), ", ".join(sorted(set(w.lower() for w in unc)))[:70]))
    elif unc:
        flags.append("uncontracted %r: contract it unless the two separate words are doing work"
                     % unc[0].lower())
    be = [m.group(0) for m in UNCONTRACTED_BE_RE.finditer(body)]
    if len(be) >= UNCONTRACTED_BE_FLAG_AT:
        flags.append("%d uncontracted 'it is / you are' forms: reads stiff, contract the ones "
                     "that are not landing a point" % len(be))

    # --- markdown and emoji -------------------------------------------------------------
    if MARKDOWN_RE.search(body):
        hard.append("markdown formatting present (LinkedIn shows the raw symbols)")
    if EMOJI_RE.search(body):
        flags.append("emoji present")

    # --- one long sentence --------------------------------------------------------------
    # A long post made only of short sentences has a flat, uniform rhythm, which is one of the
    # most reliable signs of machine writing. One long, genuinely joined-up sentence breaks it.
    body_words = len(body_no_signoff.split())
    long_words, long_over = _num("long_sentence_words"), _num("long_sentence_applies_over_words")
    sent_lens = [len(s.split()) for s in sents if s.split()]
    longest = max(sent_lens, default=0)
    if long_words and longest < long_words:
        msg = "no long sentence: longest is %d words (setting asks for %d)" % (longest, long_words)
        if long_over is not None and body_words < long_over:
            flags.append(msg + ", advisory only because the post is %d words" % body_words)
        else:
            hard.append(msg)
    if len(sent_lens) >= 5:
        mean_len = sum(sent_lens) / len(sent_lens)
        longs = [n for n in sent_lens if n >= 20]
        if len(longs) / len(sent_lens) >= 0.6 and mean_len >= 22 and min(sent_lens) >= 12:
            flags.append("%d of %d sentences are 20+ words (mean %.0f, shortest %d): uniformly "
                         "long, add a short line" % (len(longs), len(sent_lens), mean_len, min(sent_lens)))

    # --- mobile layout ------------------------------------------------------------------
    paras = paragraphs(body)
    walls = [p for p in paras if len(p) > 120 and len(p.split()) < 30]
    if walls:
        flags.append("%d paragraph(s) over ~120 characters: a wall of text on a phone" % len(walls))
    run = maxrun = 0
    for p in paras:
        longest_sent = max((len(s.split()) for s in re.split(r"(?<=[.!?])\s+", p)), default=0)
        if "\n" not in p and longest_sent < 15:
            run += 1
            maxrun = max(maxrun, run)
        else:
            run = 0
    struct = declared_structure(text)
    is_list = any(k in struct for k in LIST_STRUCTURE_WORDS)
    run_limit = 9 if is_list else 6
    if maxrun >= run_limit:
        flags.append("run of %d short one-line paragraphs with no longer sentence between them%s"
                     % (maxrun, " (list form, limit raised to 9)" if is_list else ""))

    # --- stock phrases ------------------------------------------------------------------
    low = body.lower()
    vocab = [w for w in BLACKLIST_VOCAB if re.search(r"\b" + re.escape(w) + r"\b", low)]
    if vocab:
        flags.append("machine-filler words, check each: %s" % vocab)
    reveal = reveal_tells(body)
    if reveal:
        hard.append("stock reveal phrase(s) %s: drop the wind-up, say it plainly" % reveal)
    signpost = [p for p in TEASE_SIGNPOST if p in low]
    if signpost:
        flags.append("wind-up phrase(s) %s: keep only if it earns its place" % signpost)
    if LINK_RE.search(body):
        flags.append("link in the body (links usually cut reach; put it in a comment)")
    if not NUMBER_RE.search(" ".join(nonblank[:5])):
        flags.append("no number in the first 5 lines")

    # --- signs of a real person ---------------------------------------------------------
    lived = [name for name, ok in (
        ("number", NUMBER_RE.search(body_no_signoff)),
        ("time", TEMPORAL_RE.search(body_no_signoff) or MONTH_RE.search(body_no_signoff)),
        ("name", named_entities(body_no_signoff)),
        ("scene", SCENE_RE.search(body_no_signoff))) if ok]
    if not lived:
        flags.append("nothing that happened: no number, time, name or first-person scene anywhere")
    survey = [m for m in SURVEY_MARKERS if m in low]
    first_person = re.search(r"\b(I|I'm|I've|I'd|[Mm]y|[Mm]e)\b", body_no_signoff)
    if not STANCE_RE.search(body_no_signoff) and (len(survey) >= 2 or not first_person):
        why = "both-sides phrasing %s" % survey if survey else "no first person anywhere"
        flags.append("no stated position: %s. Say what you think" % why)

    # --- invisible characters -----------------------------------------------------------
    uni = unicode_scrub.scan(body)
    if not uni["clean"]:
        detail = ", ".join("%s x%d" % (h["codepoint"], h["count"]) for h in uni["hits"][:6])
        flags.append("%d invisible character(s): %s. Fix with: python engine/unicode_scrub.py "
                     "<draft.md> --fix" % (uni["total"], detail))

    # --- sourcing shown to the reader ---------------------------------------------------
    ah, af = assert_not_evidence.scan(body)
    hard.extend(ah)
    flags.extend(af)
    return {"pass": not hard, "hard_fails": hard, "flags": flags, "body_words": body_words}


def selftest():
    base = {"signoff_line": "That's all from me this week.", "signoff_rule": "off",
            "banned_phrases": ["circle back"]}
    long_sentence = ("I sat with the owner of a small bakery last Tuesday while she counted the "
                     "invoices she had not chased, and the total came to 4,200 pounds of work "
                     "already done and never paid for.")
    good_post = ("Most unpaid invoices are a calendar problem.\n\n" + long_sentence +
                 "\n\nShe didn't need software.\n\nShe needed Friday at 3pm blocked out.\n\n"
                 "I think that's the whole fix.")
    cases = []

    def run(label, cfg, text, want_pass, must_contain=None):
        kitconfig.use(dict(base, **cfg))
        banned_words._loaded = {"hard_words": ["synergy"], "soft_words": [],
                                "allowed_phrases": [], "replace_with": {}}
        r = check_post(text)
        ok = r["pass"] == want_pass
        if must_contain:
            ok = ok and any(must_contain in h for h in r["hard_fails"])
        cases.append("%s %s" % ("pass:" if ok else "FAIL:", label) +
                     ("" if ok else "  -> %s" % r["hard_fails"]))

    try:
        run("clean post passes with sign-off off", {}, good_post, True)
        run("sign-off required and missing fails", {"signoff_rule": "required"}, good_post, False,
            "sign-off")
        run("sign-off required and present passes", {"signoff_rule": "required"},
            good_post + "\n\nThat's all from me this week.", True)
        run("sign-off optional never checked", {"signoff_rule": "optional"}, good_post, True)
        run("em dash fails", {}, good_post.replace("problem.", "problem \u2014 mostly."), False, "em dash")
        run("em dash off passes", {"em_dash_rule": "off"},
            good_post.replace("problem.", "problem \u2014 mostly."), True)
        run("two uncontracted negatives fail", {},
            good_post + "\n\nIt does not help. You cannot fix it later.", False, "uncontracted")
        run("uncontracted threshold switched off", {"uncontracted_negative_hard_at": None},
            good_post + "\n\nIt does not help. You cannot fix it later.", True)
        run("banned phrase from config fails", {}, good_post + "\n\nLet's circle back.", False,
            "banned phrase")
        run("banned word file entry fails", {}, good_post + "\n\nPure synergy.", False, "BANNED WORD")
        run("markdown fails", {}, "**Bold claim** here.\n\n" + good_post, False, "markdown")
        run("not X, it's Y fails", {}, good_post + "\n\nIt isn't the tool, it's the habit.", False,
            "reframe")
        short = "Chase invoices on Friday.\n\nI do. It works."
        run("short post without long sentence only flags", {}, short, True)
        long_flat = "\n\n".join(["Short line %d here." % i for i in range(80)])
        run("long post without long sentence fails", {}, long_flat, False, "long sentence")
        run("long sentence rule switched off", {"long_sentence_words": None}, long_flat, True)
        you_post = "\n\n".join(["You know your week %d is full." % i for i in range(8)])
        run("'you' in every sentence fails", {}, you_post, False, "speak to 'you'")
        run("sourcing shown to reader fails", {}, good_post + "\n\nOn recorded calls I said so.",
            False, "ASSERT-NOT-EVIDENCE")
    finally:
        kitconfig.use(None)
        banned_words._loaded = None
    good = not any(c.startswith("FAIL") for c in cases)
    cases.append("SELFTEST %s (%d checks)" % ("PASSED" if good else "FAILED", len(cases)))
    return "\n".join(cases), good


def main():
    kitconfig.utf8_console()
    ap = argparse.ArgumentParser(description="Mechanical checks on one draft.")
    ap.add_argument("path", nargs="?", help="path to a draft .md")
    ap.add_argument("--text", help="raw post text instead of a file")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        text, good = selftest()
        print(text)
        sys.exit(0 if good else 1)
    if args.text:
        text = args.text
    elif args.path:
        text = Path(args.path).read_text(encoding="utf-8", errors="replace")
    else:
        text = sys.stdin.read()
    result = check_post(text)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
