#!/usr/bin/env python3
"""
Find similar names in nomination athlete dataset (>85% similarity within same sport)
"""

import pandas as pd
from difflib import SequenceMatcher
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load nomination data
print("Loading nomination athlete data...")
df = pd.read_csv(BASE_DIR / "Nomination_Athletes_filtered.csv")

print(f"Total rows: {len(df):,}")
print(f"Unique athletes: {df[['Sport', 'First Name', 'Last Name']].drop_duplicates().shape[0]:,}")
print()

# Find similar name pairs within each sport
print("=" * 100)
print("FINDING SIMILAR NAMES (>85% similarity within same sport)")
print("=" * 100)
print()

similar_pairs = []
sports = df['Sport'].unique()

for sport in sorted([s for s in sports if pd.notna(s)]):
    sport_df = df[df['Sport'] == sport].copy()
    
    # Drop rows with missing First Name or Last Name
    sport_df = sport_df.dropna(subset=['First Name', 'Last Name'])
    
    unique_names = sorted(sport_df['First Name'].astype(str) + ' ' + sport_df['Last Name'].astype(str))
    
    checked = set()
    sport_pairs = []
    
    for i, name1 in enumerate(unique_names):
        for name2 in unique_names[i+1:]:
            pair_key = tuple(sorted([name1, name2]))
            if pair_key in checked:
                continue
            checked.add(pair_key)
            
            # Extract just the names for comparison (not DOB)
            name1_clean = ' '.join(name1.split()[:-1])
            name2_clean = ' '.join(name2.split()[:-1])
            
            similarity = SequenceMatcher(None, name1_clean.lower(), name2_clean.lower()).ratio()
            
            if similarity > 0.85:
                count1 = len(sport_df[sport_df['First Name'].astype(str) + ' ' + sport_df['Last Name'].astype(str) == name1_clean])
                count2 = len(sport_df[sport_df['First Name'].astype(str) + ' ' + sport_df['Last Name'].astype(str) == name2_clean])
                
                sport_pairs.append({
                    'sport': sport,
                    'name1': name1_clean,
                    'name2': name2_clean,
                    'similarity': similarity,
                    'count1': count1,
                    'count2': count2
                })
                similar_pairs.append((sport, name1_clean, name2_clean, similarity))
    
    if sport_pairs:
        print(f"[{sport}]")
        for pair in sport_pairs:
            print(f"  '{pair['name1']}' ↔ '{pair['name2']}' - {pair['similarity']:.1%} similar")
        print()

if not similar_pairs:
    print("✓ No similar name pairs found (>85% similarity)")
    print()
else:
    print()
    print(f"Total similar name pairs found: {len(similar_pairs)}")
    print()
    
    # Save to CSV for review
    output_df = pd.DataFrame(similar_pairs, columns=['Sport', 'Name1', 'Name2', 'Similarity'])
    output_df = output_df.sort_values(['Sport', 'Name1'])
    output_file = BASE_DIR / "Similar_Names_Nomination.csv"
    output_df.to_csv(output_file, index=False)
    print(f"✓ Saved to: {output_file}")
