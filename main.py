#!/usr/bin/env python3
"""THE WORLD — Saturday 21 November 2026 (news-image-20261121).

Writes the newspaper front-page image to the make.fun output directory.

The front page itself lives in ``frontpage.html`` next to this script; it was
rendered to ``entry.png`` (1024x1024, under 1 MiB) with a headless browser.
This program is pure Python standard library: it validates the image
(PNG signature, IHDR dimensions, chunk CRCs, file size) and copies it to
``$MAKEFUN_OUTPUT_DIR/entry.png``.

Usage:
    MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import hashlib
import os
import struct
import sys
import zlib

EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
MAX_BYTES = 1024 * 1024  # 1 MiB
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def fail(message):
    print("ERROR: " + message, file=sys.stderr)
    sys.exit(1)


def check_png(data):
    """Validate the PNG bytes: signature, IHDR size, and chunk CRCs."""
    if len(data) < 8 or data[:8] != PNG_SIGNATURE:
        fail("not a PNG file (bad signature)")
    if len(data) > MAX_BYTES:
        fail("image is %d bytes, over the 1 MiB limit" % len(data))

    offset = 8
    saw_ihdr = False
    saw_iend = False
    while offset + 8 <= len(data):
        length, chunk_type = struct.unpack(">I4s", data[offset:offset + 8])
        chunk_start = offset + 8
        chunk_end = chunk_start + length
        if chunk_end + 4 > len(data):
            fail("truncated PNG chunk %r" % chunk_type)
        body = data[chunk_start:chunk_end]
        stored_crc = struct.unpack(">I", data[chunk_end:chunk_end + 4])[0]
        actual_crc = zlib.crc32(chunk_type + body) & 0xFFFFFFFF
        if stored_crc != actual_crc:
            fail("bad CRC in PNG chunk %r" % chunk_type)
        if chunk_type == b"IHDR":
            width, height = struct.unpack(">II", body[:8])
            if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
                fail("image is %dx%d, expected %dx%d"
                     % (width, height, EXPECTED_WIDTH, EXPECTED_HEIGHT))
            saw_ihdr = True
        if chunk_type == b"IEND":
            saw_iend = True
            break
        offset = chunk_end + 4
    if not saw_ihdr:
        fail("PNG has no IHDR chunk")
    if not saw_iend:
        fail("PNG has no IEND chunk")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    if not os.path.isfile(source):
        fail("entry.png not found next to main.py")

    with open(source, "rb") as handle:
        data = handle.read()
    check_png(data)

    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not output_dir:
        fail("MAKEFUN_OUTPUT_DIR is not set")
    os.makedirs(output_dir, exist_ok=True)
    destination = os.path.join(output_dir, "entry.png")
    with open(destination, "wb") as handle:
        handle.write(data)

    digest = hashlib.sha256(data).hexdigest()
    print("Wrote %s (%d bytes, 1024x1024 PNG, sha256 %s)"
          % (destination, len(data), digest))


if __name__ == "__main__":
    main()
