"""
kitconfig.py  --  one place that reads your settings and works out where the folders are.

Every program in engine/ reads its personal settings through this file, so there is exactly one
copy of how settings are found:

  1. config.json in the repo root, if it exists (your own copy, which you edit).
  2. otherwise config.example.json in the repo root, with a warning printed, so the kit still
     runs straight after download.
  3. any setting missing from the file falls back to the built-in default below, so an old
     config.json does not crash a newer program.

All folder settings are relative to the repo root (the folder that holds engine/), unless you
write an absolute path. That keeps the kit working wherever you clone it, on Windows or Mac.

The self-tests in the other programs never read your config.json. They hand this module an
invented config with use(), so a test can never change your real files.

Run:  python engine/kitconfig.py              print the settings in force and where they came from
      python engine/kitconfig.py --selftest
"""

import copy
import json
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Built-in defaults. These match config.example.json; see the "_notes" there for what each does.
DEFAULTS = {
    "author_name": "Your Name",
    "author_initials": "YN",
    "author_headline": "Your one-line LinkedIn headline goes here",
    "signoff_line": "",
    "signoff_rule": "off",
    "banned_subjects": [],
    "premise_source_refused_words": ["inferred", "assumed", "guessed", "made up", "reasoned"],
    "pitch_words": ["sign up", "buy now", "dm me", "limited spots", "last chance",
                    "enrol", "enroll"],
    "hook_first_line_max_words": 14,
    "uncontracted_negative_hard_at": 2,
    "you_density_hard": 0.55,
    "you_density_flag": 0.40,
    "long_sentence_words": 30,
    "long_sentence_applies_over_words": 250,
    "banned_phrases": [],
    "em_dash_rule": "hard",
    "vague_filler_rule": "hard",
    "batch_length_short": 150,
    "batch_length_long": 280,
    "drafts_dir": "example/briefs/EXAMPLE-WAVE/drafts",
    "briefs_dir": "briefs",
    "preview_output": "preview/linkedin-preview.html",
    "transcript_dirs": ["transcripts"],
    "transcript_from_date": "2025-01-01",
    "my_speaker_labels": [],
    "mining_output_dir": "your-voice/opinions/turns",
    "mining_min_turn_chars": 45,
    "include_other_speaker_context": False,
}

# Fixed locations the kit's documents rely on. Not settings, on purpose.
VOICE_DIR = "your-voice"
BANNED_WORDS_FILE = "your-voice/banned_words.json"
FINDINGS_FILE = "data/findings.jsonl"
FINDINGS_APPLIED_FILE = "data/findings-applied.jsonl"
PROVENANCE_FILE = "data/publish-provenance.jsonl"
MY_POSTS_FILE = "your-voice/my-posts.csv"

_cache = None
_source = None
_override = None
_warned = False


def utf8_console():
    """Stop Windows consoles crashing on characters outside the local code page."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def use(cfg):
    """Replace the settings in memory (used by self-tests). None goes back to the files."""
    global _override
    if cfg is None:
        _override = None
        return
    merged = copy.deepcopy(DEFAULTS)
    merged.update(cfg)
    _override = merged


def load():
    """Return the settings dict. Reads the file once per run."""
    global _cache, _source, _warned
    if _override is not None:
        return _override
    if _cache is not None:
        return _cache
    real = REPO_ROOT / "config.json"
    example = REPO_ROOT / "config.example.json"
    data = {}
    if real.exists():
        _source = str(real)
        data = json.loads(real.read_text(encoding="utf-8"))
    elif example.exists():
        _source = str(example) + " (no config.json yet)"
        if not _warned:
            print("warning: no config.json found, using config.example.json. Copy it to "
                  "config.json and put your own details in.", file=sys.stderr)
            _warned = True
        data = json.loads(example.read_text(encoding="utf-8"))
    else:
        _source = "built-in defaults (no config file found)"
    merged = copy.deepcopy(DEFAULTS)
    merged.update({k: v for k, v in data.items() if not k.startswith("_")})
    _cache = merged
    return _cache


def get(key):
    return load().get(key, DEFAULTS.get(key))


def source():
    load()
    return _source or "self-test settings"


def resolve(p):
    """A path from settings or the command line: absolute stays, relative joins the repo root."""
    p = Path(os.path.expanduser(str(p)))
    return p if p.is_absolute() else (REPO_ROOT / p)


def cli_path(p):
    """A path typed on the command line: as typed from where you are, else from the repo root."""
    typed = Path(os.path.expanduser(str(p)))
    if typed.is_absolute() or typed.exists():
        return typed
    return REPO_ROOT / typed


def path(key):
    return resolve(get(key))


def rel(p):
    """Show a path relative to the repo root when it is inside it."""
    try:
        return Path(p).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(p)


def atomic_write_text(target, text):
    """Write to a temp file in the same folder, then swap it in. Never truncates in place."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, str(target))
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def append_jsonl(target, record):
    """Add one line to a .jsonl file. Append mode only, never a rewrite."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def selftest():
    out = []
    use({"author_name": "Test Person"})
    out.append("pass: use() overrides a setting" if get("author_name") == "Test Person"
               else "FAIL: override ignored")
    out.append("pass: missing keys fall back to defaults" if get("signoff_rule") == "off"
               else "FAIL: default missing")
    use(None)
    out.append("pass: relative paths join the repo root"
               if resolve("data/x.jsonl") == REPO_ROOT / "data" / "x.jsonl" else "FAIL: resolve")
    with tempfile.TemporaryDirectory() as td:
        t = Path(td) / "a.txt"
        atomic_write_text(t, "one")
        atomic_write_text(t, "two")
        leftovers = [x for x in os.listdir(td) if x.endswith(".tmp")]
        out.append("pass: atomic write replaces and leaves no temp file"
                   if t.read_text(encoding="utf-8") == "two" and not leftovers
                   else "FAIL: atomic write")
    fails = [x for x in out if x.startswith("FAIL")]
    out.append("SELFTEST %s (%d checks)" % ("FAILED" if fails else "PASSED", len(out)))
    return "\n".join(out), not fails


def main():
    utf8_console()
    if "--selftest" in sys.argv:
        text, ok = selftest()
        print(text)
        return 0 if ok else 1
    cfg = load()
    print("settings from: %s" % source())
    for k in sorted(cfg):
        print("  %-34s %s" % (k, json.dumps(cfg[k], ensure_ascii=False)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
