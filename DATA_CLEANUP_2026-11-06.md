# Conversion dataset cleanup — 6 Nov 2026

**File:** `Conversion_Data_2026_final.csv` (LukeSpagnuolo/Conversion, from commit `e50aafd`)
**Status:** cleaned in a local clone, not committed or pushed.

**Matching rule:** an athlete is the same person only when **name + date of birth + sport** all agree. Multi-sport athletes (587) are one person across their sports, and conversions are counted per sport.

## Headline numbers

| | Before | After |
|---|---|---|
| Rows | 45,441 | 45,247 |
| Unique athletes (Full_Name) | 16,898 | 17,022 |
| Conversions (Convert Year = Y) | 4,890 | 4,868 |
| 2026 conversions | 510 | 499 |
| Rows missing DOB | 3,213 | 3,093 |
| Rows missing gender | 457 | 431 |
| Names with conflicting DOBs | 298 | 0 |
| Duplicate / double-program rows | 29 | 0 |
| Field Hockey rows copied from Fencing | 159 | 0 |

## What was cleaned

1. **Exact duplicate rows removed: 12.** All were in 2026.
2. **Malformed dates of birth fixed: 3.** These were written YYYY-DD-MM, e.g. `2009-23-11` became `2009-11-23`.
3. **Impossible dates of birth cleared: 16.** These would make the athlete under 4 in the record year, e.g. a 2028 birth date.
4. **Wrong name merges undone: 85 athletes (135 rows).**
   The April name consolidation merged different people whose names looked alike, and copied one person's date of birth onto everyone in the group. Each merge was re-checked against the original pre-merge date of birth in `scripts/data/Conversion_Data_2026.csv` and the raw 2026 nominations. Examples:
   - Matthew Ly, Yu, Flynn and Debly had all been filed under Matthew Kelly. All four have different original dates of birth.
   - Julia Ross (field hockey and alpine ski) had been filed under Julia Grosso (soccer).
   - Christopher Lee had been filed under Christopher Lum, and Andrew Crow and Andrew Cooper under Andrew Coe.
   - Sibling pairs (different first name and gender) had been merged: Keara/Adam Klimchuk-Brown, Maia/Kai Lawrence, Sam/Sadie Taylor-Parks.
   Split-off rows got their own original date of birth back.
   - 142 genuine spelling variants **stayed merged**: date of birth and sport both agree, e.g. Logan Leach/Leech and Oliva/Olivia Boulding.
   - 19 name variants with no original date of birth were **kept separate**, because the rule can't be confirmed (e.g. Fynn Farfard/Fafard). They're listed for review.
   - 2 with the same date of birth but a different sport were kept separate (Cody Fournie/Fournier, Peggy Assinck/Assinick). They're listed for review.
5. **Different people sharing one name separated: 63 names (231 rows).** Where the same name had dates of birth in different birth years, the person with the most recent record keeps the plain key. Others get a birth-year suffix, e.g. `aaliyahdesousa_2005`.
6. **Date-of-birth typos made consistent: 233 athletes (237 rows).** For one person whose dates differed by a single digit, a swapped day/month, or a day within the same year, the most common date was used.
7. **Blanks filled from the same athlete's other rows:** 146 dates of birth and 22 genders.
8. **One record per athlete/sport/year: 23 rows removed.** Where an athlete was listed under two programs in the same year (all in 2026), the higher program was kept, which matches how the conversion logic already scores it.
9. **Years Targeted and Convert Year recalculated** with the repo's own rules (`scripts/recalculate_years_and_convert.py` logic). 57 Convert Year flags changed in total, including the sport-group effect below, mostly false 2026 conversions caused by wrong merges and double-program rows.

## Sport groups (agreed 6 Nov 2026)

Sport names are kept as recorded, but these count as the **same sport** for matching, Years Targeted and Convert Year:

- **Para versions → main sport:** Athletics, Swimming, Alpine Ski, Cross-Country Ski, Snowboard, Rowing, Cycling, Ice Hockey, Triathlon, Sailing, Badminton, Equestrian, Shooting. Also Wheelchair Curling → Curling and Sitting Volleyball → Volleyball. Para names only appear from 2026; before that, para athletes were filed under the main sport, so without the merge their history broke in 2026.
- **Disciplines:** Beach Volleyball → Volleyball, Trampoline → Artistic Gymnastics, Ski Cross → Alpine Ski, Wakeboard → Water Ski.
- **Kept separate:** Wheelchair Basketball, Wheelchair Rugby, Wheelchair Tennis, Wheelchair Athletics, and Biathlon vs Cross-Country Ski.

## Field Hockey rows copied from Fencing: removed

Of the Field Hockey rows belonging to 70 fencers, 159 (all 2008–2019) were exact copies of their Fencing rows: same athlete, year and program. The copies were already in the raw source data, and they have been removed. Fencing is unchanged.

- Field Hockey goes from 2,241 to 2,082 rows, from 554 to 485 athletes, and from 283 to 260 conversions.
- **2010 Field Hockey is now empty.** All 13 rows that year were fencer copies, so the real 2010 Field Hockey list appears to be missing from the source. Add it if the original 2010 nomination file can be found.
- Fynn Fafard's single 2019 Field Hockey row has no Fencing twin, so it was kept. It is on the review list.
- Details are in `fencing_field_hockey_review.csv`, and every removed row is in `changelog.csv` (step 8b).

## Left as is (needs a human)

`review.csv` lists 412 items. Nothing in it was changed.

| Issue | Count |
|---|---|
| Age over 45 in the record year (some may be real, e.g. masters/para athletes or coaches) | 323 |
| Both F and M recorded for the same athlete | 49 |
| Name variant kept merged, but first or last name differs a lot (nicknames, possible twins such as Kieran/Evan Hamilton or Olin/Finn Dahlstrom) | 16 |
| Kept separate: no date of birth to confirm a name match | 19 |
| Kept separate: same date of birth, different sport | 2 |
| Blank date of birth on a name that was split (assigned to the main person) | 2 |
| Blank Program (Rebecca Marino, Tennis 2025) | 1 |

**Not treated as errors:**
- **Gender "X":** this is sex of competition, mainly rugby and athletics in 2023–24, not a data problem.
- **CSS changing year to year:** this is expected.

## Notes for the next nominations update

- `2026_Nominated_athletes_formatted.csv` is stale. Every row says "SC Carded", and it uses "Hockey" where the dataset uses "Ice Hockey". The 2026 nominations are already in the main dataset with the correct levels.
- New data must be matched on **name + date of birth + sport**. Name similarity alone caused the bad merges.
- The dashboard rebuilds its own `First Last` name, so the `_YYYY` suffixes don't show in the app. They only affect the Years Targeted and Convert Year calculations.

## Files

- `cleaned.csv`: the cleaned dataset, also copied into the clone as `Conversion_Data_2026_final.csv`
- `changelog.csv`: every individual change, with old value, new value and reason
- `name_merge_decisions.csv`: each of the 227 name-merge decisions and the evidence for it
- `review.csv`: items for a human to check
- `clean_dataset.py`: the script that does all of the above and can be re-run
