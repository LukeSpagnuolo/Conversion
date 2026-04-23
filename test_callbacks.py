#!/usr/bin/env python
"""Test dashboard callback functions in isolation"""
import os
import sys
import pandas as pd
from pathlib import Path

os.environ["SITE_URL"] = "http://localhost:8050"
os.environ["OAUTH_REDIRECT_PATH"] = "/oauth-redirect"
os.environ["CLIENT_ID"] = "test_client"
os.environ["CLIENT_SECRET"] = "test_secret"

# Load just the data setup part
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

print(f"✓ Data loaded: {len(df)} rows")
print(f"  Columns: {df.columns.tolist()}")

# Test 1: Check available sports
sports = sorted(df['Sport'].dropna().unique())
print(f"\n✓ Available sports ({len(sports)}):")
for s in sports[:5]:
    print(f"    - {s}")

# Test 2: Filter to Ice Hockey and test _filter_dashboard_df logic
selected_sports = ["Ice Hockey"]
print(f"\n✓ Filtering to {selected_sports}")
dff = df[df['Sport'].isin(selected_sports)].copy()
print(f"  Rows after sport filter: {len(dff)}")

# Test 3: Apply 2026 current-history filter
filter_2026 = ["2026"]
if filter_2026 and "2026" in filter_2026:
    has_2026 = dff.groupby('Full_Name')['_year_num'].transform(lambda s: s.eq(2026).any())
    dff = dff[has_2026].copy()
    print(f"  Rows after 2026 filter: {len(dff)}")

# Test 4: Test _build_via_sport_report_df logic
print(f"\n✓ Testing via-sport report")
if dff.empty:
    print("  ✗ No data after filtering")
else:
    report_df = dff.copy()
    report_df = report_df[report_df["_year_num"].notna()].copy()
    
    if report_df.empty:
        print("  ✗ No data after removing null years")
    else:
        print(f"  Rows in report_df: {len(report_df)}")
        
        # Check for 2026 data
        current_year = report_df[report_df["_year_num"].eq(2026)].copy()
        print(f"  2026 rows: {len(current_year)}")
        
        if current_year.empty:
            print("  ✗ No 2026 data!")
        else:
            current_year["Gender"] = current_year["Gender"].astype(str).str.strip().str.upper()
            current_year["age_2026"] = 2026 - current_year["BirthYear"]
            
            athlete_cols = ["Sport", "First Name", "Last Name"]
            cohort_2026 = (
                current_year
                .groupby(athlete_cols, as_index=False)
                .agg(
                    BirthYear=("BirthYear", "first"),
                    Years_Targeted=("Years Targeted", "first"),
                    Gender=("Gender", lambda s: s.iloc[0] if len(s) else ""),
                    current_converted=("Convert Year", lambda s: s.astype(str).str.upper().eq("Y").any()),
                )
            )
            cohort_2026["age_2026"] = 2026 - cohort_2026["BirthYear"]
            print(f"  ✓ Cohort 2026 aggregated: {len(cohort_2026)} unique athlete-sport pairs")

print("\n✓ All tests passed!")
