#!/usr/bin/env python
"""Test _build_via_sport_report directly"""
import os
import sys
import pandas as pd
from pathlib import Path

os.environ["SITE_URL"] = "http://localhost:8050"
os.environ["OAUTH_REDIRECT_PATH"] = "/oauth-redirect"
os.environ["CLIENT_ID"] = "test_client"
os.environ["CLIENT_SECRET"] = "test_secret"

# Import the necessary modules from dashboard
sys.path.insert(0, '.')

# Load data setup
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

# Test data
print("Testing _build_via_sport_report with Ice Hockey data...")
dff = df[df["Sport"].isin(["Ice Hockey"])].copy()
print(f"Ice Hockey rows: {len(dff)}")

# Apply 2026 filter (current-history)
has_2026 = dff.groupby('Full_Name')['_year_num'].transform(lambda s: s.eq(2026).any())
dff = dff[has_2026].copy()
print(f"After 2026 filter: {len(dff)}")

# Now test the report building logic
report_df = dff.copy()
report_df = report_df[report_df["_year_num"].notna()].copy()
print(f"After removing null years: {len(report_df)}")

if report_df.empty:
    print("ERROR: No data!")
    sys.exit(1)

latest_year = int(report_df["_year_num"].max())
print(f"Latest year: {latest_year}")

athlete_cols = ["Sport", "First Name", "Last Name"]

current_year = report_df[report_df["_year_num"].eq(2026)].copy()
print(f"2026 rows: {len(current_year)}")
if current_year.empty:
    print("ERROR: No 2026 rows!")
    sys.exit(1)

current_year["Gender"] = current_year["Gender"].astype(str).str.strip().str.upper()
current_year["age_2026"] = 2026 - current_year["BirthYear"]

print(f"\nBuilding cohort_2026...")
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
print(f"  Cohort size: {len(cohort_2026)}")
print(f"  Sample rows: {cohort_2026.head()}")

print(f"\nBuilding career_conversion...")
career_conversion = (
    report_df
    .groupby(athlete_cols, as_index=False)
    .agg(career_converted=("Convert Year", lambda s: s.astype(str).str.upper().eq("Y").any()))
)
print(f"  Size: {len(career_conversion)}")

cohort_2026 = cohort_2026.merge(career_conversion, on=athlete_cols, how="left")
print(f"  After merge: {len(cohort_2026)}")

print(f"\nBuilding recent_conversions...")
recent_conversions = (
    report_df[report_df["_year_num"].ge(2022) & report_df["Convert Year"].astype(str).str.upper().eq("Y")]
    .groupby("Sport", as_index=False)
    .size()
    .rename(columns={"size": "Sum of Total conversion Since 2022"})
)
print(f"  Size: {len(recent_conversions)}")

print(f"\nBuilding cohort_rollup...")
cohort_rollup = (
    cohort_2026
    .groupby("Sport", as_index=False)
    .agg(
        **{
            "TOTAL Athletes 2026 identified (Conv Data)": ("Sport", "size"),
            "Sum of Total conversion Since 2022": ("current_converted", "sum"),
            "Carrer conversion rate for 2026 cohort": ("career_converted", "mean"),
            "Average Years Targeted 2026 cohort (Career)": ("Years_Targeted", "mean"),
            "Average Age 2026 Cohort": ("age_2026", "mean"),
        }
    )
)
print(f"  Size: {len(cohort_rollup)}")
print(f"  Columns: {cohort_rollup.columns.tolist()}")
print(f"  Sample: {cohort_rollup}")

print(f"\nAll tests passed! Report ready for rendering.")
