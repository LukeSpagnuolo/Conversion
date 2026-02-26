import pandas as pd
from difflib import SequenceMatcher

# Read the CSV file
df = pd.read_csv('Conversion_Data_2026_final.csv')

# Get unique full names with their counts
name_counts = df['Full_Name'].value_counts().to_dict()
unique_names = sorted(name_counts.keys())

print(f"Total unique full names: {len(unique_names)}\n")

# Group by first few characters for speed
from collections import defaultdict

name_groups = defaultdict(list)
for name in unique_names:
    # Group by first 4 characters
    prefix = name[:4] if len(name) >= 4 else name
    name_groups[prefix].append(name)

# Find similar names within each group (much faster)
def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

similar_clusters = []

for prefix, names in name_groups.items():
    if len(names) > 1:
        # Check pairs within each group
        used = set()
        for i, name1 in enumerate(names):
            if name1 in used:
                continue
            cluster = [name1]
            used.add(name1)
            
            for name2 in names[i+1:]:
                if name2 not in used:
                    sim = similarity(name1, name2)
                    if sim >= 0.85:  # Similar within the same prefix group
                        cluster.append(name2)
                        used.add(name2)
            
            if len(cluster) > 1:
                similar_clusters.append(cluster)

# Sort by total records
similar_clusters = sorted(
    similar_clusters, 
    key=lambda x: sum(name_counts[name] for name in x), 
    reverse=True
)

print(f"Found {len(similar_clusters)} clusters of similar names:\n")

for i, cluster in enumerate(similar_clusters[:50], 1):
    total = sum(name_counts[name] for name in cluster)
    print(f"{i}. Cluster ({total} total records):")
    for name in sorted(cluster):
        count = name_counts[name]
        print(f"   • {name} ({count} records)")
    print()

if len(similar_clusters) == 0:
    print("✓ No significant spelling variations or typos found!")
