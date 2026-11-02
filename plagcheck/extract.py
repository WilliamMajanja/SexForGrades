"""File text extraction using only the standard library.

Supported: plain text and markup (.txt, .md, .csv, .json, .py, ...), HTML,
Word .docx (Office Open XML) and a best-effort PDF text extractor for
unencrypted files whose text streams use standard font encodings. Scanned
image-only PDFs yield no text, as expected.
"""

from __future__ import annotations

import html as html_module
import re
import urllib.error
import urllib.request
import zipfile
import tempfile
import zlib
from pathlib import Path

TEXT_SUFFIXES = {
    ".txt",
    ".md",
    ".markdown",
    ".text",
    ".csv",
    ".tsv",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".py",
    ".js",
    ".ts",
    ".c",
    ".h",
    ".cpp",
    ".java",
    ".rb",
    ".go",
    ".rs",
    ".html",
    ".htm",
    ".docx",
    ".pdf",
}
SUPPORTED_SUFFIXES = TEXT_SUFFIXES

_HTML_SCRIPT_RE = re.compile(
    r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL
)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HTML_BLOCK_RE = re.compile(r"</(p|div|br|li|tr|h[1-6])\s*>", re.IGNORECASE)
_XMLTAG_RE = re.compile(r"<[^>]+>")
_DOCX_PARAGRAPH_RE = re.compile(r"</w:p\s*>", re.IGNORECASE)
_DOCX_TEXT_RE = re.compile(r"<w:t\b[^>]*>(.*?)</w:t>", re.IGNORECASE | re.DOTALL)

_PDF_WHITESPACE_RE = re.compile(rb"\s+")
_PDF_OBJ_RE = re.compile(rb"(?m)^\s*(\d+)\s+(\d+)\s+obj\b")
_PDF_HAS_LETTER_RE = re.compile(r"[A-Za-z\u00c0-\u024f]")


def _pdf_objects(data: bytes) -> dict[int, bytes]:
    """Map object number -> raw object body (between ``obj`` and ``endobj``)."""

    objects: dict[int, bytes] = {}
    matches = list(_PDF_OBJ_RE.finditer(data))
    for position, match in enumerate(matches):
        number = int(match.group(1))
        start = match.end()
        # The body ends at the next object or at endobj, whichever is sooner.
        next_start = matches[position + 1].start() if position + 1 < len(matches) else len(data)
        endobj = data.find(b"endobj", start)
        end = endobj if endobj != -1 and endobj < next_start else next_start
        objects[number] = data[start:end]
    return objects


def _pdf_stream(body: bytes) -> bytes | None:
    marker = body.find(b"stream")
    if marker == -1:
        return None
    start = marker + len(b"stream")
    if body[start : start + 2] == b"\r\n":
        start += 2
    elif body[start : start + 1] in (b"\n", b"\r"):
        start += 1
    end = body.find(b"endstream", start)
    if end == -1:
        return None
    chunk = body[start:end]
    try:
        return zlib.decompress(chunk)
    except zlib.error:
        return chunk


def _utf16be(hexstr: bytes) -> str:
    try:
        return bytes.fromhex(hexstr.decode("ascii")).decode("utf-16-be", "replace")
    except ValueError:
        return ""


def _parse_tounicode(cmap: bytes, mapping: dict[int, str]) -> None:
    """Merge a ToUnicode CMap's code->Unicode mappings into *mapping*."""

    for block in re.findall(rb"beginbfchar(.*?)endbfchar", cmap, re.DOTALL):
        for source, target in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            mapping[int(source, 16)] = _utf16be(target)
    for block in re.findall(rb"beginbfrange(.*?)endbfrange", cmap, re.DOTALL):
        for low, high, target in re.findall(
            rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block
        ):
            low_i, high_i, base = int(low, 16), int(high, 16), int(target, 16)
            if high_i < low_i or high_i - low_i > 0xFFFF:
                continue
            for code in range(low_i, high_i + 1):
                mapping[code] = _utf16be(b"%04x" % (base + (code - low_i)))


