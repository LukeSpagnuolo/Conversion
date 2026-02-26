#!/usr/bin/env python3
"""
Consolidate similar athlete names in the merged dataset
Focus on same sport + high name similarity to reduce unique athlete count
"""

import pandas as pd
from pathlib import Path
from difflib import SequenceMatcher

BASE_DIR = Path(__file__).resolve().parent

# Load the merged dataset
df = pd.read_csv(BASE_DIR / "Conversion_Data_2026_with_CSS_updated.csv")

print("=" * 100)
print("CONSOLIDATING SIMILAR ATHLETE NAMES")
print("=" * 100)
print()

print(f"Starting unique full names: {df['Full_Name'].nunique()}")
print()

# Build a mapping of similar names to consolidate
name_consolidation_map = {}

# Strategy: For each sport, find names with high similarity
sports = df['Sport'].unique()

consolidation_count = 0

for sport in sorted([s for s in sports if pd.notna(s)]):
    sport_df = df[df['Sport'] == sport]
    unique_names = sorted(sport_df['Full_Name'].unique())
    
    # For each pair of unique names, check similarity
    checked = set()
    for i, name1 in enumerate(unique_names):
        if name1 in name_consolidation_map:
            continue
            
        for name2 in unique_names[i+1:]:
            pair_key = tuple(sorted([name1, name2]))
            if pair_key in checked or name2 in name_consolidation_map:
                continue
            checked.add(pair_key)
            
            # Calculate similarity
            similarity = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
            
            # If very similar (>0.85), consolidate to the one appearing most
            if similarity > 0.85:
                count1 = len(sport_df[sport_df['Full_Name'] == name1])
                count2 = len(sport_df[sport_df['Full_Name'] == name2])
                
                # Consolidate to the name that appears more in this sport
                if count1 >= count2:
                    name_consolidation_map[name2] = name1
                    consolidation_count += 1
                    print(f"[{sport}] '{name2}' → '{name1}' ({similarity:.1%} similar, count: {count2}→{count1})")
                else:
                    name_consolidation_map[name1] = name2
                    consolidation_count += 1
                    print(f"[{sport}] '{name1}' → '{name2}' ({similarity:.1%} similar, count: {count1}→{count2})")

print()
print(f"Total consolidations created: {consolidation_count}")
print()

# Apply consolidations
if consolidation_count > 0:
    print("Applying consolidations to dataset...")
    
    for old_name, new_name in name_consolidation_map.items():
        df.loc[df['Full_Name'] == old_name, 'Full_Name'] = new_name
    
    print(f"New unique full names: {df['Full_Name'].nunique()}")
    print(f"Unique athletes removed: {len(name_consolidation_map)}")
    print()

# Save consolidated dataset
output_path = BASE_DIR / "Conversion_Data_2026_consolidated.csv"
df.to_csv(output_path, index=False)

print("=" * 100)
print(f"Saved consolidated dataset to: {output_path}")
print("=" * 100)
