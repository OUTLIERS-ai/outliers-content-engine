"""
findings.py  --  the lessons file, and the step that reads it back.

WHAT IT IS FOR
--------------
Every time you cut or rewrite a draft, you learn something the next draft must do differently.
The usual fate of that lesson is a note nobody reads again. This program stops that: a lesson
goes into data/findings.jsonl, and commission_gate.py --stamp copies every live lesson into the
next brief before any drafting starts. A brief without the current lessons is refused by the
gate, so a drafter cannot start without them.

WHAT COUNTS AS A LESSON
-----------------------
Something learned that must change what the next draft DOES, with the evidence that makes it
true. A lesson with no action is only an observation, and it is refused. So is an action shorter
than 4 words ("Be better."): it says nothing a writer can follow. Every command also refuses an
option it does not know, rather than ignoring it, and lists the options it accepts.

EACH LESSON NAMES THE STEPS IT CHANGES
--------------------------------------
  brief       what goes into the brief (the reader, the premise, the angle)
  hook        the first two lines
  body        the rest of the post
  check       what to look for before a draft is shown to anyone
  commission  which pieces get commissioned at all

The steps are for grouping. Stamping copies EVERY live lesson into the brief, grouped by step,
whichever steps it names.

THE HONEST CHECK
----------------
`audit` reports how many live lessons have never reached a brief, and the age of the oldest.
If lessons sit unread while briefs are being stamped, it says the loop is broken.

Nothing is ever deleted. A lesson is retired by adding a retirement line with a reason.

Run:
  python engine/findings.py add --finding "..." --action "..." --evidence "..." \
        --source "..." --steps brief,hook,body
  python engine/findings.py audit
  python engine/findings.py list
  python engine/findings.py brief                 all live lessons, grouped by step
  python engine/findings.py brief --step hook     only the lessons for one step
  python engine/findings.py retire --id F0003 --reason "..."
  python engine/findings.py --selftest
"""

import datetime
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitconfig  # noqa: E402

# Module-level so the self-test can point them at a temporary folder.
STORE = kitconfig.resolve(kitconfig.FINDINGS_FILE)
RUNLOG = kitconfig.resolve(kitconfig.FINDINGS_APPLIED_FILE)

STEPS = ("brief", "hook", "body", "check", "commission")

# An action shorter than this ("Be better.") says nothing a writer can follow.
MIN_ACTION_WORDS = 4

# The options each command accepts. Anything else is refused, never ignored, so a mistyped
# option can never add a real lesson by accident.
OPTIONS = {
    "add": ("--finding", "--action", "--evidence", "--source", "--steps"),
    "retire": ("--id", "--reason"),
    "brief": ("--step",),
    "audit": (),
    "list": (),
}

# A live lesson nobody has applied after this many days, while briefs ARE being stamped,
# is reported as a broken loop.
STALE_DAYS = 14


def _today():
    return datetime.date.today().isoformat()


