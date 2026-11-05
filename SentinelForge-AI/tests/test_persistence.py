from sentinelforge.main import FindingInput
from sentinelforge.persistence import SQLiteStore


def test_persists_between_store_instances(tmp_path):
    path = tmp_path / "findings.db"
    payload = FindingInput(source="semgrep", rule_id="R1", resource="demo.py",
                           severity="high", title="Synthetic", evidence="fixture",
                           recommendation="Review", authorized_scope="local")
    first = SQLiteStore(path).add(payload)
    second_store = SQLiteStore(path)
    assert second_store.get(first.id) == first
    assert len(second_store.list()) == 1
    assert second_store.add(payload).id == first.id
    assert len(second_store.list()) == 1
