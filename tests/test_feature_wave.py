import io
import zipfile

import pytest
from PIL import Image, ImageDraw

from speech_bubble_density_estimator.cli import main
from speech_bubble_density_estimator.core import scan


def test_page_order_directory_archive_parity(tmp_path, capsys):
    folder = tmp_path / "pages"
    folder.mkdir()
    names = [
        "page10.png",
        "page2.png",
        "page1.png",
        "nested/a2.png",
        "nested/A2x.png",
        "nested/a02.png",
    ]
    image = io.BytesIO()
    Image.new("L", (32, 32), 128).save(image, "PNG")
    payloads = {}
    for index, name in enumerate(names):
        page = Image.new("L", (32, 32), 255 if index % 2 else 128)
        if index % 2:
            draw = ImageDraw.Draw(page)
            for y in range(0, 32, 8):
                draw.rectangle((0, y, 31, y + 1), fill=0)
        encoded = io.BytesIO()
        page.save(encoded, "PNG")
        payloads[name] = encoded.getvalue()
        path = folder / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(payloads[name])
    legacy = scan(folder)
    assert [x["name"] for x in legacy["pages"]] == [
        page.relative_to(folder).as_posix() for page in sorted(folder / name for name in names)
    ]
    expected = [
        "nested/a02.png",
        "nested/a2.png",
        "nested/A2x.png",
        "page1.png",
        "page2.png",
        "page10.png",
    ]
    natural = scan(folder, page_order="natural")
    assert [x["name"] for x in natural["pages"]] == expected
    for order in [names, list(reversed(names))]:
        archive = tmp_path / "pages.cbz"
        with zipfile.ZipFile(archive, "w") as z:
            for name in order:
                z.writestr(name, payloads[name])
        assert [x["name"] for x in scan(archive)["pages"]] == order
        assert scan(archive, page_order="natural")["pages"] == natural["pages"]
        assert (
            scan(archive, page_order="lexical")["pages"]
            == scan(folder, page_order="lexical")["pages"]
        )
        assert [x["name"] for x in scan(archive, page_order="lexical")["pages"]] == sorted(names)
    assert {x["name"]: x["classification"] for x in legacy["pages"]} == {
        x["name"]: x["classification"] for x in natural["pages"]
    }
    assert natural["settings"]["page_order"] == "natural"
    assert main([str(folder), "--page-order", "natural", "--format", "json"]) == 0
    assert "natural" in capsys.readouterr().out
    with pytest.raises(ValueError, match="page order"):
        scan(folder, page_order="unknown")


def test_order_preserves_archive_guards(tmp_path):
    for name in ["../unsafe.png", "/absolute.png"]:
        archive = tmp_path / "bad.cbz"
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr(name, b"x")
        with pytest.raises(ValueError, match="unsafe"):
            scan(archive, page_order="natural")
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("a.png", b"x")
        z.writestr("A.png", b"x")
    with pytest.raises(ValueError, match="duplicate"):
        scan(archive, page_order="natural")


def test_archive_size_guards_with_natural_order(tmp_path, monkeypatch):
    from speech_bubble_density_estimator import core

    archive = tmp_path / "limits.cbz"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("page1.png", b"synthetic")
        handle.writestr("page2.png", b"synthetic")
    monkeypatch.setattr(core, "MAX_ENTRIES", 1)
    with pytest.raises(ValueError, match="entry limit"):
        scan(archive, page_order="natural")
    monkeypatch.setattr(core, "MAX_ENTRIES", 10)
    monkeypatch.setattr(core, "MAX_UNCOMPRESSED", 1)
    with pytest.raises(ValueError, match="uncompressed-size"):
        scan(archive, page_order="natural")


def test_archive_normalized_names_order(tmp_path):
    raw = io.BytesIO()
    Image.new("L", (32, 32), 128).save(raw, "PNG")
    names = [
        "nested/a2.png",
        "nested/A2x.png",
        "nested/a02.png",
        "page10.png",
        "page2.png",
        "page1.png",
    ]
    folder = tmp_path / "pages"
    folder.mkdir()
    archive = tmp_path / "paths.cbz"
    with zipfile.ZipFile(archive, "w") as handle:
        for index, name in enumerate(names):
            path = folder / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(raw.getvalue())
            member = ("./" + name) if index % 2 else name.replace("/", chr(92))
            handle.writestr(member, raw.getvalue())
    for policy in ("natural", "lexical"):
        assert scan(folder, page_order=policy)["pages"] == scan(archive, page_order=policy)["pages"]
