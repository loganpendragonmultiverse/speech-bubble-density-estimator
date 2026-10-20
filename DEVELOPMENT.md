# Development

Install with `python -m pip install -e ".[dev]"`, then run `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`, and `python -m build`.

Release metadata must be reconciled in `pyproject.toml`, the package `__version__`, `CHANGELOG.md`, the GitHub release, and the Logan Pendragon Forge catalog for every versioned release.

## 1.2.0 improvement session

Add local contact sheets with candidate-block overlays, named calibration profiles and locally labeled evaluation summaries.

HTML embeds local thumbnails and normalized candidate-block rectangles, showing why white artwork, borders or captions can produce false positives. Built-in profiles are default and wide-margins; --profiles reads a local name-to-settings JSON object and --profile selects one. Explicit CLI settings override profile settings. --labels accepts a page-name-to-class JSON object using art-heavy/balanced/dialogue-heavy, and reports disagreements, error rate and unlabeled counts. This measures agreement with your local labels, not an independent benchmark or actual speech-bubble recognition. No OCR, upload, model training or source-image modification is performed.

Local formatting, lint, strict types and regression tests pass. Public release completion requires the protected CI/CodeQL matrix, tagged artifacts and matching Forge catalog/detail deployment.

## 1.3.0 - 2026-10-16

Run `python -m pip install -e ".[dev]"`, `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`, and `python -m build`. Keep regression fixtures synthetic and source inputs unchanged. `tests/test_feature_wave.py` covers the new behavior, malformed inputs and compatibility defaults. Verify README and CHANGELOG in wheel metadata/documentation and in the source archive before release. Protected cross-platform CI and CodeQL remain required; draft PR preparation does not authorize a merge or release.

## 1.3.1 bounded and reviewable analysis

Each page is limited to 100 MiB of compressed/input bytes and 40 million decoded
pixels, checked before full image conversion. Existing 5,000-entry and 1 GiB
declared expanded-CBZ limits remain. Oversized page input refuses the scan;
oversized pixel dimensions or unreadable images become page errors when other
pages can be analyzed. HTML displays decode errors prominently so partial
analysis cannot look complete. Limits bound common allocations, not ZIP metadata
CPU use or every image codec's internal allocation.

Block size and smoothing are integer controls, excluding booleans; margins and
thresholds must be finite numbers in the documented ranges. Settings are checked
before scanning even an empty folder. Malformed ZIP headers, unsupported codecs,
encryption and directory traversal errors produce actionable errors.

Report creation is exclusive and refuses existing files or symbolic links,
including dangling links. A report created by another process during analysis is
preserved. This handles accidental collisions, not a hostile concurrent filesystem.
Keep source files stable during analysis. Filenames and decode errors remain
literal evidence in Markdown tables and HTML.

The product remains a local contrast heuristic. There is no OCR, semantic
speech recognition, remote upload or new accuracy benchmark.

Both packages install the four authority documents plus examples/README.md, profiles.json and illustrative labels.json under share/doc/speech-bubble-density-estimator. Adapt the labels to your own page names and manual assessments.

Supported image metadata is inspected explicitly; inaccessible entries refuse the scan rather than silently producing a completed subset. Browser acceptance includes long unbroken decode-error names at desktop and narrow widths.

## 2.0.0 compatibility change

Python 3.11 or newer is required. Pillow 13.0.0 supplies the upstream security
fixes and no longer supports Python 3.10; this project requires Pillow>=13.0.0,<14
for image processing. Python 3.10 users must upgrade their interpreter before
installing this supported release. Previous published releases remain unchanged
and are not represented as receiving these dependency fixes.

The six full native CI cells use Ubuntu, Windows and macOS with Python 3.11 and
3.14. All existing tests/assertions and the 90% coverage threshold remain, along
with formatting, lint, strict typing, dependency audit, builds and CodeQL.
No test skips, advisory waivers or repurposed Python 3.10 job names are introduced.
