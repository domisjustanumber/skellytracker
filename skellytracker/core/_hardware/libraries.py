"""The shared libraries that are loaded in this process, and their versions. No function here loads a library."""

import ctypes
import ntpath
import posixpath
import re
import sys

_SONAME_VERSION = re.compile(r"\.so\.(\d+(?:\.\d+)*)$")


def loaded_module_paths() -> list[str]:
    """The file path of each module that is mapped in this process."""
    if sys.platform == "win32":
        import psutil

        return [item.path for item in psutil.Process().memory_maps() if item.path.lower().endswith(".dll")]
    if sys.platform == "darwin":
        libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib")
        libc._dyld_get_image_name.restype = ctypes.c_char_p
        return [libc._dyld_get_image_name(index).decode("utf-8", "replace") for index in range(libc._dyld_image_count())]
    with open("/proc/self/maps", encoding="utf-8", errors="replace") as maps:
        return sorted({line.split(None, 5)[5].strip() for line in maps if line.count(" ") >= 5 and "/" in line})


def file_version(path: str) -> str | None:
    """The file version of a Windows DLL, from `version.dll`. `None` when the file has no version resource."""
    version = ctypes.WinDLL("version")
    size = version.GetFileVersionInfoSizeW(path, None)
    if not size:
        return None
    data = ctypes.create_string_buffer(size)
    value, length = ctypes.c_void_p(), ctypes.c_uint()
    if not version.GetFileVersionInfoW(path, 0, size, data):
        return None
    if not version.VerQueryValueW(data, "\\", ctypes.byref(value), ctypes.byref(length)) or length.value < 16:
        return None
    high, low = (ctypes.c_uint32 * 4).from_address(value.value)[2:4]  # dwFileVersionMS, dwFileVersionLS
    return f"{high >> 16}.{high & 0xFFFF}.{low >> 16}.{low & 0xFFFF}"


def library_name(path: str) -> str:
    """The basename in lower case, without a leading `lib`."""
    name = posixpath.basename(ntpath.basename(path)).lower()
    return name[3:] if name.startswith("lib") else name


def library_version(path: str) -> tuple[str | None, str]:
    """The version and its source `<kind>:<basename>`.

    shortcut: the version comes from the file, not from the version function of the library. Add the
    function call when a consumer needs the version that the library reports.
    """
    base = posixpath.basename(ntpath.basename(path))
    if sys.platform == "win32":
        try:
            return file_version(path), f"file-version:{base}"
        except OSError:
            return None, f"file-version:{base}"
    match = _SONAME_VERSION.search(base)
    return (match.group(1) if match else None), f"soname:{base}"
