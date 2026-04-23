#!/usr/bin/env python
"""Test fixed column merging logic"""
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

# Filter
dff = df[df["Sport"].isin(["Ice Hockey"])].copy()
has_2026 = dff.groupby('Full_Name')['_year_num'].transform(lambda s: s.eq(2026).any())
dff = dff[has_2026].copy()

# Report building
report_df = dff.copy()
report_df = report_df[report_df["_year_num"].notna()].copy()

NATIONAL_TARGET_LEVELS = [4, 5]
NATIONAL_SOURCE_LEVELS = [1, 2, 3]

latest_year = int(report_df["_year_num"].max())
athlete_cols = ["Sport", "First Name", "Last Name"]
current_year = report_df[report_df["_year_num"].eq(2026)].copy()

current_year["Gender"] = current_year["Gender"].astype(str).str.strip().str.upper()
current_year["age_2026"] = 2026 - current_year["BirthYear"]

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

career_conversion = (
    report_df
    .groupby(athlete_cols, as_index=False)
    .agg(career_converted=("Convert Year", lambda s: s.astype(str).str.upper().eq("Y").any()))
)
cohort_2026 = cohort_2026.merge(career_conversion, on=athlete_cols, how="left")

recent_conversions = (
    report_df[report_df["_year_num"].ge(2022) & report_df["Convert Year"].astype(str).str.upper().eq("Y")]
    .groupby("Sport", as_index=False)
    .size()
    .rename(columns={"size": "Sum of Total conversion Since 2022"})
)

yearly = (
    report_df
    .groupby(athlete_cols + ["_year_num"], as_index=False)
    .agg(
        year_best_level=("_program_level", "max"),
        convert_year_flag=("Convert Year", lambda s: s.astype(str).str.upper().eq("Y").any()),
    )
    .sort_values(athlete_cols + ["_year_num"])
)
yearly["prev_year"] = yearly.groupby(athlete_cols)["_year_num"].shift(1)
yearly["prev_level"] = yearly.groupby(athlete_cols)["year_best_level"].shift(1)
yearly["is_national_conversion"] = (
    yearly["convert_year_flag"]
    & yearly["year_best_level"].isin(NATIONAL_TARGET_LEVELS)
    & yearly["prev_level"].isin(NATIONAL_SOURCE_LEVELS)
    & (yearly["_year_num"] == yearly["prev_year"] + 1)
)
national_recent = (
    yearly[yearly["_year_num"].ge(2022) & yearly["is_national_conversion"]]
    .groupby("Sport", as_index=False)
    .size()
    .rename(columns={"size": "Sum of Total Conversion Provincial to national since 2022"})
)

cohort_gender = (
    cohort_2026.groupby("Sport")["Gender"]
    .value_counts()
    .unstack(fill_value=0)
    .reset_index()
)
for gender in ["F", "M", "X"]:
    if gender not in cohort_gender.columns:
        cohort_gender[gender] = 0
cohort_gender["Gender (F/M/X) - 2026 Cohort"] = cohort_gender.apply(
    lambda row: f"F: {int(row['F'])} / M: {int(row['M'])} / X: {int(row['X'])}",
    axis=1,
)

# THIS IS THE FIXED CODE - NO "Sum of Total conversion Since 2022" in cohort_rollup
cohort_rollup = (
    cohort_2026
    .groupby("Sport", as_index=False)
    .agg(
        **{
            "TOTAL Athletes 2026 identified (Conv Data)": ("Sport", "size"),
            "Carrer conversion rate for 2026 cohort": ("career_converted", "mean"),
            "Average Years Targeted 2026 cohort (Career)": ("Years_Targeted", "mean"),
            "Average Age 2026 Cohort": ("age_2026", "mean"),
        }
    )
)
print(f"cohort_rollup columns: {cohort_rollup.columns.tolist()}")

current_year_rollup = (
    current_year
    .groupby("Sport", as_index=False)
    .agg(current_total=("Sport", "size"), current_converted=("Convert Year", lambda s: s.astype(str).str.upper().eq("Y").sum()))
)

# THIS IS THE FIXED MERGE - using suffixes to avoid renaming conflicts
report_output = cohort_rollup.merge(current_year_rollup, on="Sport", how="left")
print(f"After merge 1: {report_output.columns.tolist()}")

report_output = report_output.merge(recent_conversions, on="Sport", how="left", suffixes=("", "_from_recent"))
print(f"After merge 2: {report_output.columns.tolist()}")

report_output = report_output.merge(national_recent, on="Sport", how="left")
print(f"After merge 3: {report_output.columns.tolist()}")

report_output = report_output.merge(cohort_gender[["Sport", "Gender (F/M/X) - 2026 Cohort"]], on="Sport", how="left")
print(f"After merge 4: {report_output.columns.tolist()}")

# Add missing columns
report_output["2026 conversion Rate (Current Year convert / Current year total)"] = (
    (report_output["current_converted"] / report_output["current_total"] * 100)
    .fillna(0)
    .round(1)
)

# Fill missing columns
report_output["Sum of Total conversion Since 2022"] = report_output["Sum of Total conversion Since 2022"].fillna(0).astype(int)
report_output["Sum of Total Conversion Provincial to national since 2022"] = report_output["Sum of Total Conversion Provincial to national since 2022"].fillna(0).astype(int)

print(f"\nAll columns after fill:")
for col in report_output.columns:
    print(f"  - {col}")

print(f"\nColumns that table will try to access:")
cols_needed = [
    "Sport",
    "TOTAL Athletes 2026 identified (Conv Data)",
    "Sum of Total conversion Since 2022",
    "Sum of Total Conversion Provincial to national since 2022",
    "2026 conversion Rate (Current Year convert / Current year total)",
    "Carrer conversion rate for 2026 cohort",
    "Average Years Targeted 2026 cohort (Career)",
    "Average Age 2026 Cohort",
    "Gender (F/M/X) - 2026 Cohort",
]
for col in cols_needed:
    exists = col in report_output.columns
    print(f"  {col}: {'✓' if exists else '✗'}")

print(f"\n✓ All columns present!")
