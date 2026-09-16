# The slide spec format

A slide spec is one JSON file that describes one carousel. `build_carousel.py` turns it into slides
and a PDF. `check/slide_checks.py` checks it first. Put your specs in this `specs/` folder; the
output lands in a folder next to the spec called `<spec name>-output/`.

The three `example-*.json` files in this folder are invented and all pass the checker. Copy one
and change it rather than starting from nothing.

---

## Top-level fields

| Field | Required | What it contains |
|---|---|---|
| `id` | yes | A short name with no spaces, e.g. `"cash-flow-checks"`. Used to name the PDF. |
| `goal` | yes | `"save"` (a reference people keep: a checklist, a method) or `"reach"` (a view people argue with in the comments). The checker stops without it. |
| `cover_device` | no, default `"numeral"` | The cover style. One of: `numeral`, `word`, `question`, `verdict`, `split`, `endstate`, `masthead`. See the cover table below. |
| `body` | no, default `"list"` | The body shape. One of: `list`, `casestudy`, `beforeafter`, `datastory`, `stakes_tldr`. |
| `theme` | no, default `"light"` | `"light"` or `"dark"`. `--theme` on the command line overrides it. |
| `number_source` | only for `datastory` | `"author"` when the number is your own, or a source web address and date. |
| `caption` | no | The text you will post above the PDF. The checker applies your house rules and sign-off rule to it. The renderer ignores it. |
| `slides` | yes | The list of slides, in order. |

Any field starting with `_` (like `_note`) is ignored by both programs. Use it for notes to yourself.

---

## Slide roles and their fields

Every slide has `n` (its number, 1, 2, 3 ...) and `role`.

### `cover` (always slide 1)

| Field | What it contains |
|---|---|
| `kicker_top` | Optional. A small label above the title, in capitals and the accent colour. |
| `lead` | The giant element. A digit for `numeral`, one word for `word`, a result for `endstate`, a `?` for `question`. |
| `title` | The headline. |
| `kicker` | Optional. One line under the title saying what is at stake: what it costs, replaces or saves. Never "swipe" or "read on": the cover already prints a swipe arrow. |
| `top`, `bottom` | `split` cover only: two short contrasting phrases. The second is drawn inverted. |

The cover may carry at most 3 of: `lead`, `title`, `kicker`, the `top`+`bottom` pair (counted as one).

| Cover style | Title words | Rule |
|---|---|---|
| `numeral` | 6 to 10 | The number in `lead` (or the title) must equal the number of item slides. |
| `word` | 3 to 10 | `lead` is one word, 6 letters at most (7 if it has a space). |
| `question` | 6 to 12 | The title must share a concrete word with an item title. |
| `verdict` | 4 to 12 | One flat statement. Must not open with Stop, Don't or Quit. |
| `split` | 0 to 12 | Needs `top` and `bottom`. |
| `endstate` | 5 to 12 | The result word must also appear in an item title. |
| `masthead` | 4 to 10 | One big line, one quiet kicker. |

A title outside the word range is a warning, not a stop. The other rules stop the render.

### `item` (the body of the deck, one item per slide)

| Field | Limit | What it contains |
|---|---|---|
| `numeral` | | The big faint number, e.g. `"1"`. Leave it out on a screenshot slide. |
| `idx` | | Optional small label, e.g. `"Check 1 of 5"`. |
| `title` | 46 characters, hard | The named item. |
| `does` | 130 characters, warning | What it is or how it works. The usable part. |
| `got` | | The result. May contain `<b>bold</b>` spans. Optional on a screenshot slide. |
| `cue` | 8 words, hard | The one highlighted phrase, copied exactly from `got`. |
| `cue_does` | 8 words, hard | Or highlight a phrase copied exactly from `does` instead. Never both. |
| `shot` | | Optional picture, path relative to the spec file, e.g. `"images/my-screen.png"`. Replaces the big number. |

Each item must be a different item that makes sense on its own. The checker stops if two items share
too many words, or if most `does` lines open the same way.

### `credibility` (optional, slide 2)

`title` and `does`. Only use it if it gives the reader something, for example a filter ("47 tried,
these 5 kept"). A slide that only says where the advice came from is stopped by the checker.

### `stakes` and `summary` (body `stakes_tldr` only)

`stakes` sits at slide 2 with `title` and `does`. `summary` sits before the last slide and has
`lines`: the item titles, one per line, copied word for word, separated by `\n`.

### `cta` (the ask, last slide)

| Field | What it contains |
|---|---|
| `title` | The closing line. |
| `cta` | The ask, drawn as an inverted block, e.g. `"Save it. Start with check 1."` |
| `button` | Optional. A button shape with text. A PDF is not clickable, so say where to go in words. |

At most 2 `cta` slides. If there is one, the last slide must be one. Neither can be slide 1 or 2.

### `graph` (optional closing diagram)

| Field | Limit | What it contains |
|---|---|---|
| `title` | | The headline above the diagram. |
| `idx` | | Optional small label. |
| `nodes` | 2 to 7 | Named points, e.g. `["Photo", "Category"]`. Keep names under about 14 characters. |
| `edges` | | Lines between points, as pairs of point numbers counting from 0: `[[0,1],[1,2]]`. |
| `lit` | exactly 1 | The one connection drawn heavy: `[[1,2]]`. |

A diagram must be the very last slide. That means a deck with a diagram has no `cta` slide.

---

## Rules on the words, on every slide

Stopped: long dashes; vague filler words (the list is `VAGUE` in `check/slide_checks.py`); a named month, a year, or "last/this/next
week/month/year"; "that's the whole X" on a closing slide; lines that tell the reader where a claim
came from ("verified against", "on recorded calls"); a handful of widely repeated platform
statistics; anything in `check/house_rules.json`.

Warned: "you" or "your" outside the `cta` slide; a short bold slogan with no number in it.

---

## A short example

```json
{
  "_note": "INVENTED EXAMPLE",
  "id": "three-garden-jobs",
  "goal": "save",
  "cover_device": "numeral",
  "body": "list",
  "theme": "light",
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
     "cta": "Save it and start with job 1."}
  ]
}
```
