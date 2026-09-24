# Prompt: add a lesson

**When to use it:** whenever a correction is made: a cut with a reason, a rewrite, a check that got a
draft wrong, a step of the loop that failed. `prompts/record-the-cuts.md` calls this for every
verdict.

**Why it exists:** 2 earlier versions of this engine diagnosed their own faults correctly, again and
again, and the only action either had was to write the diagnosis down. The notes piled up and the
same posts kept coming out. A lesson here is different because the next brief is forced to carry it:
`commission_gate.py --stamp` writes every live lesson into the brief, and the gate refuses a brief
whose lessons block is missing or out of date.

## What a lesson is made of

| Part | What goes in it | Example |
|---|---|---|
| `--finding` | What went wrong or right, in 1 plain sentence | Drafts that did sums lost the reader by the second number. |
| `--action` | **What the writer does differently next wave.** An instruction, not a note | Use at most 1 number per post. If an opinion needs sums, keep the 1 number that stings. |
| `--evidence` | What happened, with counts | 1 of 3 drafts in EXAMPLE-WAVE rewritten for this; reason given: "Too much sums." |
| `--source` | Where the evidence is recorded | example/briefs/EXAMPLE-WAVE/CUTS.md |
| `--steps` | Which steps of the loop must read it, comma separated | body |

**A lesson without an action is an observation.** Observations are what the earlier builds produced
instead of change. The engine refuses them.

## The 9 refusals

The engine refuses, says why, and changes nothing:

1. **A lesson with no finding.**
2. **A lesson with no action.**
3. **An action shorter than 4 words.** "Be better." is refused. "Open on the claim itself, never on
   a question" is accepted.
4. **A lesson naming a step the engine does not know.** The error lists the steps it accepts.
5. **A lesson routed to no step.** A lesson no step reads never changes a draft.
6. **An option the command does not know**, such as a mistyped `--acton` or `--dry-run`, or a value
   with spaces and no quotation marks round it. The error lists the options that command accepts.
7. **Retiring a lesson without a reason.** When a lesson stops being true, it is retired with the
   reason, never quietly deleted.
8. **Retiring a lesson that is not live.**
9. **A brief with a missing or out-of-date lessons block.** `commission_gate.py` prints NOT BRIEFED
   until you stamp the brief again.

What the engine does **not** check: whether an action of 4 or more words is any good. "Try to do
better next time" passes. Reading each lesson before it is added is your job.

## The prompt

Paste this into Claude Code, with the correction under it.

```
Turn the correction below into 1 lesson for data/findings.jsonl.

1. Write the finding as 1 plain sentence about what happened.
2. Write the action as an instruction a writer can follow in the next wave. If you cannot write
   an action, tell me: it is an observation, not a lesson, and it does not get added.
3. Write the evidence: what happened, with counts, and my words in quotation marks where I gave
   a reason.
4. Name the source file where the evidence is recorded.
5. Choose the steps that must read it.
6. Do not generalise beyond the evidence. A rule drawn from 1 draft says so in the evidence.
   Never write a rule from the rejected side alone when kept drafts exist that bear on it: check
   the keeps in CUTS.md first.
7. Show me the lesson. If I agree, run:
   python3 engine/findings.py add --finding "..." --action "..." --evidence "..." --source "..." --steps <steps>
   (on Windows: `python engine/findings.py add --finding "..." --action "..." --evidence "..." --source "..." --steps <steps>`)
8. Report the id it printed.

The correction:
[FILL IN: what happened, and what I said]
```

## After adding lessons

1. Stamp the next brief so it carries them (on Windows: `python engine/commission_gate.py --stamp <brief.md>`):
   ```
   python3 engine/commission_gate.py --stamp <brief.md>
   ```
2. Check the lessons are actually reaching briefs (on Windows: `python engine/findings.py audit`):
   ```
   python3 engine/findings.py audit
   ```
   If the audit reports a lesson that has gone unread while briefs went past it, the loop is not
   working. Find out why before the next wave.
