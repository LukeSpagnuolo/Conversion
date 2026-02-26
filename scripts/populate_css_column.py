#!/usr/bin/env python3
"""
Populate CSS column based on new rules:
1. For historical conversion athletes: Check if they appear in CSS dataset for that SAME year with Class='YES'
2. For nomination athletes: Check if SportLevel='CSS' OR Nominating Body='Canadian Sport School'
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

print("=" * 100)
print("REPOPULATING CSS COLUMN WITH NEW LOGIC")
print("=" * 100)
print()

# Load the CSS reference dataset
print("Loading CSS reference dataset...")
css_long = pd.read_csv(BASE_DIR / "CSSAthleteConversion_long.csv")
print(f"  Rows: {len(css_long)}")
print(f"  Columns: {list(css_long.columns)}")
print()

# Create a lookup table for CSS athletes by (First Name, Last Name, Year, Class)
css_lookup = {}
for _, row in css_long.iterrows():
    key = (row['First Name'].strip(), row['Last Name'].strip(), int(row['Year']))
    css_lookup[key] = row['Class']

print(f"CSS lookup table built: {len(css_lookup)} athlete-year combinations")
print()

# Load the conversion dataset
print("Loading historical conversion data...")
conversion_2026 = pd.read_csv(BASE_DIR / "Conversion_Data_2026.csv")
print(f"  Rows: {len(conversion_2026)}")
print()

# Populate CSS column for historical conversion data
# Check (First Name, Last Name, Year) against CSS dataset
print("Populating CSS column for historical conversion data...")
conversion_2026['CSS'] = 'NO'

matches = 0
for idx, row in conversion_2026.iterrows():
    first_name = row['First Name'].strip()
    last_name = row['Last Name'].strip()
    year = int(row['Year'])
    
    key = (first_name, last_name, year)
    
    # If athlete+year exists in CSS data and Class='YES', mark as CSV
    if key in css_lookup:
        class_value = css_lookup[key]
        if pd.notna(class_value) and str(class_value).upper() == 'YES':
            conversion_2026.loc[idx, 'CSS'] = 'YES'
            matches += 1

print(f"  Marked {matches} rows with CSS='YES'")
print()

# Load nomination data
print("Loading nomination data...")
nomination_file = BASE_DIR / "Nomination_Master_2025only(26 FY (Mar 31- Mar 31)).csv"
nomination_data = pd.read_csv(nomination_file, encoding='ISO-8859-1')
print(f"  Rows: {len(nomination_data)}")
print(f"  Columns: {list(nomination_data.columns)}")
print()

# Check for SportLevel and Nominating Body columns
has_sport_level = 'SportLevel' in nomination_data.columns
has_nominating_body = 'Nominating Body' in nomination_data.columns

print(f"  Has 'SportLevel' column: {has_sport_level}")
print(f"  Has 'Nominating Body' column: {has_nominating_body}")
print()

# Populate CSS column for nomination data
print("Populating CSS column for nomination data...")
nomination_data['CSS'] = 'NO'

css_count_sport_level = 0
css_count_nominating_body = 0

for idx, row in nomination_data.iterrows():
    is_css = False
    
    # Check SportLevel
    if has_sport_level:
        sport_level = row.get('SportLevel', '')
        if pd.notna(sport_level) and str(sport_level).strip().upper() == 'CSS':
            is_css = True
            css_count_sport_level += 1
    
    # Check Nominating Body
    if has_nominating_body and not is_css:
        nominating_body = row.get('Nominating Body', '')
        if pd.notna(nominating_body):
            nominating_body_str = str(nominating_body).strip().upper()
            if 'CANADIAN SPORT SCHOOL' in nominating_body_str or nominating_body_str == 'CSS':
                is_css = True
                css_count_nominating_body += 1
    
    if is_css:
        nomination_data.loc[idx, 'CSS'] = 'YES'

print(f"  Marked {css_count_sport_level} rows via SportLevel='CSS'")
print(f"  Marked {css_count_nominating_body} rows via Nominating Body='Canadian Sport School'")
print(f"  Total marked: {css_count_sport_level + css_count_nominating_body}")
print()

# Prepare both datasets to match consolidated format
print("Preparing datasets for consolidation...")

# Prepare conversion data
prep_conversion = conversion_2026.copy()

# Check column names and standardize them
print(f"  Conversion columns: {list(prep_conversion.columns)}")

# Rename columns with spaces to underscores
prep_conversion.columns = prep_conversion.columns.str.replace(' ', '_')

prep_conversion['Full_Name'] = (prep_conversion['First_Name'].astype(str) + ' ' + 
                                 prep_conversion['Last_Name'].astype(str))

# Reorder columns to match final format
column_order = ['Sport', 'First_Name', 'Last_Name', 'Gender', 'Date_of_Birth', 'Year', 
                'Program', 'Full_Name', 'CSS', 'Years_Targeted', 'Convert_Year']
# Filter to only existing columns
column_order = [col for col in column_order if col in prep_conversion.columns]
prep_conversion = prep_conversion[column_order]

# Rename back to space-separated for consistency with final output
prep_conversion.columns = prep_conversion.columns.str.replace('_', ' ')

# Prepare nomination data
prep_nomination = nomination_data.copy()
prep_nomination = prep_nomination.rename(columns={
    'Sex Of Competition': 'Gender',
    'DOB': 'Date of Birth',
    'Fiscal Year': 'Year',
    'Carding Level': 'Program'
}, errors='ignore')
prep_nomination['Full Name'] = (prep_nomination['First Name'].astype(str) + ' ' + 
                                prep_nomination['Last Name'].astype(str))
prep_nomination['Years Targeted'] = 1
prep_nomination['Convert Year'] = 'N'

# Reorder columns
column_order = ['Sport', 'First Name', 'Last Name', 'Gender', 'Date of Birth', 'Year', 
                'Program', 'Full Name', 'CSS', 'Years Targeted', 'Convert Year']
prep_nomination = prep_nomination[column_order]

print(f"  Conversion data prepared: {len(prep_conversion)} rows")
print(f"  Nomination data prepared: {len(prep_nomination)} rows")
print()

# Merge both datasets
print("Merging datasets...")
final_dataset = pd.concat([prep_conversion, prep_nomination], ignore_index=True)
print(f"  Merged dataset: {len(final_dataset)} rows")
print()

# Statistics
print("=" * 100)
print("FINAL CSS STATISTICS")
print("=" * 100)
css_yes_count = (final_dataset['CSS'] == 'YES').sum()
css_no_count = (final_dataset['CSS'] == 'NO').sum()
css_unique = (final_dataset[final_dataset['CSS'] == 'YES']['First Name'].astype(str) + ' ' + 
              final_dataset[final_dataset['CSS'] == 'YES']['Last Name'].astype(str)).nunique()

print(f"Total CSS='YES': {css_yes_count}")
print(f"Total CSS='NO': {css_no_count}")
print(f"Unique CSS athletes: {css_unique}")
print(f"CSS percentage: {css_yes_count/len(final_dataset)*100:.2f}%")
print()

# Show sample CSS athletes
print("Sample CSS athletes (first 5):")
css_sample = final_dataset[final_dataset['CSS'] == 'YES'][['Sport', 'First Name', 'Last Name', 'Year', 'Program']].drop_duplicates().head()
for idx, row in css_sample.iterrows():
    print(f"  {row['Sport']}: {row['First Name']} {row['Last Name']} ({row['Year']}) - {row['Program']}")
print()

# Save the dataset
output_file = BASE_DIR / "Conversion_Data_2026_final.csv"
final_dataset.to_csv(output_file, index=False)
print(f"✓ Saved: {output_file}")
print(f"  Total rows: {len(final_dataset)}")
print(f"  Total unique athletes: {(final_dataset['First Name'].astype(str) + ' ' + final_dataset['Last Name'].astype(str)).nunique()}")
