"""Append matched/new nominations (from check_nominations.py) to the conversion dataset.

usage: add_nominations.py <export.csv> <nominations_match.csv> <dataset.csv> <out.csv> <added_log.csv>
Held out: every row whose Status starts with "Check". Coaches, test sports and
GamePlan - Retired were already excluded by check_nominations.py.
"""
import re
import sys

import pandas as pd

exp_path, match_path, ds_path, out_path, log_path = sys.argv[1:6]
norm = lambda s: re.sub(r"[^a-z]", "", str(s).lower())

ds = pd.read_csv(ds_path, dtype=str, keep_default_na=False)
m = pd.read_csv(match_path, dtype=str, keep_default_na=False)
x = pd.read_csv(exp_path, dtype=str, keep_default_na=False)
x["Sport"] = x["sport"].replace({"Hockey": "Ice Hockey"})
x["Year"] = x["nomination_fiscal_year"].str[-4:]
x["k"] = x["first_name"].map(norm) + x["last_name"].map(norm)
css_keys = set(zip(x.loc[x["nomination_organization"] == "Canadian Sport School", "k"],
                   x.loc[x["nomination_organization"] == "Canadian Sport School", "Year"]))

add = m[~m["Status"].str.startswith("Check") & (m["Already in dataset for this year"] == "No")].copy()
ds_dob = ds[ds["Date of Birth"] != ""].groupby("Full_Name")["Date of Birth"].first().to_dict()
ds_keys = set(ds["Full_Name"])

rows, log = [], []
for _, r in add.iterrows():
    own = norm(r["First Name"]) + norm(r["Last Name"])
    if r["Dataset key"]:
        key = r["Dataset key"]
        dob = ds_dob.get(key, r["DOB"])
        note = r["Status"] + (f'; export DOB {r["DOB"]} kept as dataset DOB {dob}' if dob != r["DOB"] else "")
    else:
        key, dob = own, r["DOB"]
        if key in ds_keys:
            # name already in the dataset but name+DOB+sport did not match -> different athlete
            key = f"{own}_{dob[:4]}"
            note = "New athlete; name already used in dataset (no DOB+sport match), key suffixed"
        else:
            note = "New athlete"
    rows.append({"Sport": r["Sport"], "First Name": r["First Name"], "Last Name": r["Last Name"],
                 "Gender": r["Gender"], "Date of Birth": dob, "Year": r["Year"], "Program": r["Program"],
                 "Full_Name": key, "CSS": "YES" if (own, r["Year"]) in css_keys else "NO",
                 "Years Targeted": "", "Convert Year": ""})
    log.append((r["Year"], f'{r["First Name"]} {r["Last Name"]}', r["Sport"], r["Program"], key, note))

new = pd.DataFrame(rows)
out = pd.concat([ds, new], ignore_index=True)
out.to_csv(out_path, index=False)
pd.DataFrame(log, columns=["Year", "Name", "Sport", "Program", "Full_Name", "Note"]).to_csv(log_path, index=False)
print("added:", len(new), new["Year"].value_counts().to_dict(), "CSS YES:", (new["CSS"] == "YES").sum())
print("held out:", int(m["Status"].str.startswith("Check").sum()))
print(pd.Series([l[5].split(";")[0] for l in log]).value_counts().to_dict())
