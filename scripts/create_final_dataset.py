"""
Create final dataset by preserving original consolidated metrics and adding new nomination data.
Uses original Convert_Year from consolidated dataset (4,948 conversions).
For nomination athletes, populates CSS column based on:
- SportLevel='CSS' OR
- Nominating Body='Canadian Sport School'
New nomination athletes get Convert_Year='N' since they have no prior conversion history.
"""
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/workspaces/Conversion")

print("Loading datasets...")
consolidated = pd.read_csv(BASE_DIR / "Conversion_Data_2026_consolidated.csv")
nomination_master = pd.read_csv(BASE_DIR / "Nomination_Master_2025only(26 FY (Mar 31- Mar 31)).csv", encoding='ISO-8859-1')

print(f"Consolidated: {len(consolidated)} rows")
print(f"Nomination Master: {len(nomination_master)} rows")
print()

# Prepare nomination data to match consolidated columns
prepare_nom = nomination_master.copy()
prepare_nom = prepare_nom.rename(columns={
    'Sex Of Competition': 'Gender',
    'DOB': 'Date of Birth',
    'Fiscal Year': 'Year'
})
prepare_nom['Full_Name'] = prepare_nom['First Name'] + ' ' + prepare_nom['Last Name']

# Populate CSS column based on SportLevel or Nominating Body
print("Populating CSS column for nomination athletes...")
prepare_nom['CSS'] = 'NO'

css_count_sport_level = 0
css_count_nominating_body = 0

for idx, row in prepare_nom.iterrows():
    is_css = False
    
    # Check SportLevel column
    if 'SportLevel' in prepare_nom.columns:
        sport_level = row.get('SportLevel', '')
        if pd.notna(sport_level) and str(sport_level).strip().upper() == 'CSS':
            is_css = True
            css_count_sport_level += 1
    
    # Check Nominating Body column (if not already marked)
    if 'Nominating Body' in prepare_nom.columns and not is_css:
        nominating_body = row.get('Nominating Body', '')
        if pd.notna(nominating_body):
            nominating_body_str = str(nominating_body).strip().upper()
            if 'CANADIAN SPORT SCHOOL' in nominating_body_str or nominating_body_str == 'CSS':
                is_css = True
                css_count_nominating_body += 1
    
    if is_css:
        prepare_nom.loc[idx, 'CSS'] = 'YES'

print(f"  Marked {css_count_sport_level} via SportLevel='CSS'")
print(f"  Marked {css_count_nominating_body} via Nominating Body='Canadian Sport School'")
print(f"  Total CSS='YES': {(prepare_nom['CSS'] == 'YES').sum()}")
print()

prepare_nom['Years_Targeted'] = 1  # They only appear in nomination year
prepare_nom['Convert_Year'] = 'N'  # No conversion data for new athletes

# Reorder to match consolidated
prepare_nom = prepare_nom[['Sport', 'First Name', 'Last Name', 'Gender', 'Date of Birth', 'Year', 'Program', 'Full_Name', 'CSS', 'Years_Targeted', 'Convert_Year']]

# Merge
final = pd.concat([consolidated, prepare_nom], ignore_index=True)

print("Final dataset:")
print(f"  Total rows: {len(final)}")
print(f"  Unique athletes: {(final['First Name'].astype(str) + ' ' + final['Last Name'].astype(str)).nunique()}")
print()

print("CSS statistics:")
print(f"  CSS='YES': {(final['CSS'] == 'YES').sum()}")
print(f"  CSS='NO': {(final['CSS'] == 'NO').sum()}")
print()

print("Conversion statistics (preserved from original):")
print(f"  Convert_Year Y: {(final['Convert_Year'] == 'Y').sum()}")
print(f"  Convert_Year N: {(final['Convert_Year'] == 'N').sum()}")
print(f"  Conversion rate: {(final['Convert_Year'] == 'Y').sum()/len(final)*100:.1f}%")
print()

print("Years_Targeted statistics:")
print(f"  Min: {final['Years_Targeted'].min()}")
print(f"  Max: {final['Years_Targeted'].max()}")
print(f"  Average: {final['Years_Targeted'].mean():.2f}")
print()

# Save
output_file = BASE_DIR / "Conversion_Data_2026_final.csv"
final.to_csv(output_file, index=False)
print(f"✓ Saved: {output_file}")
