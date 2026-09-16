"""
assert_not_evidence.py  --  keep the sourcing in the brief, out of the post.

WHY
    Every position a post takes should be sourced: a quote from one of your calls, a file, a line
    number. That sourcing belongs in the BRIEF, where it proves the claim is real. When a drafter
    copies it into the post ("on recorded calls I said...", "verified against the numbers"), the
    post starts defending itself instead of saying what it thinks. A writer showing their working
    reads as nervous, and nervous does not persuade.

WHAT IT CATCHES
    Clauses whose only job is to tell the reader where a claim came from. Hard fails for the
    clear cases, flags for counting frames that are sometimes fine.

WHAT IT DOES NOT BAN
    Specifics, numbers, dates or scenes. "153 changes in ten days" stays. "153 changes, verified
    against the log" loses the last four words.

Used by post_checks.py and commission_gate.py (on the hook). Can also be run on its own.

Run:  python engine/assert_not_evidence.py <draft.md> [...]
      python engine/assert_not_evidence.py --selftest
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# HARD: the clause exists only to source the claim to the reader.
PROVENANCE_HARD = [
    (re.compile(r"\bon (?:a |the )?recorded calls?\b", re.I),
     "'on recorded calls' tells the reader where it came from. Cut it and state the belief."),
    (re.compile(r"\bon (?:the )?record\b(?!\s+(?:label|player))", re.I),
     "'on record' narrates the sourcing to the reader."),
    (re.compile(r"\bon tape\b", re.I),
     "'on tape' is the same move as 'on recorded calls'."),
    (re.compile(r"\bcame off (?:the )?calls?\b", re.I),
     "'came off calls' defends where the material came from instead of delivering it."),
    (re.compile(r"\bverified against\b", re.I),
     "'verified against ...' belongs in the brief, not the copy."),
    (re.compile(r"\bthe record (?:shows|says|does not show|doesn't show)\b", re.I),
     "'the record shows' is evidence language. Assert the point instead."),
    (re.compile(r"\b(?:i )?went back through\b", re.I),
     "'went back through' narrates the research, not the finding."),
    (re.compile(r"\bif you (?:go |went )?(?:back )?(?:and )?check\b", re.I),
     "inviting the reader to audit the claim. That is the writer's job, done already."),
]

# FLAG: counting frames. Sometimes the count is the point; often it is proof in disguise.
PROVENANCE_FLAGS = [
    (re.compile(r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+times\s+in\s+"
                r"(?:a|one|two|three|four|five|six|seven|eight|nine|ten|\d+)?\s*"
                r"(?:days?|weeks?|months?|years?)\b", re.I),
     "an X-times-in-Y-weeks frame counts the evidence at the reader. Keep it only if the count "
     "is the point, not the proof."),
    (re.compile(r"\b\d+\s+(?:saved\s+)?(?:commits?|changes|edits|revisions)\b", re.I),
     "a change or edit count is log language. Say what it produced, not how it was logged."),
    (re.compile(r"\b(?:according to|per) (?:my|the) (?:notes|log|records?|transcripts?)\b", re.I),
     "citing your own records inside the copy."),
]


def scan(text: str):
    """Return (hard, flags) for a blob of reader-facing copy."""
    hard, flags = [], []
    if not text:
        return hard, flags
    for rx, msg in PROVENANCE_HARD:
        m = rx.search(text)
        if m:
            hard.append(f"ASSERT-NOT-EVIDENCE: {m.group(0)!r}: {msg}")
    for rx, msg in PROVENANCE_FLAGS:
        m = rx.search(text)
        if m:
            flags.append(f"assert-not-evidence: {m.group(0)!r}: {msg}")
    return hard, flags


def selftest():
    # Invented lines. (text, expected hard count, expected flag count)
    cases = [
        ("Four times in six weeks, on recorded calls, I said I was not organised.", 1, 1),
        ("This came off calls, and the record shows it.", 2, 0),
        ("Between 3 March and 9 March the price list was changed 12 times.", 0, 0),
        ("At two grand a month, the dull answer is the right one.", 0, 0),
        ("According to my notes, 40 edits went in.", 0, 2),
    ]
    out, good = [], True
    for text, eh, ef in cases:
        h, f = scan(text)
        got = (len(h), len(f))
        if got != (eh, ef):
            good = False
        out.append("%s got %s expected %s :: %s"
                   % ("pass:" if got == (eh, ef) else "FAIL:", got, (eh, ef), text[:60]))
    out.append("SELFTEST %s (%d checks)" % ("PASSED" if good else "FAILED", len(cases)))
    return "\n".join(out), good


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if "--selftest" in argv:
        text, good = selftest()
        print(text)
        return 0 if good else 1
    if len(argv) < 2:
        print(__doc__)
        return 2
    worst = 0
    for a in argv[1:]:
        h, f = scan(Path(a).read_text(encoding="utf-8", errors="replace"))
        print("\n=== %s: %s" % (a, "SOURCING SHOWN TO THE READER" if h else "clean"))
        for x in h:
            print("  HARD:", x)
        for x in f:
            print("  flag:", x)
        worst = worst or (1 if h else 0)
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv))
