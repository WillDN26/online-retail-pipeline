import pandas as pd
from pathlib import Path

SOURCE = ".gitignore/online_retail_II.xlsx"
TARGET = Path("data/raw/online_retail_sample.xlsx")

df = pd.read_excel(SOURCE)
print(f"Full dataset: {len(df)} rows")

sample = df.sample(n=5000, random_state=42).sort_index()

TARGET.parent.mkdir(parents=True, exist_ok=True)
sample.to_excel(TARGET, index=False)
print(f"Saved {len(sample)} rows to {TARGET}")