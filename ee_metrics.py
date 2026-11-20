"""EE Metrics: per-sport conversion metrics for the Enhanced Excellence report.

Produces the three EE_Metrics columns that come from conversion data (the rest of
that sheet comes from the sports' returned EE Sport Templates):

  * % Avg Conversions to Any Level (4y)
  * % Avg Conversion Prov→Nat (4y)
  * Avg Years Targeted (Prov Dev, report year)

Sports and merges follow List Generator 7000's EE Sport Templates tab
(prebuilt_reports_7000.py: ENHANCED_EXCELLENCE_SPORTS, default_sports, ee_sport_groups).
Keep the two in step if the EE sport list changes.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

# Copied from List Generator's prebuilt_reports_7000.ENHANCED_EXCELLENCE_SPORTS.
ENHANCED_EXCELLENCE_SPORTS = {
    "alpine ski", "alpine skiing", "artistic swimming", "athletics", "diving",
    "basketball", "biathlon", "artistic gymnastics", "canoe/kayak", "canoe kayak",
    "cross country skiing", "cross-country skiing", "cross-country ski", "curling",
    "cycling", "judo", "rowing", "field hockey", "figure skating",
    "freestyle skiing", "freestyle ski", "wheelchair athletics", "wheelchair rugby",
    "wheelchair tennis", "wrestling", "rugby", "sailing", "snowboard", "swimming",
    "triathlon", "volleyball", "wheelchair basketball",
}
WHEELCHAIR_GROUP = {"wheelchair athletics", "wheelchair rugby", "wheelchair tennis"}
WHEELCHAIR_GROUP_LABEL = "Wheelchair sports"

PROGRAM_LEVELS = {"Prov Dev 3": 1, "Prov Dev 2": 2, "Prov Dev 1": 3, "Uncarded": 4, "SC Carded": 5}
PROV_DEV_LEVELS = {1, 2, 3}
NATIONAL_LEVELS = {4, 5}
WINDOW_YEARS = 4

COL_SPORT = "Sport"
COL_MEMBERS = "Sports included"
COL_YEAR = "Report year"
COL_WINDOW = "4-year window"
COL_ATHLETES = "Athletes in report year"
COL_ANY = "% Avg Conversions to Any Level (4y)"
COL_NATIONAL = "% Avg Conversion Prov→Nat (4y)"
COL_YEARS_TARGETED = "Avg Years Targeted (Prov Dev, report year)"
COLUMNS = [COL_SPORT, COL_MEMBERS, COL_YEAR, COL_WINDOW, COL_ATHLETES, COL_ANY, COL_NATIONAL, COL_YEARS_TARGETED]
# Not exported: True when the report year has under half the previous year's athletes, or no
# Prov Dev athletes after a year that had some; usually that year's nominations aren't all in.
COL_PARTIAL = "_partial_year"

GUIDE = (
    "One row per EE sport. Para sports are counted with their parent sport; Wheelchair Athletics, "
    "Rugby and Tennis are one 'Wheelchair sports' row; Wheelchair Basketball stays separate "
    "(the same groups as List Generator's EE Sport Templates). "
    "Report year defaults to the last full fiscal year (dataset Year N is fiscal N-1 to N, ending "
    "31 March of N), so a year whose nominations are still coming in is left out; the 4-year "
    "window ends at the report year. "
    "Conversions to Any Level: for each year in the window, athletes with a conversion that year "
    "÷ athletes in the sport that year; the column is the average of those yearly rates. "
    "Prov→Nat uses only conversions from Prov Dev to Uncarded/SC Carded in consecutive years "
    "(the dashboard's provincial-to-national rule). Avg Years Targeted is the career Years "
    "Targeted of athletes at Prov Dev 1–3 in the report year."
)


def last_full_year(years, today: date | None = None) -> int | None:
    """Latest dataset Year whose fiscal year (ending 31 March of that Year) has finished."""
    today = today or date.today()
    finished = today.year if today.month > 3 else today.year - 1
    candidates = [int(year) for year in years if pd.notna(year) and int(year) <= finished]
    return max(candidates) if candidates else None


def _normalize(value) -> str:
    return " ".join(str(value or "").strip().lower().split())


def default_ee_sports(sports) -> list[str]:
    """EE sports present in the data, plus their Para variants (List Generator's default_sports)."""
    selected = []
    for sport in sports:
        key = _normalize(sport)
        if key in ENHANCED_EXCELLENCE_SPORTS or (
            key.startswith("para ") and key[5:] in ENHANCED_EXCELLENCE_SPORTS
        ):
            selected.append(sport)
    return selected


def ee_sport_groups(available, chosen) -> list[tuple[str, list[str]]]:
    """(row label, member sports) for the chosen sports (List Generator's ee_sport_groups)."""
    available = list(available)
    by_normalized = {_normalize(value): value for value in available}
    selected = {_normalize(value) for value in chosen}
    groups: list[tuple[str, list[str]]] = []
    grouped: set[str] = set()

    wheelchair = sorted(value for value in available if _normalize(value) in WHEELCHAIR_GROUP)
    if selected & {_normalize(value) for value in wheelchair}:
        groups.append((WHEELCHAIR_GROUP_LABEL, wheelchair))
        grouped.update(_normalize(value) for value in wheelchair)

    for sport in chosen:
        normalized = _normalize(sport)
        if normalized in grouped:
            continue
        if normalized == "wheelchair basketball":
            groups.append((sport, [sport]))
            grouped.add(normalized)
            continue
        parent = normalized.removeprefix("para ")
        members = [by_normalized[value] for value in (parent, f"para {parent}") if value in by_normalized]
        if len(members) > 1:
            groups.append((by_normalized[parent], members))
            grouped.update(_normalize(value) for value in members)
        else:
            groups.append((sport, [sport]))
            grouped.add(normalized)
    return sorted(groups, key=lambda group: group[0].lower())


def _yearly_athletes(rows: pd.DataFrame) -> pd.DataFrame:
    """One row per athlete per year: best level that year and whether they converted that year.

    Athletes are keyed by Full_Name (the cleaned key) within the sport group, so a Para athlete
    and the same person in the parent sport count once.
    """
    working = rows.assign(
        _year=pd.to_numeric(rows["Year"], errors="coerce"),
        _level=rows["Program"].astype(str).str.strip().map(PROGRAM_LEVELS),
        _converted=rows["Convert Year"].astype(str).str.strip().str.upper().eq("Y"),
        _years_targeted=pd.to_numeric(rows["Years Targeted"], errors="coerce"),
    )
    working = working[working["_year"].notna()]
    yearly = (
        working.groupby(["Full_Name", "_year"], as_index=False)
        .agg(
            level=("_level", "max"),
            converted=("_converted", "any"),
            years_targeted=("_years_targeted", "max"),
        )
        .sort_values(["Full_Name", "_year"])
    )
    previous_year = yearly.groupby("Full_Name")["_year"].shift(1)
    previous_level = yearly.groupby("Full_Name")["level"].shift(1)
    yearly["national"] = (
        yearly["converted"]
        & yearly["level"].isin(NATIONAL_LEVELS)
        & previous_level.isin(PROV_DEV_LEVELS)
        & yearly["_year"].eq(previous_year + 1)
    )
    return yearly


def _round(value, digits):
    return None if pd.isna(value) else round(float(value), digits)


def sport_metrics(rows: pd.DataFrame, report_year: int | None = None) -> dict:
    """Metrics for one sport group's rows. ``report_year`` defaults to the group's latest year."""
    yearly = _yearly_athletes(rows)
    if yearly.empty:
        return {}
    report_year = int(report_year) if report_year else int(yearly["_year"].max())
    window = yearly[yearly["_year"].between(report_year - WINDOW_YEARS + 1, report_year)]
    per_year = window.groupby("_year").agg(
        athletes=("Full_Name", "size"), converted=("converted", "sum"), national=("national", "sum")
    )
    per_year = per_year[per_year["athletes"] > 0]
    current = yearly[yearly["_year"].eq(report_year)]
    previous = yearly[yearly["_year"].eq(report_year - 1)]
    prov_dev = current[current["level"].isin(PROV_DEV_LEVELS)]
    return {
        COL_YEAR: report_year,
        COL_WINDOW: f"{report_year - WINDOW_YEARS + 1}–{report_year}",
        COL_ATHLETES: int(len(current)),
        COL_ANY: _round((per_year["converted"] / per_year["athletes"]).mean() * 100, 1),
        COL_NATIONAL: _round((per_year["national"] / per_year["athletes"]).mean() * 100, 1),
        COL_YEARS_TARGETED: _round(prov_dev["years_targeted"].mean(), 2),
        COL_PARTIAL: bool(
            len(current) < len(previous) / 2
            or (prov_dev.empty and previous["level"].isin(PROV_DEV_LEVELS).any())
        ),
    }


def build_ee_metrics(df: pd.DataFrame, chosen_sports, report_year: int | None = None) -> pd.DataFrame:
    """One row per EE sport group; ``report_year`` None means each sport's latest year."""
    records = []
    for label, members in ee_sport_groups(df["Sport"].dropna().unique(), chosen_sports or []):
        metrics = sport_metrics(df[df["Sport"].isin(members)], report_year)
        if metrics:
            records.append({COL_SPORT: label, COL_MEMBERS: ", ".join(members), **metrics})
    return pd.DataFrame(records, columns=COLUMNS + [COL_PARTIAL])
