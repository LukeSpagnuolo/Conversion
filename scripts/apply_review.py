"""Apply Luke's decisions from the '2027 Nominations - Athletes to Check' doc (6 Nov 2026).

usage: apply_review.py <export.csv> <nominations_match.csv> <dataset.csv> <out.csv> <log.csv>
"""
import re
import sys

import pandas as pd

exp_path, match_path, ds_path, out_path, log_path = sys.argv[1:6]
norm = lambda s: re.sub(r"[^a-z]", "", str(s).lower())
ds = pd.read_csv(ds_path, dtype=str, keep_default_na=False)
m = pd.read_csv(match_path, dtype=str, keep_default_na=False)
x = pd.read_csv(exp_path, dtype=str, keep_default_na=False)
x["k"] = x["first_name"].map(norm) + x["last_name"].map(norm)
x["Year"] = x["nomination_fiscal_year"].str[-4:]
css = set(zip(x.loc[x["nomination_organization"] == "Canadian Sport School", "k"],
              x.loc[x["nomination_organization"] == "Canadian Sport School", "Year"]))
held = m[m["Status"].str.startswith("Check")].copy()
log, new_rows = [], []


def add_row(r, key, dob):
    own = norm(r["First Name"]) + norm(r["Last Name"])
    if ((ds["Full_Name"] == key) & (ds["Sport"] == r["Sport"]) & (ds["Year"] == r["Year"])).any():
        return "already in dataset for this year"
    new_rows.append({"Sport": r["Sport"], "First Name": r["First Name"], "Last Name": r["Last Name"],
                     "Gender": r["Gender"], "Date of Birth": dob, "Year": r["Year"], "Program": r["Program"],
                     "Full_Name": key, "CSS": "YES" if (own, r["Year"]) in css else "NO",
                     "Years Targeted": "", "Convert Year": ""})
    return f"added {r['Year']} {r['Program']}"


for _, r in held.iterrows():
    name, key = f'{r["First Name"]} {r["Last Name"]}', r["Dataset key"]
    if "name spelled" in r["Status"]:
        if name == "Devon Simonovic":  # decision: different person
            own = "devonsimonovic"
            k = own if own not in set(ds["Full_Name"]) else f"{own}_{r['DOB'][:4]}"
            log.append((name, r["Sport"], "Different person", add_row(r, k, r["DOB"]), k))
        else:  # decision: same person
            dob = ds.loc[ds["Full_Name"] == key, "Date of Birth"].replace("", pd.NA).dropna()
            log.append((name, r["Sport"], "Same person", add_row(r, key, dob.iloc[0] if len(dob) else r["DOB"]), key))
    elif "different DOB" in r["Status"]:  # decision: fix DOB to nomination
        rows = ds["Full_Name"] == key
        old = sorted(set(ds.loc[rows, "Date of Birth"]))
        ds.loc[rows, "Date of Birth"] = r["DOB"]
        log.append((name, r["Sport"], "Fix DOB to nomination",
                    f'DOB {old} -> {r["DOB"]} on {int(rows.sum())} rows; ' + add_row(r, key, r["DOB"]), key))
    elif "no DOB" in r["Status"]:  # decision: add DOB
        rows = ds["Full_Name"] == key
        ds.loc[rows, "Date of Birth"] = r["DOB"]
        log.append((name, r["Sport"], "Add DOB", f'DOB set on {int(rows.sum())} rows; ' + add_row(r, key, r["DOB"]), key))

# comment: "change this to 2002" -> Elliot Eade DOB 2020-06-11 -> 2002-06-11
rows = (ds["Full_Name"] == "ellioteade") & (ds["Date of Birth"] == "2020-06-11")
ds.loc[rows, "Date of Birth"] = "2002-06-11"
log.append(("Elliot Eade", "Volleyball", "Comment: change to 2002", f"DOB 2020-06-11 -> 2002-06-11 on {int(rows.sum())} rows", "ellioteade"))

out = pd.concat([ds, pd.DataFrame(new_rows)], ignore_index=True)
out.to_csv(out_path, index=False)
lg = pd.DataFrame(log, columns=["Name", "Sport", "Decision", "Result", "Full_Name"])
lg.to_csv(log_path, index=False)
pd.set_option("display.width", 220, "display.max_colwidth", 90)
print(lg.to_string())
print("rows added:", len(new_rows))
