"""
Recalculate Years_Targeted and Convert_Year metrics for merged dataset.
Applies the same logic used for consolidated dataset to the merged data.
"""
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/workspaces/Conversion")

print("Loading merged dataset...")
df = pd.read_csv(BASE_DIR / "Conversion_Data_2026_merged.csv")
print(f"Total rows: {len(df)}")
print(f"Unique athletes: {(df['First Name'].astype(str) + ' ' + df['Last Name'].astype(str)).nunique()}")
print(f"Year range: {df['Year'].min()} to {df['Year'].max()}")
print()

# Define program level hierarchy (higher number = more advanced)
LEVEL_HIERARCHY = {
    'Prov Dev 3': 0,
    'Prov Dev 2': 1,
    'Prov Dev 1': 2,
    'Uncarded': 3,
    'SC Carded': 4
}

print("Calculating Years_Targeted...")
# Years_Targeted: Count how many years the athlete was in the dataset
years_targeted = df.groupby(['First Name', 'Last Name'])['Year'].nunique().reset_index()
years_targeted.columns = ['First Name', 'Last Name', 'years_count']

# Merge back to original dataframe
df = df.merge(years_targeted, on=['First Name', 'Last Name'], how='left')
df['Years_Targeted'] = df['years_count']
df = df.drop(columns=['years_count'])

print(f"  Years_Targeted range: {df['Years_Targeted'].min()} to {df['Years_Targeted'].max()}")
print(f"  Average: {df['Years_Targeted'].mean():.2f}")
print()

print("Calculating Convert_Year...")
# For Convert_Year, check if level increased from one year to next
# First, prepare data by athlete and year
athlete_data = df.sort_values(['First Name', 'Last Name', 'Year']).copy()

# Convert Program to numeric level for comparison
athlete_data['Level'] = athlete_data['Program'].map(LEVEL_HIERARCHY)

# Check for level increases
convert_year_dict = {}

for (first, last), group in athlete_data.groupby(['First Name', 'Last Name']):
    group = group.sort_values('Year')
    converted = False
    
    for idx in range(1, len(group)):
        prev_level = group.iloc[idx-1]['Level']
        curr_level = group.iloc[idx]['Level']
        
        # Check if level increased (converted to higher level)
        if pd.notna(prev_level) and pd.notna(curr_level) and curr_level > prev_level:
            converted = True
            break
    
    convert_year_dict[(first, last)] = 'Y' if converted else 'N'

# Map back to dataframe
df['Convert_Key'] = df['First Name'].astype(str) + '|' + df['Last Name'].astype(str)
df['Convert_Year'] = df['Convert_Key'].map(
    lambda key: convert_year_dict.get(tuple(key.split('|')), 'N')
)
df = df.drop(columns=['Convert_Key'])

print(f"  Convert_Year Y: {(df['Convert_Year'] == 'Y').sum()}")
print(f"  Convert_Year N: {(df['Convert_Year'] == 'N').sum()}")
print()

# Save updated dataset
output_file = BASE_DIR / "Conversion_Data_2026_final.csv"
df.to_csv(output_file, index=False)

print(f"✓ Saved final dataset: {output_file}")
print(f"  Rows: {len(df)}")
print(f"  Unique athletes: {(df['First Name'].astype(str) + ' ' + df['Last Name'].astype(str)).nunique()}")
print(f"  Columns: {len(df.columns)}")
print()

# Summary statistics
print("Final statistics:")
print(f"  Years_Targeted: min={df['Years_Targeted'].min()}, max={df['Years_Targeted'].max()}, avg={df['Years_Targeted'].mean():.2f}")
print(f"  CSS matches: {(df['CSS'] == 'YES').sum()}")
print(f"  Conversions (Y): {(df['Convert_Year'] == 'Y').sum()} ({(df['Convert_Year'] == 'Y').sum()/len(df)*100:.1f}%)")
print(f"  Non-conversions (N): {(df['Convert_Year'] == 'N').sum()} ({(df['Convert_Year'] == 'N').sum()/len(df)*100:.1f}%)")
