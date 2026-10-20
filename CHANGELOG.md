# Changelog

## 2.0.0 — 2026-10-20

- Require Python 3.11 or newer and Pillow 13.0.0 or newer (below 14); the fixed dependency no longer supports Python 3.10.
- Retain every existing test/assertion, 90% coverage and all three operating systems; test Python 3.11 and 3.14 in six full native cells.
- Retain prior scanning and report improvements. Old published releases remain unchanged.


## 1.3.1 — 2026-10-20

- Bound per-page input bytes and decoded pixels before full image conversion.
- Validate typed settings before scanning and normalize archive/codec errors.
- Show partial decode evidence in HTML and render literal Markdown filenames/errors.
- Create report files exclusively, preserving linked or concurrent destinations.
- Install documented local profile/label examples alongside all four authority documents.

## 1.3.0 - 2026-10-16

- Added explicit natural and lexical page-order policies with deterministic relative-path tie breaks and directory/CBZ parity.
- Preserved legacy ordering, per-page classification and archive safeguards; identified ordering in all report formats.

## 1.2.0 - 2026-09-07

- Add local contact sheets with candidate-block overlays, named calibration profiles and locally labeled evaluation summaries.
- Added regression coverage for the audited behavior and invalid inputs.

## 1.1.0 - 2026-07-27

- Added configurable block size, margin exclusion, and density thresholds.
- Added median and percentile statistics, ranked page lists, dense-page warnings, and sequence smoothing.
- Preserved the local, no-OCR analysis boundary.

## 1.0.0 - 2026-07-26

- Added local directory and CBZ page scanning.
- Added transparent high-contrast light-region density scores and page classifications.
- Added archive safety limits plus Markdown and JSON reports.
