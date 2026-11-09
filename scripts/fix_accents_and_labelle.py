"""Strip accents to root letters, re-key accent-dropped Full_Names, merge Melanie Labelle (9 Nov 2026).

usage: fix_accents_and_labelle.py <dataset.csv> <changelog.csv>   (rewrites dataset.csv in place)

* First/Last Name: accents stripped to the root letter (é -> e); other characters such as ’ are kept.
  "Siã´N" (garbled Siân) -> "Sian".
* Full_Name keys that dropped accented letters (josuluma) become root-letter keys (josueluma), keeping
  any _YYYY suffix. If that key already exists, rows merge only when DOB (or a one-digit/day-month-swap
  typo) and sport group agree (name + DOB + sport rule); otherwise the birth year is used as a suffix.
* meanielabelle -> melanielabelle; "Meanie" -> "Melanie".
* Years Targeted and Convert Year recalculated (same logic as clean_dataset.py step 9).
"""
import re
import sys
import unicodedata

import pandas as pd

sys.path.insert(0, "/Users/lukespagnuolo/Documents/List_Generator")
import conversion_update_workflow as cu  # noqa: E402  (shared sport groups, keys, recompute)

path, log_path = sys.argv[1:3]
df = pd.read_csv(path, dtype=str, keep_default_na=False)
before = df.copy()
log = []


def root_letters(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return unicodedata.normalize("NFC", "".join(ch for ch in decomposed if not unicodedata.combining(ch)))


def L(i, field, old, new, reason):
    r = df.loc[i]
    log.append((r["Full_Name"], f'{r["First Name"]} {r["Last Name"]}', r["Sport"], r["Year"], field, old, new, reason))


# 1. Melanie Labelle split across two keys (same DOB 1985-04-06, Wheelchair Rugby)
for i in df.index[df["Full_Name"] == "meanielabelle"]:
    L(i, "Full_Name", "meanielabelle", "melanielabelle", "same athlete (name typo 'Meanie'); merged manually")
    df.at[i, "Full_Name"] = "melanielabelle"
for i in df.index[(df["First Name"] == "Meanie") & (df["Last Name"] == "Labelle")]:
    L(i, "First Name", "Meanie", "Melanie", "name typo")
    df.at[i, "First Name"] = "Melanie"

# 2. re-key accent-dropped keys, deciding per key (a key can hold accented and plain spellings)
legacy = df["First Name"].map(cu.legacy_norm) + df["Last Name"].map(cu.legacy_norm)
root = df["First Name"].map(cu.norm) + df["Last Name"].map(cu.norm)
base = df["Full_Name"].map(cu.base_key)
accent_dropped = (base == legacy) & (legacy != root)
targets = {key: root[rows.index[0]] for key, rows in df[accent_dropped].groupby("Full_Name")}
targets["singriffiths"] = "siangriffiths"  # garbled "Siã´N" (Siân)
group = df["Sport"].map(cu.sport_group)
for key, new_base in sorted(targets.items()):
    rows = df[df["Full_Name"] == key]
    suffix = key[len(cu.base_key(key)):]
    target = new_base + suffix
    existing = df[df["Full_Name"] == target]
    if len(existing):
        dobs_a = {d for d in rows["Date of Birth"] if d}
        dobs_b = {d for d in existing["Date of Birth"] if d}
        dob_ok = bool(dobs_a and dobs_b) and any(cu.same_dob(a, b) for a in dobs_a for b in dobs_b)
        sport_ok = bool(set(group[rows.index]) & set(group[existing.index]))
        if dob_ok and sport_ok:
            reason = f"accent-dropped key; same athlete as {target} (DOB {sorted(dobs_a)} vs {sorted(dobs_b)}, same sport)"
        else:
            birth = sorted(dobs_a)[0][:4] if dobs_a else "new"
            target = f"{new_base}_{birth}"
            reason = f"accent-dropped key; {new_base} is a different athlete (DOB/sport differ)"
    else:
        reason = "accent-dropped key -> root letters"
    for i in rows.index:
        L(i, "Full_Name", key, target, reason)
        df.at[i, "Full_Name"] = target

# 3. garbled name
for i in df.index[df["First Name"] == "Siã´N"]:
    L(i, "First Name", "Siã´N", "Sian", "garbled Siân; accent stripped")
    df.at[i, "First Name"] = "Sian"

# 4. strip accents from names
for column in ("First Name", "Last Name"):
    for i in df.index[~df[column].map(str.isascii)]:
        new = root_letters(df.at[i, column])
        if new != df.at[i, column]:
            L(i, column, df.at[i, column], new, "accent stripped to root letter")
            df.at[i, column] = new

# 5. merged athletes: one DOB (the newest year's), recompute targets
for key in {entry[6] for entry in log if entry[4] == "Full_Name"}:
    rows = df[df["Full_Name"] == key]
    dobs = rows[rows["Date of Birth"] != ""].sort_values("Year")["Date of Birth"]
    if dobs.nunique() > 1:
        newest = dobs.iloc[-1]
        for i in rows.index[rows["Date of Birth"] != newest]:
            L(i, "Date of Birth", df.at[i, "Date of Birth"], newest, "merged athlete; newest nomination DOB")
            df.at[i, "Date of Birth"] = newest

df = cu.recompute_targets(df)
for i in df.index:
    for column in ("Years Targeted", "Convert Year"):
        if df.at[i, column] != before.at[i, column]:
            L(i, column, before.at[i, column], df.at[i, column], "recalculated after merge")

df["_y"] = pd.to_numeric(df["Year"], errors="coerce")
df = df.sort_values(["Full_Name", "Sport", "_y"], kind="stable").drop(columns="_y")
df.to_csv(path, index=False)
out = pd.DataFrame(log, columns=["Full_Name", "Name", "Sport", "Year", "Field", "Old", "New", "Reason"])
out.to_csv(log_path, index=False)
print(out["Field"].value_counts().to_dict())
print(out[out["Reason"].str.contains("same athlete|different athlete|merged|recalculated")].to_string())