def _read(path):
    p = Path(path)
    if not p.exists():
        return []
    out = []
    with open(p, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                raise SystemExit("%s line %d is not valid JSON. Fix that line by hand; nothing "
                                 "else was changed." % (kitconfig.rel(p), n))
    return out


def _append(path, rec):
    kitconfig.append_jsonl(path, rec)


def load():
    """Return (live lessons, {retired id: reason})."""
    recs = _read(STORE)
    retired = {r["id"]: r.get("reason", "") for r in recs if r.get("kind") == "retire"}
    live = [r for r in recs if r.get("kind") != "retire" and r.get("id") not in retired]
    return live, retired


def live_ids():
    live, _ = load()
    return sorted(f["id"] for f in live)


def applied_map():
    """lesson id -> list of brief names it was stamped into."""
    m = {}
    for r in _read(RUNLOG):
        for i in r.get("ids", []):
            m.setdefault(i, []).append(r.get("run", "?"))
    return m


def next_id():
    n = 0
    for r in _read(STORE):
        try:
            n = max(n, int(str(r.get("id", ""))[1:]))
        except ValueError:
            pass
    return "F%04d" % (n + 1)


def add(finding, action, evidence, source, steps):
    if not finding.strip():
        raise SystemExit("refused: say what was learned in --finding.")
    if not action.strip():
        raise SystemExit(
            "refused: a lesson with no action is an observation.\n"
            "Say what a draft must DO differently, or do not add it.")
    if len(action.split()) < MIN_ACTION_WORDS:
        raise SystemExit(
            "refused: the action %r is %d word(s). A lesson action must say what to do differently,\n"
            "in at least %d words, e.g. \"Open on the claim itself, never on a question\"."
            % (action.strip(), len(action.split()), MIN_ACTION_WORDS))
    if not steps:
        raise SystemExit("refused: name at least one step this changes. Known: %s"
                         % ", ".join(STEPS))
    bad = [s for s in steps if s not in STEPS]
    if bad:
        raise SystemExit("refused: unknown step(s) %s. Known: %s" % (bad, ", ".join(STEPS)))
    rec = {"id": next_id(), "added": _today(), "source": source,
           "finding": finding.strip(), "action": action.strip(),
           "evidence": evidence.strip(), "steps": list(steps)}
    _append(STORE, rec)
    return rec


def retire(fid, reason):
    if not reason.strip():
        raise SystemExit("refused: retiring a lesson needs a reason. A lesson is never deleted.")
    live, _ = load()
    if fid not in {f["id"] for f in live}:
        raise SystemExit("refused: %s is not a live lesson." % fid)
    _append(STORE, {"kind": "retire", "id": fid, "reason": reason.strip(), "added": _today()})


def _lesson_lines(f):
    out = ["  [%s] %s" % (f["id"], f["finding"]), "        DO: %s" % f["action"]]
    if f.get("evidence"):
        out.append("        WHY: %s" % f["evidence"])
    out.append("")
    return out


def brief(step=None):
    """The text that goes into a brief.

    step=None  -> every live lesson, grouped under each step it names. A lesson that names
                  more than one step is written in full under its first step and referred to
                  under the others, so the brief carries every lesson once.
    step=name  -> only the lessons for that step.
    """
    live, _ = load()
    if not live:
        return ("WHAT WAS LEARNED THAT CHANGES THIS BRIEF\n"
                "  No lessons on file yet. That is normal before your first cuts.\n"
                "  After you cut or rewrite a draft, add one: python engine/findings.py add ...\n")
    if step:
        hits = [f for f in live if step in f.get("steps", [])]
        if not hits:
            return ("WHAT WAS LEARNED THAT CHANGES THIS STEP (%s)\n"
                    "  Nothing on file for this step.\n" % step)
        out = ["WHAT WAS LEARNED THAT CHANGES THIS STEP (%s)" % step, ""]
        for f in hits:
            out += _lesson_lines(f)
        return "\n".join(out)

    out = ["WHAT WAS LEARNED THAT CHANGES THIS BRIEF (%d lesson(s))" % len(live),
           "These are not suggestions. Each one is a change an earlier draft paid for.", ""]
    written = set()
    for s in STEPS:
        hits = [f for f in live if s in f.get("steps", [])]
        if not hits:
            continue
        out.append("-- step: %s --" % s)
        for f in hits:
            if f["id"] in written:
                out.append("  [%s] (written in full above, also applies here)" % f["id"])
                continue
            out += _lesson_lines(f)
            written.add(f["id"])
        out.append("")
    # A lesson whose steps are all unknown (edited by hand) must still reach the brief.
    orphans = [f for f in live if f["id"] not in written]
    if orphans:
        out.append("-- step: none recognised (check these lessons' steps) --")
        for f in orphans:
            out += _lesson_lines(f)
    return "\n".join(out).rstrip() + "\n"


def record_applied(run, ids, step="all"):
    _append(RUNLOG, {"run": run, "step": step, "at": _today(), "ids": list(ids)})


def _gate_is_wired():
    gate = Path(__file__).resolve().parent / "commission_gate.py"
    return gate.exists() and "RETURN-PATH" in gate.read_text(encoding="utf-8", errors="replace")


def audit():
    live, retired = load()
    ap = applied_map()
    runs = _read(RUNLOG)
    L = ["LESSONS AUDIT  (%s)" % _today(), "=" * 62,
         "live lessons           %d" % len(live),
         "retired                %d" % len(retired),
         "briefs stamped         %d" % len(runs), ""]
    if not runs:
        if _gate_is_wired():
            L += ["  Nothing has been stamped into a brief yet. This clears the first time you run:",
                  "    python engine/commission_gate.py --stamp <brief.md>"]
        else:
            L += ["  ** commission_gate.py is missing or has no lessons check. **",
                  "  Lessons are being written down and nothing reads them back."]
        L.append("")
    never = [f for f in live if f["id"] not in ap]
    L.append("never reached a brief  %d of %d" % (len(never), len(live)))
    if never:
        oldest = min(never, key=lambda f: f.get("added", _today()))
        try:
            age = (datetime.date.today() - datetime.date.fromisoformat(oldest["added"])).days
        except (KeyError, ValueError):
            age = 0
        L.append("oldest unapplied       %s, added %s (%d days)"
                 % (oldest["id"], oldest.get("added", "?"), age))
        if age >= STALE_DAYS and runs:
            L += ["", "  ** BROKEN. ** A lesson has sat unread for %d days while %d brief(s) were"
                  % (age, len(runs)),
                  "  stamped. Re-stamp your current brief. Do not retire the lesson to clear this."]
        L.append("")
        for f in never:
            L.append("  %s  %-16s %s" % (f["id"], ",".join(f.get("steps", [])), f["finding"][:70]))
    elif live:
        L += ["", "  Every live lesson has reached at least one brief."]
    L += ["", "by step:"]
    for s in STEPS:
        n = sum(1 for f in live if s in f.get("steps", []))
        seen = sum(1 for f in live if s in f.get("steps", []) and f["id"] in ap)
        L.append("  %-11s %3d lessons, %3d have reached a brief" % (s, n, seen))
    return "\n".join(L)


def show():
    live, retired = load()
    ap = applied_map()
    L = ["%d live lessons" % len(live), ""]
    for f in live:
        runs = ap.get(f["id"], [])
        L.append("%s  added %s  steps: %s  stamped into: %s"
                 % (f["id"], f.get("added", "?"), ",".join(f.get("steps", [])),
                    ", ".join(runs) if runs else "NEVER"))
        L.append("   finding : %s" % f["finding"])
        L.append("   do      : %s" % f["action"])
        if f.get("evidence"):
            L.append("   why     : %s" % f["evidence"])
        L.append("   source  : %s" % f.get("source", "?"))
        L.append("")
    if retired:
        L.append("retired: " + ", ".join("%s (%s)" % (k, v[:40]) for k, v in retired.items()))
    return "\n".join(L)


def selftest():
    """Runs against a temporary lessons file. Your data/ folder is never touched."""
    global STORE, RUNLOG
    real = (STORE, RUNLOG)
    ok = []

    def expect_refusal(label, fn, says=None):
        try:
            fn()
            ok.append("FAIL: " + label)
        except SystemExit as exc:
            if says and says not in str(exc):
                ok.append("FAIL: %s (refused for another reason: %s)" % (label, exc))
            else:
                ok.append("pass: " + label)

    with tempfile.TemporaryDirectory() as td:
        STORE = Path(td) / "findings.jsonl"
        RUNLOG = Path(td) / "findings-applied.jsonl"
        try:
            expect_refusal("refuses a lesson with no action",
                           lambda: add("x", "   ", "e", "s", ["hook"]))
            expect_refusal("refuses an unknown step", lambda: add("x", "a", "e", "s", ["nonsense"]))
            expect_refusal("refuses a lesson routed to no step", lambda: add("x", "a", "e", "s", []))
            expect_refusal("refuses to retire without a reason", lambda: retire("F0001", ""))
            expect_refusal("refuses an action shorter than %d words ('Be better.')" % MIN_ACTION_WORDS,
                           lambda: add("Weak openings", "Be better.", "e", "s", ["hook"]),
                           "must say what to do differently")
            full = ["findings.py", "add", "--finding", "Weak openings were cut",
                    "--action", "Open on the claim itself, never on a question",
                    "--evidence", "invented", "--source", "invented", "--steps", "hook"]
            expect_refusal("refuses an unknown option on add (--dry-run)",
                           lambda: main(full + ["--dry-run"]), "unknown option '--dry-run'")
            expect_refusal("refuses an unknown option on retire",
                           lambda: main(["findings.py", "retire", "--id", "F0001", "--reason", "x", "--force"]),
                           "unknown option '--force'")
            expect_refusal("refuses an unknown option on brief",
                           lambda: main(["findings.py", "brief", "--steps", "hook"]), "unknown option '--steps'")
            expect_refusal("refuses an unknown option on audit",
                           lambda: main(["findings.py", "audit", "--verbose"]), "unknown option '--verbose'")
            expect_refusal("refuses an unknown option on list",
                           lambda: main(["findings.py", "list", "--all"]), "unknown option '--all'")
            try:
                main(full[:2] + ["--dry-run"])
                ok.append("FAIL: unknown-option message")
            except SystemExit as exc:
                ok.append("pass: unknown-option message lists the valid options"
                          if "--finding, --action, --evidence, --source, --steps" in str(exc)
                          else "FAIL: unknown-option message -> %s" % exc)
            ok.append("pass: refusals wrote nothing" if not STORE.exists()
                      else "FAIL: a refusal wrote to the store")
            a = add("Openers that start with a date were skipped", "Open on the claim instead",
                    "3 of 3 date openers cut", "invented test", ["hook"])
            b = add("Posts with two ideas were cut", "One idea per post", "invented",
                    "invented test", ["brief", "body"])
            c = add("The brief named no reader", "Name one reader in every brief", "invented",
                    "invented test", ["commission"])
            ok.append("pass: ids count up" if (a["id"], b["id"], c["id"]) ==
                      ("F0001", "F0002", "F0003") else "FAIL: ids")
            text = brief()
            ok.append("pass: brief carries lessons from every step"
                      if all(i in text for i in ("F0001", "F0002", "F0003")) else "FAIL: brief")
            ok.append("pass: brief groups by step"
                      if "-- step: hook --" in text and "-- step: commission --" in text
                      else "FAIL: grouping")
            ok.append("pass: a two-step lesson is written in full once"
                      if text.count("One idea per post") == 1 else "FAIL: duplicate lesson")
            retire("F0002", "invented reason")
            ok.append("pass: retired lesson leaves the brief" if "F0002" not in brief()
                      else "FAIL: retired lesson still stamped")
            record_applied("test-brief", live_ids())
            ok.append("pass: audit sees the stamp" if "briefs stamped         1" in audit()
                      else "FAIL: audit")
        finally:
            STORE, RUNLOG = real
    fails = [x for x in ok if x.startswith("FAIL")]
    ok.append("SELFTEST %s (%d checks)" % ("FAILED" if fails else "PASSED", len(ok)))
    return "\n".join(ok), not fails


def _arg(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else default


def check_options(cmd, rest):
    """Refuse any option the command does not accept, and any stray word, before anything runs."""
    valid = OPTIONS[cmd]
    shown = ", ".join(valid) if valid else "none"
    i = 0
    while i < len(rest):
        tok = rest[i]
        if tok in valid:
            i += 2
            continue
        if tok.startswith("-"):
            raise SystemExit("refused: unknown option %r for '%s'. Nothing was changed.\n"
                             "Valid options for '%s': %s" % (tok, cmd, cmd, shown))
        raise SystemExit("refused: unexpected word %r for '%s'. Put quotation marks round a value "
                         "with spaces in it. Nothing was changed.\nValid options for '%s': %s"
                         % (tok, cmd, cmd, shown))


def main(argv):
    kitconfig.utf8_console()
    a = argv[1:]
    if "--selftest" in a:
        text, good = selftest()
        print(text)
        return 0 if good else 1
    if not a or a[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0 if a else 2
    cmd = a[0]
    if cmd in OPTIONS:
        if "-h" in a[1:] or "--help" in a[1:]:
            print(__doc__)
            return 0
        check_options(cmd, a[1:])
    if cmd == "audit":
        print(audit())
    elif cmd == "list":
        print(show())
    elif cmd == "brief":
        print(brief(_arg(a, "--step")))
    elif cmd == "add":
        steps = [s.strip() for s in (_arg(a, "--steps") or "").split(",") if s.strip()]
        r = add(_arg(a, "--finding", ""), _arg(a, "--action", ""), _arg(a, "--evidence", ""),
                _arg(a, "--source", "?"), steps)
        print("added %s. It goes into the next brief you stamp." % r["id"])
    elif cmd == "retire":
        retire(_arg(a, "--id", ""), _arg(a, "--reason", ""))
        print("retired %s" % _arg(a, "--id", ""))
    else:
        print("unknown command %r. Commands: %s, or --selftest" % (cmd, ", ".join(OPTIONS)))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
