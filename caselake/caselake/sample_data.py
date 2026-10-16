"""Deterministic synthetic data; no customer text or personal information."""

import json
from pathlib import Path

CATEGORIES = ("access", "billing", "delivery")
TEMPLATES = {
    "access": (
        "Unable to login because account authentication fails",
        "Password reset does not unlock my user account",
        "Sign in blocked by invalid credentials and authentication error",
        "Cannot access account after resetting password",
    ),
    "billing": (
        "Invoice includes a duplicate payment charge",
        "Refund missing after cancelled subscription payment",
        "Billing statement has incorrect invoice amount",
        "Charged twice and need a refund for the payment",
    ),
    "delivery": (
        "Shipment tracking shows the parcel delayed",
        "Package delivery failed and courier did not arrive",
        "Order shipment lost at the courier depot",
        "Parcel tracking is stuck and delivery is overdue",
    ),
}
FIELDS = ("ticket_id", "version", "text", "priority", "category", "split", "created_at")


def sample_events(per_class=40):
    if per_class < 4:
        raise ValueError("per_class must be at least 4")
    rows = []
    for category in CATEGORIES:
        for i in range(per_class):
            # Template 4 is never seen during training. Still synthetic, not a
            # real-world/independent benchmark. Group IDs do not cross splits.
            split = "test" if i % 4 == 3 else "train"
            rows.append({
                "ticket_id": f"{category}-{i:04d}", "version": "1",
                "text": TEMPLATES[category][i % 4] + f". Reference {i:04d}.",
                "priority": str(i % 3 + 1), "category": category,
                "split": split, "created_at": "2026-01-01T09:00:00Z",
            })
    rows += [dict(rows[0]), dict(rows[1])]  # exact replay
    update = dict(rows[0], version="2", priority="1")
    rows += [update, dict(rows[0])]  # correction then stale replay
    for i, patch in enumerate([
        {"text": ""}, {"priority": "9"}, {"version": "x"},
        {"created_at": "not-a-date"}, {"ticket_id": ""},
        {"category": "unknown"},
    ]):
        bad = dict(rows[4], ticket_id=f"bad-{i}")
        bad.update(patch)
        rows.append(bad)
    return rows


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n")
