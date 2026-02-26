#!/usr/bin/env python3
"""
Optimized recalculation of Years_Targeted and Convert_Year after consolidation
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load consolidated dataset
print("Loading dataset...")
df = pd.read_csv(BASE_DIR / "Conversion_Data_2026_consolidated.csv")

print(f"Dataset: {len(df):,} rows, {df['Full_Name'].nunique():,} unique athletes")
print()

# Define level hierarchy
level_hierarchy = {
    'Prov Dev 3': 0,
    'Prov Dev 2': 1,
    'Prov Dev 1': 2,
    'Uncarded': 3,
    'SC Carded': 4
}

# Sort by Full_Name and Year
df = df.sort_values(['Full_Name', 'Year']).reset_index(drop=True)

# Calculate Years_Targeted using groupby
print("Calculating Years_Targeted...")
years_targeted = df.groupby('Full_Name')['Year'].nunique().to_dict()
df['Years_Targeted'] = df['Full_Name'].map(years_targeted)

# Map program levels
print("Mapping program levels...")
df['Level_Value'] = df['Program'].map(level_hierarchy)

# Calculate Convert_Year
print("Calculating Convert_Year...")
df['Convert_Year'] = 'N'

# For each athlete, calculate progression
def calculate_convert_year(group):
    group = group.sort_values('Year').reset_index(drop=True)
    convert_year_list = []
    
    for i in range(len(group)):
        if i == 0:
            # First year is always 'N'
            convert_year_list.append('N')
        else:
            current_level = group.loc[i, 'Level_Value']
            prev_level = group.loc[i-1, 'Level_Value']
            
            if current_level > prev_level:
                convert_year_list.append('Y')
            else:
                convert_year_list.append('N')
    
    return pd.Series(convert_year_list, index=group.index)

print("Processing athlete progressions...")
df['Convert_Year'] = df.groupby('Full_Name', group_keys=False).apply(calculate_convert_year)

# Get statistics
y_count = len(df[df['Convert_Year'] == 'Y'])
n_count = len(df[df['Convert_Year'] == 'N'])

# Remove temporary column
df = df.drop('Level_Value', axis=1)

# Save
print()
print("Saving dataset...")
df.to_csv(BASE_DIR / "Conversion_Data_2026_consolidated.csv", index=False)

print()
print("=" * 100)
print("RECALCULATION COMPLETE")
print("=" * 100)
print()
print(f"✓ Total rows: {len(df):,}")
print(f"✓ Unique athletes: {df['Full_Name'].nunique():,}")
print(f"✓ Years_Targeted: {df['Years_Targeted'].min()}-{df['Years_Targeted'].max()} (avg: {df['Years_Targeted'].mean():.2f})")
print(f"✓ Convert_Year: Y={y_count:,} ({y_count/len(df)*100:.1f}%), N={n_count:,} ({n_count/len(df)*100:.1f}%)")
print(f"✓ CSS=YES matches: {len(df[df['CSS']=='YES']):,}")
print()
print(f"✓ Saved to: Conversion_Data_2026_consolidated.csv")
print()
