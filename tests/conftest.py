import copy
import json
from pathlib import Path

import pytest

from slidemarks_build.font import build_font

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def tokens():
    return json.loads((ROOT / "source/design-tokens.json").read_text())


@pytest.fixture(scope="session")
def manifest():
    return json.loads((ROOT / "source/symbols.json").read_text())


@pytest.fixture
def manifest_copy(manifest):
    return copy.deepcopy(manifest)


@pytest.fixture(scope="session")
def built(tokens, manifest, tmp_path_factory):
    return build_font(tokens, manifest, tmp_path_factory.mktemp("dist"))
