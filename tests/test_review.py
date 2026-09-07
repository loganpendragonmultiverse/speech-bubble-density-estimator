import io
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from speech_bubble_density_estimator.cli import main
from speech_bubble_density_estimator.core import analyze_image
from speech_bubble_density_estimator.review import evaluate, profile_settings, render_html


def page_bytes() -> bytes:
    image = Image.new("RGB", (80, 80), "white")
    draw = ImageDraw.Draw(image)
    for y in range(0, 80, 8):
        for x in range(0, 80, 8):
            draw.rectangle((x, y, x + 1, y + 1), fill="black")
    out = io.BytesIO()
    image.save(out, "PNG")
    return out.getvalue()


def test_candidate_regions_and_local_evaluation(tmp_path: Path) -> None:
    image = page_bytes()
    page = analyze_image("page.png", image, block_size=8, margin_percent=10, preview=True)
    assert page["candidate_blocks"] == len(page["candidate_regions"])
    assert page["candidate_regions"]
    assert all(0 <= x <= 1 for rect in page["candidate_regions"] for x in rect)
    assert page["candidate_regions"][0][0] == 0.1
    assert page["thumbnail"]
    report = {"pages": [page]}
    review = evaluate(report, {"page.png": "art-heavy"})
    assert review["error_rate"] == 1
    assert evaluate(report, {})["error_rate"] is None
    assert "<rect" in render_html({**report, "evaluation": review})
    folder = tmp_path / "pages"
    folder.mkdir()
    (folder / "page.png").write_bytes(image)
    profiles = tmp_path / "profiles.json"
    profiles.write_text('{"mine":{"block_size":8,"margin_percent":10}}', encoding="utf-8")
    labels = tmp_path / "labels.json"
    labels.write_text('{"page.png":"art-heavy"}', encoding="utf-8")
    for fmt in ("html", "json", "markdown"):
        output = tmp_path / (fmt + ".out")
        assert (
            main(
                [
                    str(folder),
                    "--profile",
                    "mine",
                    "--profiles",
                    str(profiles),
                    "--labels",
                    str(labels),
                    "--format",
                    fmt,
                    "--output",
                    str(output),
                    "--block-size",
                    "8",
                ]
            )
            == 0
        )
        assert "evaluation" in output.read_text(encoding="utf-8").lower()
    assert (folder / "page.png").read_bytes() == image


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"test": []},
        {"test": {"unknown": 1}},
        {"test": {"block_size": 8.5}},
        {"test": {"margin_percent": float("nan")}},
    ],
)
def test_invalid_profiles(payload: object) -> None:
    with pytest.raises((ValueError, TypeError)):
        profile_settings("test", payload)


@pytest.mark.parametrize("labels", [[], {"missing": "balanced"}, {"page.png": "not-a-class"}])
def test_invalid_labels(labels: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        evaluate({"pages": [{"name": "page.png", "classification": "balanced"}]}, labels)
