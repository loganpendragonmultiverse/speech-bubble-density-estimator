# Speech-Bubble Density Estimator

[![CI](https://github.com/loganpendragonmultiverse/speech-bubble-density-estimator/actions/workflows/ci.yml/badge.svg)](https://github.com/loganpendragonmultiverse/speech-bubble-density-estimator/actions/workflows/ci.yml)

Speech-Bubble Density Estimator scans local page images or a CBZ and measures blocks that combine a predominantly light background with dark high-contrast marks. The resulting review score helps locate pages that may be dialogue-heavy, balanced, or art-heavy without uploading images or running OCR.

## Three-minute start

```bash
python -m pip install .
bubble-density pages/
bubble-density issue.cbz --format json --output density.json
bubble-density issue.cbz --margin-percent 5 --block-size 24 --smoothing-window 5
```

PNG, JPEG, WebP, BMP, TIFF, and GIF pages are supported. Reports include image dimensions, candidate-block counts, density scores, and per-document class totals. CBZ paths, member counts, and uncompressed bytes are limited before decoding.

Version 1.1 adds configurable art/dialogue thresholds, optional page-margin exclusion, median and quartile statistics, ranked art-heavy/dialogue-heavy page lists, and a rolling density value that makes dialogue-heavy stretches easier to review. Use `--art-threshold` and `--dialogue-threshold` to calibrate a specific visual style.

This is a visual heuristic, not speech-bubble detection or accessibility certification. White artwork, captions, sound effects, dark balloons, unusual lettering, low contrast, color choices, and scanned paper can change the score. It does not recognize words, speakers, languages, panels, or reading order. Requires Python 3.10 or newer.

Part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Licensed under the [MIT License](LICENSE).

## Version 1.2.0: reviewed improvements

Add local contact sheets with candidate-block overlays, named calibration profiles and locally labeled evaluation summaries.

```bash
bubble-density ./pages --profile wide-margins --format html --output contact-sheet.html
```

HTML embeds local thumbnails and normalized candidate-block rectangles, showing why white artwork, borders or captions can produce false positives. Built-in profiles are default and wide-margins; --profiles reads a local name-to-settings JSON object and --profile selects one. Explicit CLI settings override profile settings. --labels accepts a page-name-to-class JSON object using art-heavy/balanced/dialogue-heavy, and reports disagreements, error rate and unlabeled counts. This measures agreement with your local labels, not an independent benchmark or actual speech-bubble recognition. No OCR, upload, model training or source-image modification is performed.

## 1.3.0 - 2026-10-16

`bubble-density ./pages --page-order natural --format json` selects reproducible natural filename order. `--page-order lexical` sorts exact relative path strings. Both explicit policies use normalized forward-slash relative paths and produce the same sequence for a directory and CBZ regardless of ZIP insertion order. Natural order compares ASCII digit runs as integers and text with Unicode case folding, then breaks equal keys by the exact original relative path (so `a02` precedes `a2`). Nested paths are included in the comparison. This is filename order, not inferred reading order.

The default `legacy` policy preserves sorted directory paths and ZIP insertion order. Reports identify the selected policy. Ordering affects sequence smoothing and presentation; individual page density and classifications are unchanged. Existing archive path, duplicate, entry-count and uncompressed-size safeguards remain. No OCR or model capabilities were added.
