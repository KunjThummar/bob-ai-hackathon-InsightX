"""Download the NASA C-MAPSS FD001 dataset used by the notebook and save as CSV."""
import os
import pandas as pd
from datasets import load_dataset

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "data")
os.makedirs(DATA_DIR, exist_ok=True)

print("Loading NASA C-MAPSS FD001 from HuggingFace...")
dataset = load_dataset("SoyVitou/NASA-C-MAPSS-Turbofan-Engine", "FD001")

train_df = dataset["train"].to_pandas()
test_df = dataset["test"].to_pandas()

print(f"Train shape: {train_df.shape}")
print(f"Test shape:  {test_df.shape}")

# Combine into a single dataset with unique asset_id per engine.
# unit_id overlaps (1-100) between train and test, so we disambiguate by source.
train_df = train_df.copy()
test_df = test_df.copy()
train_df["source"] = "train"
test_df["source"] = "test"

# Unique integer asset_id: train -> 1..100, test -> 1001..1100
train_df["asset_id"] = train_df["unit_id"]
test_df["asset_id"] = test_df["unit_id"] + 1000

combined = pd.concat([train_df, test_df], ignore_index=True)
combined = combined.sort_values(["source", "asset_id", "cycle"]).reset_index(drop=True)

out_path = os.path.join(DATA_DIR, "actual_dataset.csv")
combined.to_csv(out_path, index=False)
print(f"Saved combined dataset: {out_path}")
print(f"Combined shape: {combined.shape}")
print(f"Unique asset_ids: {combined['asset_id'].nunique()}")
print(f"Columns: {combined.columns.tolist()}")
