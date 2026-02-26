#!/usr/bin/env python3
"""
Comprehensive CSS column population:
1. For historical conversion athletes: Match (First Name, Last Name, Year) to CSS dataset with Class='YES'
2. For CSS athletes NOT in conversion data: Add them as new rows with CSS='YES'
3. For nomination athletes: Check SportLevel='CSS' or Nominating Body='Canadian Sport School'
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path("/workspaces/Conversion")

print("=" * 100)
print("COMPREHENSIVE CSS POPULATION")
print("=" * 100)
print()

# ============================================================================
# STEP 1: Load all source datasets
# ============================================================================
print("Loading datasets...")
css_long = pd.read_csv(BASE_DIR / "CSSAthleteConversion_long.csv")
conversion_2026 = pd.read_csv(BASE_DIR / "Conversion_Data_2026.csv")
nomination_master = pd.read_csv(BASE_DIR / "Nomination_Master_2025only(26 FY (Mar 31- Mar 31)).csv", encoding='ISO-8859-1')

css_yes = css_long[css_long['Class'] == 'YES'].copy()

print(f"  CSS dataset: {len(css_long)} rows (with Class='YES': {len(css_yes)})")
print(f"  Conversion data: {len(conversion_2026)} rows")
print(f"  Nomination data: {len(nomination_master)} rows")
print()

# ============================================================================
# STEP 2: Build CSS lookup table
# ============================================================================
print("Building CSS reference lookup...")

# Build lookup for CSS dataset (athlete, year) combinations
css_keys = set()
css_athletes = set()

for _, row in css_yes.iterrows():
    first = row['First Name'].strip()
    last = row['Last Name'].strip()
    year = int(row['Year'])
    css_keys.add((first, last, year))
    css_athletes.add((first, last))

print(f"  CSS lookup: {len(css_keys)} unique (athlete, year) combinations")
print(f"  Unique CSS athletes: {len(css_athletes)}")
print()

# Build lookup for conversion data (athlete, year) combinations
print("Building conversion data lookup...")
conv_keys = set()
for _, row in conversion_2026.iterrows():
    first = row['First Name'].strip()
    last = row['Last Name'].strip()
    year = int(row['Year'])
    conv_keys.add((first, last, year))

print(f"  Conversion data (athlete, year) combinations: {len(conv_keys)}")
print()

# ============================================================================
# STEP 3: Process historical conversion data
# ============================================================================
print("Processing historical conversion data...")
conversion_2026['CSS'] = 'NO'

matches_found = 0
for idx, row in conversion_2026.iterrows():
    first = row['First Name'].strip()
    last = row['Last Name'].strip()
    year = int(row['Year'])
    
    key = (first, last, year)
    if key in css_keys:
        conversion_2026.loc[idx, 'CSS'] = 'YES'
        matches_found += 1

print(f"  Marked {matches_found} rows with CSS='YES'")
print()

# ============================================================================
# STEP 4: Create rows for missing CSS athletes AND missing years
# ============================================================================
print("Creating rows for missing CSS (athlete, year) combinations...")

new_rows_list = []

# Process ALL CSS entries - only add if NOT already in conversion data
for first, last, year in css_keys:
    key = (first, last, year)
    
    # Only add if this (athlete, year) is NOT in conversion data
    if key not in conv_keys:
        # Find this entry in CSS dataset for sport info
        css_entry = css_yes[
            (css_yes['First Name'].str.strip() == first) &
            (css_yes['Last Name'].str.strip() == last) &
            (css_yes['Year'].astype(int) == year)
        ]
        
        if len(css_entry) > 0:
            css_row = css_entry.iloc[0]
            sport = css_row['Sport'] if pd.notna(css_row['Sport']) else ''
            
            new_row = {
                'Sport': sport,
                'First Name': first,
                'Last Name': last,
                'Gender': '',  # Not in CSS dataset
                'Date of Birth': '',  # Not in CSS dataset
                'Year': year,
                'Program': 'Prov Dev 3',  # Default for CSS athletes
                'Years Targeted': 1,
                'Convert Year': 'N',  # No conversion history
                'CSS': 'YES'
            }
            new_rows_list.append(new_row)

print(f"  Creating {len(new_rows_list)} new rows for missing CSS (athlete, year) combinations")
print()

# ============================================================================
# STEP 5: Prepare and merge datasets
# ============================================================================
print("Preparing nomination data...")

nomination_prep = nomination_master.copy()
nomination_prep = nomination_prep.rename(columns={
    'Sex Of Competition': 'Gender',
    'DOB': 'Date of Birth',
    'Fiscal Year': 'Year'
})
nomination_prep['CSS'] = 'NO'

# Populate CSS for nomination athletes
css_count_sport_level = 0
css_count_nominating_body = 0

for idx, row in nomination_prep.iterrows():
    is_css = False
    
    if 'SportLevel' in nomination_prep.columns:
        sport_level = row.get('SportLevel', '')
        if pd.notna(sport_level) and str(sport_level).strip().upper() == 'CSS':
            is_css = True
            css_count_sport_level += 1
    
    if 'Nominating Body' in nomination_prep.columns and not is_css:
        nominating_body = row.get('Nominating Body', '')
        if pd.notna(nominating_body):
            nominating_body_str = str(nominating_body).strip().upper()
            if 'CANADIAN SPORT SCHOOL' in nominating_body_str:
                is_css = True
                css_count_nominating_body += 1
    
    if is_css:
        nomination_prep.loc[idx, 'CSS'] = 'YES'

nomination_prep['Years Targeted'] = 1
nomination_prep['Convert Year'] = 'N'

print(f"  Marked {css_count_sport_level + css_count_nominating_body} nomination athletes as CSS='YES'")
print()

# Standardize columns for all datasets
print("Standardizing column names...")

conversion_2026['Full_Name'] = (conversion_2026['First Name'].astype(str) + ' ' + 
                                 conversion_2026['Last Name'].astype(str))
nomination_prep['Full_Name'] = (nomination_prep['First Name'].astype(str) + ' ' + 
                                 nomination_prep['Last Name'].astype(str))

# Reorder conversion
column_order = ['Sport', 'First Name', 'Last Name', 'Gender', 'Date of Birth', 'Year', 
                'Program', 'Full_Name', 'CSS', 'Years Targeted', 'Convert Year']
conversion_2026 = conversion_2026[column_order]

# Reorder nomination
column_order_nom = ['Sport', 'First Name', 'Last Name', 'Gender', 'Date of Birth', 'Year', 
                    'Program', 'Full_Name', 'CSS', 'Years Targeted', 'Convert Year']
# Only select columns that exist
column_order_nom = [col for col in column_order_nom if col in nomination_prep.columns]
nomination_prep = nomination_prep[column_order_nom]

# Create dataframe for new CSS athletes
new_css_df = pd.DataFrame(new_rows_list)
new_css_df['Full_Name'] = (new_css_df['First Name'].astype(str) + ' ' + 
                            new_css_df['Last Name'].astype(str))

print(f"  New CSS athletes dataframe: {len(new_css_df)} rows")
print()

# ============================================================================
# STEP 6: Merge all datasets
# ============================================================================
print("Merging all datasets...")

final_dataset = pd.concat([conversion_2026, new_css_df, nomination_prep], ignore_index=True)

print(f"  Conversion data: {len(conversion_2026)} rows")
print(f"  New CSS athletes: {len(new_css_df)} rows")
print(f"  Nomination data: {len(nomination_prep)} rows")
print(f"  Total merged: {len(final_dataset)} rows")
print()

# ============================================================================
# STEP 8: Validation and statistics
# ============================================================================
print("=" * 100)
print("FINAL CSS STATISTICS")
print("=" * 100)
print()

css_yes_count = (final_dataset['CSS'] == 'YES').sum()
css_no_count = (final_dataset['CSS'] == 'NO').sum()

print(f"Total rows: {len(final_dataset)}")
print(f"CSS='YES': {css_yes_count}")
print(f"CSS='NO': {css_no_count}")
print()

# ============================================================================
# STEP 8: Validation and statistics
# ============================================================================
print("=" * 100)
print("FINAL CSS STATISTICS")
print("=" * 100)
print()

css_yes_count = (final_dataset['CSS'] == 'YES').sum()
css_no_count = (final_dataset['CSS'] == 'NO').sum()

print(f"Total rows: {len(final_dataset)}")
print(f"CSS='YES': {css_yes_count}")
print(f"CSS='NO': {css_no_count}")
print()

# Count unique CSS athletes
css_athletes_final = set()
for _, row in final_dataset[final_dataset['CSS'] == 'YES'].iterrows():
    css_athletes_final.add((row['First Name'].strip(), row['Last Name'].strip()))

print(f"Unique CSS athletes: {len(css_athletes_final)}")
print(f"Expected (from CSS dataset): {len(css_athletes)}")
print(f"Coverage: {len(css_athletes_final)}/{len(css_athletes)} ({len(css_athletes_final)/len(css_athletes)*100:.1f}%)")
print()

# Count unique (athlete, year) combinations - from conversion data only (exclude nomination)
# to match against CSS dataset
css_entries_final = set()
for _, row in final_dataset[final_dataset['CSS'] == 'YES'].iterrows():
    # Only count if First Name and Last Name are populated (to distinguish from nomination)
    if str(row['First Name']).strip() and str(row['Last Name']).strip():
        css_entries_final.add((row['First Name'].strip(), row['Last Name'].strip(), int(row['Year'])))

print(f"Unique (athlete, year) CSS entries: {len(css_entries_final)}")
print(f"Expected (from CSS dataset): {len(css_keys)}")
print(f"Coverage: {len(css_entries_final)}/{len(css_keys)} ({len(css_entries_final)/len(css_keys)*100:.1f}%)")
print()

# Find any still unmatched
unmatched_entries = css_keys - css_entries_final
if len(unmatched_entries) > 0:
    print(f"⚠ WARNING: {len(unmatched_entries)} CSS entries still not captured:")
    for first, last, year in sorted(unmatched_entries)[:5]:
        print(f"    {first} {last} ({year})")
    if len(unmatched_entries) > 5:
        print(f"    ... and {len(unmatched_entries) - 5} more")
    print()

# Distribution by sport
print("CSS athletes by sport:")
css_by_sport = final_dataset[final_dataset['CSS'] == 'YES'].groupby('Sport' ).apply(
    lambda x: len(set(zip(x['First Name'].str.strip(), x['Last Name'].str.strip())))
).sort_values(ascending=False)
for sport, count in css_by_sport.head(15).items():
    if sport:
        print(f"  {sport}: {count}")
print()

# ============================================================================
# STEP 9: Save final dataset
# ============================================================================
print("Saving final dataset...")
output_file = BASE_DIR / "Conversion_Data_2026_final.csv"
final_dataset.to_csv(output_file, index=False)
print(f"✓ Saved: {output_file}")
print()

print("=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"✓ Captured {len(css_entries_final)}/{len(css_keys)} CSS athlete-year combinations ({len(css_entries_final)/len(css_keys)*100:.1f}%)")
print(f"✓ Added {len(new_rows_list)} rows for missing CSS entries")
print(f"✓ Included {css_count_sport_level + css_count_nominating_body} nomination athletes with CSS status")
print(f"✓ Total rows in final dataset: {len(final_dataset)}")
