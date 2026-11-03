"""Screen-reader pronunciation packs generated from the manifest.

A font can't tell a screen reader what a character means, but every major screen
reader lets users add their own pronunciations. These packs map each SlideMarks
PUA code point to its `spokenLabel`, so an installed pack makes U+E002 speak
"Harvey ball 50 percent". They help only people who install them; documents for
everyone else still need visible text (docs/accessibility.md)."""

import io
import plistlib
import zipfile
from pathlib import Path

FIXED_DATE = (2026, 1, 1, 0, 0, 0)

# Add-on symbol dictionaries arrived in NVDA 2024.3 (nvaccess/nvda#16823).
NVDA_MIN = "2024.3.0"
NVDA_LAST_TESTED = "2026.2.0"


def _nvda_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("\t", "\\t").replace("#", "\\#")


def nvda_symbols(manifest) -> str:
    """symbols.dic body. Level `none` speaks the label at every symbol level."""
    lines = [
        f"# SlideMarks {manifest['manifestVersion']} · generated from source/symbols.json",
        "complexSymbols:",
        "",
        "symbols:",
    ]
    for s in manifest["symbols"]:
        char = chr(int(s["codepoint"], 16))
        lines.append(f"{char}\t{_nvda_escape(s['spokenLabel'])}\tnone\tnever\t# {s['id']}")
    return "\n".join(lines) + "\n"


def nvda_addon(manifest) -> bytes:
    version = manifest["manifestVersion"]
    addon_manifest = f'''name = slidemarksSymbols
summary = "SlideMarks symbol names"
description = "Speaks the meaning of SlideMarks presentation symbols, e.g. Harvey ball 50 percent."
author = "SlideMarks"
url = https://github.com/pjaol/SlideMarks
version = {version}
minimumNVDAVersion = {NVDA_MIN}
lastTestedNVDAVersion = {NVDA_LAST_TESTED}

[symbolDictionaries]
\t[[slidemarks]]
\t\tdisplayName = SlideMarks symbols
\t\tmandatory = true
'''
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in (("manifest.ini", addon_manifest), ("locale/en/symbols-slidemarks.dic", nvda_symbols(manifest))):
            z.writestr(zipfile.ZipInfo(name, FIXED_DATE), data.encode("utf-8"))
    return buf.getvalue()


def jaws_symbols(manifest) -> str:
    """Lines to append to a JAWS synthesizer symbol file (.sbl)."""
    lines = [
        f"; SlideMarks {manifest['manifestVersion']} · append to your JAWS .sbl symbol file (see README in this folder)",
    ]
    lines += [f"u+{s['codepoint']}={s['spokenLabel']}" for s in manifest["symbols"]]
    return "\n".join(lines) + "\n"


# Format observed in a VoiceOver Utility export (File > Export) from macOS 26.5:
# a plist whose export/default dict holds one custom.pronunciation.<key> dict per entry.
VO_ARCHIVE_HEADER = {"ArchiveType": 1, "ArchiveVersion": "993", "ArchiveVersionOS": "260500", "ArchiveVersionVO": 4}
VO_KEY_BASE = 815500000  # fixed, so rebuilds produce the same keys


def _voiceover_entries(manifest) -> dict:
    entries = {}
    for i, s in enumerate(manifest["symbols"]):
        key = f"{VO_KEY_BASE}.{i:06d}"
        entries[f"custom.pronunciation.{key}"] = {
            "SCRComponent": "SCROutputSpeechComponent",
            "SCRDomainIdentifier": "SCRAnyApplication",
            "SCREnabled": "1",
            "SCRIgnoreCase": "1",
            "SCRPrimaryKey": key,
            "SCRSearchText": chr(int(s["codepoint"], 16)),
            "SCRSubText": s["spokenLabel"],
            "SCRSubTextKey": "",
        }
    return entries


def voiceover_archive(manifest) -> bytes:
    """VoiceOver Utility archive containing only SlideMarks pronunciations (All Apps).

    Importing an archive REPLACES the user's pronunciation list (Apple: import replaces
    each preference type; only custom labels merge). Users should install via
    voiceover_merge() into their own export instead."""
    return plistlib.dumps(VO_ARCHIVE_HEADER | {"export": {"default": _voiceover_entries(manifest)}},
                          fmt=plistlib.FMT_XML, sort_keys=True)


def voiceover_merge(manifest, user_export: bytes) -> tuple[bytes, dict]:
    """Add SlideMarks pronunciations to a user's own VoiceOver Utility export.

    Everything the user exported is kept as-is, so re-importing restores their settings
    and pronunciations plus SlideMarks. Re-running is idempotent: earlier SlideMarks
    entries, and any user entries for SlideMarks characters, are replaced."""
    archive = plistlib.loads(user_export)
    default = archive.setdefault("export", {}).setdefault("default", {})
    ours = _voiceover_entries(manifest)
    our_chars = {e["SCRSearchText"] for e in ours.values()}
    replaced = [k for k, v in default.items()
                if k.startswith("custom.pronunciation.") and isinstance(v, dict)
                and (k in ours or v.get("SCRSearchText", "").strip() in our_chars)]
    for k in replaced:
        del default[k]
    kept = sum(1 for k in default if k.startswith("custom.pronunciation."))
    default.update(ours)
    stats = {"kept": kept, "replaced": len(replaced), "added": len(ours)}
    return plistlib.dumps(archive, fmt=plistlib.FMT_XML, sort_keys=True), stats


def render(manifest, out_dir: Path) -> dict:
    version = manifest["manifestVersion"]
    nvda_dir, jaws_dir, vo_dir = out_dir / "nvda", out_dir / "jaws", out_dir / "voiceover"
    for d in (nvda_dir, jaws_dir, vo_dir):
        d.mkdir(parents=True, exist_ok=True)
    for stale in nvda_dir.glob("*.nvda-addon"):
        stale.unlink()
    addon = nvda_dir / f"SlideMarks-symbols-{version}.nvda-addon"
    addon.write_bytes(nvda_addon(manifest))
    jaws = jaws_dir / "slidemarks-jaws-symbols.txt"
    jaws.write_text(jaws_symbols(manifest), encoding="utf-8")
    voiceover = vo_dir / "SlideMarks-pronunciations.voprefs"
    voiceover.write_bytes(voiceover_archive(manifest))
    return {"nvda": addon, "jaws": jaws, "voiceover": voiceover}
