"""Check a List Generator 7000 nominations export against the conversion dataset.

usage: check_nominations.py <export.csv> <Conversion_Data.csv> <out_dir>
Matching rule: name + DOB + sport (sport groups as in clean_dataset.py).
"""
import re
import sys
from difflib import SequenceMatcher

import pandas as pd

exp_path, ds_path, out = sys.argv[1:4]
norm = lambda s: re.sub(r"[^a-z]", "", str(s).lower())
LEVEL = {"Prov Dev 3": 1, "Prov Dev 2": 2, "Prov Dev 1": 3, "Uncarded": 4, "SC Carded": 5}
CARDING = {"Prov Dev 1": "Prov Dev 1", "Prov Dev 2": "Prov Dev 2", "Prov Dev 3": "Prov Dev 3",
           "NSO Affiliated (Uncarded)": "Uncarded", "PSO Affiliated (Uncarded)": "Uncarded",
           "SR": "SC Carded", "SR1": "SC Carded", "SR2": "SC Carded", "SRI": "SC Carded",
           "D": "SC Carded", "DI": "SC Carded", "C1": "SC Carded"}
SPORT_RENAME = {"Hockey": "Ice Hockey"}
SPORT_GROUP = {
    "Para Athletics": "Athletics", "Para Swimming": "Swimming", "Para Alpine Ski": "Alpine Ski",
    "Para Cross-Country Ski": "Cross-Country Ski", "Para Snowboard": "Snowboard", "Para Rowing": "Rowing",
    "Para Cycling": "Cycling", "Para Ice Hockey": "Ice Hockey", "Para Triathlon": "Triathlon",
    "Para Sailing": "Sailing", "Para Badminton": "Badminton", "Para Equestrian": "Equestrian",
    "Shooting Para Sport": "Shooting", "Wheelchair Curling": "Curling", "Sitting Volleyball": "Volleyball",
    "Beach Volleyball": "Volleyball", "Trampoline": "Artistic Gymnastics", "Ski Cross": "Alpine Ski",
    "Wakeboard": "Water Ski",
}
grp = lambda s: SPORT_GROUP.get(s, s)
SEX = {"Male": "M", "Female": "F", "Any/Combined": "X"}

x = pd.read_csv(exp_path, dtype=str, keep_default_na=False)
issues = []  # (issue, name, sport, year, detail)


def I(issue, r, detail):
    issues.append((issue, f'{r["first_name"]} {r["last_name"]}', r["sport"], r.get("Year", ""), detail))


a = x[x["role"] == "Athlete"].copy()
coaches = int((x["role"] != "Athlete").sum())
test = a["sport"].str.contains(r"\(TEST\)")
for _, r in a[test].iterrows():
    I("Test record - excluded", r, r["sport"])
a = a[~test].copy()
a["carding"] = a["athlete_carding"].str.strip()
a["Program"] = a["carding"].map(CARDING)
for _, r in a[a["Program"].isna()].iterrows():
    I("Carding level not mapped - excluded", r, r["carding"])
a = a[a["Program"].notna()].copy()
a["Sport"] = a["sport"].replace(SPORT_RENAME)
a["Year"] = a["nomination_fiscal_year"].str[-4:]
a["Full_Name"] = a["first_name"].map(norm) + a["last_name"].map(norm)
a["sg"] = a["Sport"].map(grp)
a["Gender"] = a["sex_of_competition"].map(SEX).fillna("")
a["lvl"] = a["Program"].map(LEVEL)

# --- quality checks inside the export ---
age = pd.to_numeric(a["Year"]) - pd.to_datetime(a["dob"], errors="coerce").dt.year
for _, r in a[(age < 9) | (age > 60)].iterrows():
    I("Implausible age", r, f'DOB {r["dob"]} (carding {r["carding"]})')
for _, r in a[a["carding"] == "SRI"].iterrows():
    I("Carding 'SRI' (probably SR1)", r, "mapped to SC Carded either way")
for _, r in a[a["carding"] == "GamePlan - Retired"].iterrows():
    pass
# same person+sport+year nominated more than once
k = ["Full_Name", "dob", "sg", "Year"]
for key, g in a[a.duplicated(k, keep=False)].groupby(k):
    r = g.iloc[0]
    progs = sorted(set(g["carding"]))
    I("Nominated more than once (same year)", r, f'{len(g)} nominations: {", ".join(progs)}; highest kept')
# same name+sport, different DOB
for key, g in a.groupby(["Full_Name", "sg"]):
    if g["dob"].nunique() > 1:
        I("Same name and sport, different DOB", g.iloc[0], "; ".join(f'{y}: {d}' for y, d in zip(g["Year"], g["dob"])))
# same person, different sex across their nominations
for key, g in a.groupby(["Full_Name", "dob"]):
    s = set(g["Gender"]) - {"X"}
    if len(s) > 1:
        I("Sex of competition differs between nominations", g.iloc[0], "; ".join(f'{y} {sp}: {sx}' for y, sp, sx in zip(g["Year"], g["Sport"], g["sex_of_competition"])))

a = a.sort_values("lvl", ascending=False).drop_duplicates(k)

# --- match against dataset ---
ds = pd.read_csv(ds_path, dtype=str, keep_default_na=False)
ds["sg"] = ds["Sport"].map(grp)
ds["key"] = ds["Full_Name"].str.replace(r"_\d{4}$", "", regex=True)
ds_people = ds.groupby(["Full_Name", "key", "Date of Birth", "sg"]).agg(
    first=("First Name", "first"), last=("Last Name", "first"), gender=("Gender", lambda s: "".join(sorted(set(s)))),
    years=("Year", lambda s: sorted(set(s))), last_prog=("Program", "last")).reset_index()
