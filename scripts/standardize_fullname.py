import pandas as pd
import re

# Read the CSV file
df = pd.read_csv('Conversion_Data_2026_final.csv')

# Standardize Full_Name column: lowercase, no spaces, no special characters
def standardize_name(name):
    if pd.isna(name):
        return name
    # Convert to lowercase
    name = str(name).lower()
    # Remove spaces
    name = name.replace(' ', '')
    # Remove special characters (keep only letters and numbers)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

df['Full_Name'] = df['Full_Name'].apply(standardize_name)

# Save the updated CSV
df.to_csv('Conversion_Data_2026_final.csv', index=False)

print("✓ Full_Name column standardized successfully!")
print("\nSample of standardized names:")
print(df['Full_Name'].head(20).values)
