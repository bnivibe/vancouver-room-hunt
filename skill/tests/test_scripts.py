import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import naver_cafe  # noqa: E402
import score  # noqa: E402
import stations  # noqa: E402


class Totals(unittest.TestCase):
    def total(self, **item):
        return score.monthly_total(score.resolve(item))

    def test_rent_plus_pass(self):
        self.assertAlmostEqual(self.total(rent=900, transit="zone1"), 900 + 117.20)

    def test_walkable_room_has_no_pass(self):
        self.assertAlmostEqual(self.total(rent=950, transit="walk"), 1000.0)
        self.assertAlmostEqual(self.total(rent=950, walk=True), 1000.0)

    def test_bus_costs_a_one_zone_pass_from_anywhere(self):
        self.assertEqual(self.total(rent=800, transit="bus"), self.total(rent=800, transit="zone1"))

    def test_zone_prices_skytrain(self):
        self.assertLess(self.total(rent=800, transit="zone2"), self.total(rent=800, transit="zone3"))

    def test_utilities(self):
        self.assertEqual(self.total(rent=900, utilities="included"), self.total(rent=900, utilities=0))
        self.assertAlmostEqual(self.total(rent=900, utilities="separate") - self.total(rent=900), 60.0)
        self.assertAlmostEqual(self.total(rent=900, utilities=45) - self.total(rent=900), 45.0)

    def test_furniture_is_spread_over_the_stay(self):
        self.assertAlmostEqual(self.total(rent=800, furniture=600, stay=6) - self.total(rent=800), 100.0)

    def test_the_comparison_rule(self):
        # A cheaper rent can cost more once utilities are billed separately.
        self.assertLess(self.total(rent=950, utilities="included"), self.total(rent=900, utilities="separate") + 20)

    def test_unknown_transit_exits(self):
        with self.assertRaises(SystemExit):
            score.resolve({"rent": 900, "transit": "zone9"})

    def test_fares_can_be_overridden(self):
        room = score.resolve({"rent": 900, "transit": "zone1"}, {"zone1": 120.0})
        self.assertEqual(room["transit"], 120.0)


class Runway(unittest.TestCase):
    budget = {"savings": 10000, "start": "2026-10", "horizon": "2027-01", "other_monthly": 1000,
              "job_start": "2026-12", "monthly_income": 4000, "one_off": {"2026-10": 500}}

    def test_balance_lowest_and_broke_month(self):
        # Oct -2500, Nov -2000, Dec -2000 +4000, Jan -2000 +4000
        bal, low, broke = score.runway(1000, self.budget)
        self.assertEqual((bal, low, broke), (10000 - 2500 - 2000 + 2000 + 2000, 5500, None))

    def test_no_job_path(self):
        bal, low, broke = score.runway(2000, self.budget, job_start=None)
        self.assertEqual(bal, 10000 - 500 - 4 * 3000)
        self.assertEqual(broke, "2027-01")

    def test_months_cross_the_year(self):
        self.assertEqual(score._months("2026-11", "2027-02"), [(2026, 11), (2026, 12), (2027, 1), (2027, 2)])

    def test_furniture_is_paid_once_in_the_runway(self):
        plain = score.score(score.resolve({"rent": 900}), self.budget)
        furnished = score.score(score.resolve({"rent": 900, "furniture": 600}), self.budget)
        self.assertAlmostEqual(plain["job"][0] - furnished["job"][0], 600)

    def test_delta_against_baseline(self):
        budget = dict(self.budget, baseline={"rent": 900, "transit": "zone1"})
        s = score.score(score.resolve({"rent": 1000, "transit": "zone1"}), budget)
        self.assertAlmostEqual(s["delta"], -100 * 4)


class Cli(unittest.TestCase):
    def run_main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = score.main(list(argv))
        return code, out.getvalue()

    def test_batch_prints_cheapest_first(self):
        rows = [{"label": "dear", "rent": 1200}, {"label": "cheap", "rent": 700}]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "rows.json"
            path.write_text(json.dumps(rows))
            code, text = self.run_main("--batch", str(path))
        self.assertEqual(code, 0)
        self.assertLess(text.index("cheap"), text.index("dear"))

    def test_examples_run(self):
        code, text = self.run_main("--batch", str(ROOT / "examples/listings.example.json"),
                                   "--budget", str(ROOT / "examples/budget.example.json"))
        self.assertEqual(code, 0)
        self.assertIn("no job", text)
        self.assertIn("vs baseline room", text)


class Stations(unittest.TestCase):
    def test_station_is_its_own_nearest(self):
        name, km = stations.nearest(*stations.STATIONS["Metrotown"])
        self.assertEqual(name, "Metrotown")
        self.assertAlmostEqual(km, 0.0, places=6)

    def test_verdicts(self):
        self.assertEqual(stations.verdict(1.0), "ok")
        self.assertEqual(stations.verdict(1.5), "long walk")
        self.assertEqual(stations.verdict(2.5), "bus to station")
        self.assertEqual(stations.verdict(1.0, ok_km=0.9), "long walk")

    def test_suburban_lines_are_covered(self):
        self.assertEqual(len(stations.STATIONS), 53)
        self.assertEqual(stations.nearest(49.1890, -122.8480)[0], "Surrey Central")
        self.assertEqual(stations.nearest(49.2750, -122.8010)[0], "Coquitlam Central")
        self.assertEqual(stations.nearest(49.1680, -123.1365)[0], "Richmond-Brighouse")

    def test_distance_is_plausible(self):
        # Waterfront to Burrard is roughly 600 m.
        km = stations.haversine_km(stations.STATIONS["Waterfront"], stations.STATIONS["Burrard"])
        self.assertTrue(0.5 < km < 0.7, km)


class NaverCafe(unittest.TestCase):
    def test_default_grep_matches_a_vancouver_title(self):
        title = "".join(map(chr, (0xBC34, 0xCFE0, 0xBC84))) + " room"
        self.assertTrue(re.search(naver_cafe.DEFAULT_GREP, title))
        self.assertFalse(re.search(naver_cafe.DEFAULT_GREP, "Calgary room"))

    def test_source_is_ascii(self):
        (ROOT / "scripts/naver_cafe.py").read_bytes().decode("ascii")

    def test_read_without_cookie_exits_cleanly(self):
        saved = {k: naver_cafe.os.environ.pop(k, None) for k in ("NAVER_COOKIE", "NAVER_COOKIE_FILE")}
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(naver_cafe.read("gocan", "1"), 0)
            self.assertIn("login", out.getvalue())
        finally:
            for k, v in saved.items():
                if v is not None:
                    naver_cafe.os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
