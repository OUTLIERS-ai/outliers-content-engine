# Prompt: record the cuts

**When to use it:** step 9 of `START-HERE.md`, while the review page is open and you are reading the
wave.

**How to use it:** read the drafts on the review page. For each 1, say out loud or type KEEP, CUT or
REWRITE, and why, in your own words. Messy is fine: dictate it. Then paste the box below into Claude
Code with your verdicts under it.

**2 reasons this step matters more than it looks.**

1. **Give a reason for your keeps as well as your cuts.** A record of rejections alone teaches the
   engine what to avoid and never what worked. The original engine ended up with hundreds of
   recorded failures and almost no recorded successes, because it was only told to log rejections.
2. **The reason matters more than the verdict.** "Cut" on its own teaches the engine no lesson. "Cut: I would never call my
   clients lazy" becomes a lesson.

```
I have read the wave on the review page. My verdicts are below.

The wave folder is: [FILL IN: e.g. briefs/W01]

1. Write my verdicts into <wave folder>/CUTS.md, in its verdicts table: 1 row per draft, with the
   feeling from the draft's header block, my verdict, and my reason in my own words. Quote me word
   for word. Tidy only where a dictation error makes it unreadable, and never change what I meant.
   Record the reason for keeps as carefully as for cuts.
   If I gave no reason for a draft, write "no reason given" and ask me for 1 at the end.
   If I gave no verdict at all on a draft, write "no verdict given" in its row, add no lesson for
   it, and list those drafts at the end.

2. If a ruling covers more than 1 draft, write it under "Rulings that cover more than 1 draft".

3. Fill "What the checks said" from the check results for this wave. Name any check that
   rejected no draft.

4. For each correction I made (every CUT, every REWRITE, and any keep where I said what made it
   work), write 1 lesson using prompts/add-a-lesson.md, then add it:
     python engine/findings.py add --finding "..." --action "..." --evidence "..." --source "..." --steps <steps>
   The action must be an instruction a writer can follow next wave. The evidence is what happened
   in this wave, with counts. The source is <wave folder>/CUTS.md.
   Show me each lesson before you add it. Add only the ones I agree with.
   Record each added lesson's id in the "Lessons added from this wave" table.

5. If I rewrote a post myself and a check fails my wording, do not change my words. Report the
   failure once. If I say keep it, add this note to that draft's header block:
     gate_override: "<my words and today's date>"
   It is a note for me only. No program enforces it: the checks still fail the draft, and nothing
   stops a later edit. provenance.py copies the note into the post record when the post is
   stamped.

6. For each REWRITE: keep the earlier draft, add the new version under the next ## Draft N heading
   in the same file, run python engine/post_checks.py on it, and tell me when the rewrites are
   ready to read.

7. Update "The stopping test" section with how many drafts from this engine have been posted so
   far.

8. Do not argue with a verdict. Do not re-add a cut post under another name.

My verdicts:
[FILL IN: your verdicts, 1 per draft]
```
