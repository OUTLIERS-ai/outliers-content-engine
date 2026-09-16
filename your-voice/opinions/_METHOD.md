# How my opinions were mined

> **How to fill this in.** Claude updates this file after each month it reads, following
> `prompts/mine-a-month.md`. Keep it honest: a month not yet read says so. The traps section is for
> faults found in the transcripts themselves, so the next reader does not fall into them.

## How it was done

1. `python engine/mine_transcripts.py` read every transcript dated from [FILL IN: start date,
   YYYY-MM-DD] in [FILL IN: the transcript folders, as set in config.json] and wrote out my turns
   only, each with the file and line number. `include_other_speaker_context` was [FILL IN: false,
   so the packs contain only my lines / true, so the other person's previous line sits above each of
   mine to catch a wrongly labelled turn].
2. [FILL IN: number] of [FILL IN: number] files were set aside because 1 speaker label owned nearly
   every line. That usually means the recorder filed both people's words under 1 name, and mining
   those files would put other people's words into my opinions.
3. What remained: [FILL IN: number] transcripts, [FILL IN: number] of my turns. Read by Claude, 1
   month per run, 1 file per month in this folder.

## The rules this register keeps

- **Verbatim.** No quote is smoothed, completed or rebuilt. Recorder errors are left in.
- **Sourced.** Every entry names the file and the lines.
- **Attribution checked.** Where a turn could belong to the other person, it is marked or left out.
- **Invented opinions never appear.** An opinion I did not state is not added because it would be
  useful.
- **Recurrence recorded.** The same opinion said to 3 different people is a stronger signal than 1
  fluent sentence, and the repeats are named.
- **Only my own words.** No client's name, words or figures, and the exclusions in `_EXCLUSIONS.md`
  applied before reading.

## Coverage

| Month | Transcripts | My turns | Read | Opinions found |
|---|---|---|---|---|
| [FILL IN: YYYY-MM] | [FILL IN] | [FILL IN] | [FILL IN: yes or not yet] | [FILL IN] |
| [FILL IN: YYYY-MM] | [FILL IN] | [FILL IN] | [FILL IN: yes or not yet] | [FILL IN] |

**Totals:** [FILL IN: transcripts], [FILL IN: turns], [FILL IN: opinions] across [FILL IN: number]
month files.

## Traps found in the transcripts

- **Duplicates:** [FILL IN: the same call saved twice in different folders, and which copy the
  month files cite. Or "none found"]
- **Collapsed speaker labels:** [FILL IN: files and line ranges where the other person's words sit
  under my name. Or "none found"]
- **Other:** [FILL IN, or delete]

## Finding an opinion

Open `_INDEX.md`, find the 2 or 3 opinions that fit, then open only those month files. **Never draft
from an index line.** The quote is in the month file.
