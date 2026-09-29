"""Tests for cronlens: parser, matcher semantics, explainer, quiz, CLI."""

import datetime as dt
import io
import json
import unittest
from contextlib import redirect_stdout

from cronlens.parser import parse, matches, CronParseError
from cronlens.matcher import next_fires
from cronlens.explainer import explain
from cronlens.quiz import make_quiz, check_answer, TIERS
from cronlens.cli import main

AFTER = dt.datetime(2026, 9, 29, 10, 0)  # a Tuesday


class TestParser(unittest.TestCase):
    def test_basic_sets(self):
        s = parse("*/15 9-17 * * mon-fri")
        self.assertEqual(sorted(s.minutes), [0, 15, 30, 45])
        self.assertEqual(sorted(s.hours), list(range(9, 18)))
        self.assertEqual(sorted(s.dows), [1, 2, 3, 4, 5])

    def test_lists_and_names(self):
        s = parse("0 12 * jan,dec 1,sun")
        self.assertEqual(sorted(s.months), [1, 12])
        self.assertEqual(sorted(s.dows), [0, 1])  # sunday=0, monday=1

    def test_sunday_zero_and_seven(self):
        self.assertEqual(sorted(parse("* * * * 7").dows), [0])
        self.assertEqual(sorted(parse("* * * * 0").dows), [0])

    def test_specials(self):
        self.assertEqual(parse("@daily").original, "0 0 * * *")
        self.assertEqual(parse("@weekly").original, "0 0 * * 0")
        self.assertEqual(sorted(parse("@noon").hours), [12])

    def test_step_with_base(self):
        self.assertEqual(sorted(parse("10/20 * * * *").minutes), [10, 30, 50])

    def test_errors(self):
        for bad in ["", "* * * *", "* * * * * *", "61 * * * *", "* 24 * * *",
                    "* * 0 * *", "* * * 13 *", "*/0 * * * *", "5-1 * * * *",
                    "* * * * foo"]:
            with self.assertRaises(CronParseError, msg=bad):
                parse(bad)

    def test_restriction_flags(self):
        self.assertFalse(parse("* * * * *").dom_restricted)
        self.assertTrue(parse("0 0 1 * *").dom_restricted)
        self.assertTrue(parse("0 0 * * 1").dow_restricted)


class TestMatcher(unittest.TestCase):
    def test_simple_step(self):
        s = parse("*/10 * * * *")
        fires, _ = next_fires(s, AFTER, count=3)
        self.assertEqual([f.strftime("%H:%M") for f in fires], ["10:10", "10:20", "10:30"])

    def test_daily(self):
        s = parse("0 4 * * *")
        fires, _ = next_fires(s, AFTER, count=2)
        self.assertEqual([f.strftime("%Y-%m-%d %H:%M") for f in fires],
                         ["2026-09-30 04:00", "2026-10-01 04:00"])

    def test_dom_dow_or_semantics(self):
        # 13th OR Friday; Sept 29 2026 is a Tuesday, so Oct 2 2026 is a Friday
        s = parse("0 12 13 * 5")
        fires, _ = next_fires(s, AFTER, count=4)
        days = [(f.month, f.day, f.strftime("%a")) for f in fires]
        # first fires: Fridays Oct 2 and Oct 9 (DOW), then Tue Oct 13 (DOM), Fri Oct 16
        self.assertEqual(fires[0], dt.datetime(2026, 10, 2, 12, 0))
        self.assertEqual(fires[1], dt.datetime(2026, 10, 9, 12, 0))
        self.assertEqual(fires[2], dt.datetime(2026, 10, 13, 12, 0))
        self.assertEqual(fires[3], dt.datetime(2026, 10, 16, 12, 0))
        # both kinds appear across the window
        self.assertTrue(any(w == "Tue" for _, _, w in days))
        self.assertTrue(any(w == "Fri" for _, _, w in days))

    def test_dom_dow_and_when_only_one_restricted(self):
        s = parse("0 12 * * 1")  # every Monday
        fires, _ = next_fires(s, AFTER, count=2)
        self.assertEqual([f.strftime("%a") for f in fires], ["Mon", "Mon"])

    def test_never_fires_february_30(self):
        s = parse("0 0 30 2 *")
        fires, _ = next_fires(s, AFTER, count=1)
        self.assertEqual(fires, [])

    def test_feb_29_leap_year(self):
        s = parse("0 0 29 2 *")
        fires, _ = next_fires(s, AFTER, count=1)
        self.assertEqual(fires[0], dt.datetime(2028, 2, 29, 0, 0))  # 2028 is a leap year

    def test_year_rollover(self):
        s = parse("0 0 1 1 *")
        fires, _ = next_fires(s, dt.datetime(2026, 12, 31, 12, 0), count=1)
        self.assertEqual(fires[0], dt.datetime(2027, 1, 1, 0, 0))

    def test_month_end_clamp_not_applied(self):
        # 31st fires only in months with 31 days — matcher must skip 30-day months
        s = parse("0 0 31 * *")
        fires, _ = next_fires(s, AFTER, count=3)
        self.assertEqual([f.strftime("%B") for f in fires], ["October", "December", "January"])

    def test_matches_helper_or_rule(self):
        s = parse("0 12 13 * 5")
        tue13 = dt.datetime(2026, 10, 13, 12, 0)   # 13th, Tuesday
        fri16 = dt.datetime(2026, 10, 16, 12, 0)   # Friday
        tue20 = dt.datetime(2026, 10, 20, 12, 0)   # Tuesday, not 13th
        self.assertTrue(matches(s, tue13))
        self.assertTrue(matches(s, fri16))
        self.assertFalse(matches(s, tue20))

    def test_trace_records_skips(self):
        s = parse("0 0 13 * *")
        fires, traces = next_fires(s, AFTER, count=1, want_trace=True)
        self.assertEqual(len(fires), 1)
        self.assertTrue(any("DOM" in r for _, r in traces))


