import pandas as pd

df = pd.read_csv('/workspaces/Conversion/Conversion_Data_2026_final.csv')

with open('/tmp/final_stats.txt', 'w') as f:
    f.write("Final Dataset After Consolidation:\n")
    f.write(f"  Total rows: {len(df)}\n")
    unique = (df['First Name'].astype(str) + ' ' + df['Last Name'].astype(str)).nunique()
    f.write(f"  Unique athletes: {unique}\n")
    f.write(f"  CSS matches: {(df['CSS'] == 'YES').sum()}\n")
    f.write(f"  Convert_Year Y: {(df['Convert_Year'] == 'Y').sum()}\n")
    f.write(f"  Convert_Year N: {(df['Convert_Year'] == 'N').sum()}\n")
    f.write(f"  Conversion rate: {(df['Convert_Year'] == 'Y').sum()/len(df)*100:.1f}%\n")
    f.write(f"  Years_Targeted (avg): {df['Years_Targeted'].mean():.2f}\n")
    f.write(f"  Years_Targeted (range): {df['Years_Targeted'].min()}-{df['Years_Targeted'].max()}\n")

print("Stats written to /tmp/final_stats.txt")
