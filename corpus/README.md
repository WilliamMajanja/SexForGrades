# Reference corpus

Each file in this directory is treated as one reference source.

- Supported formats: `.txt`, `.md`, `.csv`, `.json`, `.html`, `.docx`, `.pdf`.
- The source **title** is the first non-empty line of the file.
- For academic use, add the sources students are most likely to draw on
  (prior student work, textbook excerpts, lecture notes, past papers, your own
  published writing, and so on).

Rebuild the reusable index after adding or editing files:

```sh
python3 -m plagcheck index corpus --out corpus.index.json
```

Or just run `check` and the corpus is indexed on the fly.

Only include material you are allowed to store and compare.
