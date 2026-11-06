"""Clean Conversion_Data_2026_final.csv.

usage: clean_dataset.py <in.csv> <out.csv> <changelog.csv> <review.csv>
"""
import re
import sys
from collections import Counter
from difflib import SequenceMatcher

import pandas as pd

src, out, log_path, review_path, RAW_PATH, NOM_RAW_PATH, decisions_path = sys.argv[1:8]
decisions = []
df = pd.read_csv(src, dtype=str, keep_default_na=False)
orig_rows = len(df)
log = []      # (step, full_name, sport, year, field, old, new, reason)
review = []   # (issue, full_name, first, last, sport, year, detail)
stats = Counter()

LEVEL = {"Prov Dev 3": 1, "Prov Dev 2": 2, "Prov Dev 1": 3, "Uncarded": 4, "SC Carded": 5}

# Sport equivalence (agreed 2026-11-06). Labels stay as recorded; these sports are
# treated as one sport for matching, Years Targeted and Convert Year.
# Kept separate on purpose: Wheelchair Basketball, Wheelchair Rugby, Wheelchair Tennis,
# Wheelchair Athletics, Biathlon vs Cross-Country Ski.
SPORT_GROUP = {
    "Para Athletics": "Athletics",
    "Para Swimming": "Swimming",
    "Para Alpine Ski": "Alpine Ski",
    "Para Cross-Country Ski": "Cross-Country Ski",
    "Para Snowboard": "Snowboard",
    "Para Rowing": "Rowing",
    "Para Cycling": "Cycling",
    "Para Ice Hockey": "Ice Hockey",
    "Para Triathlon": "Triathlon",
    "Para Sailing": "Sailing",
    "Para Badminton": "Badminton",
    "Para Equestrian": "Equestrian",
    "Shooting Para Sport": "Shooting",
    "Wheelchair Curling": "Curling",
    "Sitting Volleyball": "Volleyball",
    "Beach Volleyball": "Volleyball",
    "Trampoline": "Artistic Gymnastics",
    "Ski Cross": "Alpine Ski",
    "Wakeboard": "Water Ski",
}
group = lambda s: SPORT_GROUP.get(s, s)
norm = lambda s: re.sub(r"[^a-z]", "", str(s).lower())


def L(step, r, field, old, new, reason):
    log.append((step, r["Full_Name"], r["Sport"], r["Year"], f'{r["First Name"]} {r["Last Name"]}', field, old, new, reason))


# 1. exact duplicates -------------------------------------------------------
dup = df.duplicated()
for _, r in df[dup].iterrows():
    L("1 exact duplicate", r, "row", "", "removed", "identical row")
stats["exact_duplicates_removed"] = int(dup.sum())
df = df[~dup].reset_index(drop=True)

# 2. malformed DOB (YYYY-DD-MM) ---------------------------------------------
for i, v in df["Date of Birth"].items():
    if not v:
        continue
    if pd.isna(pd.to_datetime(v, errors="coerce", format="%Y-%m-%d")):
        m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", v)
        fixed = f"{m[1]}-{m[3]}-{m[2]}" if m else ""
        if fixed and pd.notna(pd.to_datetime(fixed, errors="coerce", format="%Y-%m-%d")):
            L("2 malformed DOB", df.loc[i], "Date of Birth", v, fixed, "day/month swapped (invalid month)")
            df.at[i, "Date of Birth"] = fixed
            stats["dob_format_fixed"] += 1
        else:
            L("2 malformed DOB", df.loc[i], "Date of Birth", v, "", "unparseable")
            df.at[i, "Date of Birth"] = ""
            stats["dob_unparseable_cleared"] += 1

# 3. impossible DOB (born after / <4 yrs before the record year) ---------------
dob = pd.to_datetime(df["Date of Birth"], errors="coerce")
bad = dob.notna() & (dob.dt.year > pd.to_numeric(df["Year"]) - 4)
for i in df[bad].index:
    L("3 impossible DOB", df.loc[i], "Date of Birth", df.at[i, "Date of Birth"], "", "athlete would be under 4 in record year")
    df.at[i, "Date of Birth"] = ""
