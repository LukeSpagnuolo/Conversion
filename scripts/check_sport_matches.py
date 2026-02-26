#!/usr/bin/env python3
"""
Check if potential name matches have the same sport
"""

import pandas as pd
from pathlib import Path
from difflib import SequenceMatcher

BASE_DIR = Path(__file__).resolve().parent

# Load both datasets
css_long = pd.read_csv(BASE_DIR / "CSSAthleteConversion_long.csv")
conversion_2026 = pd.read_csv(BASE_DIR / "Conversion_Data_2026.csv")

# Create full names and normalize
css_long['Full_Name'] = css_long['First Name'].str.strip() + " " + css_long['Last Name'].str.strip()
css_long['First_Name_Lower'] = css_long['First Name'].str.strip().str.lower()
css_long['Last_Name_Lower'] = css_long['Last Name'].str.strip().str.lower()

conversion_2026['Full_Name'] = conversion_2026['First Name'].str.strip() + " " + conversion_2026['Last Name'].str.strip()
conversion_2026['First_Name_Lower'] = conversion_2026['First Name'].str.strip().str.lower()
conversion_2026['Last_Name_Lower'] = conversion_2026['Last Name'].str.strip().str.lower()

# Get unique athletes with sport info
css_unique = css_long.drop_duplicates('Full_Name')[['Full_Name', 'First_Name_Lower', 'Last_Name_Lower', 'Sport']].reset_index(drop=True)
conv_unique = conversion_2026.drop_duplicates('Full_Name')[['Full_Name', 'First_Name_Lower', 'Last_Name_Lower', 'Sport']].reset_index(drop=True)

# Find already matched names
css_names = set(css_unique['Full_Name'].unique())
conv_names = set(conv_unique['Full_Name'].unique())
already_matched = css_names & conv_names

# Build unmatched lists
css_unmatched = css_unique[~css_unique['Full_Name'].isin(already_matched)]
conv_unmatched = conv_unique[~conv_unique['Full_Name'].isin(already_matched)]

# Build last name mappings
css_lastname_to_firstname = {}
for _, row in css_unmatched.iterrows():
    last_name = row['Last_Name_Lower']
    first_name = row['First_Name_Lower']
    full_name = row['Full_Name']
    sport = row['Sport']
    
    if last_name not in css_lastname_to_firstname:
        css_lastname_to_firstname[last_name] = []
    css_lastname_to_firstname[last_name].append((first_name, full_name, sport))

conv_lastname_to_firstname = {}
for _, row in conv_unmatched.iterrows():
    last_name = row['Last_Name_Lower']
    first_name = row['First_Name_Lower']
    full_name = row['Full_Name']
    sport = row['Sport']
    
    if last_name not in conv_lastname_to_firstname:
        conv_lastname_to_firstname[last_name] = []
    conv_lastname_to_firstname[last_name].append((first_name, full_name, sport))

# Find common last names
common_last_names = set(css_lastname_to_firstname.keys()) & set(conv_lastname_to_firstname.keys())

# Find similar first names with sport check
potential_matches = []

for last_name in sorted(common_last_names):
    css_first_names = css_lastname_to_firstname[last_name]
    conv_first_names = conv_lastname_to_firstname[last_name]
    
    for css_first, css_full, css_sport in css_first_names:
        for conv_first, conv_full, conv_sport in conv_first_names:
            # Calculate similarity
            similarity = SequenceMatcher(None, css_first, conv_first).ratio()
            
            # Only show if similar (>0.7) but not exact
            if 0.7 <= similarity < 1.0:
                same_sport = css_sport.lower().strip() == conv_sport.lower().strip() if pd.notna(css_sport) and pd.notna(conv_sport) else False
                potential_matches.append({
                    'CSS_Full': css_full,
                    'Conv_Full': conv_full,
                    'Last_Name': last_name,
                    'CSS_First': css_first,
                    'Conv_First': conv_first,
                    'CSS_Sport': css_sport,
                    'Conv_Sport': conv_sport,
                    'Same_Sport': same_sport,
                    'Similarity': similarity
                })

# Sort by similarity descending
potential_matches = sorted(potential_matches, key=lambda x: x['Similarity'], reverse=True)

print("=" * 100)
print("SAME LAST NAME WITH SIMILAR FIRST NAMES - SPORT COMPARISON")
print("=" * 100)
print()

same_sport_count = 0
diff_sport_count = 0

