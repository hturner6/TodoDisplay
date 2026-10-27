import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from taskFetcher.envFiles import permission_warnings

posix_only = pytest.mark.skipif(os.name != "posix", reason="needs POSIX modes")


def file_with_mode(tmp_path, name, mode):
    path = tmp_path / name
    path.write_text("FAKE_SECRET=fake-value")
    path.chmod(mode)
    return path


@posix_only
def test_a_private_file_gives_no_warning(tmp_path):
    assert permission_warnings([file_with_mode(tmp_path, ".env", 0o600)]) == []


@posix_only
@pytest.mark.parametrize("mode", [0o640, 0o604, 0o644])
def test_a_file_others_can_read_is_named_with_its_mode_and_never_its_contents(tmp_path, mode):
    path = file_with_mode(tmp_path, ".env", mode)

    (warning,) = permission_warnings([path])

    assert str(path) in warning and f"{mode:03o}" in warning and "chmod 600" in warning
    assert "fake-value" not in warning


@posix_only
def test_missing_and_unset_paths_are_skipped(tmp_path):
    assert permission_warnings([tmp_path / "absent", None, ""]) == []
