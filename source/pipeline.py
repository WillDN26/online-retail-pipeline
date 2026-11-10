import argparse
import json
import logging
import sys
import time
from pathlib import Path

import pandas as pd
from source import transformations as t

logger = logging.getLogger("pipeline")


def run(input_path: Path, output_dir: Path) -> dict:
    start = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Reading %s", input_path)
    try:
        raw = pd.read_excel(input_path)
    except FileNotFoundError:
        logger.error("Input file not found: %s", input_path)
        raise
    rows_in = len(raw)
    raw = t.rename_columns(raw)
    t.validate_schema(raw)

    df = (raw.pipe(t.remove_cancelled)
             .pipe(t.handle_nulls)
             .pipe(t.convert_types)
             .pipe(t.remove_invalid_values)
             .pipe(t.add_total_price))
    daily = t.daily_sales(df)

    df.to_csv(output_dir / "clean_orders.csv", index=False)
    daily.to_csv(output_dir / "daily_sales.csv", index=False)
    daily.to_parquet(output_dir / "daily_sales.parquet", index=False)

    metrics = {
        "records_in": rows_in,
        "records_out": len(df),
        "records_dropped": rows_in - len(df),
        "days_aggregated": len(daily),
        "runtime_seconds": round(time.perf_counter() - start, 3),
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    logger.info("Pipeline complete: %s", metrics)
    return metrics


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/raw/online_retail_sample.xlsx")
    p.add_argument("--output", default="data/processed")
    args = p.parse_args()
    try:
        run(Path(args.input), Path(args.output))
    except Exception:
        logger.exception("Pipeline failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())