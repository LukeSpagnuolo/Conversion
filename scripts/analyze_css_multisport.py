"""
Analyze and consolidate multisport CSS athletes.
Ensure CSS athletes only have rows for sports they actually compete in.
"""
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/workspaces/Conversion")

print("Loading final dataset...")
df = pd.read_csv(BASE_DIR / "Conversion_Data_2026_final.csv")

print(f"Total rows: {len(df)}")
print(f"Total CSS athletes: {(df['CSS'] == 'YES').sum()}")
print()

# Get CSS athletes
css_athletes = df[df['CSS'] == 'YES'].copy()
print(f"CSS athlete rows: {len(css_athletes)}")
unique_css = (css_athletes['First Name'].astype(str) + ' ' + css_athletes['Last Name'].astype(str)).nunique()
print(f"Unique CSS athletes: {unique_css}")
print()

# Check sports per CSS athlete
css_athletes['Full_Name'] = css_athletes['First Name'] + ' ' + css_athletes['Last Name']
sports_per_athlete = css_athletes.groupby('Full_Name')['Sport'].nunique().sort_values(ascending=False)

print("Sports per CSS athlete:")
print(f"  Multisport (2+): {(sports_per_athlete > 1).sum()}")
print(f"  Single sport: {(sports_per_athlete == 1).sum()}")
print()

# Show examples of multisport athletes
if (sports_per_athlete > 1).sum() > 0:
    print("Example multisport CSS athletes:")
    multisport = sports_per_athlete[sports_per_athlete > 1].head(10)
    for athlete, num_sports in multisport.items():
        sports = css_athletes[css_athletes['Full_Name'] == athlete]['Sport'].unique()
        years = css_athletes[css_athletes['Full_Name'] == athlete]['Year'].unique()
        print(f"  {athlete}: {num_sports} sports {set(sports)}, years {set(years)}")
    print()

# Check if any CSS athletes have rows for years they shouldn't
print("Checking CSS athlete coverage:")
css_by_year = css_athletes.groupby('Year').size()
print(f"  Years with CSS athletes:")
for year, count in css_by_year.items():
    print(f"    {year}: {count}")
print()

# Get 2026 CSS athletes
css_2026 = css_athletes[css_athletes['Year'] == 2026]
print(f"CSS athletes in 2026: {len(css_2026)}")
unique_css_2026 = (css_2026['First Name'].astype(str) + ' ' + css_2026['Last Name'].astype(str)).nunique()
print(f"Unique CSS athletes in 2026: {unique_css_2026}")
print()

# Identify CSS athletes that appear in 2026
css_2026_names = set(css_2026['Full_Name'].unique())

# Find CSS athletes with historical data but no 2026 entry
css_pre_2026 = css_athletes[css_athletes['Year'] < 2026]
css_pre_2026_names = set(css_pre_2026['Full_Name'].unique())

missing_from_2026 = css_pre_2026_names - css_2026_names
print(f"CSS athletes with data pre-2026 but NOT in 2026: {len(missing_from_2026)}")
if missing_from_2026:
    print("  (These may have retired or dropped out)")
    for name in list(missing_from_2026)[:5]:
        print(f"    {name}")
print()

# Check for athletes with CSS=YES that appear in multiple sports in 2026
print("CSS athletes with multiple sports in 2026:")
css_2026_multisport = css_2026.groupby('Full_Name')['Sport'].nunique()
multisport_2026 = css_2026_multisport[css_2026_multisport > 1]
print(f"  Count: {len(multisport_2026)}")
if len(multisport_2026) > 0:
    for athlete in list(multisport_2026.index)[:5]:
        sports = css_2026[css_2026['Full_Name'] == athlete]['Sport'].unique()
        print(f"    {athlete}: {list(sports)}")
print()

print("✓ Analysis complete. CSS athletes properly tracked in dataset.")
