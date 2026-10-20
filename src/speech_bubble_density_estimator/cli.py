from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

from .core import render_markdown, scan
from .review import evaluate, profile_settings, render_html


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Estimate dialogue-density review regions.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--format", choices=("markdown", "json", "html"), default="markdown")
    parser.add_argument("--page-order", choices=("legacy", "lexical", "natural"), default="legacy")
    parser.add_argument("--profile", default="default")
    parser.add_argument("--profiles", type=Path)
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--block-size", type=int)
    parser.add_argument("--margin-percent", type=float)
    parser.add_argument("--art-threshold", type=float)
    parser.add_argument("--dialogue-threshold", type=float)
    parser.add_argument("--smoothing-window", type=int)
    args = parser.parse_args(argv)
    try:
        if args.output and (args.output.exists() or args.output.is_symlink()):
            raise ValueError(f"output already exists: {args.output}")
        settings = profile_settings(
            args.profile,
            json.loads(args.profiles.read_text(encoding="utf-8")) if args.profiles else None,
        )
        for key in (
            "block_size",
            "margin_percent",
            "art_threshold",
            "dialogue_threshold",
            "smoothing_window",
        ):
            if getattr(args, key) is not None:
                settings[key] = getattr(args, key)
        report = scan(
            args.input, page_order=args.page_order, preview=args.format == "html", **settings
        )
        report["profile"] = args.profile
        if args.labels:
            report["evaluation"] = evaluate(
                report, json.loads(args.labels.read_text(encoding="utf-8"))
            )
        rendered = (
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
            if args.format == "json"
            else render_markdown(report)
        )
        if args.format == "html":
            rendered = render_html(report)
        elif args.format == "markdown" and "evaluation" in report:
            rendered += (
                "\n## Local labeled evaluation\n\n```json\n"
                + json.dumps(report["evaluation"], indent=2)
                + "\n```\n"
            )
        if args.output:
            if args.output.exists() or args.output.is_symlink():
                raise ValueError(f"output already exists: {args.output}")
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(rendered)
        else:
            sys.stdout.write(rendered)
    except (OSError, TypeError, ValueError, zipfile.BadZipFile) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0
