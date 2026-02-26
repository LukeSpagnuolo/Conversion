import pandas as pd

# Read the CSV file
df = pd.read_csv('Conversion_Data_2026_final.csv')

# Sort by Full_Name to consolidate names together
df = df.sort_values('Full_Name').reset_index(drop=True)

# Save the sorted CSV
df.to_csv('Conversion_Data_2026_final.csv', index=False)

print("✓ Data sorted by Full_Name column!")
print(f"✓ Total records: {len(df)}")
print("\nFirst 20 rows after sorting:")
print(df[['Full_Name', 'First Name', 'Last Name', 'Sport', 'Year']].head(20))
