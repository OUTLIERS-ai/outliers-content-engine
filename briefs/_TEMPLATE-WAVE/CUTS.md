# [FILL IN: wave name]: the cuts

> **How to fill this in.** After you read the wave on the review page, give a verdict on every
> draft: KEEP, CUT or REWRITE, and a reason in your own words. Claude writes them here the same
> session, following `prompts/record-the-cuts.md`, word for word where it can.
> **Give a reason for the keeps too.** A record with only rejections teaches the engine what to
> avoid and never what worked.
> The table has 20 rows. A first wave of 10 drafts uses rows 01 to 10: delete the rest.
> If you skip a draft, Claude writes "no verdict given" in its row and adds no lesson for it.
> See `example/briefs/EXAMPLE-WAVE/CUTS.md` for a filled version.

## The verdicts

| # | Post | Feeling aimed at | Verdict | Reason, in my words |
|---|---|---|---|---|
| 01 | [FILL IN: file name or short label] | [FILL IN: from the draft's header block] | [FILL IN: KEEP, CUT or REWRITE] | [FILL IN] |
| 02 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 03 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 04 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 05 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 06 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 07 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 08 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 09 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 10 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 11 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 12 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 13 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 14 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 15 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 16 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 17 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 18 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 19 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 20 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |

**Totals:** [FILL IN: number] kept, [FILL IN: number] rewritten, [FILL IN: number] cut.

## Rulings that cover more than 1 draft

1. [FILL IN: e.g. "every post that mentions software is too salesy". Or "none"]

## What the checks said

- `post_checks.py`: [FILL IN: how many passed, and any hard fail that reached this page]
- `batch_checks.py`: [FILL IN: what it reported for the wave]
- Checks that rejected no draft this wave: [FILL IN: name them. A check that never rejects needs
  looking at]

## Lessons added from this wave

Each correction above becomes a lesson with an action, through
`python engine/findings.py add ...` (see `prompts/add-a-lesson.md`).

| Lesson id | From which verdict | The action, in 1 line |
|---|---|---|
| [FILL IN: the id the command printed] | [FILL IN: # and post] | [FILL IN] |

## The stopping test

- **My number, set before the first wave:** [FILL IN: copied from START-HERE.md]
- **Posted so far, from drafts this engine wrote:** [FILL IN: number] of [FILL IN: drafts written
  so far]
- **Verdict so far:** [FILL IN: on track, behind, or the test has failed and the set-up changes]
