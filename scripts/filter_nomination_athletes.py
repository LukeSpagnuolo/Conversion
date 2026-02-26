#!/usr/bin/env python3
"""
Filter nomination data to athletes only, then keep necessary columns
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load nomination file
print("Loading nomination file...")
df = pd.read_csv(BASE_DIR / "Nomination_Master_2025only(26 FY (Mar 31- Mar 31)).csv", encoding='latin-1')

print(f"Original rows: {len(df):,}")
print(f"Original columns: {len(df.columns)}")
print()

# Filter for athletes only
print("Filtering for Profile Type = 'Athlete'...")
df_athletes = df[df['Profile Type'] == 'Athlete'].copy()

print(f"✓ Athletes only: {len(df_athletes):,} rows")
print()

# Keep only needed columns
columns_to_keep = ['Sport', 'First Name', 'Last Name', 'Sex Of Competition', 'DOB', 'Fiscal Year']

print(f"Selecting columns: {columns_to_keep}")
df_filtered = df_athletes[columns_to_keep].copy()

print()
print("Missing values in filtered data:")
print(df_filtered.isnull().sum())
print()

# Rename columns to match consolidated dataset format
# Check current column names
print("Current column names:")
print(df_filtered.columns.tolist())
print()

# Show sample data
print("Sample data (first 5 athletes):")
print(df_filtered.head(5).to_string())
print()

# Save filtered file
output_file = BASE_DIR / "Nomination_Athletes_filtered.csv"
df_filtered.to_csv(output_file, index=False)

print(f"✓ Saved to: {output_file}")
print(f"✓ Athletes: {len(df_filtered):,}")
print(f"✓ Columns: {len(df_filtered.columns)}")
