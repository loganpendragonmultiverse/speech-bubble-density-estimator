from __future__ import annotations

import io
import statistics
import zipfile
from collections import Counter
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import Any

from PIL import Image, UnidentifiedImageError

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
MAX_ENTRIES = 5_000
MAX_UNCOMPRESSED = 1024 * 1024 * 1024


def _classify(score: float, art_threshold: float = 0.08, dialogue_threshold: float = 0.22) -> str:
    if score < art_threshold:
        return "art-heavy"
    if score < dialogue_threshold:
        return "balanced"
    return "dialogue-heavy"


def analyze_image(
    name: str,
    content: bytes,
    *,
    block_size: int | None = None,
    margin_percent: float = 0,
    art_threshold: float = 0.08,
    dialogue_threshold: float = 0.22,
) -> dict[str, Any]:
    if block_size is not None and block_size < 8:
        raise ValueError("block size must be at least 8 pixels")
    if not 0 <= margin_percent < 40:
        raise ValueError("margin percent must be between 0 and 40")
    if not 0 <= art_threshold < dialogue_threshold <= 1:
        raise ValueError("thresholds must satisfy 0 <= art < dialogue <= 1")
    with Image.open(io.BytesIO(content)) as source:
        image = source.convert("L")
        image.thumbnail((1600, 1600))
        width, height = image.size
        if width < 8 or height < 8:
            raise ValueError(f"image is too small to analyze: {name}")
        margin_x = round(width * margin_percent / 100)
        margin_y = round(height * margin_percent / 100)
        image = image.crop((margin_x, margin_y, width - margin_x, height - margin_y))
        width, height = image.size
        block = block_size or max(8, min(width, height) // 20)
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
            "classification": _classify(score, art_threshold, dialogue_threshold),
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


def scan(
    path: Path,
    *,
    block_size: int | None = None,
    margin_percent: float = 0,
    art_threshold: float = 0.08,
    dialogue_threshold: float = 0.22,
    smoothing_window: int = 3,
) -> dict[str, Any]:
    if smoothing_window < 1:
        raise ValueError("smoothing window must be positive")
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
            results.append(
                analyze_image(
                    name,
                    content,
                    block_size=block_size,
                    margin_percent=margin_percent,
                    art_threshold=art_threshold,
                    dialogue_threshold=dialogue_threshold,
                )
            )
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            errors.append({"name": name, "error": str(exc)})
    if not results:
        raise ValueError("no decodable supported page images found")
    counts = Counter(page["classification"] for page in results)
    densities = [float(page["density"]) for page in results]
    for index, page in enumerate(results):
        start = max(0, index - smoothing_window // 2)
        end = min(len(results), start + smoothing_window)
        start = max(0, end - smoothing_window)
        page["smoothed_density"] = round(statistics.fmean(densities[start:end]), 4)
    ranked = sorted(results, key=lambda page: (-page["density"], page["name"]))
    ordered = sorted(densities)

    def percentile(fraction: float) -> float:
        return ordered[round((len(ordered) - 1) * fraction)]

    return {
        "version": 2,
        "source": str(path.resolve()),
        "source_type": source_type,
        "page_count": len(results),
        "error_count": len(errors),
        "classification_counts": dict(sorted(counts.items())),
        "statistics": {
            "median_density": round(statistics.median(densities), 4),
            "p25_density": percentile(0.25),
            "p75_density": percentile(0.75),
        },
        "dialogue_heavy_pages": [
            page["name"] for page in ranked if page["classification"] == "dialogue-heavy"
        ],
        "most_dialogue_heavy": [page["name"] for page in ranked[:5]],
        "most_art_heavy": [page["name"] for page in reversed(ranked[-5:])],
        "settings": {
            "block_size": block_size,
            "margin_percent": margin_percent,
            "art_threshold": art_threshold,
            "dialogue_threshold": dialogue_threshold,
            "smoothing_window": smoothing_window,
        },
        "pages": results,
        "errors": errors,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Speech-Bubble Density Estimate",
        "",
        f"Pages analyzed: **{report['page_count']}** · Decode errors: **{report['error_count']}**",
        "",
        f"Median density: **{report['statistics']['median_density']:.1%}**",
        "",
        "| Page | Density | Smoothed | Review class |",
        "|---|---:|---:|---|",
    ]
    lines.extend(
        f"| `{page['name']}` | {page['density']:.1%} | {page['smoothed_density']:.1%} | {page['classification']} |"
        for page in report["pages"]
    )
    if report["errors"]:
        lines.extend(["", "## Decode errors", ""])
        lines.extend(f"- `{item['name']}` — {item['error']}" for item in report["errors"])
    return "\n".join(lines).rstrip() + "\n"
