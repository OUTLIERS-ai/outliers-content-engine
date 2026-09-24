# Known problems

What this kit does not do, what was planned and never built, and what is unproven. Read it before
you trust a result.

## 1. The check on the last 3 lines against the named feeling was never built

The plan was a check that reads the last 3 lines of each draft and asks whether they deliver the
feeling the draft says it aims at. It was planned and never built. No program in `engine/` does it.
Every draft names a feeling in its header block, and you are the only judge of whether it gets there.

## 2. Carousels are unproven

The text posts came out of a loop that produced posts their owner approved and published. The
carousel maker has not. Read `carousel/KNOWN-PROBLEMS-CAROUSEL.md` before you rely on it.

## 3. Mining transcripts costs real money

`mine_transcripts.py` is cheap: it only pulls your lines out of the files. The expensive part is
Claude reading those lines afterwards. A rough guide is 1 token for every 4 characters of text, so
a month pack of 400 KB is roughly 100,000 tokens of reading before any writing. That is an estimate
from character counts, not a measurement. Check the size of each month pack before you start, and
read 1 month per run.

## 4. The taste thresholds come from 1 person's rejections

Some checks are about taste, not machine marks: how many sentences may address "you", how many
uncontracted negatives such as "does not" a post may carry, and whether a long post needs 1 long
sentence. The starting numbers were measured on the rejected posts of the person the engine was
first built for. Your voice may differ. They are defaults in `config.json`, each with a note on
where it came from and how to switch it off. Change them when your own cuts disagree with them, and
read what a check actually caught before you trust its rate.

## 5. The engine can spot machine marks. It cannot tell you a post will land

The checks find long dashes, stock AI phrases, "it's not X, it's Y" sentences, invisible characters,
and a wave where every post has the same shape. A draft that passes all of them can still be dull,
wrong or pointless. Passing the checks means the post is ready for you to read, not ready to post.

## 6. 2 checks that would have helped were never built

- **No check reads across posts for contradictions.** A draft can say the opposite of a post you
  already approved, on money or status, and the engine will not notice. Read new drafts against the
  ones you have kept.
- **No check reads a hook for whether it can be true.** A first line that makes no sense when taken
  literally passes every check. Read each hook as a plain statement and ask whether it could be true.

## 7. It does not post, schedule or measure

Posting is by hand. The engine keeps no link to LinkedIn and reads no performance numbers except the
ones you type into `your-voice/my-posts.csv`.

## 8. The engine and the carousel maker need different Python versions

- **The engine** (`engine/`) runs on Python 3.9 or later. This was tested on 3.9.
- **The carousel maker** needs Python 3.10 or later. On Windows with Python 3.9,
  installing Playwright fails: a part Playwright depends on, called greenlet, will not install
  there without Microsoft's C++ build tools. Installing Python 3.10 or later avoids this.

## 9. The gate checks that a brief is filled in, not that it is good

`commission_gate.py` refuses a brief with a missing header field, a `[FILL IN` line left in it, or
an out-of-date lessons block. It cannot tell a thoughtful reader description from a lazy one. It
does not check `GROUNDING.md` beyond making sure the file exists, so read that file yourself before
each wave.

## 10. Nothing protects a draft you have kept or rewritten yourself

No program locks a draft. If a check fails your own wording, the prompts tell Claude to report it
and leave your words alone, but nothing in the code stops a later edit. A `gate_override:` line in a
draft's header block is a note for you: `provenance.py stamp` copies it into the post record, and no
check reads it.
