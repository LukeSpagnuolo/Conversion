#!/usr/bin/env python3
"""
Remove GamePlan Retired athletes from nomination dataset
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load the deduplicated nomination file
print("Loading nomination file...")
df = pd.read_csv(BASE_DIR / "Nomination_Athletes_filtered.csv")

print(f"Original rows: {len(df):,}")
print()

# Load original file to get carding levels
print("Loading original file for carding levels...")
df_original = pd.read_csv(
    BASE_DIR / "Nomination_Master_2025only(26 FY (Mar 31- Mar 31)).csv",
    encoding='latin-1'
)

# Filter for athletes
df_original = df_original[df_original['Profile Type'] == 'Athlete'].copy()

# Keep relevant columns
df_with_carding = df_original[['Sport', 'First Name', 'Last Name', 'DOB', 'Carding Level']].copy()

# Remove GamePlan Retired athletes
retired_variants = ['GamePlan Retired', 'Gameplan Retired']
print(f"Removing athletes with carding level: {retired_variants}")

df_no_retired = df_with_carding[~df_with_carding['Carding Level'].isin(retired_variants)].copy()

print(f"After removing retired: {len(df_no_retired):,} records")
print(f"Athletes removed: {len(df_with_carding) - len(df_no_retired):,}")
print()

# Get the athlete identifiers to keep
keep_athletes = df_no_retired[['Sport', 'First Name', 'Last Name', 'DOB']].copy()

# Merge with filtered nomination data
df_final = df.merge(
    keep_athletes,
    on=['Sport', 'First Name', 'Last Name', 'DOB'],
    how='inner'
)

print(f"Final dataset: {len(df_final):,} athletes")
print()

# Save cleaned file
output_file = BASE_DIR / "Nomination_Athletes_filtered.csv"
df_final.to_csv(output_file, index=False)

print(f"✓ Saved to: {output_file}")
print(f"✓ Final count: {len(df_final):,} athletes")
print(f"✓ Removed GamePlan Retired athletes")