stats["impossible_dob_cleared"] = int(bad.sum())


def ts(v):
    return pd.Timestamp(v)


def same_dob(a, b):
    """Same person if the DOBs differ in only one of year/month/day (a typo),
    or day and month are swapped, or (for identical names) the birth year matches."""
    a, b = ts(a), ts(b)
    diffs = (a.year != b.year) + (a.month != b.month) + (a.day != b.day)
    swap = a.year == b.year and a.month == b.day and a.day == b.month
    return diffs <= 1 or swap


def same_year(a, b):
    return ts(a).year == ts(b).year


def gset(rows):
    return set(rows["Gender"]) & {"F", "M"}


# 4. undo wrong name merges ---------------------------------------------------
# The April consolidation copied the target athlete's DOB onto merged rows, so
# original DOBs come from the pre-merge raw files instead.
def parse_any(v):
    v = str(v).strip()
    if not v:
        return ""
    t = pd.to_datetime(v, errors="coerce", format="%Y-%m-%d")
    if pd.isna(t):
        t = pd.to_datetime(v, errors="coerce", dayfirst=True)
    return "" if pd.isna(t) else t.strftime("%Y-%m-%d")


raw_dob = {}
raw = pd.read_csv(RAW_PATH, dtype=str, keep_default_na=False)
for fn, ln, y, d in zip(raw["First Name"], raw["Last Name"], raw["Year"], raw["Date of Birth"]):
    d = parse_any(d)
    if d:
        raw_dob.setdefault((norm(fn) + norm(ln), y), set()).add(d)
# NOM_RAW_PATH: one or more raw nomination exports, separated by "|"
for nom_path in NOM_RAW_PATH.split("|"):
    nom = pd.read_csv(nom_path, dtype=str, keep_default_na=False)
    years = nom["nomination_fiscal_year"].str[-4:] if "nomination_fiscal_year" in nom else ["2026"] * len(nom)
    for fn, ln, d, y in zip(nom["first_name"], nom["last_name"], nom["dob"], years):
        d = parse_any(d)
        if d:
            raw_dob.setdefault((norm(fn) + norm(ln), y), set()).add(d)

