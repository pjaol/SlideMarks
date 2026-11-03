"""Content shared by the HTML, PowerPoint and Word specimens so all three
show the same glyphs in the same arrangements."""

import unicodedata
from collections import defaultdict

from .manifest import preferred_codepoint

LADDER_PT = [10, 12, 14, 18, 24, 36]

SCORECARD_HEADER = ("Capability", "Option A", "Option B", "Option C", "Status", "Trend")
SCORECARD_ROWS = [
    ("Offline use", "harvey-100", "harvey-50", "harvey-0", "status-check", "trend-up"),
    ("Font embedding", "harvey-75", "harvey-75", "harvey-25", "status-check", "arrow-right"),
    ("Web support", "harvey-50", "harvey-100", "harvey-25", "status-cross", "trend-down"),
    ("Table alignment", "harvey-100", "harvey-25", "harvey-0", "dot-filled", "arrow-up"),
    ("Recolour as text", "harvey-25", "harvey-50", "harvey-75", "dot-empty", "arrow-down"),
]


def families(manifest):
    """Ordered (family id, title, members) from the manifest's declared families."""
    members = defaultdict(list)
    for s in manifest["symbols"]:
        members[s["category"]].append(s)
    return [(f["id"], f["title"], members[f["id"]]) for f in manifest["families"] if members[f["id"]]]


def preferred_char(symbol) -> str:
    return chr(int(preferred_codepoint(symbol), 16))


def visible_text(symbol) -> str:
    """Short visible text that carries the symbol's meaning next to it in a cell."""
    if symbol["category"] == "harvey":
        return f"{round(symbol['params']['fraction'] * 100)}%"
    return symbol["spokenLabel"][:1].upper() + symbol["spokenLabel"][1:]


def alias_rows(manifest):
    """(symbol, PUA char, alias char, Unicode name) for the screen-reader encoding test."""
    return [
        (s, chr(int(s["codepoint"], 16)), chr(int(a, 16)), unicodedata.name(chr(int(a, 16))).title())
        for s in manifest["symbols"] for a in s["unicodeAliases"]
    ]
