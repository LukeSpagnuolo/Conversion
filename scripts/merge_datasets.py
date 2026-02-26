#!/usr/bin/env python3
"""
Merge CSSAthleteConversion_long.csv into Conversion_Data_2026.csv
1. Add CSS column to Conv_2026 with YES if athlete appears in CSS dataset for that specific year with Class='YES'
2. Only mark rows if both athlete AND year AND Class='YES' match
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load both datasets
css_long = pd.read_csv(BASE_DIR / "CSSAthleteConversion_long.csv")
conversion_2026 = pd.read_csv(BASE_DIR / "Conversion_Data_2026.csv")

print("=" * 80)
print("LOADING DATASETS")
print("=" * 80)
print(f"CSS Athlete Conversion (Long): {css_long.shape[0]} rows")
print(f"Conversion Data 2026: {conversion_2026.shape[0]} rows")
print()

# Create a lookup table for CSS athletes by (First Name, Last Name, Year, Class)
# Only include rows where Class='YES'
css_lookup = {}
for _, row in css_long.iterrows():
    # Only add if Class='YES'
    if pd.notna(row['Class']) and str(row['Class']).upper() == 'YES':
        key = (row['First Name'].strip(), row['Last Name'].strip(), int(row['Year']))
        css_lookup[key] = True

print(f"CSS lookup table built: {len(css_lookup)} athlete-year combinations with Class='YES'")
print()

# Initialize CSS column
conversion_2026['CSS'] = 'NO'

# Mark rows where athlete+year exists in CSS dataset with Class='YES'
matches_found = 0

for idx, row in conversion_2026.iterrows():
    first_name = row['First Name'].strip()
    last_name = row['Last Name'].strip()
    year = int(row['Year'])
    
    key = (first_name, last_name, year)
    
    # If athlete+year exists in CSS data with Class='YES', mark as CSS='YES'
    if key in css_lookup:
        conversion_2026.loc[idx, 'CSS'] = 'YES'
        matches_found += 1

print("=" * 80)
print("RESULTS")
print("=" * 80)
print(f"Original Conversion_Data_2026 rows: {conversion_2026.shape[0]}")
print(f"Rows marked with CSS='YES': {matches_found}")
print()

# Count CSS YES rows
css_yes_count = len(conversion_2026[conversion_2026['CSS'] == 'YES'])
print(f"Final rows with CSS='YES': {css_yes_count}")
print()

# Show some examples
print("=" * 80)
print("EXAMPLES OF MARKED ROWS (CSS = YES)")
print("=" * 80)
css_yes_sample = conversion_2026[conversion_2026['CSS'] == 'YES'].head(10)
print(css_yes_sample[['Sport', 'First Name', 'Last Name', 'Year', 'Program', 'CSS']])
print()

# Save the merged dataset
output_path = BASE_DIR / "Conversion_Data_2026_with_CSS.csv"
conversion_2026.to_csv(output_path, index=False)
print(f"Saved to: {output_path}")
