#!/usr/bin/env python3
"""
Remove duplicates from filtered nomination athlete data
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load filtered nomination file
print("Loading filtered nomination file...")
df = pd.read_csv(BASE_DIR / "Nomination_Athletes_filtered.csv")

print(f"Original rows: {len(df):,}")
print()

# Check for duplicates
print("Checking for duplicates...")
duplicate_mask = df.duplicated(subset=['Sport', 'First Name', 'Last Name', 'DOB'], keep=False)
n_duplicates = duplicate_mask.sum()

print(f"✓ Total duplicate rows: {n_duplicates}")
print()

if n_duplicates > 0:
    print("Sample duplicates:")
    print(df[duplicate_mask].sort_values(['First Name', 'Last Name']).head(10).to_string())
    print()

# Remove duplicates, keeping first occurrence
df_deduped = df.drop_duplicates(subset=['Sport', 'First Name', 'Last Name', 'DOB'], keep='first')

print(f"After deduplication: {len(df_deduped):,} rows")
print(f"Rows removed: {len(df) - len(df_deduped):,}")
print()

# Check for any remaining duplicates
remaining_dupes = df_deduped.duplicated(subset=['Sport', 'First Name', 'Last Name', 'DOB']).sum()
print(f"Remaining duplicates: {remaining_dupes}")
print()

# Save deduplicated file
output_file = BASE_DIR / "Nomination_Athletes_filtered.csv"
df_deduped.to_csv(output_file, index=False)

print(f"✓ Saved deduplicated data to: {output_file}")
print(f"✓ Final count: {len(df_deduped):,} unique athletes")
