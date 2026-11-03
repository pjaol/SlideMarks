import pytest

from slidemarks_build.manifest import preferred_codepoint, validate


def test_manifest_is_valid(manifest):
    assert validate(manifest) == []


def test_every_glyph_has_semantic_metadata(manifest):
    for s in manifest["symbols"]:
        assert s["spokenLabel"].strip(), s["id"]
        assert isinstance(s["needsContext"], bool), s["id"]
        assert isinstance(s["unicodeAliases"], list), s["id"]


def test_preferred_codepoint_uses_alias_only_when_present(manifest):
    by_id = {s["id"]: s for s in manifest["symbols"]}
    assert preferred_codepoint(by_id["arrow-right"]) == "2192"
    assert preferred_codepoint(by_id["harvey-75"]) == "E003"


@pytest.mark.parametrize("alias, message", [
    ("E002", "Private Use Area"),   # aliases must be standard characters
    ("0041", "letter, digit"),      # never hijack letters
    ("0031", "letter, digit"),      # or digits
    ("2192", "already belongs"),    # each alias claimed by one glyph only
])
def test_rejects_bad_aliases(manifest_copy, alias, message):
    target = next(s for s in manifest_copy["symbols"] if s["id"] == "arrow-left")
    target["unicodeAliases"] = [alias]
    assert any(message in e for e in validate(manifest_copy))
