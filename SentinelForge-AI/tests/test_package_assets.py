"""Verify the browser dashboard ships in built Python distributions."""
from importlib import resources


def test_dashboard_is_package_resource():
    dashboard = resources.files("sentinelforge").joinpath("dashboard.html")
    assert dashboard.is_file()
    assert "<html" in dashboard.read_text(encoding="utf-8").lower()
