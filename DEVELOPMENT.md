# Development

Install with `python -m pip install -e ".[dev]"`, then run `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`, and `python -m build`.

Release metadata must be reconciled in `pyproject.toml`, the package `__version__`, `CHANGELOG.md`, the GitHub release, and the Logan Pendragon Forge catalog for every versioned release.

## 1.2.0 improvement session

Add local contact sheets with candidate-block overlays, named calibration profiles and locally labeled evaluation summaries.

HTML embeds local thumbnails and normalized candidate-block rectangles, showing why white artwork, borders or captions can produce false positives. Built-in profiles are default and wide-margins; --profiles reads a local name-to-settings JSON object and --profile selects one. Explicit CLI settings override profile settings. --labels accepts a page-name-to-class JSON object using art-heavy/balanced/dialogue-heavy, and reports disagreements, error rate and unlabeled counts. This measures agreement with your local labels, not an independent benchmark or actual speech-bubble recognition. No OCR, upload, model training or source-image modification is performed.

Local formatting, lint, strict types and regression tests pass. Public release completion requires the protected CI/CodeQL matrix, tagged artifacts and matching Forge catalog/detail deployment.

## 1.3.0 - 2026-10-16

Run `python -m pip install -e ".[dev]"`, `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`, and `python -m build`. Keep regression fixtures synthetic and source inputs unchanged. `tests/test_feature_wave.py` covers the new behavior, malformed inputs and compatibility defaults. Verify README and CHANGELOG in wheel metadata/documentation and in the source archive before release. Protected cross-platform CI and CodeQL remain required; draft PR preparation does not authorize a merge or release.
