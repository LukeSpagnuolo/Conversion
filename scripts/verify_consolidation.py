import pandas as pd

# Load and analyze final dataset
df = pd.read_csv('/workspaces/Conversion/Conversion_Data_2026_final.csv')

# Basic stats
total_rows = len(df)
unique_athletes = (df['First Name'].astype(str) + ' ' + df['Last Name'].astype(str)).nunique()

# Conversion metrics  
css_matches = (df['CSS'] == 'YES').sum()
convert_y = (df['Convert_Year'] == 'Y').sum()
convert_n = (df['Convert_Year'] == 'N').sum()
conversion_rate = convert_y / total_rows * 100

# Years targeted
years_min = df['Years_Targeted'].min()
years_max = df['Years_Targeted'].max()
years_avg = df['Years_Targeted'].mean()

# Print results
print("=" * 60)
print("FINAL DATASET CONSOLIDATION COMPLETE")
print("=" * 60)
print(f"\nTotal rows: {total_rows:,}")
print(f"Unique athletes: {unique_athletes:,}")
print()
print("Conversion Metrics:")
print(f"  CSS matches: {css_matches}")
print(f"  Convert_Year Y: {convert_y:,} ({convert_y/total_rows*100:.1f}%)")
print(f"  Convert_Year N: {convert_n:,} ({convert_n/total_rows*100:.1f}%)")
print()
print("Years Targeted:")
print(f"  Range: {years_min} - {years_max}")
print(f"  Average: {years_avg:.2f}")
print()
print("✓ Final dataset ready for analysis")