by_dob_sg = ds_people.groupby(["Date of Birth", "sg"])
idx_dob_sg = {k: v for k, v in by_dob_sg}
idx_name_sg = {k: v for k, v in ds_people.groupby(["key", "sg"])}


def same_dob(d1, d2):
    a_, b_ = pd.Timestamp(d1), pd.Timestamp(d2)
    diffs = (a_.year != b_.year) + (a_.month != b_.month) + (a_.day != b_.day)
    return diffs <= 1 or (a_.year == b_.year and a_.month == b_.day and a_.day == b_.month)


rows = []
for _, r in a.iterrows():
    status, match, detail = "New athlete", "", ""
    exact = ds_people[(ds_people["key"] == r["Full_Name"]) & (ds_people["Date of Birth"] == r["dob"]) & (ds_people["sg"] == r["sg"])]
    if len(exact):
        m = exact.iloc[0]
        status, match = "Matched", m["Full_Name"]
        detail = f'in dataset {m["years"][0]}-{m["years"][-1]}'
    else:
        cand = idx_name_sg.get((r["Full_Name"], r["sg"]))
        typo = cand[cand["Date of Birth"].map(lambda d: bool(d) and same_dob(d, r["dob"]))] if cand is not None else None
        if typo is not None and len(typo):
            m = typo.iloc[0]
            status, match, detail = "Matched (DOB typo)", m["Full_Name"], f'dataset DOB {m["Date of Birth"]}'
        elif cand is not None and (cand["Date of Birth"] == "").any():
            m = cand[cand["Date of Birth"] == ""].iloc[0]
            status, match, detail = "Check - same name+sport, dataset has no DOB", m["Full_Name"], f'years {m["years"]}'
        elif cand is not None:
            status = "Check - same name+sport, different DOB"
            detail = "; ".join(f'{d} ({y[0]}-{y[-1]})' for d, y in zip(cand["Date of Birth"], cand["years"]))
            match = cand.iloc[0]["Full_Name"]
        else:
            same = idx_dob_sg.get((r["dob"], r["sg"]))
            if same is not None:
                same = same.assign(sim=same["key"].map(lambda k: SequenceMatcher(None, k, r["Full_Name"]).ratio()))
                same = same[same["sim"] >= 0.6].sort_values("sim", ascending=False)
                if len(same):
                    m = same.iloc[0]
                    status, match = "Check - same DOB+sport, name spelled differently", m["Full_Name"]
                    detail = f'dataset name {m["first"]} {m["last"]} ({m["years"][0]}-{m["years"][-1]})'
    prev = ds[(ds["Full_Name"] == match) & (ds["sg"] == r["sg"])] if match else ds.iloc[0:0]
    prev_years = prev[pd.to_numeric(prev["Year"]) < int(r["Year"])]
    prev_lvl = prev_years.sort_values("Year")["Program"].map(LEVEL).iloc[-1] if len(prev_years) else None
    in_year = match and (prev["Year"] == r["Year"]).any()
    ds_prog = "; ".join(sorted(set(prev[prev["Year"] == r["Year"]]["Program"]))) if in_year else ""
    rows.append({"Year": r["Year"], "First Name": r["first_name"], "Last Name": r["last_name"], "DOB": r["dob"],
                 "Sport": r["Sport"], "Carding": r["carding"], "Program": r["Program"], "Gender": r["Gender"],
                 "Status": status, "Dataset key": match, "Detail": detail,
                 "Already in dataset for this year": "Yes" if in_year else "No",
                 "Dataset program this year": ds_prog,
                 "Would convert": "Y" if prev_lvl is not None and r["lvl"] > prev_lvl else ""})
res = pd.DataFrame(rows).sort_values(["Year", "Status", "Last Name"])
res.to_csv(f"{out}/nominations_match.csv", index=False)
pd.DataFrame(issues, columns=["Issue", "Name", "Sport", "Year", "Detail"]).to_csv(f"{out}/nominations_issues.csv", index=False)

pd.set_option("display.width", 250, "display.max_colwidth", 90, "display.max_rows", 200)
print("coach rows skipped:", coaches)
print(pd.crosstab(res["Status"], res["Year"], margins=True))
print("\n2026 rows already in dataset:", (res[res.Year == "2026"]["Already in dataset for this year"] == "Yes").sum(), "of", (res.Year == "2026").sum())
r26 = res[(res.Year == "2026") & (res["Already in dataset for this year"] == "Yes")]
print("2026 program disagreements:", (r26["Program"] != r26["Dataset program this year"]).sum())
print(r26[r26["Program"] != r26["Dataset program this year"]][["First Name", "Last Name", "Sport", "Program", "Dataset program this year"]].to_string())
print("\n2027 by program:", res[res.Year == "2027"]["Program"].value_counts().to_dict())
print("2027 would-convert:", (res[(res.Year == "2027")]["Would convert"] == "Y").sum())
print("\nISSUES:", pd.Series([i[0] for i in issues]).value_counts().to_dict())
for i in issues:
    print(" ", i)
c = res[res.Status.str.startswith("Check") | res.Status.str.contains("typo")]
print("\nCHECK / TYPO:\n", c[["Year", "First Name", "Last Name", "DOB", "Sport", "Status", "Dataset key", "Detail"]].to_string())
