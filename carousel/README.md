# Carousel maker

Turns one JSON file describing your slides into a LinkedIn carousel: a PDF of 1080 x 1350 slides
you upload as a document post, plus phone-size images so you can see what readers will see.

Claude writes the JSON from your instructions. A checker reads it for known faults. A renderer
draws the slides in your colours, fonts and logo. You look at the phone-size images and post by hand.
Nothing in this folder posts to LinkedIn.

---

## Setup (once)

You need **Python 3.10 or newer** for the carousel maker. The text engine in `engine/` runs on 3.9,
but carousels do not: on Windows with Python 3.9, `pip install playwright` fails, because a part
Playwright depends on (greenlet) will not install there without Microsoft's C++ build tools. Check
with `python --version`. Then, from this `carousel/` folder:

```
pip install playwright Pillow
python -m playwright install chromium
python check/slide_checks.py --selftest
python build_carousel.py specs/example-list.json
```

The first two install the programs the renderer uses (Chromium is a browser it runs out of sight to
draw the slides). Use `python -m playwright install chromium` exactly as written: the shorter
`playwright install chromium` only works if Python's Scripts folder is on your PATH. The third runs the checker against invented test decks and should end with
`slide_checks selftest PASSED`. The fourth renders an invented example deck; open
`specs/example-list-output/example-list-light.pdf` to see it.

On a Mac, use `python3` and `pip3` if `python` is not found.

---

## The flow

1. **Fill in your brand.** Edit `brand/brand.css`: background, text, grey and accent colours for light
   and dark slides, the screenshot frame colours, font names, logo size and corner. Then replace the
   2 placeholder logos, which read "YOUR LOGO" (steps below).
2. **Fill in your instructions.** Edit Part 1 of `carousel-instructions.md`: your reader, what they pay
   for, lose and cannot picture, subjects you avoid, your true claims, the last-slide wording and where
   readers go, your sign-off (blank if you have none). Put words you never use in
   `check/house_rules.json`.
3. **Claude writes a spec.** Open Claude in this folder and say: *"Read carousel-instructions.md and
   make a carousel about [the subject]."* It writes `specs/<id>.json`. The format is in
   `specs/SPEC-FORMAT.md`.
4. **Check.** `python check/slide_checks.py specs/<id>.json`. Hard fails must be fixed. Flags are for
   you to judge.
5. **Render.** `python build_carousel.py specs/<id>.json`. It runs the checker again first and stops on
   a hard fail (`--force` renders anyway). It also stops if text runs off a slide or sits on the logo.
6. **Look at the phone-size images.** Open every file in `specs/<id>-output/phone/`, starting with
   `all-slides.png`. That is roughly the size a phone shows a slide. If you cannot read it easily
   there, readers will not read it either.
7. **Post by hand.** On LinkedIn, start a post, add a document, upload
   `specs/<id>-output/<id>-<theme>.pdf`, give it a title, paste your caption.

---

## Replacing the 2 placeholder logos

The renderer needs 2 logo files in `brand/`, with exactly these names:

| File | Used on | So your logo should be |
|---|---|---|
| `brand/logo-light.png` | light slides (pale background) | dark: black or your dark brand colour |
| `brand/logo-dark.png` | dark slides (dark background) | light: white or a pale version |

1. **Make each file a PNG with a transparent background.** A logo on a white box shows as a white
   rectangle on every slide. If you only have a JPG or a logo on a white background, ask whoever
   made your logo for a transparent PNG, export one from your design tool, or run it through a
   background-removal tool and save the result as PNG.
2. **Make it wide enough to stay sharp.** The placeholders are 900 x 300 pixels. Aim for at least
   900 pixels wide for a wide logo, or 600 x 600 for a square one. Trim empty space round the edges,
   because the size setting counts it.
3. **Save the 2 files over the placeholders**, keeping the names `logo-light.png` and
   `logo-dark.png`. If you only have 1 version, you can use the same picture for both, but check it
   reads on the dark slides.
4. **Set the size in `brand/brand.css`.** `--logo-width` is the width on normal slides and
   `--logo-width-cover` on the cover. The height follows. A wide logo (about 3 times wider than
   tall) suits 240px and 280px. A square logo wants about 110px and 130px.
5. **Set the corner in `brand/brand.css`** with `--logo-left`, `--logo-right`, `--logo-bottom` and
   `--logo-top`: give the 2 sides you want a distance and set the other 2 to `auto`. Bottom-left is
   the default. Bottom-right collides with the "swipe" arrow on the cover.
6. **Render the example deck again** (`python build_carousel.py specs/example-list.json`) and open
   the phone images. The renderer stops with a layout fault if text sits on the logo: make the logo
   smaller or move it.

If you want no logo at all, add `--no-logo` to the render command.

---

## What is in this folder

| Path | What it is |
|---|---|
| `build_carousel.py` | The renderer. Runs the checker, then draws slides, PDF and phone images. |
| `carousel.css` | Slide layout. Reads your brand file. Edit only to change the layout itself. |
| `brand/brand.css` | **Fill in.** Your colours, fonts, logo size and corner. |
| `brand/fonts/` | Inter and JetBrains Mono, both free to embed (licence: `brand/fonts/OFL.txt`). |
| `brand/logo-light.png`, `brand/logo-dark.png` | **Replace.** Placeholder logos. |
| `check/slide_checks.py` | The checker. `--selftest` proves it catches what it claims to. |
| `check/device_rules.py` | The rules for each cover style and body shape, shared by checker and renderer. |
| `check/assert_not_evidence.py` | Catches lines that tell the reader where a claim came from. |
| `check/house_rules.json` | **Fill in.** Your banned words and phrases, and your sign-off rule. Empty by default. |
| `specs/SPEC-FORMAT.md` | Every field in a spec, with limits and an example. |
| `specs/example-*.json` | Three invented example decks (a made-up bookkeeper called Sam). |
| `specs/images/` | Pictures used on slides. `example-shot.png` is a fake screenshot. |
| `carousel-instructions.md` | **Fill in Part 1.** What Claude reads before writing a carousel. |
| `KNOWN-PROBLEMS-CAROUSEL.md` | What this tool does not do well. Read it before your first deck. |

---

## What is not proven

- **That these carousels get results.** There is no record showing carousels made this way do better
  than a plain text post. Treat every deck as a test.
- **That passing the checker means a good deck.** In the most recent round of work with this tool,
  every deck passed every automatic check and the owner still chose not to post any of them. The
  checker catches written-rule faults. It cannot judge whether the subject is worth a reader's time.
  See `KNOWN-PROBLEMS-CAROUSEL.md`.
- **Linux.** Built on Windows, and on 2026-10-08 run on 2 Macs (Apple chip and Intel, macOS 15), where
  the slides came out the same. It has not been run on Linux.
- **Your own fonts and logos.** Tested only with the bundled fonts and the placeholder logos. A very
  tall or very wide logo may need the size and corner settings changed; the renderer stops if text
  sits on it.
