# plagcheck

A **zero-dependency**, Turnitin-style text similarity checker written in pure
Python. It compares a submitted document against a local corpus of reference
documents (and optionally web pages) and produces a similarity percentage,
per-source breakdown, and a highlighted HTML report.

Everything uses only the Python standard library. There is nothing to
`pip install`:

```sh
python3 -m plagcheck --help
```

## Why

Turnitin compares submissions against a proprietary, closed database behind a
paid service. `plagcheck` is a small, auditable, offline alternative: you
control the corpus, you see the algorithm, and nothing leaves your machine.

It does **not** reproduce Turnitin's internet index or its institutional
database. It is a similarity aid, not a verdict: a percentage is a signal for
human review.

## Features

- Word n-gram fingerprinting with the **winnowing** algorithm (MOSS-style),
  robust to small edits and reordering.
- Overall similarity score plus per-source percentages and hit counts.
- Character-level **highlighting** of matched passages in an HTML report.
- Reads `.txt`, `.md`, `.csv`, `.json`, `.html`, `.docx` and `.pdf`
  (best-effort, with ToUnicode decoding), or raw pasted text.
- Optional web sources by URL (`urllib`), opt-in per run.
- Internal **self-plagiarism** detection (repeated phrases within one document).
- Exclude quotes and/or the reference list from the score.
- Command-line interface, a native **desktop app** (Tkinter), and a local
  **browser UI** (`http.server`).
- Corpus index can be built once and reused (JSON).

## Install / run

Requires Python 3.11+ (tested on 3.13). No packages.

```sh
# from this directory (so that `import plagcheck` resolves)
python3 -m plagcheck check submission.docx --corpus corpus --html report.html

# or put the package on your path and use the same entry point
PYTHONPATH=. python3 -m plagcheck --version
```

## Command line

```sh
# Check a document against a corpus and write reports
python3 -m plagcheck check my-essay.docx \
    --corpus corpus \
    --exclude-quotes --exclude-references \
    --html report.html --json report.json --text

# Add live web sources (needs internet; repeatable)
python3 -m plagcheck check essay.txt --corpus corpus --url https://example.com/a

# Pre-build a reusable index
python3 -m plagcheck index corpus --out corpus.index.json
python3 -m plagcheck check essay.txt --index corpus.index.json

# Repeated phrases within a single document
python3 -m plagcheck internal my-essay.docx --k 8

# Launch the browser UI
python3 -m plagcheck serve --port 8000 --corpus corpus

# Launch the desktop application
python3 -m plagcheck gui --corpus corpus
```

Useful options:

| Option | Meaning |
|---|---|
| `--k N` | shingle size in words (default 5) |
| `--w N` | winnowing window (default 4) |
| `--min-run N` | minimum matched run length in words (default `k+w-1`) |
| `--exclude-quotes` | ignore quoted text |
| `--exclude-references` | ignore the reference list |
| `--url URL` | add a web source (repeatable) |

## Desktop app

```sh
python3 -m plagcheck gui --corpus corpus
```

The Tkinter window (standard library, no extra packages) lets you:

- pick a corpus directory and rebuild the index with one click;
- paste text or load a `.txt/.md/.docx/.pdf/...` file;
- toggle quote/reference exclusion and set a minimum match length;
- see the score, band, per-source table and matched-passage list;
- view the document with matched runs **colour-highlighted** per source;
- save the HTML or JSON report.

If Tk is missing from your Python build (e.g. some minimal Linux packages),
`plagcheck gui` prints a hint and you can use `plagcheck serve` instead.

## How it works

1. **Normalize** – text is tokenized into words with their character offsets;
   optional filters blank quotes or the reference list *in place* so offsets
   stay valid for highlighting.
2. **Fingerprint** – each token becomes a 64-bit BLAKE2b hash; a rolling
   polynomial hash turns them into overlapping *k*-gram hashes.
3. **Winnow** – for every window of *w* consecutive k-grams the minimum hash is
   kept. This guarantees that any shared passage of at least `k + w - 1` words
   contributes at least one shared fingerprint, while shrinking the index.
4. **Compare** – every k-gram of the submission is looked up in the corpus
   inverted index; matched k-grams are merged into maximal runs. Runs shorter
   than the threshold are discarded to avoid flagging common short phrases.
5. **Score** – similarity is the share of the submission's words that fall
   inside retained matched runs. Per-source percentages attribute each run to
   the sources that share it.
6. **Report** – HTML (highlighted), JSON and plain text.

### Tuning

- Raise `--k` and/or `--w` for fewer, longer matches (fewer false positives).
- Lower `--min-run` to catch shorter borrowings (more false positives).
- Turn on `--exclude-quotes --exclude-references` for academic submissions;
  Turnitin excludes these from its score too.

## Files

```text
plagcheck/
  normalize.py     tokenization, in-place filters
  fingerprint.py   hashing, rolling k-grams, winnowing
  index.py         corpus index + JSON persistence
  compare.py       matching, scoring, internal-duplication
  extract.py       txt/md/html/docx/pdf readers, URL fetch
  report.py        HTML/JSON/text reports
  gui.py           Tkinter desktop application
  cli.py           command-line interface
  webapp.py        stdlib browser UI
  tests/           unittest suite
corpus/            reference documents (one file per source)
examples/          sample submission
```

## Adding sources to the corpus

Drop files into `corpus/` (any supported format). Each file becomes one source;
its title is the first non-empty line. Rebuild the index or let `check` build it
on the fly.

## Limitations

- No built-in internet-wide index. Web comparison only covers URLs you supply.
- PDF extraction is best-effort. It decodes most text PDFs via ToUnicode CMaps
  but returns **no text** for image-only scans or unsupported encodings rather
  than guessing. DOCX and plain text are the most reliable inputs.
- The score is a lexical-similarity measure. It does not understand paraphrase,
  citation context or common knowledge; always review matches manually.
- Very large corpora are held in memory.

## Tests

```sh
python3 -m unittest discover -s plagcheck/tests -t .
```

## Licence

Original code in this repository: use it freely. Cited third-party documents you
add to a corpus keep their own terms.
