import pandas as pd
import numpy as np

df = pd.read_csv('Conversion_Data_2026_final.csv')

# Define program hierarchy
program_hierarchy = {
    'Prov Dev 3': 1,
    'Prov Dev 2': 2,
    'Prov Dev 1': 3,
    'Uncarded': 4,
    'SC Carded': 5
}

print("Recalculating Years Targeted and Convert Year...")

# 1. Recalculate Years Targeted - count unique years per athlete per sport
df['Years Targeted'] = df.groupby(['Full_Name', 'Sport'])['Year'].transform('nunique')

print(f"✓ Years Targeted recalculated")

# 2. Recalculate Convert Year
# Sort by Full_Name, Sport, and Year to ensure proper ordering
df = df.sort_values(['Full_Name', 'Sport', 'Year']).reset_index(drop=True)

# Initialize Convert Year as N for all
df['Convert Year'] = 'N'

def is_multisport(sport_name):
    return str(sport_name).strip().lower() == 'multisport'


# For each athlete, mark conversions when program improves within the same sport.
# Exception: Multisport acts as a wildcard predecessor for any sport.
for athlete_name in df['Full_Name'].unique():
    athlete_df = df[df['Full_Name'] == athlete_name].copy()

    # Build {sport -> {year -> max program level}} for this athlete.
    sport_year_level = {}
    for (sport, year), group in athlete_df.groupby(['Sport', 'Year']):
        max_level = max([program_hierarchy.get(p, 0) for p in group['Program'].unique()])
        sport_year_level.setdefault(sport, {})[year] = max_level

    all_sports = list(sport_year_level.keys())
    multisport_names = [s for s in all_sports if is_multisport(s)]

    # Evaluate non-multisport sports against prior same-sport or prior multisport years.
    for sport in all_sports:
        if is_multisport(sport):
            continue

        sport_years = set(sport_year_level[sport].keys())
        wildcard_years = set()
        for ms_name in multisport_names:
            wildcard_years.update(sport_year_level[ms_name].keys())

        years_in_order = sorted(sport_years.union(wildcard_years))

        for i in range(1, len(years_in_order)):
            prev_year = years_in_order[i - 1]
            curr_year = years_in_order[i]

            # Only evaluate conversion where current year contains this target sport.
            if curr_year not in sport_years:
                continue

            prev_levels = []
            if prev_year in sport_year_level[sport]:
                prev_levels.append(sport_year_level[sport][prev_year])
            for ms_name in multisport_names:
                if prev_year in sport_year_level[ms_name]:
                    prev_levels.append(sport_year_level[ms_name][prev_year])

            if not prev_levels:
                continue

            prev_max_level = max(prev_levels)
            curr_max_level = sport_year_level[sport][curr_year]

            if curr_max_level > prev_max_level:
                conversion_indices = df[
                    (df['Full_Name'] == athlete_name) &
                    (df['Sport'] == sport) &
                    (df['Year'] == curr_year)
                ].index.tolist()
                df.loc[conversion_indices, 'Convert Year'] = 'Y'

    # Evaluate multisport rows within multisport only.
    for ms_name in multisport_names:
        ms_years = sorted(sport_year_level[ms_name].keys())
        for i in range(1, len(ms_years)):
            prev_year = ms_years[i - 1]
            curr_year = ms_years[i]

            prev_max_level = sport_year_level[ms_name][prev_year]
            curr_max_level = sport_year_level[ms_name][curr_year]

            if curr_max_level > prev_max_level:
                conversion_indices = df[
                    (df['Full_Name'] == athlete_name) &
                    (df['Sport'] == ms_name) &
                    (df['Year'] == curr_year)
                ].index.tolist()
                df.loc[conversion_indices, 'Convert Year'] = 'Y'

print(f"✓ Convert Year recalculated")

# Save
df.to_csv('Conversion_Data_2026_final.csv', index=False)

print(f"\n✓ File saved!")
print(f"\nSummary:")
print(f"Total records: {len(df)}")
print(f"\nYears Targeted distribution:")
print(df['Years Targeted'].value_counts().sort_index())
print(f"\nConvert Year distribution:")
print(df['Convert Year'].value_counts())

# Show examples
print(f"\n\nExample: andrewdavis")
example = df[df['Full_Name'] == 'andrewdavis'][['Full_Name', 'Sport', 'Year', 'Program', 'Years Targeted', 'Convert Year']].sort_values('Year')
print(example.head(15).to_string())