df["_own"] = df["First Name"].map(norm) + df["Last Name"].map(norm)
df["_fn"], df["_ln"] = df["First Name"].map(norm), df["Last Name"].map(norm)
sim = lambda a, b: SequenceMatcher(None, a, b).ratio()
for key, grp in df[df["_own"] != df["Full_Name"]].groupby("Full_Name"):
    members = df[df["Full_Name"] == key]
    anchors = members[members["_own"] == key]
    if anchors.empty:
        top = Counter(members["_own"]).most_common(1)[0][0]
        anchors = members[members["_own"] == top]
    a_fn, a_ln = anchors["_fn"].iloc[0], anchors["_ln"].iloc[0]
    da = {x for x in anchors["Date of Birth"] if x}
    for own, v in members[members["_own"] != key].groupby("_own"):
        if own == anchors["_own"].iloc[0]:
            continue
        dv = set().union(*[raw_dob.get((own, y), set()) for y in v["Year"]])
        fs, ls_ = sim(v["_fn"].iloc[0], a_fn), sim(v["_ln"].iloc[0], a_ln)
        gender_conflict = bool(gset(v)) and bool(gset(anchors)) and not (gset(v) & gset(anchors))
        if gender_conflict and fs < 0.75:
            same, why = False, f"different first name and gender ({sorted(gset(v))} vs {sorted(gset(anchors))}) - likely siblings"
        elif dv and da:
            # Rule: match on name + DOB + sport
            dob_ok = any(same_dob(a, b) for a in dv for b in da)
            sport_ok = bool(set(map(group, v["Sport"])) & set(map(group, anchors["Sport"])))
            same = dob_ok and sport_ok
            why = (f"original DOB {'matches' if dob_ok else 'differs'} ({sorted(dv)} vs {sorted(da)}); "
                   f"sport {'matches' if sport_ok else 'differs'}")
        elif gender_conflict:
            same, why = False, f"gender differs ({sorted(gset(v))} vs {sorted(gset(anchors))}), no original DOB"
        else:
            same = False
            why = f"no original DOB, so name + DOB + sport can't be confirmed (name sim {fs:.2f}/{ls_:.2f})"
            review.append(("Kept separate - no DOB to confirm match", own, v["First Name"].iloc[0], v["Last Name"].iloc[0],
                           "; ".join(sorted(set(v["Sport"]))), "; ".join(sorted(set(v["Year"]))),
                           f'possible match: {anchors["First Name"].iloc[0]} {anchors["Last Name"].iloc[0]} ({key})'))
        if not same and dv and da and "DOB matches" in why:
            review.append(("Kept separate - same DOB, different sport", own, v["First Name"].iloc[0], v["Last Name"].iloc[0],
                           "; ".join(sorted(set(v["Sport"]))), "; ".join(sorted(set(v["Year"]))),
                           f'possible match: {anchors["First Name"].iloc[0]} {anchors["Last Name"].iloc[0]} ({key}) in {"; ".join(sorted(set(anchors["Sport"])))}'))
        if same and (fs < 0.75 or ls_ < 0.75):
            review.append(("Name variant kept merged - check", key, v["First Name"].iloc[0], v["Last Name"].iloc[0],
                           "; ".join(sorted(set(v["Sport"]))), "; ".join(sorted(set(v["Year"]))),
                           f'merged with {anchors["First Name"].iloc[0]} {anchors["Last Name"].iloc[0]}: {why}'))
        decisions.append((key, own, f'{v["First Name"].iloc[0]} {v["Last Name"].iloc[0]}',
                          f'{anchors["First Name"].iloc[0]} {anchors["Last Name"].iloc[0]}',
                          "; ".join(sorted(set(v["Sport"]))), "; ".join(sorted(set(anchors["Sport"]))),
                          len(v), "kept merged" if same else "SPLIT", why))
        if same:
            stats["name_variants_kept_merged"] += 1
            continue
        stats["name_merges_undone_people"] += 1
        new_dob = sorted(dv)[0] if len(dv) == 1 else ""
        for i in v.index:
            L("4 wrong name merge", df.loc[i], "Full_Name", key, own, why)
            df.at[i, "Full_Name"] = own
            if df.at[i, "Date of Birth"] != new_dob:
                L("4 wrong name merge", df.loc[i], "Date of Birth", df.at[i, "Date of Birth"], new_dob,
                  "DOB had been copied from the other athlete; restored from raw data" if new_dob else "DOB had been copied from the other athlete; no original available")
                df.at[i, "Date of Birth"] = new_dob
            stats["name_merges_undone_rows"] += 1
df = df.drop(columns=["_fn", "_ln"])

# 5. split different people sharing one Full_Name (DOB clusters) --------------
for key, grp in df.groupby("Full_Name"):
    dobs = sorted({x for x in grp["Date of Birth"] if x})
    if len(dobs) < 2:
        continue
    clusters = []
    for d in dobs:
        for c in clusters:
            if any(same_dob(d, e) or same_year(d, e) for e in c):
                c.append(d)
                break
        else:
            clusters.append([d])
    if len(clusters) == 1:
        continue
    # cluster with the most recent record keeps the plain key
    def latest(c):
        return pd.to_numeric(grp[grp["Date of Birth"].isin(c)]["Year"]).max()
    clusters.sort(key=latest, reverse=True)
    stats["shared_names_split"] += 1
    for c in clusters[1:]:
        new_key = f"{key}_{ts(c[0]).year}"
        for i in grp[grp["Date of Birth"].isin(c)].index:
            L("5 different people, same name", df.loc[i], "Full_Name", key, new_key,
              f"DOB {df.at[i, 'Date of Birth']} vs {clusters[0]}")
            df.at[i, "Full_Name"] = new_key
            stats["shared_name_rows_moved"] += 1
    blanks = grp[grp["Date of Birth"] == ""]
    for i, r in blanks.iterrows():
        review.append(("Blank DOB in split name (left with main person)", key, r["First Name"], r["Last Name"], r["Sport"], r["Year"],
                       f"could belong to any of {[c[0] for c in clusters]}"))