def _find_matching_paren(data: bytes, start: int) -> int:
    """Return the index just past the balanced ``)`` for a ``(`` at *start*."""

    depth = 0
    index = start
    length = len(data)
    while index < length:
        char = data[index]
        if char == 0x5C:  # backslash escape
            index += 2
            continue
        if char == 0x28:  # (
            depth += 1
        elif char == 0x29:  # )
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return length


def _unescape_pdf_bytes(raw: bytes) -> bytes:
    body = raw[1:-1]  # strip parentheses
    out = bytearray()
    index = 0
    while index < len(body):
        char = body[index]
        if char == 0x5C and index + 1 < len(body):
            nxt = body[index + 1]
            mapping = {0x6E: 0x0A, 0x72: 0x0D, 0x74: 0x09, 0x62: 0x08, 0x66: 0x0C, 0x28: 0x28, 0x29: 0x29, 0x5C: 0x5C}
            if nxt in mapping:
                out.append(mapping[nxt])
                index += 2
                continue
            if 0x30 <= nxt <= 0x37:  # octal escape
                octal = bytearray()
                cursor = index + 1
                while cursor < len(body) and len(octal) < 3 and 0x30 <= body[cursor] <= 0x37:
                    octal.append(body[cursor])
                    cursor += 1
                out.append(int(octal.decode("ascii"), 8) & 0xFF)
                index = cursor
                continue
            out.append(nxt)
            index += 2
            continue
        out.append(char)
        index += 1
    return bytes(out)


def _decode_codes(raw: bytes, mapping: dict[int, str], two_byte: bool) -> str:
    if not mapping:
        return raw.decode("cp1252", "replace")
    chars: list[str] = []
    if two_byte:
        for index in range(0, len(raw) - 1, 2):
            chars.append(mapping.get((raw[index] << 8) | raw[index + 1], ""))
    else:
        for byte in raw:
            chars.append(mapping.get(byte, chr(byte)))
    return "".join(chars)


def _font_maps(objects: dict[int, bytes]) -> dict[int, tuple[dict[int, str], bool]]:
    """Build a code->Unicode map for every font object that has a ToUnicode."""

    fonts: dict[int, tuple[dict[int, str], bool]] = {}
    for number, body in objects.items():
        reference = re.search(rb"/ToUnicode\s+(\d+)\s+0\s+R", body)
        subtype = re.search(rb"/Subtype\s*/(\w+)", body)
        is_type0 = bool(subtype and subtype.group(1) == b"Type0")
        if not reference and not is_type0:
            continue
        mapping: dict[int, str] = {}
        if reference:
            cmap_object = objects.get(int(reference.group(1)))
            if cmap_object is not None:
                cmap_stream = _pdf_stream(cmap_object) or cmap_object
                _parse_tounicode(cmap_stream, mapping)
        fonts[number] = (mapping, is_type0)
    return fonts


def _font_names(objects: dict[int, bytes]) -> dict[str, int]:
    """Map font resource names (/F1, /F2, ...) to font object numbers."""

    names: dict[str, int] = {}
    for body in objects.values():
        for dictionary in re.findall(rb"/Font\s*<<(.*?)>>", body, re.DOTALL):
            for name, number in re.findall(
                rb"/([A-Za-z0-9#]+)\s+(\d+)\s+0\s+R", dictionary
            ):
                names[name.decode("latin-1")] = int(number)
        for indirect in re.findall(rb"/Font\s+(\d+)\s+0\s+R", body):
            target = objects.get(int(indirect))
            if not target:
                continue
            for name, number in re.findall(
                rb"/([A-Za-z0-9#]+)\s+(\d+)\s+0\s+R", target
            ):
                names.setdefault(name.decode("latin-1"), int(number))
    return names


