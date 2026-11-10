import json
import sys
from pathlib import Path

import pandas as pd

out = Path("data/processed")
errors = []

for f in ["clean_orders.csv", "daily_sales.csv", "daily_sales.parquet", "metrics.json"]:
    if not (out / f).exists():
        errors.append(f"Missing output: {f}")

if not errors:
    daily = pd.read_csv(out / "daily_sales.csv")
    clean = pd.read_csv(out / "clean_orders.csv")
    if daily.empty:
        errors.append("daily_sales is empty")
    if (daily["total_sales"] <= 0).any():
        errors.append("daily_sales has non-positive totals")
    if clean["InvoiceNo"].astype(str).str.startswith("C").any():
        errors.append("Cancelled orders still present")
    if daily["SaleDate"].duplicated().any():
        errors.append("Duplicate dates in daily_sales")
    metrics = json.loads((out / "metrics.json").read_text())
    if metrics["records_out"] == 0:
        errors.append("No records processed")

if errors:
    print("VALIDATION FAILED:\n- " + "\n- ".join(errors))
    sys.exit(1)
print("Output validation passed")