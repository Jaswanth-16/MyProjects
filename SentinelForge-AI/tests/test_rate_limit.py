from sentinelforge.rate_limit import RateLimiter


def test_rate_limiter_rejects_excess_requests():
    limiter = RateLimiter(limit=2, window_seconds=60)
    assert limiter.allow("client-a")
    assert limiter.allow("client-a")
    assert not limiter.allow("client-a")
    assert limiter.allow("client-b")


def test_rate_limiter_expires_window(monkeypatch):
    import sentinelforge.rate_limit as module
    clock = [100.0]
    monkeypatch.setattr(module, "monotonic", lambda: clock[0])
    limiter = RateLimiter(limit=1, window_seconds=10)
    assert limiter.allow("client")
    assert not limiter.allow("client")
    clock[0] = 111.0
    assert limiter.allow("client")
