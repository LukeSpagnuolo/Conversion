import pandas as pd
from difflib import SequenceMatcher
from collections import defaultdict

# Read the CSV file
df = pd.read_csv('Conversion_Data_2026_final.csv')
name_counts = df['Full_Name'].value_counts().to_dict()
unique_names = sorted(name_counts.keys())

# Group names by first 3 characters
groups = defaultdict(list)
for name in unique_names:
    prefix = name[:3] if len(name) >= 3 else name
    groups[prefix].append(name)

# Calculate similarity
def sim(a, b):
    return SequenceMatcher(None, a, b).ratio()

# Find all similar pairs (85%+ similarity)
similar = []
for prefix, names in groups.items():
    if len(names) > 1:
        for i, name1 in enumerate(names):
            for name2 in names[i+1:]:
                s = sim(name1, name2)
                if s >= 0.85:
                    similar.append((name1, name2, s, name_counts[name1], name_counts[name2]))

# Find qualified pairs (same sport or multisport)
qualified_consolidations = []

for n1, n2, s, c1, c2 in similar:
    sports1 = set(df[df['Full_Name'] == n1]['Sport'].unique())
    sports2 = set(df[df['Full_Name'] == n2]['Sport'].unique())
    
    has_multisport = 'Multisport' in sports1 or 'Multisport' in sports2
    same_sport = len(sports1 & sports2) > 0
    
    if has_multisport or same_sport:
        # Choose canonical name (more records, or if tied, alphabetically first)
        if c1 >= c2:
            canonical = n1
            non_canonical = n2
        else:
            canonical = n2
            non_canonical = n1
        
        qualified_consolidations.append({
            'canonical': canonical,
            'non_canonical': non_canonical,
            'canonical_count': max(c1, c2),
            'non_canonical_count': min(c1, c2)
        })

# Apply consolidations
df_consolidated = df.copy()
rows_removed_duplicates = 0
rows_consolidated = 0

for cons in qualified_consolidations:
    canonical = cons['canonical']
    non_canonical = cons['non_canonical']
    
    # Get all records with non-canonical name
    non_canonical_records = df_consolidated[df_consolidated['Full_Name'] == non_canonical].copy()
    
    # Get all records with canonical name (for duplicate checking)
    canonical_records = df_consolidated[df_consolidated['Full_Name'] == canonical]
    canonical_year_sport_combos = set(zip(canonical_records['Year'], canonical_records['Sport']))
    
    # Filter non-canonical records: keep only if new year/sport combo
    rows_to_update = []
    rows_to_drop = []
    
    for idx, row in non_canonical_records.iterrows():
        year_sport_combo = (row['Year'], row['Sport'])
        
        if year_sport_combo in canonical_year_sport_combos:
            # This is a duplicate - drop it
            rows_to_drop.append(idx)
            rows_removed_duplicates += 1
        else:
            # This is a new year/sport - update the Full_Name
            rows_to_update.append(idx)
            rows_consolidated += 1
    
    # Update the Full_Name for non-duplicate rows
    df_consolidated.loc[rows_to_update, 'Full_Name'] = canonical
    
    # Drop duplicate rows
    df_consolidated = df_consolidated.drop(rows_to_drop)

# Re-sort by Full_Name to keep data organized
df_consolidated = df_consolidated.sort_values('Full_Name').reset_index(drop=True)

# Save the consolidated CSV
df_consolidated.to_csv('Conversion_Data_2026_final.csv', index=False)

print("✓ Consolidation complete!")
print(f"\n📊 Summary:")
print(f"   Consolidation pairs applied: {len(qualified_consolidations)}")
print(f"   Rows consolidated (names updated): {rows_consolidated}")
print(f"   Duplicate rows removed: {rows_removed_duplicates}")
print(f"   Original row count: {len(df)}")
print(f"   New row count: {len(df_consolidated)}")
print(f"   Net reduction: {len(df) - len(df_consolidated)} rows")
print(f"\n✓ File saved: Conversion_Data_2026_final.csv")
