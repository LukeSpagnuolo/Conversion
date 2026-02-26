#!/usr/bin/env python3
"""
Display all consolidations that were made
"""

import pandas as pd
from pathlib import Path
from difflib import SequenceMatcher

BASE_DIR = Path(__file__).resolve().parent

# Load the original dataset (before consolidation)
df = pd.read_csv(BASE_DIR / "Conversion_Data_2026_with_CSS_updated.csv")

# Build the same consolidation map
name_consolidation_map = {}
sports = df['Sport'].unique()

for sport in sorted([s for s in sports if pd.notna(s)]):
    sport_df = df[df['Sport'] == sport]
    unique_names = sorted(sport_df['Full_Name'].unique())
    
    checked = set()
    for i, name1 in enumerate(unique_names):
        if name1 in name_consolidation_map:
            continue
            
        for name2 in unique_names[i+1:]:
            pair_key = tuple(sorted([name1, name2]))
            if pair_key in checked or name2 in name_consolidation_map:
                continue
            checked.add(pair_key)
            
            similarity = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
            
            if similarity > 0.85:
                count1 = len(sport_df[sport_df['Full_Name'] == name1])
                count2 = len(sport_df[sport_df['Full_Name'] == name2])
                
                if count1 >= count2:
                    name_consolidation_map[name2] = name1
                else:
                    name_consolidation_map[name1] = name2

# Sort and display by sport
print("=" * 120)
print("ALL CONSOLIDATED NAMES (381 consolidations total)")
print("=" * 120)

# Create output with sport and consolidation info
consolidations_by_sport = {}

df_test = df.copy()
for old_name, new_name in name_consolidation_map.items():
    sport = df_test[df_test['Full_Name'] == old_name]['Sport'].iloc[0] if len(df_test[df_test['Full_Name'] == old_name]) > 0 else "Unknown"
    
    if sport not in consolidations_by_sport:
        consolidations_by_sport[sport] = []
    
    old_count = len(df[df['Full_Name'] == old_name])
    new_count = len(df[df['Full_Name'] == new_name])
    similarity = SequenceMatcher(None, old_name.lower(), new_name.lower()).ratio()
    
    consolidations_by_sport[sport].append({
        'old': old_name,
        'new': new_name,
        'similarity': similarity,
        'old_count': old_count,
        'new_count': new_count + old_count
    })

# Print by sport
for sport in sorted(consolidations_by_sport.keys()):
    print(f"\n[{sport}]")
    for item in sorted(consolidations_by_sport[sport], key=lambda x: x['old']):
        print(f"  '{item['old']}' → '{item['new']}' ({item['similarity']:.1%} similar)")

print(f"\n" + "=" * 120)
print(f"Total: {len(name_consolidation_map)} consolidations across {len(consolidations_by_sport)} sports")
print("=" * 120)

# Also save to CSV for easy review
output_df = []
for old_name, new_name in sorted(name_consolidation_map.items()):
    old_count = len(df[df['Full_Name'] == old_name])
    new_count = len(df[df['Full_Name'] == new_name])
    similarity = SequenceMatcher(None, old_name.lower(), new_name.lower()).ratio()
    sport = df[df['Full_Name'] == old_name]['Sport'].iloc[0] if len(df[df['Full_Name'] == old_name]) > 0 else "Unknown"
    
    output_df.append({
        'Sport': sport,
        'Original_Name': old_name,
        'Consolidated_To': new_name,
        'Similarity_%': f"{similarity:.1%}",
        'Original_Count': old_count,
        'Consolidated_Count': new_count + old_count
    })

output_csv = pd.DataFrame(output_df)
csv_path = BASE_DIR / "consolidations_mapping.csv"
output_csv.to_csv(csv_path, index=False)
print(f"\n✓ Mapping saved to: {csv_path}")
