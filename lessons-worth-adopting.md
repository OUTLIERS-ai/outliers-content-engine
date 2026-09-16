# Lessons worth adopting

These are lessons the original engine learned from its owner's rejections, restated so they apply
to anyone. Each one cost at least 1 batch of posts. They come from 1 person's work, so treat them as
a strong starting point, not as law.

None of them is in `data/findings.jsonl`, which starts empty. If one of these proves true in your
own cuts, add it as your own lesson with your own evidence (`prompts/add-a-lesson.md`). From then
on the gate stamps it into every brief.

## About the machinery

**1. A model scoring its own drafts for quality rejects almost none of them.**
Do this: do not add a step where a model rates the drafts. Write a full wave and cut on your own taste.

**2. A check that never rejects is broken, and a rejection rate alone does not prove a check works.**
Do this: note how often each check fails a draft. If the rate is zero, look at the check. After
adding or changing a check, print what it actually caught and read it before you trust it.

**3. A step written in a document does not run.**
Do this: if a step is required, make it a command the loop runs and that fails when the step is
missing. An instruction in a document gets skipped.

**4. When output is weak, look at what the writer was given before adding another check.**
Do this: check the brief, the opinions and the standard first. A stricter check over a thin brief
produces the same weak drafts, more slowly.

**5. A way of spotting the machine is not a writing rule.**
Do this: if you notice machine drafts always do X, use that to spot them. Do not turn it into a
rule that forbids X in every draft. That inversion once removed good material from a whole wave.

## About the drafts

**6. Chasing an advisory flag softened a post.**
Do this: flags are advice. If clearing a flag would make a post vaguer or softer, leave the flag
and note why.

**7. Drafts go vague in their last third.**
Do this: every noun should name an object the reader could point at: the van, the hour, the
invoice, the child's age. Read the last third of each draft hardest.

**8. Write the opinion, not the conversation it came from.**
Do this: the call where you said it is where the opinion is sourced, never the subject of the post.
If a draft mostly retells 1 conversation, the reader is a spectator. Put the reader in the sentence.

**9. A correct diagnosis delivered coldly gets rejected.**
Do this: write from liking the reader. If a draft names the reader's mistake without any warmth, it
reads as contempt, however accurate it is.

**10. The voice gets invented from the subject when the standard is not read.**
Do this: take how warm, loose, long or short a post is from your real posts in the standard, every
wave. A draft about money is not automatically hard and clipped because the subject is money.

**11. A hook has to survive being read literally.**
Do this: restate the first line as a plain claim and ask whether it could be true. A hook that
makes no sense on a literal reading passes every check and still gets rejected.

**12. When a source leaves a number unclear, leave the number out.**
Do this: write only the half you are sure of. Never pick the reading that makes the better sentence.
A number that makes no sense as a financial statement can sink the whole post.

## About the record

**13. A post you write yourself outranks the checker.**
Do this: when you write or rewrite a post and a check fails it, decide yourself. If you keep your
wording, write `gate_override:` with your reason and the date into the draft's header block. It is a
note for you, and `provenance.py stamp` copies it into the post record. No program enforces it: the
checks still fail the draft and nothing stops a later edit, so tell Claude plainly not to change
your words.

**14. Record who wrote every post at the moment you post it.**
Do this: fill the `author` column in `my-posts.csv` every time. Without it you can never answer
whether the machine's posts do better or worse than yours, and the question closes once the post
dates are lost.

**15. A stopping test that cannot fail is useless.**
Do this: set a real positive number of posts that must reach publishing, before the first wave,
and write it down. Never compare against zero.
