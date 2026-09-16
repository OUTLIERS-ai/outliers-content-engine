# Prompt: write a wave of drafts

**When to use it:** step 6 of `START-HERE.md`, after your brief prints MAY BE BRIEFED.

**How to use it:** open Claude Code in the kit's top folder, replace the 1 path marked [FILL IN],
and paste the whole of the box.

**How many drafts:** 1 per opinion listed in the brief's table. Your first wave lists your 10
opinions, so it is 10 drafts. Later waves list 20 once you have at least 20 opinions.

**Where it came from:** every instruction below is one the original engine actually ran on when it
produced posts its owner approved: the wave commission it used and the rules it was built on. 3
instructions were added after a test run of this kit found the old ones contradicted the checks:
1 draft per opinion, no sentence reused across drafts, and when a draft is fixed in place.

```
You are writing a wave of LinkedIn text post drafts: exactly 1 draft for each opinion listed in the
brief's table. The number of drafts equals the number of opinions listed. Never write 2 drafts from
1 opinion.

The brief is: [FILL IN: e.g. briefs/W01/WAVE-COMMISSION.md]
The drafts folder is the drafts/ folder beside the brief.

BEFORE YOU WRITE

1. Run: python engine/commission_gate.py <the brief>
   If it prints NOT BRIEFED, stop. Tell me the reasons it gave. Do not write a single draft
   against a brief that fails.

2. Read your-voice/THE-STANDARD.md in full. These are my real published posts.
   Do not extract rules from them. Do not summarise them.
   Write posts that could sit next to them without looking like a guest.
   Take the voice (how warm, how loose, how long, how rough) from these posts.
   Never infer the voice from the subject of the brief.

3. Read the lessons block at the bottom of the brief, between RETURN-PATH:BEGIN and
   RETURN-PATH:END. Each lesson is a change an earlier wave paid for. Obey every DO line in it.
   These are not suggestions.

4. For each opinion in the brief's table, open the opinion file and entry it names and copy my
   words from there. Never write from a label, a title or an index line. Those are notes, not my
   words.

RULES FOR EVERY DRAFT

- 1 opinion per post, and each opinion in 1 post only. My words go into the post exactly as
  written: never improved, shortened, tidied or completed.
- Never reuse a sentence across drafts. Apart from my quoted opinion, every sentence in a draft is
  new to this wave. batch_checks.py fails the wave when 2 drafts share a sentence or a run of 6 or
  more words.
- Do not add an opinion of your own. Do not reason from the reader to a new claim. If a post will
  not stand up on its opinion, stop on that post and tell me. Suggest a different opinion from
  the file. Never invent one.
- State the position flat. No run-up, no scene-setting, no evidence first.
- Do not argue the case. No structured build-up, no list of 3, no restatement, no rhetorical
  question at the end.
- Do not explain where the opinion came from. The call or conversation is where it is sourced,
  never what the post is about.
- Aim each post at 1 named feeling in the reader, and name the person who will dislike it.
  A post nobody would object to is not written.
- Vary length and shape across the wave. Some posts a few lines, some long. A wave where every post
  lands in the same middle length reads as a machine.
- Obey every line under "What no post in this wave may do" in the brief.
- Follow the sign-off setting in config.json.

WRITING THE FILES

- 1 file per draft in the drafts folder, named <piece>-<2 or 3 word label>.md
- Frontmatter, exactly these fields:
    ---
    type: social-post
    approved: false
    wave: <wave name from the brief>
    piece: <this draft's id, e.g. W01-07>
    brief_id: <the brief's piece id>
    premise_source: "<opinion file and entry>"
    feeling: "<the 1 feeling this post aims at>"
    objector: "<who will dislike it>"
    author: machine
    image_path: ""
    ---
- Put the post under a heading: ## Draft 1
- Before I have read a draft, fix its hard fails in place under ## Draft 1.
- Once I have read a draft, a rewrite goes under ## Draft 2 below it. Never overwrite a draft I
  have read. Every program reads only the last ## Draft section of a file.

AFTER WRITING

1. Run: python engine/post_checks.py <draft> on every draft.
   Fix every hard fail in your own drafts, then run the check again.
   Flags are advice. If clearing a flag would make the post softer or vaguer, leave the flag and
   say why.
   If a post was written or rewritten by me, never change my words to pass a check. Report the
   failure once and let me decide.

2. Run: python engine/batch_checks.py --dir <drafts folder>
   Report what it says. Fix a hard fail by changing the drafts, not by explaining it away.

3. Run: python engine/preview_linkedin.py --dir <drafts folder> --open

4. Do not rank, score or pick among the drafts. Do not tell me which are best. I cut on my own
   taste.

5. Report, and only this:
   - how many draft files were written, and where
   - for each draft, whether post_checks passed, and any hard fail you fixed
   - what batch_checks reported
   - any post you stopped on, and why
   - that the review page is open
```
