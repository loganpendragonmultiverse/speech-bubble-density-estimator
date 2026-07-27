# Development

Install with `python -m pip install -e ".[dev]"`, then run `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`, and `python -m build`.

Release metadata must be reconciled in `pyproject.toml`, the package `__version__`, `CHANGELOG.md`, the GitHub release, and the Logan Pendragon Forge catalog for every versioned release.
