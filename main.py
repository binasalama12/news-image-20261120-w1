#!/usr/bin/env python3
"""Publisher for "Atlas Fidelity - one-day front page, Friday 20 November 2026".

The artwork was rendered ahead of time and is stored in this repository
as entry.png. This program is the entrypoint the grader runs: it relies
only on the Python standard library, verifies the bundled image, and
copies it into the output directory.
"""

import os
import shutil
import sys
from pathlib import Path

TITLE = "Atlas Fidelity - one-day front page, Friday 20 November 2026"
IMAGE_NAME = "entry.png"
MAX_BYTES = 1048576  # competition limit: 1 MiB
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"


def find_source() -> Path:
    """Return the path of the artwork bundled next to this script."""
    return Path(__file__).resolve().parent / IMAGE_NAME


def check_image(path: Path) -> int:
    """Validate the bundled image and return its size in bytes."""
    if not path.is_file():
        raise SystemExit(f"bundled artwork not found: {path}")
    size = path.stat().st_size
    if size > MAX_BYTES:
        raise SystemExit(f"artwork too large: {size} bytes (limit {MAX_BYTES})")
    with path.open("rb") as handle:
        head = handle.read(len(PNG_MAGIC))
    if head != PNG_MAGIC and not head.startswith(JPEG_MAGIC):
        raise SystemExit("artwork is neither a PNG nor a JPEG image")
    return size


def publish(source: Path) -> Path:
    """Copy the artwork into the output directory and return its path."""
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / IMAGE_NAME
    shutil.copyfile(source, target)
    return target


def main() -> int:
    source = find_source()
    size = check_image(source)
    target = publish(source)
    print(TITLE)
    print(f"published artwork to {target} ({size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
