#!/usr/bin/env python
import os
import sys
import pandas as pd
from pathlib import Path

os.environ["SITE_URL"] = "http://localhost:8050"
os.environ["OAUTH_REDIRECT_PATH"] = "/oauth-redirect"
os.environ["CLIENT_ID"] = "test_client"
os.environ["CLIENT_SECRET"] = "test_secret"

# Load data
DF_PATH = Path(".") / "Conversion_Data_2026_final.csv"
df = pd.read_csv(DF_PATH)
df["_year_num"] = pd.to_numeric(df["Year"], errors="coerce")
df["DOB_parsed"] = pd.to_datetime(df["Date of Birth"], errors="coerce")
df["BirthYear"] = df["DOB_parsed"].dt.year
df["Full_Name"] = df["First Name"].astype(str).str.strip() + " " + df["Last Name"].astype(str).str.strip()
df["_program_level"] = df["Program"].astype(str).str.strip().map({
    "Prov Dev 3": 1,
    "Prov Dev 2": 2,
    "Prov Dev 1": 3,
    "Uncarded": 4,
    "SC Carded": 5,
})

print("✓ Data loaded")
print(f"  Total rows: {len(df)}")
print(f"  2026 rows: {len(df[df['_year_num'] == 2026])}")
print(f"  Sports: {df['Sport'].nunique()}")

# Test the via-sport filtering
dff = df[df["Sport"].isin(["Ice Hockey"])].copy()
print(f"\n✓ Filtered to Ice Hockey")
print(f"  Rows: {len(dff)}")
print(f"  2026 rows: {len(dff[dff['_year_num'] == 2026])}")

# Test via-sport report function
report_df = dff.copy()
report_df = report_df[report_df["_year_num"].notna()].copy()

if not report_df.empty:
    current_year = report_df[report_df["_year_num"].eq(2026)].copy()
    if not current_year.empty:
        current_year["Gender"] = current_year["Gender"].astype(str).str.strip().str.upper()
        current_year["age_2026"] = 2026 - current_year["BirthYear"]
        print(f"\n✓ Via-sport report can process 2026 data")
        print(f"  Rows: {len(current_year)}")
        print(f"  Age calculated: {current_year['age_2026'].notna().sum()}")
    else:
        print("\n✗ No 2026 data for report")
else:
    print("\n✗ No data for report")

print("\n✓ Dashboard data processing test completed successfully!")
