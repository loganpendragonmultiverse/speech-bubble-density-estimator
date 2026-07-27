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
