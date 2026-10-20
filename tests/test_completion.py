import io
import json
import lzma
import zlib
from pathlib import Path
from zipfile import ZipFile, ZipInfo

import pytest
from PIL import Image

from speech_bubble_density_estimator import core, review
from speech_bubble_density_estimator.cli import main


def png(size=(16, 16)):
    stream = io.BytesIO()
    Image.new("RGB", size, "white").save(stream, format="PNG")
    return stream.getvalue()


@pytest.mark.parametrize(
    "settings,pattern",
    [
        ({"block_size": True}, "block"),
        ({"block_size": 8.5}, "block"),
        ({"smoothing_window": True}, "smoothing"),
        ({"smoothing_window": 1.5}, "smoothing"),
        ({"smoothing_window": None}, "smoothing"),
        ({"margin_percent": None}, "margin"),
        ({"margin_percent": True}, "margin"),
        ({"margin_percent": float("nan")}, "margin"),
        ({"margin_percent": 10**400}, "margin"),
        ({"art_threshold": None}, "threshold"),
        ({"art_threshold": True}, "threshold"),
        ({"dialogue_threshold": float("inf")}, "threshold"),
    ],
    ids=[
        "bool-block",
        "fraction-block",
        "bool-window",
        "fraction-window",
        "null-window",
        "null-margin",
        "bool-margin",
        "nan-margin",
        "huge-margin",
        "null-art",
        "bool-art",
        "inf-dialogue",
    ],
)
def test_settings_checked_before_empty_scan(tmp_path, settings, pattern):
    with pytest.raises((ValueError, TypeError), match=pattern):
        core.scan(tmp_path, **settings)


def test_huge_profile_integer_is_actionable(tmp_path, capsys):
    profile = tmp_path / "profiles.json"
    profile.write_text(json.dumps({"huge": {"smoothing_window": 10**400}}))
    assert main([str(tmp_path), "--profiles", str(profile), "--profile", "huge"]) == 2
    assert "finite" in capsys.readouterr().err


def test_actual_pixel_limit_precedes_full_conversion(monkeypatch):
    stream = io.BytesIO()
    Image.new("1", (6400, 6400)).save(stream, format="PNG")

    def forbidden(*args, **kwargs):
        raise AssertionError("oversized image must not convert")

    monkeypatch.setattr(Image.Image, "convert", forbidden)
    with pytest.raises(ValueError, match="pixel limit"):
        core.analyze_image("large.png", stream.getvalue())


@pytest.mark.parametrize("kind", ["directory", "archive", "direct"])
def test_page_input_limit(tmp_path, monkeypatch, kind):
    content = png()
    monkeypatch.setattr(core, "MAX_PAGE_BYTES", 10)
    if kind == "direct":
        with pytest.raises(ValueError, match="input limit"):
            core.analyze_image("large.png", content)
    else:
        target = tmp_path
        if kind == "directory":
            (target / "page.png").write_bytes(content)
        else:
            target = tmp_path / "input.cbz"
            with ZipFile(target, "w") as archive:
                archive.writestr("page.png", content)
        with pytest.raises(ValueError, match="input limit"):
            core.scan(target)


def test_partial_decode_evidence_in_html_and_literal_markdown(tmp_path, monkeypatch):
    (tmp_path / "good.png").write_bytes(png())
    (tmp_path / "large.png").write_bytes(png((24, 24)))
    monkeypatch.setattr(core, "MAX_PIXELS", 500)
    report = core.scan(tmp_path, preview=True)
    assert report["page_count"] == 1 and report["error_count"] == 1
    report["pages"][0]["name"] = "page|" + chr(96) + "<b>" + chr(10) + "# injected"
    report["errors"][0]["name"] = "<script>.png"
    report["errors"][0]["error"] = "bad|" + chr(10) + "# error"
    html = review.render_html(report)
    assert "Decode errors — partial analysis" in html
    assert "&lt;script&gt;.png" in html and "<script>.png" not in html
    markdown = core.render_markdown(report)
    assert "&#124;" in markdown and "&#96;" in markdown and "&#10;" in markdown
    assert chr(10) + "# injected" not in markdown
    assert chr(10) + "# error" not in markdown


def test_unsupported_zip_header_and_windows_drive_are_actionable(tmp_path, capsys):
    target = tmp_path / "bad.cbz"
    info = ZipInfo("page.png")
    info.extract_version = 99
    info.create_version = 99
    with ZipFile(target, "w") as archive:
        archive.writestr(info, png())
    with pytest.raises(ValueError, match="Cannot decode"):
        core.scan(target)
    assert main([str(target)]) == 2
    assert "Cannot decode" in capsys.readouterr().err
    with ZipFile(target, "w") as archive:
        archive.writestr("C:/page.png", png())
    with pytest.raises(ValueError, match="unsafe"):
        core.scan(target)


@pytest.mark.parametrize(
    "failure", [RuntimeError, zlib.error, lzma.LZMAError], ids=["encrypted", "deflate", "lzma"]
)
def test_archive_member_decode_errors_are_actionable(tmp_path, monkeypatch, failure):
    target = tmp_path / "bad.cbz"
    with ZipFile(target, "w") as archive:
        archive.writestr("page.png", png())

    def failed(*args, **kwargs):
        raise failure("fixture")

    monkeypatch.setattr(ZipFile, "open", failed)
    with pytest.raises(ValueError, match="Cannot decode"):
        core.scan(target)


def test_directory_walk_error_is_actionable(tmp_path, monkeypatch):
    def walk(path, *, onerror):
        onerror(PermissionError("fixture"))
        return iter(())

    monkeypatch.setattr(core.os, "walk", walk)
    with pytest.raises(ValueError, match="Cannot read image directory"):
        core.scan(tmp_path)


@pytest.mark.parametrize("dangling", [False, True], ids=["existing", "dangling"])
def test_report_links_preserved(tmp_path, dangling):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "page.png").write_bytes(png())
    target = tmp_path / "target"
    if not dangling:
        target.write_text("valuable")
    output = tmp_path / "output"
    try:
        output.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    assert main([str(pages), "--output", str(output)]) == 2
    assert output.is_symlink()
    assert target.read_text() == "valuable" if not dangling else not target.exists()


def test_concurrent_report_preserved(tmp_path, monkeypatch):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "page.png").write_bytes(png())
    output = tmp_path / "output"
    original = Path.open

    def raced(path, mode="r", *args, **kwargs):
        if path == output and mode == "x":
            with original(path, "w") as handle:
                handle.write("concurrent")
        return original(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", raced)
    assert main([str(pages), "--output", str(output)]) == 2
    assert output.read_text() == "concurrent"


def test_unreadable_supported_image_metadata_is_not_skipped(tmp_path, monkeypatch):
    source = tmp_path / "unreadable.png"
    source.write_bytes(png())
    (tmp_path / "good.png").write_bytes(png())
    original = Path.lstat

    def inaccessible(path, *args, **kwargs):
        if path == source:
            raise PermissionError("fixture image")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", inaccessible)
    with pytest.raises(PermissionError, match="fixture image"):
        core.scan(tmp_path)
