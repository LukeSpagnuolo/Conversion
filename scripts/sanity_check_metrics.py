import pandas as pd
import numpy as np

# Load the data
df = pd.read_csv('Conversion_Data_2026_final.csv')

print("=" * 80)
print("SANITY CHECK: Calculated Metrics for Convert Year and Years Targeted")
print("=" * 80)
print(f"\nTotal records: {len(df)}")
print(f"Date range: {df['Year'].min()} - {df['Year'].max()}")
print(f"Number of unique athletes: {df['Full_Name'].nunique()}")

# ============================================================================
# CHECK 1: Years Targeted Consistency
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 1: Years Targeted Consistency")
print("=" * 80)

# Fast check using groupby
years_targeted_consistency = df.groupby('Full_Name')['Years Targeted'].nunique()
inconsistent_athletes = years_targeted_consistency[years_targeted_consistency > 1]

if len(inconsistent_athletes) > 0:
    print(f"\n❌ ISSUE: {len(inconsistent_athletes)} athletes have INCONSISTENT 'Years Targeted' values:")
    for athlete_name in inconsistent_athletes.head(20).index:
        athlete_data = df[df['Full_Name'] == athlete_name]
        values = sorted(athlete_data['Years Targeted'].unique())
        print(f"  - {athlete_name}: {values} ({len(athlete_data)} records)")
    if len(inconsistent_athletes) > 20:
        print(f"  ... and {len(inconsistent_athletes) - 20} more")
else:
    print("\n✓ PASS: All athletes have consistent 'Years Targeted' values")

# ============================================================================
# CHECK 2: Years Targeted vs Actual Years Count
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 2: Years Targeted Validation (vs actual count in dataset)")
print("=" * 80)

# For each athlete, get their Years Targeted and count of records
athlete_stats = df.groupby('Full_Name').agg({
    'Years Targeted': 'first',
    'Full_Name': 'count'
}).rename(columns={'Full_Name': 'Actual_Years_Count'})

# Find mismatches
mismatches = athlete_stats[athlete_stats['Years Targeted'] != athlete_stats['Actual_Years_Count']]

if len(mismatches) > 0:
    print(f"\n⚠ WARNING: {len(mismatches)} athletes have mismatch between 'Years Targeted' and actual years in dataset:")
    for athlete_name in mismatches.head(25).index:
        targeted = mismatches.loc[athlete_name, 'Years Targeted']
        actual = mismatches.loc[athlete_name, 'Actual_Years_Count']
        diff = actual - targeted
        symbol = "❌" if diff != 0 else "⚠"
        print(f"  {symbol} {athlete_name}: Targeted={int(targeted)}, Actual={actual} (diff: {diff:+d})")
    if len(mismatches) > 25:
        print(f"  ... and {len(mismatches) - 25} more")
else:
    print("\n✓ PASS: All athletes have matching 'Years Targeted' and actual years in dataset")

# ============================================================================
# CHECK 3: Convert Year Distribution
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 3: Convert Year Distribution")
print("=" * 80)

convert_dist = df['Convert Year'].value_counts()
print(f"\nConvert Year value counts:")
print(f"  Y (Converted): {convert_dist.get('Y', 0)} ({convert_dist.get('Y', 0)/len(df)*100:.1f}%)")
print(f"  N (Not Converted): {convert_dist.get('N', 0)} ({convert_dist.get('N', 0)/len(df)*100:.1f}%)")

# Check athletes who converted
athletes_with_conversion = df[df['Convert Year'] == 'Y']['Full_Name'].nunique()
total_athletes = df['Full_Name'].nunique()
print(f"\nAthletes with at least one 'Convert Year=Y': {athletes_with_conversion}")
print(f"Total unique athletes: {total_athletes}")
print(f"Athletes without conversion: {total_athletes - athletes_with_conversion}")

# ============================================================================
# CHECK 4: Program Transitions and Convert Year Logic
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 4: Program Status at Conversion Records")
print("=" * 80)

conversion_program_dist = df[df['Convert Year'] == 'Y']['Program'].value_counts()
print(f"\nProgram distribution for 'Convert Year=Y' records:")
for program, count in conversion_program_dist.items():
    pct = count / df[df['Convert Year'] == 'Y'].shape[0] * 100
    print(f"  {program}: {count} ({pct:.1f}%)")

# ============================================================================
# CHECK 5: First Conversion Year Statistics
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 5: First Conversion Timing")
print("=" * 80)

# Get first conversion year for each athlete
conversion_data = df[df['Convert Year'] == 'Y'].groupby('Full_Name')['Year'].min()

if len(conversion_data) > 0:
    print(f"\nFirst conversion year distribution (must convert before or at latest year):")
    print(f"  Earliest conversion: {conversion_data.min()}")
    print(f"  Latest conversion: {conversion_data.max()}")
    print(f"  Mean: {conversion_data.mean():.1f}")
    
    year_dist = conversion_data.value_counts().sort_index()
    print(f"\nFirst conversions by year:")
    for year in sorted(year_dist.index):
        count = year_dist[year]
        print(f"  {int(year)}: {count} athletes")
else:
    print("\n  No athletes with Convert Year=Y found")

# ============================================================================
# CHECK 6: Missing Values
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 6: Data Completeness")
print("=" * 80)

print(f"\nMissing values:")
print(f"  Years Targeted: {df['Years Targeted'].isna().sum()}")
print(f"  Convert Year: {df['Convert Year'].isna().sum()}")
print(f"  Program: {df['Program'].isna().sum()}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

issues_found = len(inconsistent_athletes) + len(mismatches)
print(f"\nTotal issues found: {issues_found}")
print(f"  - Inconsistent Years Targeted: {len(inconsistent_athletes)}")
print(f"  - Years Targeted mismatches: {len(mismatches)}")

if issues_found == 0:
    print("\n✓ ALL SANITY CHECKS PASSED!")
else:
    print(f"\n⚠ {issues_found} issues require investigation")

print("\n" + "=" * 80)
