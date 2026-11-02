"""Ensure the independently signed APK contains exactly this build's contents."""
from pathlib import Path
import sys
from zipfile import ZipFile

unsigned, signed = map(Path, sys.argv[1:])
with ZipFile(unsigned) as original, ZipFile(signed) as release:
    assert sorted(original.namelist()) == sorted(release.namelist()), "APK entries differ"
    for name in original.namelist():
        assert original.read(name) == release.read(name), f"Signed APK differs from current source: {name}"
print("Signed APK matches the freshly compiled Android source")
