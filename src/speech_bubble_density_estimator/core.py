from __future__ import annotations

import io
import zipfile
from collections import Counter
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import Any

from PIL import Image, UnidentifiedImageError

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
MAX_ENTRIES = 5_000
MAX_UNCOMPRESSED = 1024 * 1024 * 1024


def _classify(score: float) -> str:
    if score < 0.08:
        return "art-heavy"
    if score < 0.22:
        return "balanced"
    return "dialogue-heavy"


def analyze_image(name: str, content: bytes) -> dict[str, Any]:
    with Image.open(io.BytesIO(content)) as source:
        image = source.convert("L")
        image.thumbnail((1600, 1600))
        width, height = image.size
        if width < 8 or height < 8:
            raise ValueError(f"image is too small to analyze: {name}")
        block = max(8, min(width, height) // 20)
        candidates = 0
        total = 0
        for top in range(0, height, block):
            for left in range(0, width, block):
                crop = image.crop((left, top, min(left + block, width), min(top + block, height)))
                values = list(crop.tobytes())
                if not values:
                    continue
                total += 1
                light = sum(value >= 220 for value in values) / len(values)
                dark = sum(value <= 80 for value in values) / len(values)
                if light >= 0.55 and dark >= 0.03:
                    candidates += 1
        score = round(candidates / total if total else 0, 4)
        return {
            "name": name,
            "width": source.width,
            "height": source.height,
            "candidate_blocks": candidates,
            "total_blocks": total,
            "density": score,
            "classification": _classify(score),
        }


def _directory_pages(path: Path) -> Iterable[tuple[str, bytes]]:
    for page in sorted(path.rglob("*")):
        if page.is_file() and not page.is_symlink() and page.suffix.casefold() in EXTENSIONS:
            yield page.relative_to(path).as_posix(), page.read_bytes()


def _archive_pages(path: Path) -> Iterable[tuple[str, bytes]]:
    with zipfile.ZipFile(path, "r") as archive:
        infos = archive.infolist()
        if len(infos) > MAX_ENTRIES:
            raise ValueError("archive exceeds the entry limit")
        if sum(info.file_size for info in infos) > MAX_UNCOMPRESSED:
            raise ValueError("archive exceeds the uncompressed-size limit")
        seen: set[str] = set()
        for info in infos:
            member = PurePosixPath(info.filename.replace("\\", "/"))
            if member.is_absolute() or ".." in member.parts:
                raise ValueError(f"unsafe archive member path: {info.filename}")
            key = member.as_posix().casefold()
            if key in seen:
                raise ValueError(f"duplicate archive member path: {info.filename}")
            seen.add(key)
            if not info.is_dir() and member.suffix.casefold() in EXTENSIONS:
                yield member.as_posix(), archive.read(info)


def scan(path: Path) -> dict[str, Any]:
    if path.is_dir():
        pages = _directory_pages(path)
        source_type = "directory"
    elif path.is_file() and path.suffix.casefold() in {".cbz", ".zip"}:
        pages = _archive_pages(path)
        source_type = "cbz"
    else:
        raise ValueError("input must be an image directory or CBZ/ZIP archive")
    results = []
    errors = []
    for name, content in pages:
        try:
            results.append(analyze_image(name, content))
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            errors.append({"name": name, "error": str(exc)})
    if not results:
        raise ValueError("no decodable supported page images found")
    counts = Counter(page["classification"] for page in results)
    return {
        "version": 1,
        "source": str(path.resolve()),
        "source_type": source_type,
        "page_count": len(results),
        "error_count": len(errors),
        "classification_counts": dict(sorted(counts.items())),
        "pages": results,
        "errors": errors,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Speech-Bubble Density Estimate",
        "",
        f"Pages analyzed: **{report['page_count']}** · Decode errors: **{report['error_count']}**",
        "",
        "| Page | Density | Review class |",
        "|---|---:|---|",
    ]
    lines.extend(
        f"| `{page['name']}` | {page['density']:.1%} | {page['classification']} |"
        for page in report["pages"]
    )
    if report["errors"]:
        lines.extend(["", "## Decode errors", ""])
        lines.extend(f"- `{item['name']}` — {item['error']}" for item in report["errors"])
    return "\n".join(lines).rstrip() + "\n"
