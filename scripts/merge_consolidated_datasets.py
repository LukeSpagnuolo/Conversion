"""
Merge consolidated nomination dataset with main consolidated dataset.
Combines 43,469 rows of historical data with 1,022 new nomination athletes.
"""
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/workspaces/Conversion")

print("Loading datasets...")
main_df = pd.read_csv(BASE_DIR / "Conversion_Data_2026_consolidated.csv")
nomination_df = pd.read_csv(BASE_DIR / "Nomination_Athletes_consolidated.csv")

print(f"Main dataset: {len(main_df)} rows, {list(main_df.columns)}")
print(f"Nomination dataset: {len(nomination_df)} rows, {list(nomination_df.columns)}")
print()

# Check column alignment
main_cols = set(main_df.columns)
nom_cols = set(nomination_df.columns)

print("Column comparison:")
print(f"  Main only: {main_cols - nom_cols}")
print(f"  Nomination only: {nom_cols - main_cols}")
print()

# Prepare nomination data to match main dataset columns
# Main dataset columns: Sport, First Name, Last Name, Gender, Date of Birth, Year, Program, Full_Name, CSS, Years_Targeted, Convert_Year

# Map nomination columns to main dataset
prep_nomination = nomination_df.copy()

# Rename columns to match
prep_nomination = prep_nomination.rename(columns={
    'Sex Of Competition': 'Gender',
    'DOB': 'Date of Birth',
    'Fiscal Year': 'Year'
})

# Create Full_Name column
prep_nomination['Full_Name'] = prep_nomination['First Name'] + ' ' + prep_nomination['Last Name']

# Add missing columns from main dataset
prep_nomination['CSS'] = 'NO'  # New athletes are not CSS
prep_nomination['Years_Targeted'] = 0  # Will recalculate
prep_nomination['Convert_Year'] = 'N'  # No conversion data for nomination

# Reorder columns to match main dataset
column_order = ['Sport', 'First Name', 'Last Name', 'Gender', 'Date of Birth', 'Year', 'Program', 'Full_Name', 'CSS', 'Years_Targeted', 'Convert_Year']
prep_nomination = prep_nomination[column_order]

print(f"Nomination dataset prepared: {len(prep_nomination)} rows")
print(f"Columns: {list(prep_nomination.columns)}")
print()

# Concatenate datasets
merged_df = pd.concat([main_df, prep_nomination], ignore_index=True)
print(f"Merged dataset: {len(merged_df)} rows")
print(f"Expected: {len(main_df) + len(prep_nomination)} rows")
print()

# Count unique athletes
unique_athletes = (merged_df['First Name'].astype(str) + ' ' + merged_df['Last Name'].astype(str)).nunique()
print(f"Unique athletes: {unique_athletes}")
print()

# Statistics
print("Conversion statistics before recalculation:")
print(f"  CSS matches: {(merged_df['CSS'] == 'YES').sum()}")
print(f"  Convert_Year Y: {(merged_df['Convert_Year'] == 'Y').sum()}")
print(f"  Convert_Year N: {(merged_df['Convert_Year'] == 'N').sum()}")
print()

# Save merged dataset
output_file = BASE_DIR / "Conversion_Data_2026_merged.csv"
merged_df.to_csv(output_file, index=False)
print(f"✓ Saved merged dataset: {output_file}")
print(f"  Rows: {len(merged_df)}")
print(f"  Unique athletes: {unique_athletes}")
print(f"  Columns: {len(merged_df.columns)}")
