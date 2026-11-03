"""Manifest integrity rules (PRD §2.1, §6): unique ids, unique PUA code points, required
metadata, and Unicode aliases that are standard characters claimed by exactly one glyph."""

from .glyphs import BUILDERS

REQUIRED = ("id", "codepoint", "name", "category", "tags", "builder", "params", "geometryGroup", "status", "introduced",
            "spokenLabel", "needsContext", "unicodeAliases")
PUA = range(0xE000, 0xF8FF + 1)


def validate(manifest) -> list[str]:
    errors = []
    ids, cps = set(), set()
    families = {f["id"] for f in manifest.get("families", [])}
    aliases = []
    for i, s in enumerate(manifest["symbols"]):
        where = s.get("id", f"#{i}")
        missing = [k for k in REQUIRED if k not in s]
        if missing:
            errors.append(f"{where}: missing {', '.join(missing)}")
            continue
        if s["id"] in ids:
            errors.append(f"{where}: duplicate id")
        ids.add(s["id"])
        cp = int(s["codepoint"], 16)
        if cp not in PUA:
            errors.append(f"{where}: U+{s['codepoint']} is outside the Private Use Area")
        if cp in cps:
            errors.append(f"{where}: duplicate code point U+{s['codepoint']}")
        cps.add(cp)
        if families and s["category"] not in families:
            errors.append(f"{where}: category '{s['category']}' is not a declared family")
        if s["builder"] not in BUILDERS:
            errors.append(f"{where}: unknown builder '{s['builder']}'")
        if not s["spokenLabel"].strip():
            errors.append(f"{where}: empty spokenLabel")
        aliases.extend((where, a) for a in s["unicodeAliases"])

    seen = {}
    for where, a in aliases:
        cp = int(a, 16)
        if cp in PUA or cp in cps:
            errors.append(f"{where}: alias U+{a} is in the Private Use Area; aliases must be standard characters")
        elif cp < 0x21 or chr(cp).isalnum():
            errors.append(f"{where}: alias U+{a} would hijack a letter, digit, space or control character")
        if cp in seen:
            errors.append(f"{where}: alias U+{a} already belongs to {seen[cp]}")
        seen[cp] = where
    return errors


def preferred_codepoint(symbol) -> str:
    """What pickers, CSS and docs should insert: the standard Unicode alias when one
    exists (meaningful without the font), otherwise the stable PUA code point."""
    return symbol["unicodeAliases"][0] if symbol["unicodeAliases"] else symbol["codepoint"]
