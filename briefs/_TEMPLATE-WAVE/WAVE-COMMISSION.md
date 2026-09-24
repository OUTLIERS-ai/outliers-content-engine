---
date: [FILL IN: YYYY-MM-DD]
type: commission
wave: [FILL IN: wave name, e.g. W01]
piece: [FILL IN: e.g. W01-00]
grounding: [FILL IN: path to this wave's GROUNDING.md from the kit's top folder, e.g. briefs/W01/GROUNDING.md]
premise_source: "[FILL IN: the opinion file, and that the entries are listed in the table below with their entry numbers]"
named_reader: "[FILL IN: the reader in 1 sentence, the same person as in GROUNDING.md]"
grain: "[FILL IN: the position this wave takes that somebody would dispute, AND who will dislike it and why. Use the words: will dislike]"
buyer_pays_for: "[FILL IN: what the reader is paying today, in time, money or years, by staying as they are]"
buyer_loses: "[FILL IN: what they lose if they stay as they are, in the currency they care about]"
buyer_cant_picture: "[FILL IN: the outcome they cannot imagine, because they have never seen it]"
hook: "[FILL IN: optional. At most 2 lines separated by //, first line at most 14 words. For a wave brief, delete this line: each post carries its own opening]"
scene_source: "[FILL IN: optional. A real event the wave may draw on, with where it is recorded. Delete if none]"
format: [FILL IN: optional, e.g. 10 single text posts. Delete if unused]
format_rationale: "[FILL IN: optional. Why this format, and how the lengths should vary across the wave. Delete if unused]"
---

# [FILL IN: wave name]: the wave commission

> **How to fill this in.** This is the brief the writer works from. Fill the header block above: the
> gate refuses the brief if a required field is missing. Delete every optional line you do not
> use. Then fill the table of opinions below, 1 row per draft: your first wave lists your 10
> opinions, later waves list 20 once you have at least 20. Delete the rows you do not use.
> **The gate refuses the brief while any `[FILL IN` is left anywhere in this file**, and prints the
> line numbers.
> Do not write a lessons block yourself: `python3 engine/commission_gate.py --stamp <this file>`
> (on Windows: `python engine/commission_gate.py --stamp <this file>`) writes it at the bottom.
> Then run `python3 engine/commission_gate.py <this file>`
> (on Windows: `python engine/commission_gate.py <this file>`) until it prints
> MAY BE BRIEFED. Delete these instruction lines when you are done.
> See `example/briefs/EXAMPLE-WAVE/EX-01-brief.md` for a filled version.

> **For the writer: the opinions below are the owner's, word for word, and cannot be altered.**
> Build each post out of its opinion. Do not improve the wording of a quote, do not add an opinion
> of your own, and do not reason from the reader to a new claim. If a post will not stand up on its
> opinion, the answer is a different opinion, not an invented one.

## The standard

`your-voice/THE-STANDARD.md`: my real posts, ranked by comments per 1,000 impressions. Read them. Do
not extract rules from them. Write posts that could sit beside them without looking like a guest.

## The marks of machine writing to avoid

Start with these 2, which the original engine measured. Once you have machine drafts on record,
add the marks from the optional table in `THE-STANDARD.md` below them.

1. Every post landing in the same middle length. Vary it: some posts a few lines, some long.
2. Arguing a case: a structured build-up, a list of 3, a restatement, a rhetorical question at the
   end.

## The opinions: 1 row per draft, up to 20

| # | Opinion label | Source: file and entry | Feeling aimed at | Who will dislike it |
|---|---|---|---|---|
| 01 | [FILL IN] | [FILL IN: e.g. OPINIONS.md entry 3] | [FILL IN] | [FILL IN] |
| 02 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 03 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 04 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 05 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 06 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 07 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 08 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 09 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
| 10 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |

Rows 01 to 10 are for your first wave. For a wave of 20, add rows 11 to 20 in the same layout.
Each opinion appears once. Never list the same opinion twice in 1 wave: the writer copies the
opinion into the post word for word, so 2 posts from 1 opinion share a sentence, and
`batch_checks.py` fails a wave where posts share a sentence.

A post nobody would object to is not written.

## What no post in this wave may do

- [FILL IN: e.g. name a price, a date or an offer]
- [FILL IN: e.g. cite an author, a book or a study. Opinions are stated as the owner's own]
- [FILL IN: e.g. teach a subject the reader does not need from you]
- Use the "it's not X, it's Y" sentence or a long dash. The checker fails both.

## The checks that run

Code only: `post_checks.py` on every draft, `batch_checks.py` across the wave. No draft is scored
for quality by a model. The owner cuts, and every cut is recorded in `CUTS.md` with a reason, on the
keeps and the cuts alike.
