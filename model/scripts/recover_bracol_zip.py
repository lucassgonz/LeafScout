#!/usr/bin/env python3
"""Recover files from the BRACOL inner zip, which has no valid End-Of-Central-
Directory record (the upload on Mendeley itself appears to be missing it —
CRC on the outer wrapper zip passes, so the bytes weren't corrupted in
transit; the inner archive was already like this).

This is a STORE-method zip (no compression), so every file's data sits
directly after a 30-byte local file header + filename + extra field, with a
known length — meaning every entry can be recovered with a single linear
scan for "PK\\x03\\x04" signatures, without ever reading the (missing)
central directory.
"""
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

LOCAL_HEADER_SIG = b"PK\x03\x04"


def recover(inner_zip_path: Path, out_dir: Path) -> int:
    data = inner_zip_path.read_bytes()
    out_dir.mkdir(parents=True, exist_ok=True)

    pos = 0
    n_recovered = 0
    while True:
        idx = data.find(LOCAL_HEADER_SIG, pos)
        if idx == -1:
            break

        # Local file header (fixed 30 bytes after the signature):
        # version(2) flags(2) method(2) mtime(2) mdate(2) crc32(4)
        # comp_size(4) uncomp_size(4) fname_len(2) extra_len(2)
        header = data[idx : idx + 30]
        if len(header) < 30:
            break
        (
            _version,
            flags,
            method,
            _mtime,
            _mdate,
            _crc32,
            comp_size,
            uncomp_size,
            fname_len,
            extra_len,
        ) = struct.unpack("<HHHHHIIIHH", header[4:30])

        name_start = idx + 30
        name = data[name_start : name_start + fname_len].decode("utf-8", errors="replace")
        data_start = name_start + fname_len + extra_len

        if flags & 0x08:
            # Data-descriptor flag: size fields are zero in the local header
            # and the real sizes follow the file data instead — we can't
            # know where this entry ends without the (missing) central
            # directory. Not observed in this archive, but guard anyway.
            print(f"  skip (streamed/unknown size): {name}")
            pos = name_start + 4
            continue

        if method not in (0, 8):
            print(f"  skip (unsupported method={method}): {name}")
            pos = name_start + 4
            continue

        raw = data[data_start : data_start + comp_size]
        if len(raw) != comp_size:
            print(f"  truncated at end of archive: {name} (wanted {comp_size}, got {len(raw)})")
            break

        if method == 0:
            file_bytes = raw
        else:  # method == 8, DEFLATE
            try:
                file_bytes = zlib.decompress(raw, -15)  # raw deflate, no zlib/gzip header
            except zlib.error as e:
                print(f"  decompress failed, skipping: {name} ({e})")
                pos = data_start + comp_size
                continue

        if name and not name.endswith("/") and file_bytes:
            dest = out_dir / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(file_bytes)
            n_recovered += 1

        pos = data_start + comp_size

    return n_recovered


if __name__ == "__main__":
    inner_zip = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    if not inner_zip or not out_dir:
        print("Usage: recover_bracol_zip.py <inner_zip_path> <out_dir>")
        sys.exit(1)

    n = recover(inner_zip, out_dir)
    print(f"Recovered {n} files to {out_dir}")
