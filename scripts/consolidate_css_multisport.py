"""
Consolidate multisport CSS athletes.
For athletes appearing in both a specific sport and 'Multisport', keep the specific sport entry.
Update CSS column accordingly.
"""
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/workspaces/Conversion")

print("Loading final dataset...")
df = pd.read_csv(BASE_DIR / "Conversion_Data_2026_final.csv")

print(f"Initial dataset: {len(df)} rows")
print(f"Initial CSS entries: {(df['CSS'] == 'YES').sum()}")
print()

# Identify CSS athletes with multiple sports
css_df = df[df['CSS'] == 'YES'].copy()
css_df['Full_Name'] = css_df['First Name'] + ' ' + css_df['Last Name']

multisport_athletes = css_df.groupby('Full_Name')['Sport'].apply(list)
multisport_athletes = multisport_athletes[multisport_athletes.apply(lambda x: len(set(x)) > 1)]

print(f"Found {len(multisport_athletes)} CSS athletes with multiple sports:")
for athlete, sports in multisport_athletes.items():
    print(f"  {athlete}: {set(sports)}")
print()

# For each multisport athlete, identify and consolidate
rows_to_drop = []

for athlete_name in multisport_athletes.index:
    athlete_rows = css_df[css_df['Full_Name'] == athlete_name]
    sports = athlete_rows['Sport'].unique()
    
    # Prioritize: keep specific sport, drop 'Multisport'
    if 'Multisport' in sports and len(sports) > 1:
        # Find the non-Multisport sport
        specific_sport = [s for s in sports if s != 'Multisport'][0]
        
        # Drop all Multisport entries for this athlete
        multisport_rows = athlete_rows[athlete_rows['Sport'] == 'Multisport']
        rows_to_drop.extend(multisport_rows.index.tolist())
        
        print(f"Consolidating {athlete_name}:")
        print(f"  Keeping: {specific_sport}")
        print(f"  Dropping: Multisport ({len(multisport_rows)} rows)")

print()

# Drop the Multisport entries
if rows_to_drop:
    print(f"Removing {len(rows_to_drop)} Multisport entries...")
    df = df.drop(rows_to_drop)
    df = df.reset_index(drop=True)
    print(f"✓ Dataset reduced to {len(df)} rows")
else:
    print("No consolidations needed")

print()

# Verify CSS column
css_count = (df['CSS'] == 'YES').sum()
css_unique = (df[(df['CSS'] == 'YES')]['First Name'].astype(str) + ' ' + 
              df[(df['CSS'] == 'YES')]['Last Name'].astype(str)).nunique()

print(f"Final CSS statistics:")
print(f"  CSS entries: {css_count}")
print(f"  Unique CSS athletes: {css_unique}")
print()

# Check for remaining multisport athletes
if css_count > 0:
    css_df_final = df[df['CSS'] == 'YES'].copy()
    css_df_final['Full_Name'] = css_df_final['First Name'] + ' ' + css_df_final['Last Name']
    remaining_multisport = css_df_final.groupby('Full_Name')['Sport'].nunique()
    remaining_multisport = remaining_multisport[remaining_multisport > 1]
    
    if len(remaining_multisport) > 0:
        print(f"Remaining multisport CSS athletes: {len(remaining_multisport)}")
        for athlete, num_sports in remaining_multisport.items():
            print(f"  {athlete}: {num_sports} sports")
    else:
        print("✓ All CSS athletes have single sport entries")
else:
    print("No CSS athletes in final dataset")

# Save
output_file = BASE_DIR / "Conversion_Data_2026_final.csv"
df.to_csv(output_file, index=False)
print()
print(f"✓ Saved: {output_file}")
print(f"  Total rows: {len(df)}")
print(f"  Total unique athletes: {(df['First Name'].astype(str) + ' ' + df['Last Name'].astype(str)).nunique()}")
