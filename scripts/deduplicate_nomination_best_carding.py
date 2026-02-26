#!/usr/bin/env python3
"""
Remove duplicates from nomination data, keeping the record with highest carding level
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load original filtered nomination file
print("Loading filtered nomination file...")
df = pd.read_csv(BASE_DIR / "Nomination_Athletes_filtered.csv")

print(f"Original rows: {len(df):,}")
print()

# Define carding level hierarchy (higher number = higher level)
carding_hierarchy = {
    'Prov Dev 3': 1,
    'Prov Dev 2': 2,
    'Prov Dev 1': 3,
    'Uncarded': 4,
    'SC Carded': 5,
    None: 0,
    '': 0
}

# Load the original file to get carding levels
print("Loading original nomination file for carding levels...")
df_original = pd.read_csv(
    BASE_DIR / "Nomination_Master_2025only(26 FY (Mar 31- Mar 31)).csv",
    encoding='latin-1'
)

# Filter for athletes
df_original = df_original[df_original['Profile Type'] == 'Athlete'].copy()

# Keep relevant columns
df_with_carding = df_original[['Sport', 'First Name', 'Last Name', 'DOB', 'Carding Level']].copy()

print(f"Total records with carding levels: {len(df_with_carding):,}")
print()

# Map carding level to numeric value
df_with_carding['Carding_Value'] = df_with_carding['Carding Level'].map(carding_hierarchy)

# Sort by carding value (descending) - highest first
df_with_carding = df_with_carding.sort_values('Carding_Value', ascending=False)

# Drop duplicates, keeping the one with highest carding level
df_deduped = df_with_carding.drop_duplicates(
    subset=['Sport', 'First Name', 'Last Name', 'DOB'],
    keep='first'
)

# Check duplicates
print("Duplicate analysis:")
print(f"Original rows: {len(df_with_carding):,}")
print(f"After deduplication (keeping highest carding level): {len(df_deduped):,}")
print(f"Duplicates removed: {len(df_with_carding) - len(df_deduped):,}")
print()

# Show distribution of carding levels kept
print("Carding levels in final dataset:")
print(df_deduped['Carding Level'].value_counts().to_string())
print()

# Merge back with original filtered data (Sport, First Name, Last Name, Sex, DOB, Fiscal Year)
# Reload the filtered file to get the original columns
df_filtered = pd.read_csv(BASE_DIR / "Nomination_Athletes_filtered.csv")

# Get the athlete identifiers we're keeping
keep_athletes = df_deduped[['Sport', 'First Name', 'Last Name', 'DOB']].copy()

# Merge to keep only those athletes
df_final = df_filtered.merge(
    keep_athletes,
    on=['Sport', 'First Name', 'Last Name', 'DOB'],
    how='inner'
)

print(f"Final clean dataset: {len(df_final):,} unique athletes")
print()

# Save deduplicated file
output_file = BASE_DIR / "Nomination_Athletes_filtered.csv"
df_final.to_csv(output_file, index=False)

print(f"✓ Saved to: {output_file}")
print(f"✓ Final count: {len(df_final):,} unique athletes")
print(f"✓ Kept the record with the highest carding level for each athlete")
