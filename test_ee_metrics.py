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

    def test_metrics_average_yearly_rates_over_four_years(self):
        df = pd.DataFrame([
            # 2023: 2 athletes, 1 conversion (A moves Prov Dev -> Uncarded next year too)
            row("a", "Rowing", 2023, "Prov Dev 2"), row("b", "Rowing", 2023, "Prov Dev 1", "Y"),
            # 2024: 2 athletes, 1 national conversion (a: Prov Dev 2 -> SC Carded)
            row("a", "Rowing", 2024, "SC Carded", "Y"), row("b", "Para Rowing", 2024, "Prov Dev 1"),
            # 2025 and 2026: 1 athlete, no conversions; a 2019 conversion is outside the window
            row("b", "Rowing", 2025, "Prov Dev 1", years_targeted=3),
            row("b", "Rowing", 2026, "Prov Dev 1", years_targeted=4),
            row("c", "Rowing", 2019, "Prov Dev 1", "Y"),
        ])
        result = m.build_ee_metrics(df, ["Rowing", "Para Rowing"]).iloc[0]
        self.assertEqual(result[m.COL_SPORT], "Rowing")
        self.assertEqual(result[m.COL_YEAR], 2026)
        self.assertEqual(result[m.COL_WINDOW], "2023–2026")
        self.assertEqual(result[m.COL_ATHLETES], 1)
        self.assertEqual(result[m.COL_ANY], round((0.5 + 0.5 + 0 + 0) / 4 * 100, 1))
        self.assertEqual(result[m.COL_NATIONAL], round((0 + 0.5 + 0 + 0) / 4 * 100, 1))
        self.assertEqual(result[m.COL_YEARS_TARGETED], 4)
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
