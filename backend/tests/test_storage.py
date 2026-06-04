from pathlib import Path

import pytest

from app.services.storage_service import ensure_relative_child


def test_ensure_relative_child_rejects_path_traversal(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()

    with pytest.raises(ValueError):
        ensure_relative_child(root, "../outside.txt")


def test_ensure_relative_child_accepts_nested_relative_path(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()

    child = ensure_relative_child(root, "metadata/report.json")

    assert child == root / "metadata" / "report.json"
