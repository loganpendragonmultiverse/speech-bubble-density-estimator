from __future__ import annotations

import base64
import html
import io
import lzma
import os
import re
import stat
import statistics
import zipfile
import zlib
from collections import Counter
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import Any

from PIL import Image, UnidentifiedImageError

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
MAX_PAGE_BYTES = 100 * 1024 * 1024
MAX_PIXELS = 40_000_000
MAX_ENTRIES = 5_000
MAX_UNCOMPRESSED = 1024 * 1024 * 1024


def _classify(score: float, art_threshold: float = 0.08, dialogue_threshold: float = 0.22) -> str:
    if score < art_threshold:
        return "art-heavy"
    if score < dialogue_threshold:
        return "balanced"
    return "dialogue-heavy"


def _validate_settings(
    block_size: int | None, margin_percent: float, art_threshold: float, dialogue_threshold: float
) -> None:
    if block_size is not None and (type(block_size) is not int or block_size < 8):
        raise ValueError("block size must be an integer of at least 8 pixels")
    if (
        isinstance(margin_percent, bool)
        or not isinstance(margin_percent, (int, float))
        or not 0 <= margin_percent < 40
    ):
        raise ValueError("margin percent must be a finite number between 0 and 40")
    if (
        any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            for value in (art_threshold, dialogue_threshold)
        )
        or not 0 <= art_threshold < dialogue_threshold <= 1
    ):
        raise ValueError("thresholds must satisfy finite numbers 0 <= art < dialogue <= 1")


