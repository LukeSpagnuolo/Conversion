#!/usr/bin/env python3
"""
Transform the CSV from wide format (year levels as columns) to long format
(year levels as rows)
"""

import pandas as pd
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Read the CSV, skipping the metadata rows (first 5 rows)
df = pd.read_csv(BASE_DIR / "CSSAthleteConversion_old.csv", skiprows=5)

# Identify the year level columns and their pairs
# Pattern: columns like "11/12 Level" and "11/12 Class"
year_pattern = re.compile(r'(\d{2}/\d{2})\s+(Level|Class)')

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

for idx, row in df.iterrows():
    # Get the ID information for this person
    id_values = row[id_cols].to_dict()
    
    # Create a row for each year
    for year in years:
        level_col = f"{year} Level"
        class_col = f"{year} Class"
        
        # Check if these columns exist
        if level_col in df.columns and class_col in df.columns:
            new_row = id_values.copy()
            # Convert year format (e.g., "11/12" -> 2012)
            year_parts = year.split('/')
            later_year = int(year_parts[1])
            # Add 2000 to convert 2-digit year to 4-digit year
            full_year = 2000 + later_year
            new_row['Year'] = full_year
            new_row['Level'] = row.get(level_col, '')
            new_row['Class'] = row.get(class_col, '')
            long_rows.append(new_row)

# Create the long format dataframe
long_df = pd.DataFrame(long_rows)

# Keep only the specified columns in the requested order
cols_order = ['Sport', 'First Name', 'Last Name', 'Year', 'Level', 'Class']
long_df = long_df[cols_order]

# Remove rows where Level is 'X' or NaN (actual null values)
long_df = long_df[~long_df['Level'].isin(['X']) & long_df['Level'].notna()]

# Keep only rows where Class is "YES" AND Level is 0 or Prov Dev 3
long_df = long_df[
    (long_df['Class'].str.upper() == 'YES') & 
    (long_df['Level'].isin(['0', 'Prov Dev 3', 'PD3', 'prov dev 3', 'pd3']))
]

# Save to a new CSV
output_path = BASE_DIR / "CSSAthleteConversion_long.csv"
long_df.to_csv(output_path, index=False)

print(f"\nOriginal shape: {df.shape}")
print(f"Long format shape: {long_df.shape}")
print(f"\nSaved to: {output_path}")
print(f"\nFirst few rows of transformed data:")
print(long_df.head(15))
