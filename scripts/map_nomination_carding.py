#!/usr/bin/env python3
"""
Map athlete_carding from 2026_Nominated athletes.csv to Program column
Maps: Prov Dev 3, Prov Dev 2, Prov Dev 1, Uncarded, SC Carded
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load the nomination file
print("Loading 2026_Nominated athletes.csv...")
df = pd.read_csv(BASE_DIR / "2026_Nominated athletes.csv")

print(f"Rows: {len(df):,}")
print(f"Columns: {df.columns.tolist()}")
print()

# Show current carding level distribution
print("Current athlete_carding values:")
print(df['athlete_carding'].value_counts().to_string())
print()

# Strip whitespace from carding levels first
df['athlete_carding'] = df['athlete_carding'].astype(str).str.strip()

# Define mapping to Program levels
carding_mapping = {
    'Prov Dev 3': 'Prov Dev 3',
    'Prov Dev 2': 'Prov Dev 2',
    'Prov Dev 1': 'Prov Dev 1',
    'Prov dev 1': 'Prov Dev 1',  # Handle case variation
    'Uncarded': 'Uncarded',
    'NSO Affiliated (Uncarded)': 'Uncarded',
    'PSO Affiliated (Uncarded)': 'Uncarded',
    # SC Carded (senior/development)
    'D': 'SC Carded',
    'SR': 'SC Carded',
    'SR1': 'SC Carded',
    'SR2': 'SC Carded',
    'C1': 'SC Carded',
    'DI': 'SC Carded',
    'SRI': 'SC Carded',
}

# Apply mapping
df['Program'] = df['athlete_carding'].map(carding_mapping)

# Check for unmapped values
unmapped = df[df['Program'].isna()]
if len(unmapped) > 0:
    print(f"⚠ WARNING: {len(unmapped)} records with unmapped carding levels:")
    unique_unmapped = unmapped['athlete_carding'].unique()
    for val in unique_unmapped:
        count = (unmapped['athlete_carding'] == val).sum()
        print(f"  '{val}': {count}")
    print()
else:
    print("✓ All carding levels mapped successfully")
    print()

# Show final Program distribution
print("Final Program values:")
print(df['Program'].value_counts().to_string())
print()

# Save with Program column
output_file = BASE_DIR / "2026_Nominated athletes.csv"
df.to_csv(output_file, index=False)

print(f"✓ Saved to: {output_file}")
print(f"✓ Total rows: {len(df):,}")
