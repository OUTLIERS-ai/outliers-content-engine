# A content engine that writes from your own opinions

This kit writes LinkedIn text posts from opinions you have actually said, checks them with code,
shows them to you on a page laid out like LinkedIn, and turns every cut you make into a lesson
the next batch is forced to carry. It also makes carousels, which are less proven than the text
posts. See `carousel/README.md`.

Every personal file is blank and waiting for you. A fully invented worked example sits in
`example/`, so you can see what a filled file looks like before you fill your own.

> **Keep your filled-in copy private.** Once you fill it in, this folder contains private material:
> your clients' words from call transcripts, your post numbers, your settings. `.gitignore` keeps
> the main private files out of git, but check `git status` before every commit. If you put your
> copy on GitHub, make the repository private.

## What it is

- **Templates** for your opinions, your best posts, and each batch of drafts. A batch of drafts
  is called a wave. Your first wave is 10 drafts, 1 for each of your 10 opinions. Later waves are
  20 drafts, once you have at least 20 opinions on file. Each draft uses a different opinion.
- **4 prompts** you give Claude Code: write a wave, record the cuts, add a lesson, mine a month
  of call transcripts.
- **Python programs** that refuse a brief with missing parts, stamp your lessons into each brief,
  check every draft, compare the drafts in a wave against each other, build the review page, and
  pull your own lines out of call transcripts.

## What it is not

- **It does not post.** You post by hand.
- **It does not choose what you think.** Every post starts from an opinion you wrote or said,
  handed to the writer word for word.
- **It does not judge whether a post is good.** No model scores the drafts. You do, by cutting.
- **It does not know your voice** until you give it your best real posts.
- **It cannot tell you a post will land.** It can spot the marks machine writing leaves. It
  cannot predict a reaction. The rest of what is unproven is in `KNOWN-PROBLEMS.md`.

## 2 ways in

### Quick start: about 1 hour

1. Copy `config.example.json` to `config.json` and fill it in. Each setting carries a note.
   **Tip:** you do not have to edit the JSON by hand. Tell Claude Code your name, headline and
   the subjects you avoid, and ask it to fill in `config.json` from your answers. A missing comma
   or quote mark breaks the whole file.
2. Write 10 opinions by hand in `your-voice/opinions/OPINIONS.md`. Write them the way you would
   say them out loud to a client, not the way you would write a post.
3. Copy your best real posts, exactly as published, into `your-voice/THE-STANDARD.md`.
4. Run your first wave: 10 drafts, 1 per opinion. `START-HERE.md` steps 4 to 10 walk it with the
   command for each step. Your next waves are 20 drafts, once you have at least 20 opinions.

### Mining your transcripts: later, once the loop works

If you record your calls, `python engine/mine_transcripts.py` pulls your own lines out of them,
month by month, with the line numbers. By default the month files contain only your lines. A
setting, `include_other_speaker_context`, also writes the other person's previous line above each
of yours, which helps you spot a wrongly labelled speaker but copies their words, names and
figures into the file. It is off unless you switch it on. Claude then reads 1 month at a time
using `prompts/mine-a-month.md` and writes down the opinions you state flatly, word for word.

Do this after the quick start has produced a wave you would post, not before. Fill in
`your-voice/opinions/_EXCLUSIONS.md` before any reading starts: your calls contain other
people's words, names and numbers. And budget for it. A model reading months of transcripts
costs real money.

## What to install

1. **Python.** Check with `python --version`.
   - **The engine** (everything in `engine/`) works on **Python 3.9 or later**. It uses only
     what comes with Python.
   - **Carousels** need **Python 3.10 or later**. On Windows with Python 3.9, installing
     Playwright fails, because a part it depends on (greenlet) has to be built from source there,
     which needs Microsoft's C++ build tools.
2. **Claude Code.** The prompts are written for it.
3. **Carousels only:** Playwright. The install lines are in `carousel/README.md`.

## The first commands

Run every command from this folder, the one this README sits in.

```
cp config.example.json config.json            Mac or Linux
copy config.example.json config.json          Windows

python engine/post_checks.py example/briefs/EXAMPLE-WAVE/drafts/EX-01-03-the-vat-account.md
python engine/preview_linkedin.py --dir example/briefs/EXAMPLE-WAVE/drafts --open
```

The third line runs the checker on an invented draft with 2 faults planted in it: a long dash and
an "it's not X, it's Y" sentence. It takes a few seconds and should report both as hard fails.
The fourth line opens the review page on the 3 invented drafts in your default browser.

## Where to go next

1. `START-HERE.md`: the 6 rules, the loop in 10 steps, and the stopping test you set before your
   first wave.
2. `example/`: Sam, an invented bookkeeper, with every file filled in.
3. `lessons-worth-adopting.md`: lessons the original engine paid for, restated so you can use
   them from your first wave.
4. `KNOWN-PROBLEMS.md`: read it before you trust any result.

## What sits where

| Folder or file | What is in it |
|---|---|
| `START-HERE.md` | The rules and the loop |
| `config.example.json` | Every personal setting. Copy to `config.json` |
| `your-voice/` | Your best posts, your opinions, your banned words, your post record |
| `briefs/_TEMPLATE-WAVE/` | Copy this folder for each new wave |
| `prompts/` | The 4 prompts for Claude Code |
| `engine/` | The programs |
| `data/findings.jsonl` | Your lessons, 1 per line. Starts empty |
| `example/` | The invented worked example |
| `carousel/` | The carousel maker, with its own README |
| `.gitignore` | Keeps your private files (config, transcripts, month files, post record) out of git |
