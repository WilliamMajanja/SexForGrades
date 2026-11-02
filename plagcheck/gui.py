"""Tkinter desktop interface for plagcheck.

Uses only the Python standard library (tkinter ships with CPython). Importing
this module fails with :class:`ImportError` on builds without Tk, so callers
should import it lazily and report a friendly message.
"""

from __future__ import annotations

import threading
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .cli import build_corpus_index
from .compare import Result, analyze, analyze_internal
from .extract import SUPPORTED_SUFFIXES, extract_text
from .fingerprint import DEFAULT_K, DEFAULT_W
from .index import CorpusIndex
from .report import BAND_COLORS, PALETTE, render_html, render_json

OPEN_FILETYPES = [
    ("Supported documents", "*.txt *.md *.markdown *.csv *.json *.html *.htm *.docx *.pdf"),
    ("Text", "*.txt *.md *.csv"),
    ("Word document", "*.docx"),
    ("PDF", "*.pdf"),
    ("All files", "*.*"),
]


class PlagCheckApp(ttk.Frame):
    """Main application window."""

    def __init__(self, master: tk.Tk, corpus: Path, k: int, w: int) -> None:
        super().__init__(master, padding=10)
        self.master = master
        self.corpus_dir = Path(corpus)
        self.k = k
        self.w = w

        self.index: CorpusIndex | None = None
        self.result: Result | None = None
        self.submission_name = "pasted text"
        self._busy = False

        self.grid(row=0, column=0, sticky="nsew")
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        self._build_toolbar()
        self._build_body()
        self._build_status()
        self._bind_keys()

        self.after(150, self.rebuild_index)

    # ------------------------------------------------------------------ ui
    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self)
        bar.grid(row=0, column=0, sticky="ew")
        bar.columnconfigure(4, weight=1)

        ttk.Button(bar, text="Open corpus...", command=self.choose_corpus).grid(
            row=0, column=0, padx=(0, 4)
        )
        ttk.Button(bar, text="Rebuild index", command=self.rebuild_index).grid(
            row=0, column=1, padx=4
        )
        self.corpus_label = ttk.Label(bar, text="", foreground="#475569")
        self.corpus_label.grid(row=0, column=2, padx=8)

        ttk.Separator(bar, orient="vertical").grid(row=0, column=3, sticky="ns", padx=8)

        ttk.Button(bar, text="Load file...", command=self.load_file).grid(
            row=0, column=5, padx=4
        )
        ttk.Button(bar, text="Clear", command=self.clear_text).grid(
            row=0, column=6, padx=4
        )

        ttk.Separator(bar, orient="vertical").grid(row=0, column=7, sticky="ns", padx=8)

        self.exclude_quotes = tk.BooleanVar(value=True)
        self.exclude_references = tk.BooleanVar(value=True)
        ttk.Checkbutton(bar, text="Quotes", variable=self.exclude_quotes).grid(
            row=0, column=8, padx=2
        )
        ttk.Checkbutton(bar, text="References", variable=self.exclude_references).grid(
            row=0, column=9, padx=2
        )
        ttk.Label(bar, text="Min run").grid(row=0, column=10, padx=(10, 2))
        self.min_run = tk.StringVar(value="")
        ttk.Spinbox(bar, from_=1, to=100, width=4, textvariable=self.min_run).grid(
            row=0, column=11, padx=2
        )
        self.analyze_button = ttk.Button(bar, text="Analyze", command=self.run_check)
        self.analyze_button.grid(row=0, column=12, padx=(10, 0))

    def _build_body(self) -> None:
        pane = ttk.Panedwindow(self, orient="horizontal")
        pane.grid(row=2, column=0, sticky="nsew", pady=(10, 6))

        left = ttk.Frame(pane)
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)
        ttk.Label(left, text="Submission", font=("", 10, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        text_frame = ttk.Frame(left)
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        self.input = tk.Text(text_frame, wrap="word", undo=True, width=48)
        self.input.grid(row=0, column=0, sticky="nsew")
        in_scroll = ttk.Scrollbar(text_frame, command=self.input.yview)
        in_scroll.grid(row=0, column=1, sticky="ns")
        self.input.configure(yscrollcommand=in_scroll.set)
        pane.add(left, weight=1)

        right = ttk.Frame(pane)
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        self.notebook = ttk.Notebook(right)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        self._build_summary_tab()
        self._build_highlight_tab()
        pane.add(right, weight=2)

    def _build_summary_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=8)
        tab.rowconfigure(3, weight=1)
        tab.columnconfigure(0, weight=1)
        self.notebook.add(tab, text="Summary")

        head = ttk.Frame(tab)
        head.grid(row=0, column=0, sticky="ew")
        head.columnconfigure(1, weight=1)
        self.score_label = tk.Label(
            head, text="--", font=("", 34, "bold"), fg="#334155"
        )
        self.score_label.grid(row=0, column=0, rowspan=2, padx=(0, 14))
        self.band_label = tk.Label(head, text="not analysed", font=("", 12, "bold"))
        self.band_label.grid(row=0, column=1, sticky="w")
        self.stats_label = ttk.Label(head, text="", foreground="#475569")
        self.stats_label.grid(row=1, column=1, sticky="w")

        ttk.Separator(tab, orient="horizontal").grid(
            row=1, column=0, sticky="ew", pady=8
        )

        ttk.Label(tab, text="Sources", font=("", 10, "bold")).grid(
            row=2, column=0, sticky="w"
        )
        cols = ("title", "words", "percent", "hits")
        self.sources = ttk.Treeview(tab, columns=cols, show="headings", height=6)
        self.sources.heading("title", text="Source")
        self.sources.heading("words", text="Words")
        self.sources.heading("percent", text="%")
        self.sources.heading("hits", text="Hits")
        self.sources.column("title", width=280, anchor="w")
        self.sources.column("words", width=70, anchor="e")
        self.sources.column("percent", width=70, anchor="e")
        self.sources.column("hits", width=60, anchor="e")
        self.sources.grid(row=3, column=0, sticky="nsew", pady=(4, 8))
        self.sources.bind("<Double-1>", self._focus_source)

        ttk.Label(tab, text="Matched passages", font=("", 10, "bold")).grid(
            row=4, column=0, sticky="w"
        )
        list_frame = ttk.Frame(tab)
        list_frame.grid(row=5, column=0, sticky="nsew")
        tab.rowconfigure(5, weight=1)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.passages = tk.Listbox(list_frame, height=6)
        self.passages.grid(row=0, column=0, sticky="nsew")
        p_scroll = ttk.Scrollbar(list_frame, command=self.passages.yview)
        p_scroll.grid(row=0, column=1, sticky="ns")
        self.passages.configure(yscrollcommand=p_scroll.set)
        self.passages.bind("<Double-1>", self._focus_passage)

    def _build_highlight_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=8)
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        self.notebook.add(tab, text="Highlighted")

        frame = ttk.Frame(tab)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.highlight = tk.Text(frame, wrap="word", state="disabled", padx=6, pady=6)
        self.highlight.grid(row=0, column=0, sticky="nsew")
        h_scroll = ttk.Scrollbar(frame, command=self.highlight.yview)
        h_scroll.grid(row=0, column=1, sticky="ns")
        self.highlight.configure(yscrollcommand=h_scroll.set)

    def _build_status(self) -> None:
        self.status = ttk.Label(self, text="Ready", anchor="w", foreground="#475569")
        self.status.grid(row=3, column=0, sticky="ew")

    def _bind_keys(self) -> None:
        self.master.bind("<Control-o>", lambda _event: self.load_file())
        self.master.bind("<Control-Return>", lambda _event: self.run_check())

    # -------------------------------------------------------------- actions
    def _set_status(self, message: str) -> None:
        self.status.configure(text=message)

    def _set_busy(self, busy: bool, message: str = "Working...") -> None:
        self._busy = busy
        self.analyze_button.configure(state="disabled" if busy else "normal")
        if busy:
            self._set_status(message)

    def _run_async(self, work, on_done) -> None:
        def runner() -> None:
            try:
                value = work()
            except Exception as error:  # noqa: BLE001 - surface in the UI
                self.after(0, lambda: self._async_error(error))
                return
            self.after(0, lambda: on_done(value))

        threading.Thread(target=runner, daemon=True).start()

    def _async_error(self, error: Exception) -> None:
        self._busy = False
        self.analyze_button.configure(state="normal")
        self._set_status(f"Error: {error}")
        messagebox.showerror("plagcheck", str(error))

    def choose_corpus(self) -> None:
        chosen = filedialog.askdirectory(
            title="Choose corpus directory", initialdir=str(self.corpus_dir)
        )
        if chosen:
            self.corpus_dir = Path(chosen)
            self.rebuild_index()

    def rebuild_index(self) -> None:
        if self._busy:
            return

        def work():
            return build_corpus_index(
                self.corpus_dir,
                k=self.k,
                w=self.w,
                exclude_quotes=False,
                exclude_references=False,
            )

        def done(index: CorpusIndex) -> None:
            self._busy = False
            self.index = index
            self.analyze_button.configure(state="normal")
            self.corpus_label.configure(
                text=f"{index.source_count()} sources  ({self.corpus_dir.name})"
            )
            self._set_status(
                f"Indexed {index.source_count()} source(s) from {self.corpus_dir}"
            )

        self._set_busy(True, f"Indexing {self.corpus_dir} ...")
        self._run_async(work, done)

    def load_file(self) -> None:
        path = filedialog.askopenfilename(title="Open document", filetypes=OPEN_FILETYPES)
        if not path:
            return
        try:
            text = extract_text(Path(path))
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("plagcheck", f"Could not read file:\n{error}")
            return
        if not text.strip():
            messagebox.showwarning(
                "plagcheck",
                "No extractable text found. Scanned/image PDFs are not supported.",
            )
            return
        self.input.delete("1.0", "end")
        self.input.insert("1.0", text)
        self.submission_name = path
        self._set_status(f"Loaded {Path(path).name} ({len(text.split())} words)")

    def clear_text(self) -> None:
        self.input.delete("1.0", "end")
        self.submission_name = "pasted text"
        self._set_status("Cleared")

    def run_check(self) -> None:
        if self._busy:
            return
        text = self.input.get("1.0", "end-1c")
        if not text.strip():
            messagebox.showinfo("plagcheck", "Enter or load a document first.")
            return
        index = self.index
        if index is None:
            messagebox.showinfo("plagcheck", "The corpus is still being indexed.")
            return
        if index.source_count() == 0:
            messagebox.showwarning(
                "plagcheck",
                "The corpus has no sources. Add files and rebuild the index.",
            )
            return

        min_run_text = self.min_run.get().strip()
        min_run = int(min_run_text) if min_run_text.isdigit() else None
        exclude_quotes = self.exclude_quotes.get()
        exclude_references = self.exclude_references.get()

        def work():
            return analyze(
                text,
                index,
                min_run=min_run,
                exclude_quotes=exclude_quotes,
                exclude_references=exclude_references,
            )

        self._set_busy(True, "Analyzing...")
        self._run_async(work, self._apply_result)

    # -------------------------------------------------------------- results
    def _source_colors(self) -> dict[str, str]:
        colors: dict[str, str] = {}
        if self.result:
            for position, source in enumerate(self.result.sources):
                colors[source.source_id] = PALETTE[position % len(PALETTE)]
        return colors

    def _apply_result(self, result: Result) -> None:
        self._busy = False
        self.result = result
        self.analyze_button.configure(state="normal")

        band = result.score_band
        color = BAND_COLORS.get(band, "#334155")
        self.score_label.configure(text=f"{result.percent:.0f}%", fg=color)
        self.band_label.configure(text=band.upper(), fg=color)
        self.stats_label.configure(
            text=(
                f"{result.total_words} words analysed  |  "
                f"{result.matched_words} matching  |  "
                f"{result.excluded_words} excluded  |  "
                f"match >= {result.guarantee} words"
            )
        )

        self.sources.delete(*self.sources.get_children())
        colors = self._source_colors()
        for number, source in enumerate(result.sources, 1):
            self.sources.insert(
                "",
                "end",
                iid=source.source_id,
                values=(
                    f"{number}. {source.title}",
                    source.matched_words,
                    f"{source.percent:.1f}%",
                    len(source.matches),
                ),
                tags=(source.source_id,),
            )
            self.sources.tag_configure(source.source_id, background=colors[source.source_id])

        self.passages.delete(0, "end")
        for run in result.runs:
            snippet = " ".join(run.text.split())
            if len(snippet) > 90:
                snippet = snippet[:87] + "..."
            self.passages.insert("end", f"[{run.words}w] {snippet}")

        self._render_highlight(result)
        self._set_status(
            f"{result.percent:.1f}% similarity ({band}) across "
            f"{len(result.sources)} source(s)"
        )

    def _render_highlight(self, result: Result) -> None:
        widget = self.highlight
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", result.analyzed_text)

        for source_id, color in self._source_colors().items():
            widget.tag_configure(f"src::{source_id}", background=color)

        for index, run in enumerate(result.runs):
            start = widget.index(f"1.0 + {run.char_start} chars")
            end = widget.index(f"1.0 + {run.char_end} chars")
            primary = run.sources[0] if run.sources else None
            if primary:
                widget.tag_add(f"src::{primary}", start, end)
            widget.tag_add(f"run::{index}", start, end)

        widget.configure(state="disabled")

    def _focus_source(self, _event) -> None:
        selection = self.sources.selection()
        if not selection or not self.result:
            return
        source_id = selection[0]
        for index, run in enumerate(self.result.runs):
            if source_id in run.sources:
                self.notebook.select(1)
                self.highlight.see(f"1.0 + {run.char_start} chars")
                self._set_status(
                    f"First match of source at {run.words} words: "
                    f"{' '.join(run.text.split())[:80]}"
                )
                return
        self._set_status("No highlighted passage for that source.")

    def _focus_passage(self, _event) -> None:
        if not self.result:
            return
        selection = self.passages.curselection()
        if not selection:
            return
        index = selection[0]
        if index >= len(self.result.runs):
            return
        run = self.result.runs[index]
        self.notebook.select(1)
        self.highlight.see(f"1.0 + {run.char_start} chars")

    # --------------------------------------------------------------- export
    def save_report(self, kind: str) -> None:
        if not self.result:
            messagebox.showinfo("plagcheck", "Analyze a document first.")
            return
        if kind == "html":
            path = filedialog.asksaveasfilename(
                title="Save HTML report", defaultextension=".html",
                filetypes=[("HTML", "*.html")],
            )
            if not path:
                return
            Path(path).write_text(
                render_html(self.result, title=f"Similarity report: {self.submission_name}"),
                encoding="utf-8",
            )
        else:
            path = filedialog.asksaveasfilename(
                title="Save JSON report", defaultextension=".json",
                filetypes=[("JSON", "*.json")],
            )
            if not path:
                return
            meta = {
                "submission": self.submission_name,
                "corpus_sources": self.index.source_count() if self.index else 0,
            }
            Path(path).write_text(
                render_json(self.result, meta=meta), encoding="utf-8"
            )
        self._set_status(f"Saved {path}")


