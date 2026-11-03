import io
import plistlib
import zipfile

from slidemarks_build.screen_readers import jaws_symbols, nvda_addon, nvda_symbols, voiceover_archive, voiceover_merge


def test_nvda_dictionary_names_every_glyph(manifest):
    body = nvda_symbols(manifest)
    assert body.splitlines()[1:4] == ["complexSymbols:", "", "symbols:"]
    entries = [line.split("\t") for line in body.splitlines()[4:]]
    assert {e[0]: e[1] for e in entries} == {chr(int(s["codepoint"], 16)): s["spokenLabel"] for s in manifest["symbols"]}
    assert all(e[2] == "none" and e[3] == "never" for e in entries)


def test_nvda_addon_declares_mandatory_dictionary(manifest):
    with zipfile.ZipFile(io.BytesIO(nvda_addon(manifest))) as z:
        assert set(z.namelist()) == {"manifest.ini", "locale/en/symbols-slidemarks.dic"}
        ini = z.read("manifest.ini").decode()
    assert "[symbolDictionaries]" in ini and "[[slidemarks]]" in ini and "mandatory = true" in ini
    assert "minimumNVDAVersion = 2024.3.0" in ini


def test_jaws_lines_cover_every_glyph(manifest):
    lines = [l for l in jaws_symbols(manifest).splitlines() if not l.startswith(";")]
    assert lines == [f"u+{s['codepoint']}={s['spokenLabel']}" for s in manifest["symbols"]]


def test_voiceover_archive_only_contains_slidemarks_pronunciations(manifest):
    archive = plistlib.loads(voiceover_archive(manifest))
    entries = archive["export"]["default"]
    assert all(k.startswith("custom.pronunciation.") for k in entries)
    assert {e["SCRSearchText"]: e["SCRSubText"] for e in entries.values()} == {
        chr(int(s["codepoint"], 16)): s["spokenLabel"] for s in manifest["symbols"]
    }
    assert all(e["SCRDomainIdentifier"] == "SCRAnyApplication" and e["SCREnabled"] == "1" for e in entries.values())
    assert len({e["SCRPrimaryKey"] for e in entries.values()}) == len(entries)


def _user_export():
    return plistlib.dumps({
        "ArchiveType": 1, "ArchiveVersion": "993",
        "export": {"default": {
            "SCRDisplayTextEnabled": True,
            "custom.pronunciation.1.1": {"SCRSearchText": ":-)", "SCRSubTextKey": "SCRUserSubstitution.smiley"},
            "custom.pronunciation.1.2": {"SCRSearchText": "\ue002 ", "SCRSubText": "Harvey balls 50%"},
        }},
    })


def test_voiceover_merge_keeps_user_settings_and_replaces_overlaps(manifest):
    merged, stats = voiceover_merge(manifest, _user_export())
    default = plistlib.loads(merged)["export"]["default"]
    assert default["SCRDisplayTextEnabled"] is True                      # other settings untouched
    assert default["custom.pronunciation.1.1"]["SCRSearchText"] == ":-)"  # Apple default kept
    assert "custom.pronunciation.1.2" not in default                     # hand-made SlideMarks entry replaced
    assert stats == {"kept": 1, "replaced": 1, "added": len(manifest["symbols"])}


def test_voiceover_merge_is_idempotent(manifest):
    once, _ = voiceover_merge(manifest, _user_export())
    twice, stats = voiceover_merge(manifest, once)
    assert twice == once
    assert stats["replaced"] == len(manifest["symbols"])
