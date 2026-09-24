# Prompt: mine 1 month of your transcripts

**When to use it:** after the quick start has produced a wave you would post. This replaces the 10
hand-written opinions with opinions pulled from what you have actually said on calls.

**What it costs.** Pulling your lines out of the transcripts is cheap: it is a Python program.
Reading them is not. A rough guide is 1 token for every 4 characters, so a month pack of 400 KB is
roughly 100,000 tokens of reading before Claude writes a line. That is an estimate from character
counts, not a measurement. Check each pack's size before you start. **Read 1 month per run, never
all of them at once.**

## Before any reading: 4 steps, in this order

1. **Consent.** Your calls contain other people's words, names, money and private lives. Only your own
   words are mined. If you ever want to quote someone else, you need their explicit yes, each time.
2. **Fill in `your-voice/opinions/_EXCLUSIONS.md`.** Read the standing categories, add your own, and
   list any call or passage you already know must never be used. This happens before reading, so it
   is not left to judgement on the day.
3. **Set your speaker labels in `config.json`.** Every name your recorder uses for you: full name,
   first name, company name, account name. Also your transcript folders and the start date.
   Decide `include_other_speaker_context`. Leave it `false` (the default) and the month packs contain
   only your own lines. Set it to `true` and the other person's previous line is written above
   each of yours: it makes a wrongly labelled line easier to spot, but it copies their words, names
   and figures into the pack, and Claude reads all of it.
4. **Pull your lines out** (on Windows: `python engine/mine_transcripts.py`):
   ```
   python3 engine/mine_transcripts.py
   ```
   It writes 1 pack per month with your turns, each with the file and line number. The other
   person's previous line is added above each of yours only when `include_other_speaker_context`
   is `true`. It sets aside any file where 1 speaker label owns nearly every line, because the
   recorder has filed both people's words under 1 name. Do not mine the set-aside files.

## The reading prompt

Paste this into Claude Code with the month filled in. 1 month per run.

```
Read 1 month of my call transcripts and write down the opinions I state, word for word.

The month is: [FILL IN: YYYY-MM]
The pack is: [FILL IN: the month pack mine_transcripts.py wrote]
The output file is: your-voice/opinions/[FILL IN: YYYY-MM].md, copied from
your-voice/opinions/_TEMPLATE-MONTH.md

BEFORE READING

1. Read your-voice/opinions/_EXCLUSIONS.md in full. Every category and row in it is off limits for this run.
2. Read your-voice/opinions/_METHOD.md.

HOW TO READ

- Read the whole pack, in chunks of about 450 lines. Do not sample and do not skim.
- Only my own turns. If the pack shows the other person's line above mine (an italic line), it is
  there only to check who is speaking. Never copy it, and never note a name or figure from it.
- If a turn could be the other person talking, check: with the other person's line in the pack,
  read it; without it, open the source file at the line number and read either side. If you
  still cannot tell, mark it or leave it out.

WHAT TO PICK

- An opinion I state flatly, that somebody would dispute. Not an instruction, not small talk, not
  a question.
- Never a client's name, a client's words, or any figure about a client's business, income or
  prices, even when I say it.
- No material from any category in _EXCLUSIONS.md. When you leave a passage out for that reason, add a
  row to the table in _EXCLUSIONS.md: file, line range, the category and a plain reason. Never
  repeat the material itself in the row.

HOW TO WRITE EACH ENTRY

- A label you write, so it can be found later.
- The quote, verbatim. Copy it exactly: recorder errors left in, blanked words left blank.
  Never smooth, complete or rebuild a sentence.
- Source: the short code for the transcript file and the line numbers.
- Why it carries a post: 1 or 2 sentences.
- Who would object: a named kind of reader.
- Tier: 1 lands hardest (a stranger reading it would react), 2 is an argument, 3 is a working
  position.
- Recurrence: if I say the same opinion again in this month, name where, with the line.
- Never invent an opinion because it would be useful.

AFTER THE MONTH

1. Fill the short-code table at the top of the month file.
2. Update the coverage row for this month in _METHOD.md, and add any trap you found:
   the same call saved twice, or labels that put the other person's words under my name.
3. Report: how many opinions by tier, how many passages were left out and under which
   categories, and any trap found. Then stop. Do not start the next month.
```

## The index step, once some months are done

Run this as its own step, after 1 or more month files are finished.

```
Build your-voice/opinions/_INDEX.md from the finished month files, using the template already in
that file.

1. Read every finished month file in your-voice/opinions/ (files named YYYY-MM.md).
2. Choose subjects that fit what is actually there. Each entry goes under 1 subject only: the
   subject a writer would look in first.
3. Under each subject: 1 line saying what belongs there, then Tier 1 entries, then the rest by
   date. Each line is the month, the entry number and the label, e.g. T1 . 2026-03 #4 . label.
4. Fill the table of subjects with counts, and the total.
5. Keep the warning at the top: never draft from an index line. The quote lives in the month file.
```

## Using the mined opinions

A brief then names an opinion by month file and entry, for example
`premise_source: "your-voice/opinions/2026-03.md entry 4"`. The writer opens the month file and
copies the quote from there, never from the index.