# 6. harmonise DOB typos within one person -------------------------------------
for key, grp in df.groupby("Full_Name"):
    dobs = [x for x in grp["Date of Birth"] if x]
    if len(set(dobs)) < 2:
        continue
    cnt = Counter(dobs)
    latest_dob = grp[grp["Date of Birth"] != ""].sort_values("Year")["Date of Birth"].iloc[-1]
    best = max(cnt, key=lambda d: (cnt[d], d == latest_dob))
    stats["dob_harmonised_people"] += 1
    for i in grp[(grp["Date of Birth"] != "") & (grp["Date of Birth"] != best)].index:
        L("6 DOB typo harmonised", df.loc[i], "Date of Birth", df.at[i, "Date of Birth"], best, f"most common DOB for this athlete {dict(cnt)}")
        df.at[i, "Date of Birth"] = best
        stats["dob_harmonised_rows"] += 1

# 7. fill blank DOB / gender from same athlete --------------------------------
for key, grp in df.groupby("Full_Name"):
    d = {x for x in grp["Date of Birth"] if x}
    if len(d) == 1:
        birth_year = int(next(iter(d))[:4])
        # never fill a DOB that would make the row impossible (see step 3)
        for i in grp[(grp["Date of Birth"] == "") & (pd.to_numeric(grp["Year"]) - birth_year >= 4)].index:
            L("7 filled from same athlete", df.loc[i], "Date of Birth", "", next(iter(d)), "athlete's other rows")
            df.at[i, "Date of Birth"] = next(iter(d))
            stats["dob_filled"] += 1
    g = gset(grp)
    if len(g) == 1:
        for i in grp[grp["Gender"] == ""].index:
            L("7 filled from same athlete", df.loc[i], "Gender", "", next(iter(g)), "athlete's other rows")
            df.at[i, "Gender"] = next(iter(g))
            stats["gender_filled"] += 1

# 8. one program per athlete/sport/year (keep highest) -------------------------
df["_lvl"] = df["Program"].map(LEVEL).fillna(0)
df = df.sort_values("_lvl", ascending=False)
k = ["Full_Name", "Sport", "Year"]
drop = df.duplicated(k)
for i, r in df[drop].iterrows():
    keep = df[(df["Full_Name"] == r["Full_Name"]) & (df["Sport"] == r["Sport"]) & (df["Year"] == r["Year"])]["Program"].iloc[0]
    L("8 duplicate athlete-sport-year", r, "row", r["Program"], f"removed (kept {keep})", "one record per athlete/sport/year; highest level kept")
    stats["multi_program_rows_removed"] += 1
df = df[~drop]

# 8b. Field Hockey rows that are copies of Fencing rows (agreed 2026-11-06) -----
# 2008-2019 source data duplicated fencers into Field Hockey with identical
# athlete/year/program. Remove the copies; 2010 Field Hockey is left empty.
fe_keys = set(zip(df.loc[df["Sport"] == "Fencing", "Full_Name"], df.loc[df["Sport"] == "Fencing", "Year"],
                  df.loc[df["Sport"] == "Fencing", "Program"]))
