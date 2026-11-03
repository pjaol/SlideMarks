"""Package a TTF for embedding in Office documents.

PowerPoint stores embedded fonts as ppt/fonts/fontN.fntdata in EOT form and
only uses them when the EOT is uncompressed (version 0x00020001, Flags 0) and
p:presentation has embedTrueTypeFonts="1". A raw TTF in that part is ignored.
Layout: W3C EOT submission, https://www.w3.org/submissions/EOT/ (little-endian).

Word stores embedded fonts as word/fonts/*.odttf: the raw TTF with its first
32 bytes XORed against a key derived from the w:fontKey GUID (ECMA-376 Part 1
§17.8.1). The key is the GUID's 32 hex digits read as bytes, then reversed.
"""

import struct
import uuid
from pathlib import Path

from fontTools.ttLib import TTFont

EOT_VERSION = 0x00020001
MAGIC = 0x504C
DEFAULT_CHARSET = 1


def _name_field(text: str) -> bytes:
    data = text.encode("utf-16-le")
    return struct.pack("<HH", 0, len(data)) + data  # PaddingN, NameSize, Name


def ttf_to_eot(ttf_path: Path) -> bytes:
    font_data = ttf_path.read_bytes()
    font = TTFont(str(ttf_path))
    os2, head, name = font["OS/2"], font["head"], font["name"]
    panose = os2.panose
    panose_bytes = bytes([
        panose.bFamilyType, panose.bSerifStyle, panose.bWeight, panose.bProportion, panose.bContrast,
        panose.bStrokeVariation, panose.bArmStyle, panose.bLetterForm, panose.bMidline, panose.bXHeight,
    ])

    fixed = struct.pack(
        "<II10sBBIHH4I2II4I",
        EOT_VERSION,
        0,  # Flags: no MTX compression, no XOR
        panose_bytes,
        DEFAULT_CHARSET,
        os2.fsSelection & 1,  # Italic
        os2.usWeightClass,
        os2.fsType,
        MAGIC,
        os2.ulUnicodeRange1, os2.ulUnicodeRange2, os2.ulUnicodeRange3, os2.ulUnicodeRange4,
        os2.ulCodePageRange1, os2.ulCodePageRange2,
        head.checkSumAdjustment,
        0, 0, 0, 0,  # Reserved1-4
    )
    names = b"".join(_name_field(name.getDebugName(i) or "") for i in (1, 2, 5, 4))  # family, style, version, full
    names += struct.pack("<HH", 0, 0)  # Padding5, RootStringSize (no root-string restriction)

    header_size = 8 + len(fixed) + len(names)
    return struct.pack("<II", header_size + len(font_data), len(font_data)) + fixed + names + font_data


def obfuscate_odttf(ttf_path: Path, font_key: uuid.UUID) -> bytes:
    """XOR is symmetric, so this also de-obfuscates."""
    key = bytes.fromhex(font_key.hex)[::-1]
    data = bytearray(ttf_path.read_bytes())
    for i in range(32):
        data[i] ^= key[i % 16]
    return bytes(data)


def font_key_for(family: str) -> uuid.UUID:
    """Deterministic GUID so rebuilds stay byte-stable."""
    return uuid.uuid5(uuid.NAMESPACE_URL, f"slidemarks:{family}")
