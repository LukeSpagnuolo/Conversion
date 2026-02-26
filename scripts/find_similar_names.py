#!/usr/bin/env python3
"""
Find potential name matches with same last name but similar first names
This helps identify additional matches we might be missing due to name variations
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

# Get unique athletes (only one row per person)
css_unique = css_long.drop_duplicates('Full_Name')[['Full_Name', 'First_Name_Lower', 'Last_Name_Lower']].reset_index(drop=True)
conv_unique = conversion_2026.drop_duplicates('Full_Name')[['Full_Name', 'First_Name_Lower', 'Last_Name_Lower']].reset_index(drop=True)

# Find already matched names
css_names = set(css_unique['Full_Name'].unique())
conv_names = set(conv_unique['Full_Name'].unique())
already_matched = css_names & conv_names

print("=" * 80)
print("FINDING POTENTIAL MATCHES WITH SAME LAST NAME BUT DIFFERENT FIRST NAMES")
print("=" * 80)
print()

# Build last name to first names mapping for unmatched athletes
css_unmatched = css_unique[~css_unique['Full_Name'].isin(already_matched)]
conv_unmatched = conv_unique[~conv_unique['Full_Name'].isin(already_matched)]

css_lastname_to_firstname = {}
for _, row in css_unmatched.iterrows():
    last_name = row['Last_Name_Lower']
    first_name = row['First_Name_Lower']
    full_name = row['Full_Name']
    
    if last_name not in css_lastname_to_firstname:
        css_lastname_to_firstname[last_name] = []
    css_lastname_to_firstname[last_name].append((first_name, full_name))

conv_lastname_to_firstname = {}
for _, row in conv_unmatched.iterrows():
    last_name = row['Last_Name_Lower']
    first_name = row['First_Name_Lower']
    full_name = row['Full_Name']
    
    if last_name not in conv_lastname_to_firstname:
        conv_lastname_to_firstname[last_name] = []
    conv_lastname_to_firstname[last_name].append((first_name, full_name))

# Find common last names
common_last_names = set(css_lastname_to_firstname.keys()) & set(conv_lastname_to_firstname.keys())

print(f"Common last names in unmatched athletes: {len(common_last_names)}")
print()

# Find similar first names for each common last name
potential_matches = []

for last_name in sorted(common_last_names):
    css_first_names = css_lastname_to_firstname[last_name]
    conv_first_names = conv_lastname_to_firstname[last_name]
    
    for css_first, css_full in css_first_names:
        for conv_first, conv_full in conv_first_names:
            # Calculate similarity
            similarity = SequenceMatcher(None, css_first, conv_first).ratio()
            
            # Only show if similar (>0.7) but not exact (not already matched)
            if 0.7 <= similarity < 1.0:
                potential_matches.append({
                    'CSS_Full': css_full,
                    'Conv_Full': conv_full,
                    'Last_Name': last_name,
                    'CSS_First': css_first,
                    'Conv_First': conv_first,
                    'Similarity': similarity
                })

# Sort by similarity descending
potential_matches = sorted(potential_matches, key=lambda x: x['Similarity'], reverse=True)

print(f"Potential matches found (0.7-1.0 similarity): {len(potential_matches)}")
print()

if potential_matches:
    print("=" * 80)
    print("TOP POTENTIAL MATCHES")
    print("=" * 80)
    print()
    
    for i, match in enumerate(potential_matches[:50], 1):
        print(f"{i:2}. Last Name: {match['Last_Name'].upper()}")
        print(f"    CSS:  {match['CSS_Full']:35} (First: {match['CSS_First']})")
        print(f"    Conv: {match['Conv_Full']:35} (First: {match['Conv_First']})")
        print(f"    Similarity: {match['Similarity']:.1%}")
        print()

# Also show exact same first name but potentially different last names
print("=" * 80)
print("SAME FIRST NAME BUT DIFFERENT LAST NAMES")
print("=" * 80)
print()

css_firstname_to_lastname = {}
for _, row in css_unmatched.iterrows():
    first_name = row['First_Name_Lower']
    last_name = row['Last_Name_Lower']
    full_name = row['Full_Name']
    
    if first_name not in css_firstname_to_lastname:
        css_firstname_to_lastname[first_name] = []
    css_firstname_to_lastname[first_name].append((last_name, full_name))

conv_firstname_to_lastname = {}
for _, row in conv_unmatched.iterrows():
    first_name = row['First_Name_Lower']
    last_name = row['Last_Name_Lower']
    full_name = row['Full_Name']
    
    if first_name not in conv_firstname_to_lastname:
        conv_firstname_to_lastname[first_name] = []
    conv_firstname_to_lastname[first_name].append((last_name, full_name))

# Find common first names
common_first_names = set(css_firstname_to_lastname.keys()) & set(conv_firstname_to_lastname.keys())

same_first_name_matches = []
for first_name in common_first_names:
    css_last_names = css_firstname_to_lastname[first_name]
    conv_last_names = conv_firstname_to_lastname[first_name]
    
    for css_last, css_full in css_last_names:
        for conv_last, conv_full in conv_last_names:
            # Calculate similarity of last names
            similarity = SequenceMatcher(None, css_last, conv_last).ratio()
            
            # Only show if somewhat similar but not exact
            if 0.7 <= similarity < 1.0:
                same_first_name_matches.append({
                    'CSS_Full': css_full,
                    'Conv_Full': conv_full,
                    'First_Name': first_name,
                    'CSS_Last': css_last,
                    'Conv_Last': conv_last,
                    'Similarity': similarity
                })

same_first_name_matches = sorted(same_first_name_matches, key=lambda x: x['Similarity'], reverse=True)

print(f"Same first name with similar last names: {len(same_first_name_matches)}")
print()

if same_first_name_matches:
    for i, match in enumerate(same_first_name_matches[:30], 1):
        print(f"{i:2}. First Name: {match['First_Name'].upper()}")
        print(f"    CSS:  {match['CSS_Full']:35} (Last: {match['CSS_Last']})")
        print(f"    Conv: {match['Conv_Full']:35} (Last: {match['Conv_Last']})")
        print(f"    Last Name Similarity: {match['Similarity']:.1%}")
        print()
