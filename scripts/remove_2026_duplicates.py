#!/usr/bin/env python3
"""
Remove nomination athletes that are already in consolidated dataset for year 2026
Keeps nomination athletes who are:
- Not in consolidated dataset at all, OR
- In consolidated dataset but only for years other than 2026
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load both datasets
print("Loading datasets...")
df_nomination = pd.read_csv(BASE_DIR / "Nomination_Athletes_filtered.csv")
df_consolidated = pd.read_csv(BASE_DIR / "Conversion_Data_2026_consolidated.csv")

print(f"Nomination athletes: {len(df_nomination):,}")
print(f"Consolidated records: {len(df_consolidated):,}")
print()

# Filter consolidated for 2026 only
df_consol_2026 = df_consolidated[df_consolidated['Year'] == 2026].copy()

print(f"Consolidated records for year 2026: {len(df_consol_2026):,}")
print(f"Unique athletes in 2026: {df_consol_2026[['First Name', 'Last Name']].drop_duplicates().shape[0]:,}")
print()

# Create match keys for comparison
# Match on: Sport + First Name + Last Name + DOB
print("Finding overlaps...")

# Rename columns to match for merging
df_consol_2026['Sport_c'] = df_consol_2026['Sport']
df_consol_2026['First Name_c'] = df_consol_2026['First Name']
df_consol_2026['Last Name_c'] = df_consol_2026['Last Name']
df_consol_2026['DOB_c'] = df_consol_2026['Date of Birth']

# Get unique 2026 athletes from consolidated
consol_2026_athletes = df_consol_2026[['Sport_c', 'First Name_c', 'Last Name_c', 'DOB_c']].drop_duplicates()
consol_2026_athletes.columns = ['Sport', 'First Name', 'Last Name', 'DOB']

print(f"Unique athlete combinations in 2026 consolidated: {len(consol_2026_athletes):,}")
print()

# Mark which nomination athletes are in 2026 consolidated
df_nomination['in_2026_consolidated'] = df_nomination.merge(
    consol_2026_athletes,
    on=['Sport', 'First Name', 'Last Name', 'DOB'],
    how='left',
    indicator=True
)['_merge'] == 'both'

# Count overlaps
overlaps = df_nomination['in_2026_consolidated'].sum()
print(f"Nomination athletes already in 2026 consolidated: {overlaps:,}")
print()

# Remove duplicates
df_nomination_cleaned = df_nomination[~df_nomination['in_2026_consolidated']].drop(columns=['in_2026_consolidated'])

print(f"Nomination athletes after removing 2026 duplicates: {len(df_nomination_cleaned):,}")
print(f"Rows removed: {len(df_nomination) - len(df_nomination_cleaned):,}")
print()

# Save cleaned file
output_file = BASE_DIR / "Nomination_Athletes_filtered.csv"
df_nomination_cleaned.to_csv(output_file, index=False)

print(f"✓ Saved cleaned nomination file to: {output_file}")
print(f"✓ Final count: {len(df_nomination_cleaned):,} athletes (new additions only)")
