import io
import json
import zipfile
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from speech_bubble_density_estimator.cli import main
from speech_bubble_density_estimator.core import analyze_image, render_markdown, scan


def image_bytes(dialogue: bool = True) -> bytes:
    image = Image.new("L", (200, 200), 40 if not dialogue else 255)
    if dialogue:
        draw = ImageDraw.Draw(image)
        for y in range(15, 190, 16):
            draw.rectangle((10, y, 190, y + 5), fill=0)
    output = io.BytesIO()
    image.save(output, "PNG")
    return output.getvalue()


def test_analysis_classes() -> None:
    dialogue = analyze_image("dialogue.png", image_bytes())
    art = analyze_image("art.png", image_bytes(False))
    assert dialogue["density"] > art["density"]
    assert dialogue["classification"] == "dialogue-heavy"
    assert art["classification"] == "art-heavy"
    with pytest.raises(ValueError, match="too small"):
        tiny = io.BytesIO()
        Image.new("L", (4, 4), 255).save(tiny, "PNG")
        analyze_image("tiny.png", tiny.getvalue())


def test_directory_and_archive_scan(tmp_path: Path) -> None:
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "001.png").write_bytes(image_bytes())
    (pages / "bad.jpg").write_bytes(b"not-image")
    report = scan(pages)
    assert report["page_count"] == 1
    assert report["error_count"] == 1
    assert "Decode errors" in render_markdown(report)
    archive = tmp_path / "issue.cbz"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("001.png", image_bytes(False))
    assert scan(archive)["source_type"] == "cbz"


def test_validation(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="directory or CBZ"):
        scan(tmp_path / "missing")
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="no decodable"):
        scan(empty)
    unsafe = tmp_path / "unsafe.cbz"
    with zipfile.ZipFile(unsafe, "w") as handle:
        handle.writestr("../001.png", image_bytes())
    with pytest.raises(ValueError, match="unsafe"):
        scan(unsafe)


def test_cli_json_and_safe_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "001.png").write_bytes(image_bytes())
    assert main([str(pages), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["page_count"] == 1
    output = tmp_path / "report.md"
    assert main([str(pages), "--output", str(output)]) == 0
    assert main([str(pages), "--output", str(output)]) == 2