def _extract_pdf_stream(
    content: bytes,
    fonts: dict[int, tuple[dict[int, str], bool]],
    names: dict[str, int],
    fallback: tuple[dict[int, str], bool],
) -> list[str]:
    """Linear scan of a content stream, decoding with the active font's CMap."""

    lines: list[str] = []
    current: list[str] = []
    index = 0
    length = len(content)
    last_name = ""
    active_map: dict[int, str] = {}
    active_two = False
    array_depth = 0
    while index < length:
        char = content[index]
        if char == 0x28:  # literal string
            end = _find_matching_paren(content, index)
            raw = _unescape_pdf_bytes(content[index:end])
            mapping, two_byte = _active_font(active_map, active_two, fallback, last_name, names, fonts)
            current.append(_decode_codes(raw, mapping, two_byte))
            index = end
            continue
        if char == 0x3C and not (index + 1 < length and content[index + 1] == 0x3C):
            close = content.find(b">", index + 1)
            if close == -1:
                break
            cleaned = _PDF_WHITESPACE_RE.sub(b"", content[index + 1 : close])
            if len(cleaned) % 2:
                cleaned += b"0"
            try:
                raw = bytes.fromhex(cleaned.decode("ascii"))
                mapping, two_byte = _active_font(active_map, active_two, fallback, last_name, names, fonts)
                current.append(_decode_codes(raw, mapping, two_byte))
            except ValueError:
                pass
            index = close + 1
            continue
        if char == 0x2F:  # '/' begins a name token
            cursor = index + 1
            while cursor < length and content[cursor] not in b" \t\r\n/[]<>()":
                cursor += 1
            last_name = content[index + 1 : cursor].decode("latin-1")
            index = cursor
            continue
        if char == 0x5B:  # [
            array_depth += 1
            index += 1
            continue
        if char == 0x5D:  # ]
            array_depth = max(0, array_depth - 1)
            index += 1
            continue
        if content[index : index + 2] == b"Tf":
            number = names.get(last_name)
            if number in fonts:
                active_map, active_two = fonts[number]
            else:
                active_map, active_two = {}, False
            index += 2
            continue
        if content[index : index + 2] in (b"Tj", b"TJ"):
            if current:
                lines.append("".join(current))
                current = []
            index += 2
            continue
        if content[index : index + 2] in (b"Td", b"TD", b"ET"):
            if current:
                lines.append("".join(current))
                current = []
            index += 2
            continue
        if array_depth > 0 and (0x30 <= char <= 0x39 or char in (0x2D, 0x2E)):
            cursor = index
            while cursor < length and (
                0x30 <= content[cursor] <= 0x39 or content[cursor] in (0x2D, 0x2E)
            ):
                cursor += 1
            try:
                if float(content[index:cursor]) <= -100:  # word gap in a TJ array
                    current.append(" ")
            except ValueError:
                pass
            index = cursor
            continue
        index += 1
    if current:
        lines.append("".join(current))
    return lines


def _active_font(
    active_map: dict[int, str],
    active_two: bool,
    fallback: tuple[dict[int, str], bool],
    last_name: str,
    names: dict[str, int],
    fonts: dict[int, tuple[dict[int, str], bool]],
) -> tuple[dict[int, str], bool]:
    if active_map or active_two:
        return active_map, active_two
    number = names.get(last_name)
    if number in fonts:
        return fonts[number]
    return fallback


_COMMON_WORDS = {
    "the", "of", "and", "to", "in", "is", "a", "that", "for", "it", "as",
    "with", "was", "on", "are", "by", "this", "be", "from", "at", "or", "an",
    "not", "which", "but", "have", "has", "we", "they", "their", "you",
}
_PDF_ALPHA_RE = re.compile(r"[A-Za-z\u00c0-\u024f]+")


def _language_score(text: str) -> float:
    """Rough natural-language score used to accept or reject decoded text."""

    if len(text) < 40:
        return 0.0
    space_ratio = (text.count(" ") + text.count("\n")) / len(text)
    words = _PDF_ALPHA_RE.findall(text.lower())
    if not words:
        return 0.0
    common_ratio = sum(1 for word in words if word in _COMMON_WORDS) / len(words)
    letters = len(_PDF_HAS_LETTER_RE.findall(text)) / len(text)
    # Natural prose has clear word spacing; glyph soup does not.
    if space_ratio < 0.08:
        return 0.0
    return space_ratio * 3.0 + common_ratio * 5.0 + letters


