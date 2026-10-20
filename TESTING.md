# Testing

Run `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`, and `python -m build`. CI also audits dependencies and runs the supported OS/Python matrix.

## 1.2.0 regression acceptance

Run the complete existing suite plus the new regression fixtures. Confirm the documented command produces the selected output, malformed input remains actionable, and source files remain unchanged. Add local contact sheets with candidate-block overlays, named calibration profiles and locally labeled evaluation summaries.

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

Release acceptance runs all tests against separate fresh wheel and source-package
installs outside the checkout with verified import provenance and exact installed
README/DEVELOPMENT/TESTING/CHANGELOG bytes. Exercise real directory and CBZ
JSON/Markdown/HTML commands, natural ordering, local labels/profiles, partial
decode evidence, source preservation and no-overwrite behavior. Review HTML on
desktop and narrow screens. Repeat against successful exact tag-workflow assets.

Both packages install the four authority documents plus examples/README.md, profiles.json and illustrative labels.json under share/doc/speech-bubble-density-estimator. Adapt the labels to your own page names and manual assessments.

Supported image metadata is inspected explicitly; inaccessible entries refuse the scan rather than silently producing a completed subset. Browser acceptance includes long unbroken decode-error names at desktop and narrow widths.
