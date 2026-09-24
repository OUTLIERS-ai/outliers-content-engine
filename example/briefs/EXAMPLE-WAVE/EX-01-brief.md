---
# INVENTED EXAMPLE. Sam is not a real person.
date: 2026-09-14
type: commission
wave: EXAMPLE-WAVE
piece: EX-01
grounding: example/briefs/EXAMPLE-WAVE/GROUNDING.md
premise_source: "example/your-voice/opinions/OPINIONS.md entries 1, 4 and 5, each listed in the table below and copied word for word."
named_reader: "The owner of a trades business with 1 to 5 people, out on jobs all day, doing quotes and invoices at the kitchen table at night, who calls himself rubbish with numbers."
grain: "An owner who is proud of doing all his own paperwork will dislike this wave, because it says the late nights cost him more than a bookkeeper would. Some will argue that late payment is just how the trade works."
buyer_pays_for: "His evenings, and the money he never claims back or collects on time because the paperwork happens when he is too tired to do it well."
buyer_loses: "Cash he has already earned, and the Sunday nights he could spend with his family."
buyer_cant_picture: "Getting paid within a week of finishing a job. He has only ever chased money, so being paid on time sounds like a story about a bigger firm."
format: 3 single text posts, as a worked example. A first real wave is 10 posts, later waves 20.
format_rationale: "3 is enough to show the loop. The 3 drafts should differ in length: 1 short, 1 medium, 1 longer."
---

INVENTED EXAMPLE. Sam is not a real person.

# EX-01: the example wave commission

> This is a filled copy of `briefs/_TEMPLATE-WAVE/WAVE-COMMISSION.md` for Sam Price, an invented
> bookkeeper. It has no lessons block yet. To see the loop, stamp it and run the gate:
> `python3 engine/commission_gate.py --stamp example/briefs/EXAMPLE-WAVE/EX-01-brief.md`
> (on Windows: `python engine/commission_gate.py --stamp example/briefs/EXAMPLE-WAVE/EX-01-brief.md`)
> then `python3 engine/commission_gate.py example/briefs/EXAMPLE-WAVE/EX-01-brief.md`
> (on Windows: `python engine/commission_gate.py example/briefs/EXAMPLE-WAVE/EX-01-brief.md`).

> **For the writer: the opinions below are Sam's, word for word, and cannot be altered.** Build
> each post out of its opinion. Do not improve the wording of a quote, do not add an opinion of your
> own, and do not reason from the reader to a new claim. If a post will not stand up on its opinion,
> the answer is a different opinion, not an invented one.

## The standard

`example/your-voice/THE-STANDARD.md`: Sam's real posts, ranked by comments per 1,000 impressions.
Read them. Do not extract rules from them. Write posts that could sit beside them without looking
like a guest.

## The marks of machine writing to avoid

Sam has no machine drafts on record yet, so this wave starts with the 2 the original engine
measured:

1. Every post landing in the same middle length. Vary it.
2. Arguing a case: a structured build-up, a list of 3, a restatement, a rhetorical question at the
   end.

## The 3 opinions

| # | Opinion label | Source: file and entry | Feeling aimed at | Who will dislike it |
|---|---|---|---|---|
| 01 | Sunday night books | OPINIONS.md entry 1 | Recognition, with a sting | Owners proud of doing it all themselves |
| 02 | Invoice from the van | OPINIONS.md entry 4 | A guilty laugh, then a resolution | People too tired after a job for paperwork |
| 03 | The VAT account | OPINIONS.md entry 5 | A jolt of worry | Owners who treat the VAT pot as a cash buffer |

A post nobody would object to is not written.

## What no post in this wave may do

- Name a price, a package or a way to book Sam.
- Give tax advice on a specific case.
- Name an app or a piece of software.
- Cite an author, a book or a study.
- Use the "it's not X, it's Y" sentence or a long dash. The checker fails both.

## The checks that run

Code only: `post_checks.py` on every draft, `batch_checks.py` across the wave. No draft is scored
for quality by a model. Sam cuts, and every cut is recorded in `CUTS.md` with a reason, on the keeps
and the cuts alike.
