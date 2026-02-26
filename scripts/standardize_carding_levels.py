#!/usr/bin/env python3
"""
Standardize carding levels in nomination data to match consolidated dataset format
Maps various carding levels to: Prov Dev 3, Prov Dev 2, Prov Dev 1, Uncarded, SC Carded
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load filtered nomination file
print("Loading filtered nomination file...")
df = pd.read_csv(BASE_DIR / "Nomination_Athletes_filtered.csv")

print(f"Rows: {len(df):,}")
print(f"Columns: {df.columns.tolist()}")
print()

# Load original file to get carding levels
print("Loading original nomination file...")
df_original = pd.read_csv(
    BASE_DIR / "Nomination_Master_2025only(26 FY (Mar 31- Mar 31)).csv",
    encoding='latin-1'
)

# Filter for athletes only
df_original = df_original[df_original['Profile Type'] == 'Athlete'].copy()

# Keep carding level column
df_carding = df_original[['Sport', 'First Name', 'Last Name', 'DOB', 'Carding Level']].copy()

print(f"Original carding levels:")
print(df_carding['Carding Level'].value_counts().to_string())
print()

# Define mapping to consolidated format
carding_mapping = {
    'Prov Dev 3': 'Prov Dev 3',
    'Prov Dev 2': 'Prov Dev 2',
    'Prov Dev 1': 'Prov Dev 1',
    'Prov dev 1': 'Prov Dev 1',  # Handle case variations
    'Uncarded': 'Uncarded',
    'Uncarded ': 'Uncarded',  # Handle trailing space
    # SC Carded mappings
    'D': 'SC Carded',
    'SR': 'SC Carded',
    'SR1': 'SC Carded',
    'SR2': 'SC Carded',
    'C1': 'SC Carded',
    'DI': 'SC Carded',
    'SRI': 'SC Carded',
}

# Apply mapping
df_carding['Carding_Level_Std'] = df_carding['Carding Level'].map(carding_mapping)

# Remove any GamePlan Retired records that slipped through
df_carding = df_carding[~df_carding['Carding Level'].str.contains('GamePlan|Gameplan', case=False, na=False)].copy()

# Check for unmapped values
unmapped = df_carding[df_carding['Carding_Level_Std'].isna()]
if len(unmapped) > 0:
    print(f"⚠ WARNING: {len(unmapped)} records with unmapped carding levels:")
    print(unmapped['Carding Level'].unique())
    print()
else:
    print("✓ All carding levels mapped successfully")
    print()

# Merge with filtered nomination data
df_merged = df.merge(
    df_carding[['Sport', 'First Name', 'Last Name', 'DOB', 'Carding_Level_Std']],
    on=['Sport', 'First Name', 'Last Name', 'DOB'],
    how='left'
)

# Rename column
df_merged = df_merged.rename(columns={'Carding_Level_Std': 'Program'})

print(f"Program column data type: {df_merged['Program'].dtype}")
print(f"Programs in result:")
prog_counts = df_merged['Program'].value_counts(dropna=True)
for prog, count in prog_counts.items():
    print(f"  {prog}: {count}")
print()

# Verify all have a program level
missing_program = df_merged['Program'].isna().sum()
print(f"Records without program level: {missing_program}")
print()

# Save updated file
output_file = BASE_DIR / "Nomination_Athletes_filtered.csv"
df_merged.to_csv(output_file, index=False)

print(f"✓ Saved to: {output_file}")
print(f"✓ Columns: {df_merged.columns.tolist()}")
print(f"✓ Final count: {len(df_merged):,} athletes")