def read_pdf(path: Path) -> str:
    """Best-effort PDF text extraction with per-font ToUnicode decoding.

    Each content stream is scanned and its strings are decoded with the
    ToUnicode CMap of the font selected by the most recent ``Tf`` operator,
    which recovers real characters from subset-encoded fonts. If the result
    does not look like natural prose (for example, an image-only scan or an
    unsupported encoding), an empty string is returned rather than noise.
    """

    data = path.read_bytes()
    objects = _pdf_objects(data)
    fonts = _font_maps(objects)
    names = _font_names(objects)
    fallback: dict[int, str] = {}
    for mapping, two_byte in fonts.values():
        if not two_byte:
            fallback.update(mapping)

    content_streams: list[bytes] = []
    for body in objects.values():
        stream = _pdf_stream(body)
        if stream is None:
            continue
        if b"BT" in stream and (b"Tj" in stream or b"TJ" in stream):
            content_streams.append(stream)

    if not content_streams:
        return ""

    pieces: list[str] = []
    for stream in content_streams:
        lines = _extract_pdf_stream(stream, fonts, names, (fallback, False))
        candidate = "\n".join(lines)
        # Drop streams that did not decode into prose (undecodable fonts, art).
        if _language_score(candidate) >= 0.7:
            pieces.append(candidate)
    text = "\n".join(pieces)
    if _language_score(text) < 1.0:
        return ""
    return text


def _decode_bytes(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "replace")


def read_plain(path: Path) -> str:
    return _decode_bytes(path.read_bytes())


def read_html(path: Path) -> str:
    source = _decode_bytes(path.read_bytes())
    source = _HTML_SCRIPT_RE.sub(" ", source)
    source = _HTML_BLOCK_RE.sub("\n", source)
    source = _HTML_TAG_RE.sub(" ", source)
    return html_module.unescape(source)


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        target = "word/document.xml"
        if target not in names:
            raise ValueError(f"not a valid .docx file: {path.name}")
        xml = archive.read(target).decode("utf-8", "replace")
    xml = _DOCX_PARAGRAPH_RE.sub("\n", xml)
    texts = _DOCX_TEXT_RE.findall(xml)
    text = "".join(texts)
    text = _XMLTAG_RE.sub(" ", text)
    return html_module.unescape(text)


def extract_text(path: str | Path) -> str:
    """Extract plain text from *path*, dispatching on the file suffix."""

    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"no such file: {source}")
    suffix = source.suffix.lower()
    if suffix == ".docx":
        return read_docx(source)
    if suffix == ".pdf":
        return read_pdf(source)
    if suffix in {".html", ".htm"}:
        return read_html(source)
    return read_plain(source)


def fetch_url(url: str, *, timeout: float = 15.0) -> str:
    """Fetch a URL and return visible text (HTML stripped).

    Requires network access. Only http/https URLs are accepted. The caller is
    responsible for respecting the target site's terms and robots policy.
    """

    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError(f"refusing non-http(s) URL: {url}")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "plagcheck/1.0 (+offline-similarity-checker)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        data = response.read()
    try:
        source = data.decode(charset, "replace")
    except LookupError:
        source = _decode_bytes(data)
    source = _HTML_SCRIPT_RE.sub(" ", source)
    source = _HTML_BLOCK_RE.sub("\n", source)
    source = _HTML_TAG_RE.sub(" ", source)
    return html_module.unescape(source)


def extract_bytes(filename: str, data: bytes) -> str:
    """Extract text from an in-memory upload, using the filename's suffix."""

    suffix = Path(filename).suffix.lower()
    if suffix == ".docx":
        import io

        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", "replace")
        xml = _DOCX_PARAGRAPH_RE.sub("\n", xml)
        return html_module.unescape(_XMLTAG_RE.sub(" ", "".join(_DOCX_TEXT_RE.findall(xml))))
    if suffix in {".html", ".htm"}:
        source = _decode_bytes(data)
        source = _HTML_SCRIPT_RE.sub(" ", source)
        source = _HTML_BLOCK_RE.sub("\n", source)
        return html_module.unescape(_HTML_TAG_RE.sub(" ", source))
    if suffix == ".pdf":
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
            handle.write(data)
            temp_path = Path(handle.name)
        try:
            return read_pdf(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)
    return _decode_bytes(data)
