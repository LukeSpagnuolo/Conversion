#!/usr/bin/env python3
"""
Update Years Targeted and Convert Year columns based on CSS merged data
- Years Targeted: count of distinct years an athlete appears
- Convert Year: Y if level increased from previous year, N otherwise
Level hierarchy (lowest to highest): Prov Dev 3, Prov Dev 2, Prov Dev 1, Uncarded, SC Carded
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load merged dataset
df = pd.read_csv(BASE_DIR / "Conversion_Data_2026_with_CSS.csv")

print("=" * 80)
print("LOADING DATASET")
print("=" * 80)
print(f"Total rows: {df.shape[0]}")
print()

# Define level hierarchy (lower index = lower level)
level_hierarchy = {
    'Prov Dev 3': 0,
    'prov dev 3': 0,
    'PD3': 0,
    'Prov Dev 2': 1,
    'prov dev 2': 1,
    'PD2': 1,
    'Prov Dev 1': 2,
    'prov dev 1': 2,
    'PD1': 2,
    'Uncarded': 3,
    'uncarded': 3,
    'SC Carded': 4,
    'sc carded': 4,
    'SC Carded ': 4,  # with trailing space
    'Non-Targeted': 5,
    'non-targeted': 5,
}

def get_level_value(program):
    """Get numeric value for program level"""
    if pd.isna(program):
        return -1
    program_str = str(program).strip()
    return level_hierarchy.get(program_str, -1)

# Create full name for grouping
df['Full_Name'] = df['First Name'].str.strip() + " " + df['Last Name'].str.strip()

print("=" * 80)
print("PROCESSING DATA")
print("=" * 80)

# Sort by Name and Year to process chronologically
df = df.sort_values(['Full_Name', 'Year']).reset_index(drop=True)

# Initialize columns
df['Years_Targeted'] = 0
df['Convert_Year'] = 'N'

# Get unique athletes
athletes = df['Full_Name'].unique()
print(f"Total unique athletes: {len(athletes)}")

# Process each athlete
for athlete in athletes:
    athlete_rows = df[df['Full_Name'] == athlete].copy()
    athlete_indices = athlete_rows.index
    
    # Calculate Years Targeted (number of unique years)
    years_count = athlete_rows['Year'].nunique()
    df.loc[athlete_indices, 'Years_Targeted'] = years_count
    
    # Sort by year to check level progression
    athlete_rows = athlete_rows.sort_values('Year')
    
    prev_level_value = -1
    for idx, (row_idx, row) in enumerate(athlete_rows.iterrows()):
        current_level_value = get_level_value(row['Program'])
        
        # Check if level increased from previous year (only if not the first occurrence)
        if idx == 0:
            # First year - no previous year to compare, so always N
            df.loc[row_idx, 'Convert_Year'] = 'N'
        elif current_level_value > prev_level_value:
            # Level increased from previous year
            df.loc[row_idx, 'Convert_Year'] = 'Y'
        else:
            # No level increase
            df.loc[row_idx, 'Convert_Year'] = 'N'
        
        prev_level_value = current_level_value

print(f"Updated {len(df)} rows")
print()

print("=" * 80)
print("RESULTS")
print("=" * 80)

# Show statistics
print(f"Years Targeted - Min: {df['Years_Targeted'].min()}, Max: {df['Years_Targeted'].max()}, Mean: {df['Years_Targeted'].mean():.2f}")
print(f"Convert Year - Y count: {len(df[df['Convert_Year'] == 'Y'])}, N count: {len(df[df['Convert_Year'] == 'N'])}")
print()

# Show examples
print("=" * 80)
print("EXAMPLES OF UPDATED DATA")
print("=" * 80)

# Example 1: Show a user with multiple years and progression
multi_year_athletes = df[df['Years_Targeted'] > 2].drop_duplicates('Full_Name').head(3)
for _, athlete in multi_year_athletes.iterrows():
    athlete_name = athlete['Full_Name']
    athlete_data = df[df['Full_Name'] == athlete_name][['Sport', 'First Name', 'Last Name', 'Year', 'Program', 'Years_Targeted', 'Convert_Year']].sort_values('Year')
    print(f"\n{athlete_name} (Years Targeted: {athlete['Years_Targeted']})")
    print(athlete_data.to_string(index=False))

# Show CSS athletes with conversion
print()
print("=" * 80)
print("CSS ATHLETES WITH CONVERSION")
print("=" * 80)
css_converts = df[(df['CSS'] == 'YES') & (df['Convert_Year'] == 'Y')].drop_duplicates('Full_Name').head(5)
for _, athlete in css_converts.iterrows():
    athlete_name = athlete['Full_Name']
    athlete_data = df[df['Full_Name'] == athlete_name][['Sport', 'Year', 'Program', 'Years_Targeted', 'Convert_Year', 'CSS']].sort_values('Year')
    print(f"\n{athlete_name}")
    print(athlete_data.to_string(index=False))

print()

# Save updated dataset
output_path = BASE_DIR / "Conversion_Data_2026_with_CSS_updated.csv"
df.to_csv(output_path, index=False)
print("=" * 80)
print(f"Saved to: {output_path}")
print("=" * 80)
