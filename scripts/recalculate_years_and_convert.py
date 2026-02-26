import pandas as pd
import numpy as np

df = pd.read_csv('Conversion_Data_2026_final.csv')

# Define program hierarchy
program_hierarchy = {
    'Prov Dev 3': 1,
    'Prov Dev 2': 2,
    'Prov Dev 1': 3,
    'Uncarded': 4,
    'SC Carded': 5
}

print("Recalculating Years Targeted and Convert Year...")

# 1. Recalculate Years Targeted - count unique years per athlete
years_targeted_map = df.groupby('Full_Name')['Year'].nunique().to_dict()
df['Years Targeted'] = df['Full_Name'].map(years_targeted_map)

print(f"✓ Years Targeted recalculated")

# 2. Recalculate Convert Year
# Sort by Full_Name and Year to ensure proper ordering
df = df.sort_values(['Full_Name', 'Year']).reset_index(drop=True)

# Initialize Convert Year as N for all
df['Convert Year'] = 'N'

# For each athlete, mark conversions when program improves
for athlete_name in df['Full_Name'].unique():
    athlete_mask = df['Full_Name'] == athlete_name
    athlete_df = df[athlete_mask].copy()
    athlete_indices = df[athlete_mask].index.tolist()
    
    # Get unique years for this athlete in order
    years_in_order = sorted(athlete_df['Year'].unique())
    
    for i in range(1, len(years_in_order)):
        curr_year = years_in_order[i]
        prev_year = years_in_order[i-1]
        
        # Get program levels for each year
        prev_year_programs = athlete_df[athlete_df['Year'] == prev_year]['Program'].unique()
        curr_year_programs = athlete_df[athlete_df['Year'] == curr_year]['Program'].unique()
        
        # Get max program level for each year (in case multiple programs per year)
        prev_max_level = max([program_hierarchy.get(p, 0) for p in prev_year_programs])
        curr_max_level = max([program_hierarchy.get(p, 0) for p in curr_year_programs])
        
        # If current year's max level > previous year's max level, mark as conversion
        if curr_max_level > prev_max_level:
            # Mark all records in current year as Y
            conversion_indices = df[(df['Full_Name'] == athlete_name) & (df['Year'] == curr_year)].index.tolist()
            df.loc[conversion_indices, 'Convert Year'] = 'Y'

print(f"✓ Convert Year recalculated")

# Save
df.to_csv('Conversion_Data_2026_final.csv', index=False)

print(f"\n✓ File saved!")
print(f"\nSummary:")
print(f"Total records: {len(df)}")
print(f"\nYears Targeted distribution:")
print(df['Years Targeted'].value_counts().sort_index())
print(f"\nConvert Year distribution:")
print(df['Convert Year'].value_counts())

# Show examples
print(f"\n\nExample: andrewdavis")
example = df[df['Full_Name'] == 'andrewdavis'][['Full_Name', 'Sport', 'Year', 'Program', 'Years Targeted', 'Convert Year']].sort_values('Year')
print(example.head(15).to_string())
