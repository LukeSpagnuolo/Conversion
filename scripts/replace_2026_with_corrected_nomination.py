#!/usr/bin/env python3
"""
Replace 2026 athletes in final dataset with corrected nomination data
Uses the newly mapped Program levels from 2026_Nominated athletes.csv
"""

import pandas as pd
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent

print("=" * 100)
print("REPLACING 2026 ATHLETES WITH CORRECTED NOMINATION DATA")
print("=" * 100)
print()

# Load the corrected nomination file with proper Program mapping
print("Loading corrected 2026_Nominated athletes.csv...")
nomination = pd.read_csv(BASE_DIR / "2026_Nominated athletes.csv")
print(f"  Rows: {len(nomination):,}")
print(f"  Columns: {nomination.columns.tolist()}")
print()

# Rename columns to match final dataset schema
nomination_renamed = nomination.rename(columns={
    'last_name': 'Last Name',
    'first_name': 'First Name',
    'sport': 'Sport',
    'sex_of_competition': 'Gender',
    'dob': 'Date of Birth',
    'nomination_fiscal_year': 'Year',
    'athlete_carding': 'Carding Level',  # Keep original for reference
})

# Standardize Year to just the year part (2025-2026 -> 2026)
nomination_renamed['Year'] = 2026

# Create Full_Name
nomination_renamed['Full_Name'] = (
    nomination_renamed['First Name'].astype(str).str.strip() + " " + 
    nomination_renamed['Last Name'].astype(str).str.strip()
)

# Add required columns
nomination_renamed['CSS'] = 'NO'
nomination_renamed['Years Targeted'] = 1
nomination_renamed['Convert Year'] = 'N'

# Select and order columns to match final dataset
final_columns = ['Sport', 'First Name', 'Last Name', 'Gender', 'Date of Birth', 
                 'Year', 'Program', 'Full_Name', 'CSS', 'Years Targeted', 'Convert Year']
nomination_formatted = nomination_renamed[final_columns].copy()

print(f"Formatted nomination data:")
print(f"  Rows: {len(nomination_formatted):,}")
print(f"  Columns: {nomination_formatted.columns.tolist()}")
print(f"  Program distribution:")
for prog in sorted(nomination_formatted['Program'].unique()):
    count = (nomination_formatted['Program'] == prog).sum()
    print(f"    {prog}: {count}")
print()

# Load the current final dataset
print("Loading Conversion_Data_2026_final.csv...")
final_df = pd.read_csv(BASE_DIR / "Conversion_Data_2026_final.csv")
print(f"  Total rows: {len(final_df):,}")
print(f"  2026 rows: {len(final_df[final_df['Year'] == 2026]):,}")
print()

# Separate pre-2026 data
pre_2026 = final_df[final_df['Year'] != 2026].copy()
print(f"Pre-2026 rows retained: {len(pre_2026):,}")
print()

# Combine pre-2026 data with corrected 2026 nomination data
print("Combining pre-2026 data with corrected 2026 nomination data...")
combined = pd.concat([pre_2026, nomination_formatted], ignore_index=True)
print(f"  Combined total rows: {len(combined):,}")
print()

# Sort by Full_Name and Year for consistency
combined = combined.sort_values(['Full_Name', 'Year']).reset_index(drop=True)

# Save the updated dataset
output_file = BASE_DIR / "Conversion_Data_2026_final.csv"
combined.to_csv(output_file, index=False)

print(f"✓ Saved updated dataset: {output_file}")
print(f"  Total rows: {len(combined):,}")
print(f"  2026 rows: {len(combined[combined['Year'] == 2026]):,}")
print()

# Show final 2026 Program distribution
print("Final 2026 Program distribution:")
final_2026 = combined[combined['Year'] == 2026]
for prog in sorted(final_2026['Program'].unique()):
    count = (final_2026['Program'] == prog).sum()
    print(f"  {prog}: {count}")
print()

print("✓ Replacement complete!")
