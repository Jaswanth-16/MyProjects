from pathlib import Path
from unittest.mock import patch
import pytest

from sentinelforge.backup import backup, restore


def test_backup_refuses_to_overwrite(tmp_path):
    output = tmp_path / "existing.dump"
    output.write_bytes(b"existing")
    with pytest.raises(FileExistsError):
        backup("postgresql://localhost/fixture", output)


def test_restore_requires_explicit_confirmation(tmp_path):
    dump = tmp_path / "fixture.dump"
    dump.write_bytes(b"test")
    with pytest.raises(ValueError):
        restore("postgresql://localhost/fixture", dump)


def test_restore_invokes_pg_restore_with_confirmation(tmp_path):
    dump = tmp_path / "fixture.dump"
    dump.write_bytes(b"test")
    with patch("sentinelforge.backup.subprocess.run") as run:
        restore("postgresql://localhost/fixture", dump, confirmed=True)
    assert run.call_args.args[0][0] == "pg_restore"
    assert run.call_args.kwargs["check"] is True
