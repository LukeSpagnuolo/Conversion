#!/usr/bin/env python3
"""
Transform the CSV from wide format (class columns by year) to long format.

Only rows with a class value of YES are kept, and the resulting CSS year uses
the latter year from the source column heading (for example, 11/12 -> 2012).
"""

import pandas as pd
import re
import unicodedata
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SOURCE_PATH = BASE_DIR.parent / "CSSAthleteConversion_old.csv"
OUTPUT_PATH = BASE_DIR / "CSSAthleteConversion_long.csv"


def normalize_full_name(value):
    if pd.isna(value):
        return ''

    normalized = unicodedata.normalize('NFKD', str(value))
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+', '', ascii_text.lower())


TYPO_FULL_NAMES = {
    'mustaphahayestroare',
    'juiletteporter',
    'bryonlambert',
}

# Read the CSV.
df = pd.read_csv(SOURCE_PATH)

# Identify the class columns.
# Pattern: columns like "11/12 Class"
year_pattern = re.compile(r'(\d{2}/\d{2})\s+Class$')

# Extract unique years from the columns
years = set()
for col in df.columns:
    match = year_pattern.match(col)
    if match:
        years.add(match.group(1))

years = sorted(years)
print(f"Found years: {years}")

# Identify ID columns (those not matching the year pattern)
id_cols = []
year_cols = []

for col in df.columns:
    if year_pattern.match(col):
        year_cols.append(col)
    else:
        id_cols.append(col)

print(f"ID columns: {id_cols}")
print(f"Year columns: {year_cols}")

# Create list to hold rows for long format
long_rows = []

for _, row in df.iterrows():
    # Get the ID information for this person
    id_values = row[id_cols].to_dict()

    # Create a row for each year where the class value is YES
    for year in years:
        class_col = f"{year} Class"

        if class_col in df.columns:
            class_value = row.get(class_col, '')
            if pd.notna(class_value) and str(class_value).strip().upper() == 'YES':
                new_row = id_values.copy()
                year_parts = year.split('/')
                later_year = int(year_parts[1])
                new_row['CSS year'] = 2000 + later_year
                long_rows.append(new_row)

# Create the long format dataframe
long_df = pd.DataFrame(long_rows)

# Keep only the specified columns in the requested order
cols_order = ['Last Name', 'First Name', 'Full Name', 'Sport', 'Region', 'CSS year']
long_df = long_df[cols_order]

# Normalize Full Name to a single lowercase token for consistent matching.
long_df['Full Name'] = long_df['Full Name'].apply(normalize_full_name)

# Drop known typo variants from the dataset.
before_typos = len(long_df)
long_df = long_df[~long_df['Full Name'].isin(TYPO_FULL_NAMES)].copy()
after_typos = len(long_df)

# Deduplicate on the normalized name and CSS year.
before_dedup = len(long_df)
long_df = long_df.drop_duplicates(subset=['Full Name', 'CSS year'], keep='first').reset_index(drop=True)
after_dedup = len(long_df)

# Save to a new CSV
long_df.to_csv(OUTPUT_PATH, index=False)

print(f"\nOriginal shape: {df.shape}")
print(f"Long format shape: {long_df.shape}")
print(f"Typo rows removed: {before_typos - after_typos}")
print(f"Deduplicated rows removed: {before_dedup - after_dedup}")
print(f"\nSaved to: {OUTPUT_PATH}")
print(f"\nFirst few rows of transformed data:")
print(long_df.head(15))
