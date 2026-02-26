#!/usr/bin/env python3
"""
Compare and combine CSSAthleteConversion_long.csv and Conversion_Data_2026.csv
Step 1: Analyze name matches across the datasets with enhanced matching
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load both datasets
css_long = pd.read_csv(BASE_DIR / "CSSAthleteConversion_long.csv")
conversion_2026 = pd.read_csv(BASE_DIR / "Conversion_Data_2026.csv")

print("=" * 80)
print("DATASET OVERVIEW")
print("=" * 80)
print(f"CSS Athlete Conversion (Long): {css_long.shape[0]} rows")
print(f"Conversion Data 2026: {conversion_2026.shape[0]} rows")
print()

# Create full name identifier for matching (with normalization)
css_long['Full_Name'] = css_long['First Name'].str.strip() + " " + css_long['Last Name'].str.strip()
css_long['Full_Name_Normalized'] = css_long['Full_Name'].str.lower().str.replace(r'\s+', ' ', regex=True)
# Remove all whitespace and special characters for aggressive matching
css_long['Full_Name_NoSpace'] = css_long['Full_Name'].str.lower().str.replace(r'[\s\-\']', '', regex=True)

conversion_2026['Full_Name'] = conversion_2026['First Name'].str.strip() + " " + conversion_2026['Last Name'].str.strip()
conversion_2026['Full_Name_Normalized'] = conversion_2026['Full_Name'].str.lower().str.replace(r'\s+', ' ', regex=True)
# Remove all whitespace and special characters for aggressive matching
conversion_2026['Full_Name_NoSpace'] = conversion_2026['Full_Name'].str.lower().str.replace(r'[\s\-\']', '', regex=True)

# Get unique athletes from each dataset
css_unique_names = set(css_long['Full_Name'].unique())
css_unique_normalized = {name.lower().replace(' ', ' '): name for name in css_unique_names}
css_unique_nospace = {name.lower().replace(' ', '').replace('-', '').replace("'", ''): name for name in css_unique_names}

conv_unique_names = set(conversion_2026['Full_Name'].unique())
conv_unique_normalized = {name.lower().replace(' ', ' '): name for name in conv_unique_names}
conv_unique_nospace = {name.lower().replace(' ', '').replace('-', '').replace("'", ''): name for name in conv_unique_names}

print(f"Unique athletes in CSS data: {len(css_unique_names)}")
print(f"Unique athletes in Conversion 2026: {len(conv_unique_names)}")
print()

# Find exact matches
exact_matches = css_unique_names & conv_unique_names

# Find case-insensitive matches (not already in exact)
case_insensitive_matches = []
css_not_exact = css_unique_normalized.keys() - {n.lower().replace(' ', ' ') for n in exact_matches}
conv_set_normalized = set(conv_unique_normalized.keys())

for css_norm in css_not_exact:
    if css_norm in conv_set_normalized:
        css_orig = css_unique_normalized[css_norm]
        conv_orig = conv_unique_normalized[css_norm]
        case_insensitive_matches.append((css_orig, conv_orig))

# Find whitespace-insensitive matches (not already matched)
whitespace_insensitive_matches = []
css_not_matched = css_unique_nospace.keys() - {n.lower().replace(' ', '').replace('-', '').replace("'", '') for n in exact_matches}
css_not_matched = css_not_matched - {n.lower().replace(' ', '').replace('-', '').replace("'", '') for m in case_insensitive_matches for n in [m[0]]}
conv_set_nospace = set(conv_unique_nospace.keys())

for css_nospace in css_not_matched:
    if css_nospace in conv_set_nospace:
        css_orig = css_unique_nospace[css_nospace]
        conv_orig = conv_unique_nospace[css_nospace]
        whitespace_insensitive_matches.append((css_orig, conv_orig))

# Find remaining unmatched
css_only = css_unique_names - exact_matches - {m[0] for m in case_insensitive_matches} - {m[0] for m in whitespace_insensitive_matches}
conv_only = conv_unique_names - exact_matches - {m[1] for m in case_insensitive_matches} - {m[1] for m in whitespace_insensitive_matches}

print("=" * 80)
print("NAME MATCHING ANALYSIS")
print("=" * 80)
print(f"Exact matches:                    {len(exact_matches)}")
print(f"Case-insensitive matches:         {len(case_insensitive_matches)}")
print(f"Whitespace-insensitive matches:   {len(whitespace_insensitive_matches)}")
total_matches = len(exact_matches) + len(case_insensitive_matches) + len(whitespace_insensitive_matches)
print(f"Total matches:                    {total_matches}")
print(f"Names only in CSS data:           {len(css_only)}")
print(f"Names only in Conversion 2026:    {len(conv_only)}")
print()

# Show some examples of whitespace-insensitive matches
if whitespace_insensitive_matches:
    print("=" * 80)
    print("EXAMPLES OF WHITESPACE-INSENSITIVE MATCHES")
    print("=" * 80)
    for css_name, conv_name in sorted(whitespace_insensitive_matches)[:15]:
        css_count = len(css_long[css_long['Full_Name'] == css_name])
        conv_count = len(conversion_2026[conversion_2026['Full_Name'] == conv_name])
        print(f"CSS: {css_name:30} <-> Conv: {conv_name:30}")
        print(f"     {css_count} records in CSS, {conv_count} records in Conv 2026")
    print()

# Show some examples of case-insensitive matches
if case_insensitive_matches:
    print("=" * 80)
    print("EXAMPLES OF CASE-INSENSITIVE MATCHES")
    print("=" * 80)
    for css_name, conv_name in sorted(case_insensitive_matches)[:10]:
        css_count = len(css_long[css_long['Full_Name'] == css_name])
        conv_count = len(conversion_2026[conversion_2026['Full_Name'] == conv_name])
        print(f"CSS: {css_name:30} <-> Conv: {conv_name:30}")
        print(f"     {css_count} records in CSS, {conv_count} records in Conv 2026")
    print()

# Show some examples of exact matches
print("=" * 80)
print("EXAMPLES OF EXACT MATCHES")
print("=" * 80)
for name in sorted(list(exact_matches))[:15]:
    css_count = len(css_long[css_long['Full_Name'] == name])
    conv_count = len(conversion_2026[conversion_2026['Full_Name'] == name])
    print(f"{name:40} | CSS: {css_count:3} | Conv: {conv_count:3}")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
match_rate = total_matches / len(css_unique_names) * 100
print(f"Match rate: {match_rate:.1f}% of CSS athletes matched in Conversion 2026")
print(f"  - Exact matches:                {len(exact_matches)} ({len(exact_matches)/len(css_unique_names)*100:.1f}%)")
print(f"  - Case-insensitive matches:     {len(case_insensitive_matches)} ({len(case_insensitive_matches)/len(css_unique_names)*100:.1f}%)")
print(f"  - Whitespace-insensitive match: {len(whitespace_insensitive_matches)} ({len(whitespace_insensitive_matches)/len(css_unique_names)*100:.1f}%)")
print()
