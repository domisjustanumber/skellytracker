"""Print SONAME and NEEDED of each shared library of each wheel. Nothing is loaded. Usage: sonames.py WHEEL..."""
import io
import sys
import zipfile
from pathlib import PurePosixPath

from elftools.elf.dynamic import DynamicSection
from elftools.elf.elffile import ELFFile

for wheel in sys.argv[1:]:
    print("==", PurePosixPath(wheel.replace("\\", "/")).name)
    with zipfile.ZipFile(wheel) as archive:
        for name in archive.namelist():
            if ".so" not in PurePosixPath(name).name:
                continue
            data = archive.read(name)
            if data[:4] != b"\x7fELF":
                print("  ", name, "NOT ELF", len(data))
                continue
            tags = [t for s in ELFFile(io.BytesIO(data)).iter_sections() if isinstance(s, DynamicSection) for t in s.iter_tags()]
            print("  ", name, "| SONAME", [t.soname for t in tags if t.entry.d_tag == "DT_SONAME"],
                  "| NEEDED", sorted(t.needed for t in tags if t.entry.d_tag == "DT_NEEDED" and not t.needed.startswith(("libc.", "libm.", "libdl.", "libpthread.", "librt.", "libgcc_s", "libstdc++", "ld-linux"))),
                  "| RUNPATH", [t.runpath for t in tags if t.entry.d_tag == "DT_RUNPATH"])
