"""Contact sheets and local, author-labeled calibration review."""

from __future__ import annotations

import html
import json
import math
from typing import Any

PROFILES = {
    "default": {
        "art_threshold": 0.08,
        "dialogue_threshold": 0.22,
        "margin_percent": 0,
        "smoothing_window": 3,
    },
    "wide-margins": {
        "art_threshold": 0.08,
        "dialogue_threshold": 0.22,
        "margin_percent": 10,
        "smoothing_window": 3,
    },
}
SETTINGS = {
    "art_threshold",
    "dialogue_threshold",
    "margin_percent",
    "smoothing_window",
    "block_size",
}
CLASSES = {"art-heavy", "balanced", "dialogue-heavy"}


def profile_settings(name: str, payload: Any = None) -> dict[str, Any]:
    profiles = PROFILES if payload is None else payload
    if (
        not isinstance(profiles, dict)
        or name not in profiles
        or not isinstance(profiles[name], dict)
    ):
        raise ValueError("Profile file must map the selected profile name to settings")
    settings = profiles[name]
    if set(settings) - SETTINGS:
        raise ValueError("Unknown calibration profile setting")
    for key, value in settings.items():
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(f"Profile {key} must be a finite number")
        if (
            key in ("block_size", "smoothing_window")
            and value is not None
            and not isinstance(value, int)
        ):
            raise TypeError(f"Profile {key} must be an integer")
    return dict(settings)


def evaluate(report: dict[str, Any], labels: Any) -> dict[str, Any]:
    if not isinstance(labels, dict):
        raise TypeError("Labels must map page names to authored class labels")
    known = {p["name"]: p for p in report["pages"]}
    if set(labels) - known.keys():
        raise ValueError("Labels reference pages absent from this scan")
    comparisons = []
    for name, expected in sorted(labels.items()):
        if not isinstance(expected, str) or expected not in CLASSES:
            raise ValueError("Labels must be art-heavy, balanced or dialogue-heavy")
        predicted = known[name]["classification"]
        comparisons.append(
            {
                "page": name,
                "expected": expected,
                "predicted": predicted,
                "matches": expected == predicted,
            }
        )
    mismatches = [row for row in comparisons if not row["matches"]]
    return {
        "labeled_pages": len(comparisons),
        "unlabeled_pages": len(known) - len(comparisons),
        "mismatches": mismatches,
        "error_rate": len(mismatches) / len(comparisons) if comparisons else None,
        "comparisons": comparisons,
        "note": "Agreement with your local labels, not proof of speech-bubble recognition or an independent benchmark",
    }


def render_html(report: dict[str, Any]) -> str:
    parts = [
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Density contact sheet</title>',
        "<style>body{font:17px system-ui;max-width:1150px;margin:auto;padding:22px;background:#f5f1e8;color:#203442}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:20px}article{background:white;padding:16px;border:1px solid #abc;border-radius:12px;overflow-wrap:anywhere}.page{position:relative}.page img{width:100%;display:block}.page svg{position:absolute;inset:0;width:100%;height:100%}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>",
        "<h1>Density contact sheet</h1><p>Red rectangles mark light/dark candidate blocks. White artwork and captions can produce false positives; this is a density heuristic.</p>",
        "<p>Profile: " + html.escape(report.get("profile", "explicit settings")) + "</p>",
    ]
    if "evaluation" in report:
        parts.append(
            "<h2>Local labeled evaluation</h2><pre>"
            + html.escape(json.dumps(report["evaluation"], indent=2))
            + "</pre>"
        )
    parts.append('<main class="grid">')
    for index, page in enumerate(report["pages"]):
        parts.append(
            f'<article id="page-{index}"><h2><a href="#page-{index}">{html.escape(page["name"])}</a></h2><p>{page["classification"]} · density {page["density"]}</p><div class="page">'
        )
        if page.get("thumbnail"):
            parts.append(
                f'<img alt="Local page preview" src="data:image/jpeg;base64,{page["thumbnail"]}"><svg viewBox="0 0 1 1" preserveAspectRatio="none" aria-label="Candidate block overlay">'
            )
            for x, y, width, height in page["candidate_regions"]:
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="none" stroke="red" stroke-width="0.004"/>'
                )
            parts.append("</svg>")
        parts.append(
            "</div><p>"
            + str(page["candidate_blocks"])
            + " candidate blocks; review manually.</p></article>"
        )
    parts.append("</main></html>")
    return "\n".join(parts)
