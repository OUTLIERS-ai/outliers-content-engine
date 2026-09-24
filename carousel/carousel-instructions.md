# Carousel instructions for Claude

**How to use this file.** Fill in Part 1 once, in your own words. Then, when you want a carousel,
open Claude in this `carousel/` folder and say: *"Read carousel-instructions.md and make a carousel
about [subject]."* Part 2 is written for Claude and needs no editing.

Anything in `[square brackets]` is a placeholder. Replace it or delete the line.

---

# PART 1: FILL THIS IN

## 1. What a carousel is for, in this kit

A carousel is built from **what you have learned**: something you made, tried, counted or fixed,
and what each part of it gave you. It is **not** a place for your opinions or a theory of how the
world works. Opinions suit a text post. A carousel is a report someone can keep.

If you cannot point at the real work behind a carousel, there is no carousel.

## 2. Your reader

One specific person, described so Claude could pick them out of a room.

- **Who they are:** [e.g. owner of a café or bakery with 2 to 10 staff, does their own books on Sunday nights]
- **What they already pay for** (a tool, a service, a subscription): [e.g. accounting software, a part-time bookkeeper]
- **What they lose** (money, time, clients, sleep, something that slips through): [e.g. cash they did not know was going out]
- **What they cannot picture doing themselves:** [e.g. a 13-week cash forecast]

Every carousel must name what this reader pays for, loses and cannot picture. If a subject cannot name them,
Claude must say so and not build it.

## 3. Subjects you avoid

Subjects you never make carousels about, even if they would do well.

- [e.g. tax advice for a specific person's situation]
- [e.g. anything about competitors by name]
- [e.g. how you make your own content]

## 4. Your true claims

The facts about you and your work that Claude may state. Numbers with units. If it is not on this
list or in the brief, Claude must not state it as fact.

- [e.g. 11 years doing books for small food businesses]
- [e.g. 40 current clients]
- [e.g. the 13-week forecast template, used by 22 clients]

## 5. The last slide, and where readers go

- **What you want readers to do:** [e.g. save the deck / comment with their answer / visit your profile]
- **Where they go to reach you** (a PDF is not clickable, so name the place in words): [e.g. "the link in my profile"]
- **Wording you like for the last slide:** [e.g. "Save it. Start with check 1."]

## 6. Your post sign-off (optional)

The line you end every caption with, if you have one. It never goes on a slide.
If you fill it in and want it enforced, also set it in `check/house_rules.json`.

- **Sign-off line:** []

## 7. Words and phrasings you never use

Put them in `check/house_rules.json` (`banned_words`, `banned_phrases`). The checker then stops any
spec that contains them. List any softer preferences here for Claude to follow:

- [e.g. say "clients", never "customers"]

---

# PART 2: HOW CLAUDE MAKES A CAROUSEL (no need to edit)

## Step 1. Decide whether this carousel should exist

1. Read Part 1.
2. Name the real work the carousel reports on. If there is none (it is an opinion, a theory or a
   framework with nothing made or tried behind it), stop and say so. Suggest a text post instead.
3. Name, for the reader in section 2, what they pay for, what they lose, and what they cannot
   picture, as they apply to this subject. If any of the three is missing, stop and say which.
4. Check the subject against section 3. If it is on the list, stop.

## Step 2. Name the items first

Write the list of items before writing any slide. Each item must be **different** and must
**make sense on its own**. Test: shuffle the slides. If they only make sense in order, this is one
argument chopped into pieces, which is the most common reason carousels get thrown away. Rebuild it
as separate items or return it as a text post.

If you cannot name at least 3 genuinely different items, there is no carousel.

## Step 3. Choose the settings

- `goal`: `save` for a keepable reference (checklist, method, template); `reach` for a view people
  will argue with.
- `cover_device`: vary it between decks. Do not default to the giant number every time; a run of
  number covers reads as lazy. See `specs/SPEC-FORMAT.md` for the 7 styles.
- `body`: `list`, `casestudy` (problem, action, result), `beforeafter`, `datastory` (needs a source
  for the number) or `stakes_tldr`.
- `theme`: whatever the brief says; otherwise `light`.

## Step 4. Write the spec

Save it as `specs/<id>.json`, following `specs/SPEC-FORMAT.md`. Rules for the words:

- The cover must work in under a second: a flat claim, a specific number or an open question
  tied to a named subject. Not a description, not a scene-setter.
- The cover kicker says what is at stake (what it costs, replaces or saves), never "swipe".
- Each item: `title` names it, `does` gives the usable part, `got` gives the result with a number
  where there is one. One highlighted phrase per slide, copied exactly, 8 words at most.
- Only claims from section 4 or the brief. No invented numbers, names, dates or results.
- No sentence that explains where a claim came from ("on recorded calls", "verified against").
  Where it came from belongs in the brief. State the claim.
- No long dashes. No vague filler words (the list is in `check/slide_checks.py`). No months or years on slides.
- **Show, where you can.** A deck of text-only slides reads as boring. If an item could be shown
  (a screenshot, a before-and-after, a table), make the picture, save it in `specs/images/`, and use
  the `shot` field. Pictures must be real or clearly invented examples, never decoration.
- The last slide lands one clear point and one ask (section 5). No recap of every item.

## Step 5. Check, render, look

Run these from this `carousel/` folder. Start each command with `python3` (on Windows: `python`):

```
python3 check/slide_checks.py specs/<id>.json
python3 build_carousel.py specs/<id>.json
```

1. Fix every hard fail the checker reports. Do not use `--force` to get past a hard fail unless the
   person asks for it.
2. Read every flag and decide, out loud, whether it matters.
3. If the render stops with a LAYOUT FAULT, shorten the copy. Do not shrink the font.
4. **Open every image in `specs/<id>-output/phone/` with the Read tool and look at it.** These are
   the size a phone shows. For each slide, say honestly: can the title be read, can the body be read,
   does anything overlap or get cut off, is the highlighted phrase the right one. Also look at
   `cover-small.png`: does the cover still read as one clear idea at feed size?
5. Passing the checker proves only that no written rule was broken. It says nothing about whether
   the deck is any good. The phone images are the real test.

## Step 6. Caption

Write the caption as a short introduction that opens a question and hands over to the slides.
The value lives in the slides. If section 6 has a sign-off line, it is the caption's last line,
word for word. Put the caption in the spec's `caption` field so the checker applies your house rules.

## Step 7. Hand back

Report, in this order:

1. The biggest risk in this deck (a weak item, a claim you softened, a flag you judged harmless).
2. The PDF path and slide count.
3. Your per-slide verdict from the phone images, including anything you changed after looking.
4. The caption.

You never post. The person reads the PDF and the phone images and posts by hand.

## Self-check before hand-back

- [ ] The subject reports real work, not an opinion.
- [ ] Reader's pay-for, lose and cannot-picture are named for this subject.
- [ ] Each item stands alone; shuffled, the slides still make sense.
- [ ] `goal`, `cover_device`, `body`, `theme` are set; the cover style is not the same as last time by default.
- [ ] `slide_checks.py` passes; every flag has been judged.
- [ ] Every claim is in section 4 or the brief.
- [ ] Nothing on a slide explains where a claim came from.
- [ ] At least some slides show a picture where one was possible.
- [ ] Every phone-size image has been opened and looked at, and the verdict is in the hand-back.
- [ ] The sign-off, if any, is only in the caption.
