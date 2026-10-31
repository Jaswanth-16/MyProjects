import pytest
from sentinelforge.tokens import TokenError, issue_token, verify_token


SECRET = "this-is-a-long-random-test-secret-32-chars"


def test_issue_verify_scoped_token():
    token = issue_token(SECRET, "analyst-1", "team-a", ttl_seconds=300)
    claims = verify_token(SECRET, token)
    assert claims["sub"] == "analyst-1"
    assert claims["scope"] == "team-a"


def test_tampered_token_rejected():
    token = issue_token(SECRET, "analyst-1", "team-a")
    with pytest.raises(TokenError):
        verify_token(SECRET, token + "x")


def test_expired_token_rejected(monkeypatch):
    import sentinelforge.tokens as tokens
    monkeypatch.setattr(tokens.time, "time", lambda: 1000)
    token = issue_token(SECRET, "analyst-1", "team-a", ttl_seconds=1)
    monkeypatch.setattr(tokens.time, "time", lambda: 1002)
    with pytest.raises(TokenError):
        verify_token(SECRET, token)


def test_weak_signing_secret_rejected():
    with pytest.raises(ValueError):
        issue_token("weak", "analyst-1", "team-a")
