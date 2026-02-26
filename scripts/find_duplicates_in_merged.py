#!/usr/bin/env python3
"""
Find potential duplicate athletes within the merged dataset - OPTIMIZED
Focus on DOB and gender variations
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load the merged dataset
df = pd.read_csv(BASE_DIR / "Conversion_Data_2026_with_CSS_updated.csv")

print("=" * 100)
print("ANALYZING MERGED DATASET FOR DUPLICATE ATHLETES")
print("=" * 100)
print()

print(f"Total rows: {df.shape[0]}")
print(f"Unique Full Names: {df['Full_Name'].nunique()}")
print()

# Check 1: Same DOB with different names
print("=" * 100)
print("CHECK 1: SAME DATE OF BIRTH WITH DIFFERENT NAMES")
print("=" * 100)
print()

dob_name_groups = df[df['Date of Birth'].notna()].groupby('Date of Birth')['Full_Name'].nunique()
dobs_with_multiple_names = dob_name_groups[dob_name_groups > 1].sort_values(ascending=False)

print(f"DOBs appearing with multiple different names: {len(dobs_with_multiple_names)}")
print()

if len(dobs_with_multiple_names) > 0:
    print("TOP 30 CASES - VERY LIKELY DUPLICATES:")
    print()
    
    for i, (dob, count) in enumerate(dobs_with_multiple_names.head(30).items(), 1):
        athletes = df[df['Date of Birth'] == dob][['Full_Name', 'Sport', 'Gender', 'Year', 'CSS']].drop_duplicates()
        print(f"{i}. DOB: {dob} ({count} different names)")
        for _, row in athletes.iterrows():
            css_marker = " [CSS=YES]" if row['CSS'] == 'YES' else ""
            print(f"   - {row['Full_Name']:40} ({row['Gender']}, {row['Sport']}, Year {int(row['Year'])}){css_marker}")
        print()

# Check 2: Same name with different genders
print("=" * 100)
print("CHECK 2: SAME NAME WITH DIFFERENT GENDER")
print("=" * 100)
print()

gender_check = df[df['Gender'].notna()].groupby('Full_Name')['Gender'].unique()
multi_gender = gender_check[gender_check.apply(len) > 1]

print(f"Names appearing with multiple genders: {len(multi_gender)}")
print()

if len(multi_gender) > 0:
    print("Cases:")
    print()
    for i, (name, genders) in enumerate(multi_gender.items(), 1):
        athletes = df[df['Full_Name'] == name][['Gender', 'Sport', 'Year', 'Program', 'CSS']].drop_duplicates()
        print(f"{i}. '{name}' appears as: {', '.join([str(g) for g in genders if pd.notna(g)])}")
        for _, row in athletes.iterrows():
            css_marker = " [CSS=YES]" if row['CSS'] == 'YES' else ""
            print(f"   - {row['Gender']}, {row['Sport']}, Year {int(row['Year'])}, {row['Program']}{css_marker}")
        print()

# Check 3: Look for entries with only whitespace/spacing differences
print("=" * 100)
print("CHECK 3: NEARLY IDENTICAL NAMES (likely data entry errors)")
print("=" * 100)
print()

df['Full_Name_NoSpace'] = df['Full_Name'].str.lower().str.replace(r'[\s\-\']', '', regex=True)
noSpace_groups = df.groupby('Full_Name_NoSpace')['Full_Name'].unique()
multi_spacing = noSpace_groups[noSpace_groups.apply(len) > 1]

print(f"Names with spacing/punctuation variations: {len(multi_spacing)}")
print()

if len(multi_spacing) > 0:
    print("TOP 20 CASES:")
    print()
    for i, (nospace, names) in enumerate(list(multi_spacing.items())[:20], 1):
        name_counts = {name: len(df[df['Full_Name'] == name]) for name in names}
        total_rows = sum(name_counts.values())
        print(f"{i}. Total rows: {total_rows} | Variations: {len(names)}")
        for name, count in sorted(name_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   - '{name}' ({count} rows)")
        print()

# Check 4: Same first + last name but different middle names
print("=" * 100)
print("CHECK 4: SAME FIRST+LAST NAME WITH MULTIPLE VARIATIONS")
print("=" * 100)
print()

# Use a simple approach - group by first+last name pattern
df['Name_Parts'] = df['Full_Name'].str.lower().apply(lambda x: ' '.join(x.split()[:2]) if len(x.split()) >= 2 else x)

fl_groups = df.groupby('Name_Parts')['Full_Name'].nunique()
multi_fl = fl_groups[fl_groups > 1].sort_values(ascending=False)

print(f"First+Last name combinations with variations: {len(multi_fl)}")
print()

if len(multi_fl) > 0:
    print("TOP 20 CASES (LIKELY SAME PERSON):")
    print()
    
    for i, (fl, count) in enumerate(multi_fl.head(20).items(), 1):
        names = df[df['Name_Parts'] == fl]['Full_Name'].unique()
        rows = df[df['Full_Name'].isin(names)][['Full_Name', 'Sport', 'Year', 'Date of Birth', 'CSS']].drop_duplicates()
        print(f"{i}. First+Last: {fl.title()} ({len(names)} total variations)")
        for name in sorted(names):
            name_rows = len(df[df['Full_Name'] == name])
            print(f"   - '{name}' ({name_rows} rows)")
        print()