for i, match in enumerate(potential_matches, 1):
    same_sport = "✓ YES" if match['Same_Sport'] else "✗ NO"
    if match['Same_Sport']:
        same_sport_count += 1
    else:
        diff_sport_count += 1
    
    print(f"{i}. {match['Last_Name'].upper():20} | Similarity: {match['Similarity']:5.1%} | Same Sport: {same_sport}")
    print(f"   CSS:  {match['CSS_Full']:35} | Sport: {match['CSS_Sport']}")
    print(f"   Conv: {match['Conv_Full']:35} | Sport: {match['Conv_Sport']}")
    print()

print("=" * 100)
print(f"SAME LAST NAME MATCHES: {len(potential_matches)} total")
print(f"  - Same Sport: {same_sport_count}")
print(f"  - Different Sport: {diff_sport_count}")
print()

# Now check same first names with different last names
print("=" * 100)
print("SAME FIRST NAME WITH SIMILAR LAST NAMES - SPORT COMPARISON")
print("=" * 100)
print()

css_firstname_to_lastname = {}
for _, row in css_unmatched.iterrows():
    first_name = row['First_Name_Lower']
    last_name = row['Last_Name_Lower']
    full_name = row['Full_Name']
    sport = row['Sport']
    
    if first_name not in css_firstname_to_lastname:
        css_firstname_to_lastname[first_name] = []
    css_firstname_to_lastname[first_name].append((last_name, full_name, sport))

conv_firstname_to_lastname = {}
for _, row in conv_unmatched.iterrows():
    first_name = row['First_Name_Lower']
    last_name = row['Last_Name_Lower']
    full_name = row['Full_Name']
    sport = row['Sport']
    
    if first_name not in conv_firstname_to_lastname:
        conv_firstname_to_lastname[first_name] = []
    conv_firstname_to_lastname[first_name].append((last_name, full_name, sport))

# Find common first names
common_first_names = set(css_firstname_to_lastname.keys()) & set(conv_firstname_to_lastname.keys())

same_first_name_matches = []
for first_name in common_first_names:
    css_last_names = css_firstname_to_lastname[first_name]
    conv_last_names = conv_firstname_to_lastname[first_name]
    
    for css_last, css_full, css_sport in css_last_names:
        for conv_last, conv_full, conv_sport in conv_last_names:
            # Calculate similarity of last names
            similarity = SequenceMatcher(None, css_last, conv_last).ratio()
            
            # Only show if somewhat similar but not exact
            if 0.7 <= similarity < 1.0:
                same_sport = css_sport.lower().strip() == conv_sport.lower().strip() if pd.notna(css_sport) and pd.notna(conv_sport) else False
                same_first_name_matches.append({
                    'CSS_Full': css_full,
                    'Conv_Full': conv_full,
                    'First_Name': first_name,
                    'CSS_Last': css_last,
                    'Conv_Last': conv_last,
                    'CSS_Sport': css_sport,
                    'Conv_Sport': conv_sport,
                    'Same_Sport': same_sport,
                    'Similarity': similarity
                })

same_first_name_matches = sorted(same_first_name_matches, key=lambda x: x['Similarity'], reverse=True)

same_sport_count_2 = 0
diff_sport_count_2 = 0

for i, match in enumerate(same_first_name_matches, 1):
    same_sport = "✓ YES" if match['Same_Sport'] else "✗ NO"
    if match['Same_Sport']:
        same_sport_count_2 += 1
    else:
        diff_sport_count_2 += 1
    
    print(f"{i}. {match['First_Name'].upper():20} | Last Name Sim: {match['Similarity']:5.1%} | Same Sport: {same_sport}")
    print(f"   CSS:  {match['CSS_Full']:35} | Sport: {match['CSS_Sport']}")
    print(f"   Conv: {match['Conv_Full']:35} | Sport: {match['Conv_Sport']}")
    print()

print("=" * 100)
print(f"SAME FIRST NAME MATCHES: {len(same_first_name_matches)} total")
print(f"  - Same Sport: {same_sport_count_2}")
print(f"  - Different Sport: {diff_sport_count_2}")
print()

print("=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"Total potential matches: {len(potential_matches) + len(same_first_name_matches)}")
print(f"Matches with SAME SPORT: {same_sport_count + same_sport_count_2} (HIGHLY LIKELY to be the same person)")
print(f"Matches with DIFFERENT SPORT: {diff_sport_count + diff_sport_count_2} (likely different people)")
