"""
Final consolidation on complete dataset to ensure consistent athlete matching.
Finds similar names (>85% similarity) within each sport and consolidates them.
Recalculates Years_Targeted and Convert_Year after consolidation.
"""
import pandas as pd
from pathlib import Path
from difflib import SequenceMatcher

BASE_DIR = Path("/workspaces/Conversion")

print("Loading final dataset...")
df = pd.read_csv(BASE_DIR / "Conversion_Data_2026_final.csv")
print(f"Total rows: {len(df)}")
print(f"Unique athletes: {(df['First Name'].astype(str) + ' ' + df['Last Name'].astype(str)).nunique()}")
print()

# Define program level hierarchy
LEVEL_HIERARCHY = {
    'Prov Dev 3': 0,
    'Prov Dev 2': 1,
    'Prov Dev 1': 2,
    'Uncarded': 3,
    'SC Carded': 4
}

print("Finding similar names (>85% similarity within same sport)...")
consolidations = []
similar_pairs = []

for sport in sorted(df['Sport'].unique()):
    if pd.isna(sport):
        continue
    
    sport_df = df[df['Sport'] == sport].copy()
    sport_df = sport_df.dropna(subset=['First Name', 'Last Name'])
    
    # Get unique full names
    unique_names = sorted(set(sport_df['First Name'].astype(str) + ' ' + sport_df['Last Name'].astype(str)))
    
    # Compare all pairs
    for i, name1 in enumerate(unique_names):
        for name2 in unique_names[i+1:]:
            similarity = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
            
            if similarity > 0.85:
                # Count occurrences
                count1 = len(sport_df[(sport_df['First Name'].astype(str) + ' ' + sport_df['Last Name'].astype(str)) == name1])
                count2 = len(sport_df[(sport_df['First Name'].astype(str) + ' ' + sport_df['Last Name'].astype(str)) == name2])
                
                # Keep more frequent variant
                if count1 >= count2:
                    target = name1
                    source = name2
                else:
                    target = name2
                    source = name1
                
                # Parse names
                source_parts = source.rsplit(' ', 1)
                target_parts = target.rsplit(' ', 1)
                
                consolidations.append({
                    'sport': sport,
                    'source_first': source_parts[0],
                    'source_last': source_parts[1] if len(source_parts) > 1 else '',
                    'target_first': target_parts[0],
                    'target_last': target_parts[1] if len(target_parts) > 1 else '',
                    'similarity': similarity
                })
                similar_pairs.append((sport, source, target, similarity))

print(f"Found {len(similar_pairs)} similar name pairs")
print()

# Show sample consolidations
if consolidations:
    print("Sample consolidations:")
    for c in consolidations[:10]:
        print(f"  {c['sport']}: {c['source_first']} {c['source_last']} → {c['target_first']} {c['target_last']} ({c['similarity']:.1%})")
    if len(consolidations) > 10:
        print(f"  ... and {len(consolidations) - 10} more")
    print()

# Create consolidation mapping
consolidation_map = {}
for c in consolidations:
    source_key = f"{c['source_first']} {c['source_last']}".lower()
    target_first = c['target_first']
    target_last = c['target_last']
    consolidation_map[source_key] = (target_first, target_last)

print(f"Applying {len(consolidation_map)} consolidations to dataset...")

# Apply consolidation
consolidated_count = 0
df['Full_Name_Lower'] = (df['First Name'].astype(str) + ' ' + df['Last Name'].astype(str)).lower()

for idx, row in df.iterrows():
    full_name_lower = row['Full_Name_Lower']
    if full_name_lower in consolidation_map:
        target_first, target_last = consolidation_map[full_name_lower]
        df.at[idx, 'First Name'] = target_first
        df.at[idx, 'Last Name'] = target_last
        consolidated_count += 1

df = df.drop(columns=['Full_Name_Lower'])

print(f"✓ Consolidated {consolidated_count} rows")
unique_before = (df['First Name'].astype(str) + ' ' + df['Last Name'].astype(str)).nunique()
print(f"  Unique athletes after consolidation: {unique_before}")
print()

print("Recalculating Years_Targeted...")
years_targeted = df.groupby(['First Name', 'Last Name'])['Year'].nunique().reset_index()
years_targeted.columns = ['First Name', 'Last Name', 'years_count']
df = df.merge(years_targeted, on=['First Name', 'Last Name'], how='left')
df['Years_Targeted'] = df['years_count']
df = df.drop(columns=['years_count'])
print(f"  Range: {df['Years_Targeted'].min()}-{df['Years_Targeted'].max()}, avg {df['Years_Targeted'].mean():.2f}")
print()

print("Recalculating Convert_Year...")
# For each athlete, check if they increased program level year-over-year
athlete_data = df.sort_values(['First Name', 'Last Name', 'Year']).copy()
athlete_data['Level'] = athlete_data['Program'].map(LEVEL_HIERARCHY)

convert_year_dict = {}

for (first, last), group in athlete_data.groupby(['First Name', 'Last Name']):
    group = group.sort_values('Year')
    converted = False
    
    for idx in range(1, len(group)):
        prev_level = group.iloc[idx-1]['Level']
        curr_level = group.iloc[idx]['Level']
        
        if pd.notna(prev_level) and pd.notna(curr_level) and curr_level > prev_level:
            converted = True
            break
    
    convert_year_dict[(first, last)] = 'Y' if converted else 'N'

# Apply to dataframe
df['Convert_Key'] = df['First Name'].astype(str) + '|' + df['Last Name'].astype(str)
df['Convert_Year'] = df['Convert_Key'].map(
    lambda key: convert_year_dict.get(tuple(key.split('|')), 'N')
)
df = df.drop(columns=['Convert_Key'])

print(f"  Convert Y: {(df['Convert_Year'] == 'Y').sum()}")
print(f"  Convert N: {(df['Convert_Year'] == 'N').sum()}")
print()

# Save consolidated dataset
output_file = BASE_DIR / "Conversion_Data_2026_final.csv"
df.to_csv(output_file, index=False)

print("Final Statistics:")
print(f"  Total rows: {len(df)}")
print(f"  Unique athletes: {(df['First Name'].astype(str) + ' ' + df['Last Name'].astype(str)).nunique()}")
print(f"  CSS matches: {(df['CSS'] == 'YES').sum()}")
print(f"  Conversions (Y): {(df['Convert_Year'] == 'Y').sum()} ({(df['Convert_Year'] == 'Y').sum()/len(df)*100:.1f}%)")
print(f"  Years Targeted (avg): {df['Years_Targeted'].mean():.2f}")
print()
print(f"✓ Saved: {output_file}")
