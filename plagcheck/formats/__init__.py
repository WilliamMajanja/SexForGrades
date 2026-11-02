"""Format inspectors for plagcheck."""
from ..core.registry import (
    Inspection,
    Format,
    identify,
    inspect_file,
    list_formats,
    register,
    SCHEMA,
)
from . import text, htmlfmt, jsonfmt, csvfmt, docx, pdf, code

REGISTRY = [
    text.TextFormat,
    htmlfmt.HtmlFormat,
    jsonfmt.JsonFormat,
    csvfmt.CsvFormat,
    code.CodeFormat,
    docx.DocxFormat,
    pdf.PdfFormat,
]

# populate global registry in core
from ..core import registry as _registry
_registry.REGISTRY = REGISTRY

__all__ = [
    "Inspection",
    "Format",
    "identify",
    "inspect_file",
    "list_formats",
    "register",
    "SCHEMA",
    "REGISTRY",
]
