import json
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd

CUSTOMER_COLUMNS = ["customer_id", "segment", "tenure_months", "churned_next_month"]
USAGE_COLUMNS = ["usage_id", "customer_id", "period", "active_days", "support_calls", "monthly_spend"]


def generate(folder, count=600, seed=42):
    if count < 100:
        raise ValueError("Use at least 100 synthetic customers")
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    customers, usage = [], []
    for i in range(count):
        tenure = int(rng.integers(1, 61))
        active = int(rng.integers(1, 29))
        calls = int(rng.poisson(2))
        segment = str(rng.choice(["small", "mid", "enterprise"]))
        probability = 1 / (1 + np.exp(-(-0.7 + 0.5 * calls - 0.09 * active - 0.015 * tenure)))
        customers.append([f"C{i:05d}", segment, tenure, int(rng.random() < probability)])
        for month in ["2025-11", "2025-12"]:
            usage.append([f"{i}-{month}", f"C{i:05d}", month,
                          max(0, min(31, active + int(rng.integers(-2, 3)))),
                          calls, round(float(rng.uniform(20, 250)), 2)])
    c = pd.DataFrame(customers, columns=CUSTOMER_COLUMNS)
    u = pd.DataFrame(usage, columns=USAGE_COLUMNS)
    c = pd.concat([c, c.iloc[[0]]], ignore_index=True)  # duplicate replay
    bad = u.iloc[[0]].copy()
    bad["usage_id"], bad["active_days"] = "bad-activity", -2
    u = pd.concat([u, bad], ignore_index=True)
    c.to_csv(folder / "customers.csv", index=False)
    u.to_csv(folder / "usage.csv", index=False)


def _unique(frame, key):
    frame = frame.drop_duplicates().copy()
    if frame[key].duplicated().any():
        raise ValueError(f"Conflicting duplicate {key}")
    return frame


def load_and_join(folder):
    folder = Path(folder)
    c, u = [pd.read_csv(folder / f"{name}.csv", dtype={"customer_id": "string"})
            for name in ["customers", "usage"]]
    for frame, expected in [(c, CUSTOMER_COLUMNS), (u, USAGE_COLUMNS)]:
        if set(frame.columns) != set(expected):
            raise ValueError(f"Expected columns {expected}")
    c, u = _unique(c, "customer_id"), _unique(u, "usage_id")
    for col in ["tenure_months", "churned_next_month"]:
        c[col] = pd.to_numeric(c[col], errors="coerce")
    for col in ["active_days", "support_calls", "monthly_spend"]:
        u[col] = pd.to_numeric(u[col], errors="coerce")
    good_c = (c.customer_id.fillna("").str.fullmatch(r"C\d{5}") &
              c.segment.isin(["small", "mid", "enterprise"]) &
              c.tenure_months.between(0, 120) & c.churned_next_month.isin([0, 1]))
    good_u = (u.customer_id.isin(c.loc[good_c, "customer_id"]) &
              u.usage_id.notna() &
              u.period.astype(str).isin(["2025-11", "2025-12"]) &
              u.active_days.between(0, 31) & u.support_calls.between(0, 100) &
              u.monthly_spend.between(0, 100000))
    rejected = {"customer_rows": int((~good_c).sum()), "usage_rows": int((~good_u).sum())}
    bad_c, bad_u = c.loc[~good_c].copy(), u.loc[~good_u].copy()
    c, u = c.loc[good_c], u.loc[good_u]
    with sqlite3.connect(":memory:") as connection:
        c.to_sql("customers", connection, index=False)
        u.to_sql("usage", connection, index=False)
        joined = pd.read_sql_query("""
          SELECT c.customer_id, c.segment, c.tenure_months, c.churned_next_month,
                 AVG(u.active_days) AS active_days,
                 AVG(u.support_calls) AS support_calls,
                 AVG(u.monthly_spend) AS monthly_spend
          FROM customers c LEFT JOIN usage u ON c.customer_id = u.customer_id
          GROUP BY c.customer_id, c.segment, c.tenure_months, c.churned_next_month
          ORDER BY c.customer_id
        """, connection)
    if len(joined) < 100 or joined.churned_next_month.nunique() != 2:
        raise ValueError("Insufficient valid customers or target classes")
    return joined, rejected, bad_c, bad_u
