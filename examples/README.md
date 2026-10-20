# Local review examples

Use synthetic images or page images you own. No comic pages are bundled.

Run bubble-density pages/ --page-order natural --profiles examples/profiles.json
--profile review --format html --output contact-sheet.html on one line. The
profile demonstrates explicit block, margin, threshold and smoothing settings.
These values are illustrative defaults, not an accuracy calibration.

The labels.json file demonstrates manually authored classes for page2.png and
page10.png. Replace its names and classes with your own assessments before using
--labels examples/labels.json. Names must exactly match relative scan paths;
unknown names are rejected. Disagreement with these illustrative labels is not
an independent benchmark or a recognition score.

Both release packages install these files with the four authority documents under
share/doc/speech-bubble-density-estimator in the installation prefix.
