"""
Create consolidation mapping for nomination dataset similar names.
Uses full name (First + Last) similarity to identify duplicates within sports.
"""
import pandas as pd
from pathlib import Path
from difflib import SequenceMatcher

BASE_DIR = Path("/workspaces/Conversion")

print("Loading nomination athlete data...")
df = pd.read_csv(BASE_DIR / "Nomination_Athletes_filtered.csv")
print(f"Total rows: {len(df)}")
print(f"Unique athletes: {df['First Name'].nunique()}")
print()

# Load similar names
similar_df = pd.read_csv(BASE_DIR / "Similar_Names_Nomination.csv")

# Filter for >85% similarity or exact matches
high_similarity = similar_df[similar_df['Similarity'] >= 0.85].copy()
print(f"Found {len(high_similarity)} similar name pairs (>85%)")
print()

# Group by sport and first name pairs to understand the consolidations
consolidations = []

for sport in high_similarity['Sport'].unique():
    sport_similar = high_similarity[high_similarity['Sport'] == sport]
    sport_df = df[df['Sport'] == sport].copy()
    
    for _, row in sport_similar.iterrows():
        name1 = row['Name1'].lower()
        name2 = row['Name2'].lower()
        similarity = row['Similarity']
        
        if similarity == 1.0 and name1 == name2:
            # Skip identical names for now (could be different people)
            continue
        
        # Find athletes with these first names and check actual full names
        athletes1 = sport_df[sport_df['First Name'].str.lower() == name1.split()[0]]
        athletes2 = sport_df[sport_df['First Name'].str.lower() == name2.split()[0]]
        
        if len(athletes1) > 0 and len(athletes2) > 0:
            for athlete1_idx, athlete1 in athletes1.iterrows():
                for athlete2_idx, athlete2 in athletes2.iterrows():
                    full_name1 = f"{athlete1['First Name']} {athlete1['Last Name']}"
                    full_name2 = f"{athlete2['First Name']} {athlete2['Last Name']}"
                    
                    full_similarity = SequenceMatcher(None, full_name1.lower(), full_name2.lower()).ratio()
                    
                    # Check if it's a meaningful consolidation (different first name, same last name - likely nickname)
                    # Or same first name parts (Sacha/Sascha), different capitalization, etc.
                    if full_similarity > 0.85 and full_name1.lower() != full_name2.lower():
                        # Find which name appears more frequently
                        count1 = len(athletes1)
                        count2 = len(athletes2)
                        
                        # Keep the more frequent variant, or if equal, keep the first one alphabetically
                        if count1 >= count2:
                            target_name = full_name1
                            source_name = full_name2
                        else:
                            target_name = full_name2
                            source_name = full_name1
                        
                        consolidations.append({
                            'sport': sport,
                            'source_first': athlete2['First Name'] if count1 >= count2 else athlete1['First Name'],
                            'source_last': athlete2['Last Name'] if count1 >= count2 else athlete1['Last Name'],
                            'target_first': athlete1['First Name'] if count1 >= count2 else athlete2['First Name'],
                            'target_last': athlete1['Last Name'] if count1 >= count2 else athlete2['Last Name'],
                            'full_similarity': full_similarity
                        })

print(f"Found {len(consolidations)} potential full-name consolidations:")
for c in consolidations:
    print(f"  {c['sport']}: {c['source_first']} {c['source_last']} → {c['target_first']} {c['target_last']} ({c['full_similarity']:.1%})")
print()

# Remove duplicates (keep only unique source→target mappings)
consolidations_df = pd.DataFrame(consolidations)
consolidations_df = consolidations_df.drop_duplicates(subset=['source_first', 'source_last', 'target_first', 'target_last'])

print(f"Unique consolidation mappings: {len(consolidations_df)}")

# Create a consolidation mapping dictionary
consolidation_map = {}
for _, row in consolidations_df.iterrows():
    source_key = f"{row['source_first']} {row['source_last']}"
    target_key = f"{row['target_first']} {row['target_last']}"
    consolidation_map[source_key.lower()] = (row['target_first'], row['target_last'])

print()
print("Consolidation map created:")
for source, (target_first, target_last) in list(consolidation_map.items())[:10]:
    print(f"  {source} → {target_first} {target_last}")

# Apply consolidation to nomination dataset
print()
print("Applying consolidation to nomination dataset...")
df['Full_Name_Lower'] = (df['First Name'] + ' ' + df['Last Name']).str.lower()

consolidated_count = 0
for idx, row in df.iterrows():
    full_name_lower = row['Full_Name_Lower']
    if full_name_lower in consolidation_map:
        target_first, target_last = consolidation_map[full_name_lower]
        df.at[idx, 'First Name'] = target_first
        df.at[idx, 'Last Name'] = target_last
        consolidated_count += 1

print(f"✓ Consolidated {consolidated_count} athlete names")

# Recalculate unique athletes
unique_before = 1006  # from earlier
unique_after = (df['First Name'].astype(str) + ' ' + df['Last Name'].astype(str)).nunique()
print(f"  Unique athletes: {unique_before} → {unique_after} (reduced by {unique_before - unique_after})")

# Drop temporary column and save
df = df.drop(columns=['Full_Name_Lower'])
output_file = BASE_DIR / "Nomination_Athletes_consolidated.csv"
df.to_csv(output_file, index=False)
print()
print(f"✓ Saved consolidated nomination dataset: {output_file}")
print(f"  Rows: {len(df)}")
print(f"  Columns: {df.columns.tolist()}")
