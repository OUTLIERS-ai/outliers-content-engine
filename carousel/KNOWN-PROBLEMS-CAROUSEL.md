# Known problems with the carousel maker

Read this before your first deck. It lists what went wrong when this tool was used for real, and
the faults in the tool itself. Nothing here is solved by the checker.

---

## 1. Passing every check is not the same as a deck worth posting

In the most recent version of this tool, 7 carousels were made. **The owner set all 7 aside and
posted none of them.** All 7 pass every automatic check with no hard fails and no warnings.

So the fault is something the checker cannot see. What exactly was wrong with them was never
written down, and this kit does not guess. What it means for you:

- A clean checker result tells you no written rule was broken. Nothing more.
- Judge every deck yourself, as a reader, on the phone-size images, before you post it.
- Expect to throw decks away. That is normal with this tool, not a sign you set it up wrong.

## 2. What was rejected, and why

These are the reasons decks were turned down while this tool was in use, in plain terms.

1. **Slides that are one argument chopped up.** A carousel where each slide is the next paragraph of
   one essay was rejected as nothing more than a long post split into pages. Each slide should be a separate item that makes
   sense on its own. Test: shuffle the slides. If they stop making sense, rebuild.
2. **A subject about the maker's own tools.** A deck about the checker that reviews posts was
   rejected as boring. Readers care about their problems, not your workshop.
3. **Faults the checker passed and only the phone images caught.** A closing line reading "that's
   the whole X", a cover telling people to swipe, and a page counter that disagreed with the slide
   number. The checker now catches these three. Others like them will exist.
4. **Colours and backgrounds.** Gold accents looked cheap. Decorative backgrounds and AI-made
   background photos were removed because they made the text harder to read and added nothing.
5. **Every cover a giant number.** A run of covers all built on one big digit read as lazy. Vary the
   cover style between decks (there are 7 in `specs/SPEC-FORMAT.md`).
6. **Text-only slides.** Decks with no pictures read as boring, and this came up more than once. Where
   an item can be shown (a screenshot, a table, a before-and-after), show it with the `shot` field.
7. **Vague, flat decks.** A whole batch was rejected for vague covers, a colourless tone, and slides
   that could not be read on the review screen.
8. **Too safe, and explaining sources.** A whole batch was rejected as boring and not punchy enough,
   with nothing anyone could disagree with. Slides explaining where claims came from (for example, that the advice
   came from client calls) were rejected: readers do not care where it came from. The checker now stops the common
   phrasings.
9. **Opinions instead of learning.** Decks built on a model, a theory or a framework were rejected.
   The pattern that was wanted: a carousel reports on something actually made or tried, and what each
   part of it gave.

## 3. Always look at the phone-size images

Every run writes `specs/<id>-output/phone/`. Open every image in it, starting with `all-slides.png`
and `cover-small.png`. Several of the faults above were invisible in the spec and obvious at phone
size. The checker reads words; only a person reading the pictures sees the slide.

## 4. Faults in the tool itself

- **Old images are not cleared.** If you re-render a deck with fewer slides, the extra
  `slide-NN.png`, `slide-NN.jpg` and `phone-NN.png` files from the earlier run stay in the output
  folder. The PDF and `all-slides.png` are always from the latest run. If in doubt, rename the old
  output folder before rendering.
- **The phone images are not tied to a version of the spec.** If you edit the spec and do not
  re-render, the images show the old copy. Re-render after every change.
- **The layout check covers text running off a slide and text on top of the logo.** It does not
  check text on top of the big faint number (by design) or a screenshot that is too small to read.
  Look.
- **A highlighted phrase can split across 2 lines.** In a test deck, 2 of 5 slides broke the
  highlighted phrase in the middle ("from 11 a / month to 26"). It still reads, but it looks untidy.
  No check catches it. Choose a shorter phrase, or reword so the phrase sits at the start of a
  line, and look at the phone images.
- **The small "swipe" label cannot be read on the tiny cover.** At the size of `cover-small.png`
  the "swipe" label is unreadable. The small counters on item slides, such as "FIX 1 OF 3", are
  also very small at phone size. Do not rely on either to tell a reader anything.
- **Item slides leave the lower half mostly empty.** On a slide with 1 item and no picture, the text
  sits in the top half and the lower half shows little more than the big pale number, which can
  look unfinished. A picture added with the `shot` field uses some of that space; look at the phone
  images to judge. The layout itself has not been changed.
- **Diagram labels.** Point names longer than about 14 characters on the left or right of a diagram
  can run off the slide; the renderer stops if they do.
- **A diagram must be the last slide**, so a deck with a diagram has no call-to-action slide.
- **Built and tested on Windows only.**
- **Needs Python 3.10 or later.** On Windows with Python 3.9, Playwright will not install without
  Microsoft's C++ build tools.
- **No proof carousels outperform text posts.** Earlier performance numbers showed no clear difference
  between carousels and other formats.