def analyze_image(
    name: str,
    content: bytes,
    *,
    block_size: int | None = None,
    margin_percent: float = 0,
    art_threshold: float = 0.08,
    dialogue_threshold: float = 0.22,
    preview: bool = False,
) -> dict[str, Any]:
    _validate_settings(block_size, margin_percent, art_threshold, dialogue_threshold)
    if len(content) > MAX_PAGE_BYTES:
        raise ValueError("image exceeds the 100 MiB input limit")
    with Image.open(io.BytesIO(content)) as source:
        if source.width * source.height > MAX_PIXELS:
            raise ValueError("image exceeds the 40 million pixel limit")
        image = source.convert("L")
        image.thumbnail((1600, 1600))
        width, height = image.size
        full_width, full_height = width, height
        if width < 8 or height < 8:
            raise ValueError(f"image is too small to analyze: {name}")
        margin_x = round(width * margin_percent / 100)
        margin_y = round(height * margin_percent / 100)
        image = image.crop((margin_x, margin_y, width - margin_x, height - margin_y))
        width, height = image.size
        block = block_size or max(8, min(width, height) // 20)
        candidates = 0
        regions = []
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
                    regions.append(
                        [
                            (left + margin_x) / full_width,
                            (top + margin_y) / full_height,
                            min(block, width - left) / full_width,
                            min(block, height - top) / full_height,
                        ]
                    )
        score = round(candidates / total if total else 0, 4)
        result = {
            "name": name,
            "width": source.width,
            "height": source.height,
            "candidate_blocks": candidates,
            "total_blocks": total,
            "density": score,
            "classification": _classify(score, art_threshold, dialogue_threshold),
            "candidate_regions": regions,
        }
        if preview:
            thumbnail = source.convert("RGB")
            thumbnail.thumbnail((360, 500))
            output = io.BytesIO()
            thumbnail.save(output, format="JPEG", quality=80)
            result["thumbnail"] = base64.b64encode(output.getvalue()).decode("ascii")
        return result


def _page_key(name: str, policy: str) -> tuple[Any, ...]:
    if policy == "lexical":
        return (name,)
    parts = tuple(
        (1, int(part)) if part.isascii() and part.isdigit() else (0, part.casefold())
        for part in re.split(r"([0-9]+)", name)
    )
    return (parts, name)


def _directory_pages(path: Path, policy: str = "legacy") -> Iterable[tuple[str, bytes]]:
    def failed(error: OSError) -> None:
        raise ValueError(f"Cannot read image directory: {error}") from error

    entries = [
        Path(directory) / name
        for directory, _dirs, files in os.walk(path, onerror=failed)
        for name in files
    ]
    ordered = (
        sorted(entries)
        if policy == "legacy"
        else sorted(entries, key=lambda page: _page_key(page.relative_to(path).as_posix(), policy))
    )
    for page in ordered:
        if page.suffix.casefold() in EXTENSIONS:
            metadata = page.lstat()
            if not stat.S_ISREG(metadata.st_mode):
                continue
            if metadata.st_size > MAX_PAGE_BYTES:
                raise ValueError(f"image exceeds the 100 MiB input limit: {page.name}")
            with page.open("rb") as handle:
                content = handle.read(MAX_PAGE_BYTES + 1)
            if len(content) > MAX_PAGE_BYTES:
                raise ValueError(f"image exceeds the 100 MiB input limit: {page.name}")
            yield page.relative_to(path).as_posix(), content


def _archive_pages(path: Path, policy: str = "legacy") -> Iterable[tuple[str, bytes]]:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ENTRIES:
                raise ValueError("archive exceeds the entry limit")
            if sum(info.file_size for info in infos) > MAX_UNCOMPRESSED:
                raise ValueError("archive exceeds the uncompressed-size limit")
            if policy != "legacy":
                infos.sort(
                    key=lambda info: _page_key(
                        PurePosixPath(info.filename.replace(chr(92), "/")).as_posix(), policy
                    )
                )
            seen: set[str] = set()
            for info in infos:
                member = PurePosixPath(info.filename.replace(chr(92), "/"))
                if (
                    member.is_absolute()
                    or ".." in member.parts
                    or re.match(r"^[A-Za-z]:", member.as_posix())
                ):
                    raise ValueError(f"unsafe archive member path: {info.filename}")
                key = member.as_posix().casefold()
                if key in seen:
                    raise ValueError(f"duplicate archive member path: {info.filename}")
                seen.add(key)
                if not info.is_dir() and member.suffix.casefold() in EXTENSIONS:
                    if info.file_size > MAX_PAGE_BYTES:
                        raise ValueError(f"image exceeds the 100 MiB input limit: {info.filename}")
                    with archive.open(info) as handle:
                        content = handle.read(MAX_PAGE_BYTES + 1)
                    if len(content) > MAX_PAGE_BYTES:
                        raise ValueError(f"image exceeds the 100 MiB input limit: {info.filename}")
                    yield member.as_posix(), content
    except (
        OSError,
        EOFError,
        RuntimeError,
        NotImplementedError,
        UnicodeError,
        zipfile.BadZipFile,
        zlib.error,
        lzma.LZMAError,
    ) as exc:
        raise ValueError(f"Cannot decode CBZ/ZIP archive: {exc}") from exc


def scan(
    path: Path,
    *,
    block_size: int | None = None,
    margin_percent: float = 0,
    art_threshold: float = 0.08,
    dialogue_threshold: float = 0.22,
    smoothing_window: int = 3,
    page_order: str = "legacy",
    preview: bool = False,
) -> dict[str, Any]:
    if page_order not in {"legacy", "lexical", "natural"}:
        raise ValueError("page order must be legacy, lexical, or natural")
    _validate_settings(block_size, margin_percent, art_threshold, dialogue_threshold)
    if type(smoothing_window) is not int or smoothing_window < 1:
        raise ValueError("smoothing window must be positive")
    if path.is_dir():
        pages = _directory_pages(path, page_order)
        source_type = "directory"
    elif path.is_file() and path.suffix.casefold() in {".cbz", ".zip"}:
        pages = _archive_pages(path, page_order)
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
                    preview=preview,
                )
            )
        except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
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
            "page_order": page_order,
        },
        "pages": results,
        "errors": errors,
    }


def _literal(value: str) -> str:
    return (
        html.escape(value, quote=False)
        .replace("|", "&#124;")
        .replace(chr(96), "&#96;")
        .replace(chr(13), "&#13;")
        .replace(chr(10), "&#10;")
    )


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Speech-Bubble Density Estimate",
        "",
        f"Pages analyzed: **{report['page_count']}** · Decode errors: **{report['error_count']}**",
        "",
        f"Page order: **{report['settings']['page_order']}**",
        "",
        f"Median density: **{report['statistics']['median_density']:.1%}**",
        "",
        "| Page | Density | Smoothed | Review class |",
        "|---|---:|---:|---|",
    ]
    lines.extend(
        f"| {_literal(page['name'])} | {page['density']:.1%} | {page['smoothed_density']:.1%} | {page['classification']} |"
        for page in report["pages"]
    )
    if report["errors"]:
        lines.extend(["", "## Decode errors", ""])
        lines.extend(
            f"- {_literal(item['name'])} — {_literal(item['error'])}" for item in report["errors"]
        )
    return "\n".join(lines).rstrip() + "\n"
