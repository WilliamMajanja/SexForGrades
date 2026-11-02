from __future__ import annotations

import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from plagcheck import __version__  # noqa: F401
from plagcheck.compare import analyze, analyze_internal
from plagcheck.extract import extract_bytes, extract_text, read_pdf
from plagcheck.fingerprint import shingle_hashes, token_hashes, winnow
from plagcheck.index import CorpusIndex, build_index
from plagcheck.normalize import mask_quotes, mask_references, tokenize
from plagcheck.report import render_json, render_text

DOC_A = (
    "Elephants raid banana farms during the dry season when water and forage "
    "are scarce, and community members report repeated crop damage near the "
    "forest edge every year in coastal Kenya."
)
DOC_B = (
    "Coral reefs bleach when ocean temperatures rise and symbiotic algae leave "
    "their hosts, which changes the colour and health of the reef ecosystem."
)


class NormalizeTests(unittest.TestCase):
    def test_token_spans(self):
        text = "Don't stop, Ngũgĩ!"
        tokens = tokenize(text)
        self.assertEqual([t.text for t in tokens], ["Don't", "stop", "Ngũgĩ"])
        for token in tokens:
            self.assertEqual(text[token.start : token.end], token.text)

    def test_mask_quotes_preserves_length(self):
        text = 'He said "this exact phrase is copied" and left.'
        masked = mask_quotes(text)
        self.assertEqual(len(masked), len(text))
        self.assertNotIn("copied", masked)
        self.assertIn("left", masked)

    def test_mask_references_blanks_tail(self):
        text = "Body sentence here.\n\nReferences\n[1] Someone, 2020."
        masked = mask_references(text)
        self.assertEqual(len(masked), len(text))
        self.assertIn("Body", masked)
        self.assertNotIn("Someone", masked)


class FingerprintTests(unittest.TestCase):
    def test_short_input_has_no_shingles(self):
        self.assertEqual(shingle_hashes([1, 2], 5), [])

    def test_winnow_selects_within_windows(self):
        shingles = [5, 3, 8, 1, 9, 2, 7]
        selected = winnow(shingles, 3)
        self.assertTrue(selected)
        for index, value in selected:
            self.assertEqual(shingles[index], value)
        positions = [index for index, _ in selected]
        self.assertEqual(positions, sorted(positions))

    def test_identical_documents_share_fingerprints(self):
        a = winnow(shingle_hashes(token_hashes(tokenize(DOC_A)), 5), 4)
        b = winnow(shingle_hashes(token_hashes(tokenize(DOC_A)), 5), 4)
        self.assertEqual([h for _, h in a], [h for _, h in b])


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.index = build_index([("a", "Doc A", DOC_A)])

    def test_identical_text_scores_high(self):
        result = analyze(DOC_A, self.index)
        self.assertGreater(result.percent, 85.0)
        self.assertEqual(len(result.sources), 1)
        self.assertEqual(result.sources[0].source_id, "a")

    def test_unrelated_text_scores_zero(self):
        result = analyze(DOC_B, self.index)
        self.assertEqual(result.percent, 0.0)
        self.assertEqual(result.sources, [])

    def test_partial_copy_is_detected(self):
        submission = DOC_B + " " + DOC_A
        result = analyze(submission, self.index)
        self.assertGreater(result.matched_words, 0)
        for run in result.runs:
            self.assertGreaterEqual(run.words, result.guarantee)
            self.assertIn("a", run.sources)

    def test_below_threshold_not_flagged(self):
        submission = "Elephants raid banana farms tonight"
        result = analyze(submission, self.index)
        self.assertEqual(result.percent, 0.0)

    def test_exclude_quotes_reduces_match(self):
        submission = 'X "Elephants raid banana farms during the dry season" Y'
        with_quotes = analyze(submission, self.index, exclude_quotes=False, min_run=4)
        without = analyze(submission, self.index, exclude_quotes=True, min_run=4)
        self.assertGreaterEqual(with_quotes.percent, without.percent)

    def test_internal_duplicates(self):
        text = "alpha beta gamma delta epsilon zeta eta theta " * 2
        report = analyze_internal(text, k=6)
        self.assertGreater(report["percent"], 0.0)
        self.assertTrue(report["duplicates"])


class IndexTests(unittest.TestCase):
    def test_round_trip(self):
        index = build_index([("a", "Doc A", DOC_A), ("b", "Doc B", DOC_B)])
        restored = CorpusIndex.from_dict(json.loads(json.dumps(index.to_dict())))
        self.assertEqual(restored.source_count(), 2)
        self.assertEqual(restored.k, index.k)
        self.assertEqual(len(restored.postings), len(index.postings))
        self.assertEqual(restored.title_for("b"), "Doc B")


class ExtractTests(unittest.TestCase):
    def test_plain_text(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.txt"
            path.write_text("Hello extraction world", encoding="utf-8")
            self.assertIn("extraction", extract_text(path))

    def test_docx_bytes(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr(
                "word/document.xml",
                "<w:document><w:body><w:p><w:r><w:t>Hello docx world</w:t></w:r></w:p>"
                "</w:body></w:document>",
            )
        text = extract_bytes("x.docx", buffer.getvalue())
        self.assertIn("Hello docx world", text)

    def test_html_extraction(self):
        html = "<html><body><h1>Title</h1><p>Body <b>text</b> here</p></body></html>"
        self.assertIn("Body", extract_bytes("x.html", html.encode("utf-8")))

    def test_pdf_bytes_no_garbage(self):
        self.assertEqual(extract_bytes("x.pdf", b"%PDF-1.4\n%%EOF"), "")

    def test_pdf_returns_text_not_garbage(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "empty.pdf"
            path.write_bytes(b"%PDF-1.4\n%%EOF")
            self.assertEqual(read_pdf(path), "")


class ReportTests(unittest.TestCase):
    def test_json_and_text(self):
        index = build_index([("a", "Doc A", DOC_A)])
        result = analyze(DOC_A, index)
        payload = json.loads(render_json(result))
        self.assertIn("result", payload)
        self.assertIn("Similarity", render_text(result))


class GuiSmokeTest(unittest.TestCase):
    """Construct the Tkinter app headlessly; skipped when no display exists."""

    def test_app_constructs(self):
        try:
            import tkinter as tk
        except Exception as error:  # noqa: BLE001
            self.skipTest(f"tkinter unavailable: {error}")
        try:
            root = tk.Tk()
        except Exception as error:  # noqa: BLE001
            self.skipTest(f"no display: {error}")
        root.withdraw()
        from plagcheck import gui

        original = gui.PlagCheckApp.rebuild_index
        gui.PlagCheckApp.rebuild_index = lambda self: None  # avoid worker thread
        try:
            app = gui.PlagCheckApp(root, Path("."), 5, 4)
            self.assertIsNotNone(app.sources)
            self.assertIsNotNone(app.highlight)
            self.assertIsNotNone(app.passages)
        finally:
            gui.PlagCheckApp.rebuild_index = original
            root.destroy()


if __name__ == "__main__":
    unittest.main()
