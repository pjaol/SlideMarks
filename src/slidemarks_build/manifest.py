"""Manifest integrity rules (PRD §2.1, §6): unique ids, unique PUA code points, required metadata."""

from .glyphs import BUILDERS

REQUIRED = ("id", "codepoint", "name", "category", "tags", "builder", "params", "geometryGroup", "status", "introduced")
PUA = range(0xE000, 0xF8FF + 1)


def validate(manifest) -> list[str]:
    errors = []
    ids, cps = set(), set()
    families = {f["id"] for f in manifest.get("families", [])}
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
    return errors
