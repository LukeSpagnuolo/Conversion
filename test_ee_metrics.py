"""Tests for ee_metrics (run: python -m unittest test_ee_metrics)."""
import unittest

import pandas as pd

import ee_metrics as m


def row(name, sport, year, program, convert="N", years_targeted=1):
    return {"Full_Name": name, "Sport": sport, "Year": year, "Program": program,
            "Convert Year": convert, "Years Targeted": years_targeted}


class EEMetricsTests(unittest.TestCase):
    def test_defaults_and_groups_follow_list_generator(self):
        sports = ["Alpine Ski", "Para Alpine Ski", "Wheelchair Rugby", "Wheelchair Tennis",
                  "Wheelchair Athletics", "Wheelchair Basketball", "Soccer", "Artistic Swimming"]
        chosen = m.default_ee_sports(sports)
        self.assertNotIn("Soccer", chosen)
        self.assertIn("Para Alpine Ski", chosen)
        groups = dict(m.ee_sport_groups(sports, chosen))
        self.assertEqual(groups["Alpine Ski"], ["Alpine Ski", "Para Alpine Ski"])
        self.assertEqual(groups["Wheelchair sports"], ["Wheelchair Athletics", "Wheelchair Rugby", "Wheelchair Tennis"])
        self.assertEqual(groups["Wheelchair Basketball"], ["Wheelchair Basketball"])
        self.assertEqual(len(groups), 4)

    def test_conversions_are_measured_against_last_years_pool(self):
        df = pd.DataFrame([
            # 2022 (pool year only): a, b Prov Dev; d Can Dev (Uncarded)
            row("a", "Rowing", 2022, "Prov Dev 2"), row("b", "Rowing", 2022, "Prov Dev 1"),
            row("d", "Rowing", 2022, "Uncarded"),
            # 2023: b Prov Dev -> Uncarded (any + Prov→Nat); d Uncarded -> SC Carded (any only);
            # e is flagged but has no 2022 row, so isn't counted
            row("a", "Rowing", 2023, "Prov Dev 2"), row("b", "Rowing", 2023, "Uncarded", "Y"),
            row("d", "Rowing", 2023, "SC Carded", "Y"), row("e", "Rowing", 2023, "Prov Dev 1", "Y"),
            # 2024: a Prov Dev -> SC Carded (any + Prov→Nat); Para Rowing counts with Rowing
            row("a", "Rowing", 2024, "SC Carded", "Y"), row("b", "Para Rowing", 2024, "Uncarded"),
            row("b", "Rowing", 2025, "Uncarded"), row("f", "Rowing", 2025, "Prov Dev 1", years_targeted=3),
            row("f", "Rowing", 2026, "Prov Dev 1", years_targeted=4),
            row("c", "Rowing", 2019, "Prov Dev 1", "Y"),  # outside the window
        ])
        result = m.build_ee_metrics(df, ["Rowing", "Para Rowing"]).iloc[0]
        self.assertEqual(result[m.COL_SPORT], "Rowing")
        self.assertEqual(result[m.COL_YEAR], 2026)
        self.assertEqual(result[m.COL_WINDOW], "2023–2026")
        self.assertEqual(result[m.COL_ATHLETES], 1)
        # Pools 2022–2025: any-level 3 + 3 + 1 + 2 = 9 athlete-years; Prov Dev 2 + 2 + 0 + 1 = 5.
        self.assertEqual((result[m.COL_ABS_ANY], result[m.COL_ABS_NATIONAL]), (3, 2))
        self.assertEqual((result[m.COL_AVG_ANY_POOL], result[m.COL_AVG_PROV_POOL]), (2.25, 1.25))
        self.assertEqual(result[m.COL_ANY], round(3 / 9 * 100, 1))
        self.assertEqual(result[m.COL_NATIONAL], 40.0)
        self.assertEqual(result[m.COL_YEARS_TARGETED], 4)
        self.assertEqual([result[name] for name in m.RAW_COLUMNS], [9, 5, 1, 4])
        self.assertFalse(result[m.COL_PARTIAL])

    def test_report_year_can_be_chosen_and_partial_years_flagged(self):
        df = pd.DataFrame(
            [row(f"p{i}", "Judo", 2026, "Prov Dev 2", years_targeted=2) for i in range(10)]
            + [row("p0", "Judo", 2027, "SC Carded")]
        )
        latest = m.build_ee_metrics(df, ["Judo"]).iloc[0]
        self.assertEqual(latest[m.COL_YEAR], 2027)
        self.assertTrue(latest[m.COL_PARTIAL])
        self.assertTrue(pd.isna(latest[m.COL_YEARS_TARGETED]))
        chosen = m.build_ee_metrics(df, ["Judo"], 2026).iloc[0]
        self.assertEqual((chosen[m.COL_YEAR], chosen[m.COL_YEARS_TARGETED]), (2026, 2.0))

    def test_last_full_year_skips_the_fiscal_year_in_progress(self):
        from datetime import date
        years = [2024, 2025, 2026, 2027]
        self.assertEqual(m.last_full_year(years, date(2026, 11, 20)), 2026)
        self.assertEqual(m.last_full_year(years, date(2027, 3, 31)), 2026)
        self.assertEqual(m.last_full_year(years, date(2027, 4, 1)), 2027)


if __name__ == "__main__":
    unittest.main()