def launch(corpus: Path | str, k: int = DEFAULT_K, w: int = DEFAULT_W) -> None:
    """Open the desktop application."""

    root = tk.Tk()
    root.title("plagcheck - zero-dependency similarity checker")
    root.geometry("1120x740")
    root.minsize(900, 600)
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass

    app = PlagCheckApp(root, Path(corpus), k, w)

    menubar = tk.Menu(root)
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Load document...", command=app.load_file)
    file_menu.add_command(label="Clear", command=app.clear_text)
    file_menu.add_separator()
    file_menu.add_command(label="Save HTML report...", command=lambda: app.save_report("html"))
    file_menu.add_command(label="Save JSON report...", command=lambda: app.save_report("json"))
    file_menu.add_separator()
    file_menu.add_command(label="Quit", command=root.destroy)
    menubar.add_cascade(label="File", menu=file_menu)

    tools_menu = tk.Menu(menubar, tearoff=0)
    tools_menu.add_command(label="Open corpus...", command=app.choose_corpus)
    tools_menu.add_command(label="Rebuild index", command=app.rebuild_index)
    tools_menu.add_command(label="Analyze", command=app.run_check)
    menubar.add_cascade(label="Tools", menu=tools_menu)
    root.configure(menu=menubar)

    root.mainloop()


def main(argv: list[str] | None = None) -> int:
    from .cli import main as cli_main

    return cli_main(["gui", *(argv or [])])


if __name__ == "__main__":
    raise SystemExit(main())


# Expose the supported-suffix list for callers that mirror the file dialog.
__all__ = ["PlagCheckApp", "launch", "SUPPORTED_SUFFIXES"]
