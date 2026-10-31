from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from sentinelforge.ai import OllamaInvestigator, configured_investigator
from sentinelforge.main import DeterministicInvestigator, Finding, Severity


def finding():
    return Finding(
        id="sample", source="checkov", rule_id="TEST", resource="fixture.tf",
        severity=Severity.high, title="Synthetic issue", evidence="fixture only",
        recommendation="Review configuration", authorized_scope="local",
        risk_score=80, recorded_at=datetime.now(timezone.utc),
    )


def test_default_is_offline(monkeypatch):
    monkeypatch.delenv("SENTINELFORGE_AI_PROVIDER", raising=False)
    assert isinstance(configured_investigator(), DeterministicInvestigator)


def test_ollama_requires_localhost():
    with pytest.raises(ValueError):
        OllamaInvestigator(endpoint="https://external.example")


def test_ollama_unavailable_falls_back():
    with patch("sentinelforge.ai.urlopen", side_effect=OSError("offline")):
        report = OllamaInvestigator().explain(finding())
    assert report["provider"] == "deterministic"


def test_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("SENTINELFORGE_AI_PROVIDER", "ollama")
    assert isinstance(configured_investigator(), OllamaInvestigator)


def test_success_response():
    class Response:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self, size):
            return b'{"response":"Review the synthetic misconfiguration."}'
    with patch("sentinelforge.ai.urlopen", return_value=Response()):
        result = OllamaInvestigator().explain(finding())
    assert result["provider"] == "ollama-local"