fh_copy = (df["Sport"] == "Field Hockey") & pd.Series(
    [k in fe_keys for k in zip(df["Full_Name"], df["Year"], df["Program"])], index=df.index)
for i, r in df[fh_copy].iterrows():
    L("8b Field Hockey copy of Fencing", r, "row", "Field Hockey", "removed", "identical Fencing row for same athlete/year/program")
stats["field_hockey_copies_removed"] = int(fh_copy.sum())
df = df[~fh_copy]

# 9. recompute Years Targeted + Convert Year (repo logic) ----------------------
df["_y"] = pd.to_numeric(df["Year"])
df["_sg"] = df["Sport"].map(group)
df["Years Targeted"] = df.groupby(["Full_Name", "_sg"])["_y"].transform("nunique").astype(str)
lvl = df.groupby(["Full_Name", "_sg", "_y"])["_lvl"].max()
conv = {}
for name, sub in lvl.groupby(level=0):
    s = sub.droplevel(0)
    sports = s.index.get_level_values(0).unique()
    ms = [x for x in sports if x.strip().lower() == "multisport"]
    for sp in sports:
        own = s.loc[sp]
        wild = {}
        if sp not in ms:
            for m in ms:
                for y, v in s.loc[m].items():
                    wild[y] = max(wild.get(y, 0), v)
        years = sorted(set(own.index) | set(wild))
        for a, b in zip(years, years[1:]):
            if b not in own.index:
                continue
            prev = [v for v in [own.get(a), wild.get(a)] if v is not None]
            if prev and own[b] > max(prev):
                conv[(name, sp, b)] = "Y"
new_conv = [conv.get(t, "N") for t in zip(df["Full_Name"], df["_sg"], df["_y"])]
stats["convert_year_changed"] = int((pd.Series(new_conv, index=df.index) != df["Convert Year"]).sum())
stats["convert_Y_before"] = int((df["Convert Year"] == "Y").sum())
df["Convert Year"] = new_conv
stats["convert_Y_after"] = int((df["Convert Year"] == "Y").sum())

# 10. flags for human review (not changed) ------------------------------------
for _, r in df[df["Program"] == ""].iterrows():
    review.append(("Blank Program", r["Full_Name"], r["First Name"], r["Last Name"], r["Sport"], r["Year"], "no program recorded"))
age = df["_y"] - pd.to_datetime(df["Date of Birth"], errors="coerce").dt.year
for _, r in df[age > 45].iterrows():
    review.append(("Age over 45", r["Full_Name"], r["First Name"], r["Last Name"], r["Sport"], r["Year"], f"DOB {r['Date of Birth']}"))
for key, grp in df.groupby("Full_Name"):
    if gset(grp) == {"F", "M"}:
        review.append(("Both F and M recorded", key, grp["First Name"].iloc[0], grp["Last Name"].iloc[0], "; ".join(sorted(set(grp["Sport"]))), "",
                       "; ".join(f"{y}:{g}" for y, g in zip(grp["Year"], grp["Gender"]))))

df = df.sort_values(["Full_Name", "Sport", "_y"]).drop(columns=["_own", "_lvl", "_y", "_sg"])
df.to_csv(out, index=False)
pd.DataFrame(log, columns=["Step", "Full_Name", "Sport", "Year", "Name", "Field", "Old", "New", "Reason"]).to_csv(log_path, index=False)
pd.DataFrame(review, columns=["Issue", "Full_Name", "First Name", "Last Name", "Sport", "Year", "Detail"]).to_csv(review_path, index=False)
pd.DataFrame(decisions, columns=["Merged key", "Own key", "Merged name", "Kept as", "Merged sports", "Main sports", "Rows", "Decision", "Evidence"]).to_csv(decisions_path, index=False)
stats["rows_before"], stats["rows_after"] = orig_rows, len(df)
stats["review_items"] = len(review)
for k_, v in stats.items():
    print(f"{k_}: {v}")
print("review by issue:", Counter(x[0] for x in review))