class TestExplainer(unittest.TestCase):
    def test_explain_lines_and_or_warning(self):
        s = parse("0 12 13 * 5")
        lines, warnings = explain(s)
        joined = "\n".join(lines)
        self.assertIn("minute", joined)
        self.assertIn("day-of-week", joined)
        self.assertTrue(any("OR" in w for w in warnings))

    def test_never_fire_warning(self):
        s = parse("0 0 30 2 *")
        _, warnings = explain(s)
        self.assertTrue(any("February" in w for w in warnings))

    def test_no_warning_for_simple(self):
        s = parse("*/15 9-17 * * *")
        _, warnings = explain(s)
        self.assertEqual(warnings, [])


class TestQuiz(unittest.TestCase):
    def test_deterministic_items(self):
        a = make_quiz(tier=2, rounds=6, seed=7)
        b = make_quiz(tier=2, rounds=6, seed=7)
        self.assertEqual([(i["expr"], i["after"]) for i in a], [(i["expr"], i["after"]) for i in b])

    def test_answers_are_future_and_correct(self):
        for item in make_quiz(tier=1, rounds=7, seed=3):
            if item["answer"] is not None:
                self.assertGreater(item["answer"], item["after"])
                sched = parse(item["expr"])
                self.assertTrue(matches(sched, item["answer"]))

    def test_tier3_contains_never_firing_item(self):
        items = make_quiz(tier=3, rounds=20, seed=11)
        self.assertTrue(any(i["answer"] is None for i in items))

    def test_check_answer_paths(self):
        item = {"expr": "30 4 * * *", "after": AFTER, "answer": dt.datetime(2026, 9, 30, 4, 30)}
        ok, _ = check_answer(item, dt.datetime(2026, 9, 30, 4, 30))
        self.assertTrue(ok)
        ok, note = check_answer(item, dt.datetime(2026, 9, 30, 5, 30))
        self.assertFalse(ok)
        self.assertIn("off by +60 minutes", note)
        never = {"expr": "0 0 30 2 *", "after": AFTER, "answer": None}
        ok, note = check_answer(never, "never")
        self.assertTrue(ok)
        self.assertIn("never fire", note)

    def test_unknown_tier_raises(self):
        with self.assertRaises(ValueError):
            make_quiz(tier=9, rounds=1)


class TestCli(unittest.TestCase):
    def _out(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(argv)
        return buf.getvalue()

    def test_explain_cli(self):
        out = self._out(["explain", "*/15 9-17 * * mon-fri"])
        self.assertIn("field", out)
        self.assertIn("fires:", out)

    def test_next_cli_and_json(self):
        out = self._out(["next", "*/10 * * * *", "-n", "3", "--utc", "2026-09-29T10:00:00"])
        self.assertIn("10:10", out)
        j = json.loads(self._out(["next", "@daily", "-n", "2",
                                  "--utc", "2026-09-29T10:00:00", "--json"]))
        self.assertEqual(j["fires"][0], "2026-09-30T00:00:00")

    def test_parse_error_exit_2(self):
        with self.assertRaises(SystemExit) as cm:
            main(["next", "0 0 30 2 * *", "-n", "1"])
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
