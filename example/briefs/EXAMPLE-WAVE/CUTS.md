INVENTED EXAMPLE. Sam is not a real person.

# EXAMPLE-WAVE: the cuts

> This is a filled copy of `briefs/_TEMPLATE-WAVE/CUTS.md` for Sam Price, an invented bookkeeper.
> Sam read the 3 drafts on the review page and dictated a verdict on each. Every word is made up.

## The verdicts

| # | Post | Feeling aimed at | Verdict | Reason, in Sam's words |
|---|---|---|---|---|
| 01 | EX-01-01 sunday night books | Recognition, with a sting | REWRITE | "First line's mine and it's good. Then it turns into a maths lesson. My lot switch off at the second number. Say it and stop." |
| 02 | EX-01-02 invoice from the van | A guilty laugh, then a resolution | KEEP | "That's exactly how it goes. Tonight becomes Thursday is word for word what they tell me. Post it." |
| 03 | EX-01-03 the VAT account | A jolt of worry | CUT | "I'd never call a client undisciplined. They're not lazy, they're flat out. This reads like I'm telling them off." |

**Totals:** 1 kept, 1 rewritten, 1 cut.

## Rulings that cover more than 1 draft

1. "Don't tell them off. I'm on their side." Applies to every draft in future waves.

## What the checks said

- `post_checks.py`: 2 of 3 passed. EX-01-03 hard-failed twice, on the long dash and on the "it's not
  a cash flow problem, it's a discipline problem" sentence. Both faults were planted on purpose so
  the example shows the checker catching them. In a real wave the writer fixes hard fails before
  the review page.
- `batch_checks.py`: failed, as expected for this example. All 3 drafts were written from 1
  opinion, so the check reads them as 1 idea told 3 ways (the same words, such as invoice, job and
  bill, turn up in 2 or more posts). A real wave takes a different opinion for every post (10 in a
  first wave, 20 later), and this check is how you catch a wave that quietly repeated itself. Run
  `python engine/batch_checks.py --dir example/briefs/EXAMPLE-WAVE/drafts` to see it.
- Checks that rejected no draft this wave: not judged. 3 drafts are too few to say whether a check
  is working.

## Lessons added from this wave

Sam agreed to 2 lessons. The keep on EX-01-02 was recorded with its reason, and no lesson was drawn
from 1 keep alone.

```
python engine/findings.py add --finding "A draft that did sums lost the reader by the second number." --action "Use at most 1 number per post. If an opinion needs sums, keep only the 1 number that stings and cut the working." --evidence "EXAMPLE-WAVE: 1 of 3 drafts marked REWRITE for this. Sam: 'My lot switch off at the second number.'" --source "example/briefs/EXAMPLE-WAVE/CUTS.md" --steps body

python engine/findings.py add --finding "A draft told the reader off, and the owner cut it for sounding like a telling-off." --action "Write from the reader's side. Never call the reader a name the owner would not say to a client's face, such as lazy, undisciplined or careless." --evidence "EXAMPLE-WAVE: 1 of 3 drafts cut for this. Sam: 'I'd never call a client undisciplined.' Also given as a ruling for every future draft." --source "example/briefs/EXAMPLE-WAVE/CUTS.md" --steps brief,body
```

| Lesson id | From which verdict | The action, in 1 line |
|---|---|---|
| [the id the first command prints] | 01 sunday night books | At most 1 number per post |
| [the id the second command prints] | 03 the VAT account | Write from the reader's side, never call them names |

After both are added, stamping the brief again writes them into it:
`python engine/commission_gate.py --stamp example/briefs/EXAMPLE-WAVE/EX-01-brief.md`

## The stopping test

- **Sam's number, set before the first wave:** of the first 30 drafts this engine writes, at least
  6 will be posted within 4 weeks of the review.
- **Posted so far, from drafts this engine wrote:** 0 of 3. EX-01-02 is kept and waiting for Sam to
  check it and post it.
- **Verdict so far:** too early. 3 of 30 drafts written.
