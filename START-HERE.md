# Start here

Read this once, all the way through, before you run a wave. It is short on purpose. The rules
below came out of 2 earlier versions of this engine that failed, and each rule is here because
breaking it cost a batch of posts.

## The 6 rules of this engine

1. **A post exists to get a reaction from a reader.** Being well made and being correct are only
   the floor. A tidy, accurate post that nobody answers has failed.
2. **The writer never picks the opinion.** It is handed 1 of yours, word for word, and cannot
   change it. If a post will not stand up on its opinion, the answer is a different opinion, never
   an invented one.
3. **The standard is examples, never rules.** `your-voice/THE-STANDARD.md` contains your best real
   posts. The writer reads them and is told not to turn them into rules.
4. **No part of the engine marks its own work, and no model judges the feeling.** The code checks
   for machine marks. Whether a post makes a reader feel what it aims at is your call alone.
5. **Fact checks come after you approve a post, not before drafting.** Checking an invented figure
   is worth doing. Checking an opinion for correctness flattens it.
6. **Write a full wave and cut.** You choose from the whole wave on your own taste: 10 drafts in
   your first wave, 20 in later waves. The machine never narrows the batch to 2 for you.

## The return-path rule

**Every correction you make becomes a lesson with an action, and the next brief is forced to carry
it.**

A lesson is a line in `data/findings.jsonl`. It has to say what to do differently, or the engine
refuses it. When you stamp your next brief, every live lesson is written into it, and the gate
refuses a brief whose lessons block is missing or out of date. That is the whole point of the
engine. Without it, you end up with a growing list of accurate notes about what went wrong and the
same posts coming out.

A lesson never goes into a rules document or a prompt. It goes into `data/findings.jsonl`, through
the command, where the gate reads it.

## Before your first wave: set the stopping test

Write this down now, with a real number, before a single draft exists.

> **Of the first 30 drafts this engine writes for me (my first 2 waves: 10, then 20), at least
> [FILL IN: a number above 0] will be posted within [FILL IN: a number] weeks of the review. If fewer are, I stop and change how the
> engine is set up, rather than tweaking it wave by wave.**

2 warnings about this number.

- **Never compare against zero, and never against "fewer than my last 20 posts" if your last 20
  produced none.** A test that cannot fail tells you no more about the engine than no test at all.
- **The same applies to every check.** If a check never rejects a draft, the check is broken, not
  the drafts clean.

Copy your number into the `CUTS.md` of every wave so the tally stays in front of you.

## The loop in 10 steps

Run every command from the kit's top folder. `<wave>` means your wave folder, for example
`briefs/W01`. Type folder names with the same capital letters every time: on a Mac, `briefs/W01`
and `briefs/w01` are 2 different folders.

You need Python 3.9 or later for every step below. Carousels, which are not part of this loop,
need Python 3.10 or later (see `README.md`).

### Step 1. Fill in your settings

```
cp config.example.json config.json          (Windows: copy config.example.json config.json)
```

Open `config.json` and fill every setting. Each carries a note saying what it does and where its
default came from.

**Tip:** rather than editing the JSON by hand, answer the questions in the notes to Claude Code and
ask it to fill in `config.json` for you. Hand-edited JSON breaks on a single missing comma or quote
mark. Then run `python engine/kitconfig.py` to print the settings in force and check them.

### Step 2. Write your opinions

Quick start: fill `your-voice/opinions/OPINIONS.md` with 10 opinions by hand, in the words you
would say out loud. Your first wave uses each of them once, so it is 10 drafts. To run waves of
20, add opinions until the file has at least 20.

Mining path, later: fill `your-voice/opinions/_EXCLUSIONS.md` first, then

```
python engine/mine_transcripts.py
```

and give Claude `prompts/mine-a-month.md` for 1 month at a time.

### Step 3. Write your standard

Copy your best real posts, exactly as published, into `your-voice/THE-STANDARD.md`. Copy
`your-voice/my-posts.example.csv` to `your-voice/my-posts.csv` (the copy stays on your computer:
it is listed in `.gitignore`) and record your posts in it, so you can rank them by comments per 1,000 impressions and
choose which ones go in. The file has no column for that number: work it out as comments divided by
impressions, times 1,000.

**Tip:** a post runs over several lines, and a line break typed straight into a CSV file breaks the
row. Ask Claude Code to add the rows for you: paste the post and its numbers and say which file.
Or open the file in a spreadsheet app such as Excel or Google Sheets and keep the whole post in 1
cell.

### Step 4. Write the brief for the wave

Copy `briefs/_TEMPLATE-WAVE/` to a new folder, for example `briefs/W01/`. Fill in `GROUNDING.md`
(who the reader is) and `WAVE-COMMISSION.md`: the header block at the top of the file, which the
gate needs, and the table with 1 row per opinion. Your first wave lists all 10 of your opinions.
Later waves list 20, once you have at least 20. Never list the same opinion twice in 1 wave.
Delete the table rows you do not use and every optional line you leave empty: the gate refuses a
brief that still contains `[FILL IN`.

### Step 5. Stamp the lessons in, then run the gate

```
python engine/commission_gate.py --stamp <wave>/WAVE-COMMISSION.md
python engine/commission_gate.py <wave>/WAVE-COMMISSION.md
```

The second command prints **MAY BE BRIEFED** or **NOT BRIEFED** with the reasons. Fix every reason
and run it again. No drafting starts on a brief that prints NOT BRIEFED. The gate checks that the
header fields exist and that no `[FILL IN` line is left. It cannot tell whether what you wrote in
them is any good.

### Step 6. Have Claude write the drafts

Give Claude Code `prompts/write-a-wave.md` with the brief path filled in. It writes 1 draft file per
opinion in the brief's table into `<wave>/drafts/`: 10 for your first wave, 20 later.

### Step 7. Run the checks

```
python engine/post_checks.py <wave>/drafts/<draft>.md
python engine/batch_checks.py --dir <wave>/drafts
```

The first checks 1 draft and runs on every draft. The second compares the whole wave: shared lines,
the same opening shape, lengths that barely vary. The writing prompt runs both, but run them
yourself if you change a draft by hand.

### Step 8. Read the drafts on the review page

```
python engine/preview_linkedin.py --dir <wave>/drafts --open
```

Read each draft as a reader would meet it in the feed, cut off at the "see more" point. For each,
decide KEEP, CUT or REWRITE, and say why in your own words. Give a reason for your keeps as well as
your cuts. Keeps are the scarce half of the record.

### Step 9. Record the cuts and turn each correction into a lesson

Give Claude `prompts/record-the-cuts.md`. It writes your verdicts into `<wave>/CUTS.md` and adds a
lesson for each correction:

```
python engine/findings.py add --finding "..." --action "..." --evidence "..." --source "..." --steps brief,hook,body
```

`prompts/add-a-lesson.md` says what a good lesson looks like and the 9 cases the engine refuses.

### Step 10. Check the facts, post by hand, record it

For every post you kept:

1. Check every figure, name and date in it yourself. This is where fact checks belong.
2. Stamp a record of the exact text before it goes out:
   ```
   python engine/provenance.py stamp <wave>/drafts/<draft>.md
   ```
3. Post it by hand.
4. Add a row to `your-voice/my-posts.csv`, with `author` set to `me`, `machine` or
   `machine-then-rewritten`. Without the author on every row, you can never tell whether the
   machine's posts do better or worse than yours.
5. Confirm the lessons are reaching the briefs:
   ```
   python engine/findings.py audit
   ```

Then start the next wave at step 4. The stamp in step 5 carries every lesson you added.
