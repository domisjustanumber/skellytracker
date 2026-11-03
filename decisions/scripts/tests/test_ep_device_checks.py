"""Unit tests for the rules table of `ep_device_checks/run_checks.py`, with fake GPU facts."""

from __future__ import annotations

import unittest

from ep_device_checks import run_checks as rc

# One driver version for each scenario. Pascal stops at R580, so its scenario C is 582.
DRIVERS = {"A": "516.94", "B": "576.88", "C": "621.01"}
PASCAL_C = "582.78"


def gpu(cc: str, driver: str) -> dict:
    return {"name": "fake", "cc": cc, "driver_version": driver, "driver_branch": rc.driver_branch(driver),
            "vram_total_mb": 4096, "pci": "10de:0000:00000000"}


def verdicts(cc: str, driver: str, osk: str = "win32") -> dict:
    return {route: rc.predict(route, gpu(cc, driver), osk)["verdict"] for route in rc.RULES}


class PredictTable(unittest.TestCase):
    def test_turing_cc75(self):
        self.assertEqual(verdicts("7.5", DRIVERS["A"]), {
            "cpu": "ok", "cuda-cu13": "update-driver", "cuda-cu12": "update-driver",
            "trt-rtx-cu13": "unsupported", "trt-rtx-cu12": "unsupported"})
        self.assertEqual(verdicts("7.5", DRIVERS["B"]), {
            "cpu": "ok", "cuda-cu13": "update-driver", "cuda-cu12": "ok",
            "trt-rtx-cu13": "unsupported", "trt-rtx-cu12": "unsupported"})
        # Measured on a GTX 1650: the cu12 pack passes on 566.36 (R565), above the R525 floor.
        self.assertEqual(rc.predict("cuda-cu12", gpu("7.5", "566.36"), "win32")["verdict"], "ok")
        self.assertEqual(verdicts("7.5", DRIVERS["C"]), {
            "cpu": "ok", "cuda-cu13": "ok", "cuda-cu12": "ok",
            "trt-rtx-cu13": "unsupported", "trt-rtx-cu12": "unsupported"})

    def test_pascal_cc61_is_arch_unsupported_not_update_driver(self):
        for driver in (DRIVERS["A"], DRIVERS["B"], PASCAL_C):
            result = verdicts("6.1", driver)
            for route in ("cuda-cu13", "trt-rtx-cu13", "trt-rtx-cu12"):
                self.assertEqual(result[route], "unsupported", (route, driver))
                self.assertIn("CC 6.1", rc.predict(route, gpu("6.1", driver), "win32")["reason"])
        self.assertEqual(verdicts("6.1", DRIVERS["A"])["cuda-cu12"], "update-driver")
        self.assertEqual(verdicts("6.1", DRIVERS["B"])["cuda-cu12"], "ok")
        self.assertEqual(verdicts("6.1", PASCAL_C)["cuda-cu12"], "ok")

    def test_pascal_update_target_never_past_r580(self):
        for route in rc.RULES:
            for driver in ("470.00", "566.36", "576.88"):
                pred = rc.predict(route, gpu("6.1", driver), "win32")
                if pred["verdict"] == "update-driver":
                    self.assertLessEqual(pred["target_branch"], 580)

    def test_ampere_cc86(self):
        self.assertEqual(set(verdicts("8.6", DRIVERS["A"]).values()), {"ok", "update-driver"})
        result = verdicts("8.6", DRIVERS["B"])
        self.assertEqual((result["cuda-cu12"], result["trt-rtx-cu12"]), ("ok", "ok"))
        self.assertEqual((result["cuda-cu13"], result["trt-rtx-cu13"]), ("update-driver", "update-driver"))
        self.assertEqual(set(verdicts("8.6", DRIVERS["C"]).values()), {"ok"})

    def test_update_targets(self):
        self.assertEqual(rc.predict("cuda-cu13", gpu("7.5", DRIVERS["B"]), "win32")["target_branch"], 580)
        self.assertEqual(rc.predict("cuda-cu12", gpu("7.5", DRIVERS["A"]), "win32")["target_branch"], 525)

    def test_cu12_sass_differs_by_os(self):
        self.assertEqual(rc.predict("cuda-cu12", gpu("8.0", DRIVERS["C"]), "win32")["verdict"], "unsupported")
        self.assertEqual(rc.predict("cuda-cu12", gpu("8.0", DRIVERS["C"]), "linux")["verdict"], "ok")
        self.assertEqual(rc.predict("cuda-cu12", gpu("7.0", DRIVERS["C"]), "linux")["verdict"], "ok")
        self.assertEqual(rc.predict("cuda-cu12", gpu("7.0", DRIVERS["C"]), "win32")["verdict"], "unsupported")

    def test_no_gpu(self):
        self.assertEqual(rc.predict("cuda-cu12", None, "win32")["verdict"], "no-nvidia-gpu")
        self.assertEqual(rc.predict("cpu", None, "win32")["verdict"], "ok")


class Scenarios(unittest.TestCase):
    def test_driver_branch(self):
        self.assertEqual([rc.driver_branch(v) for v in ("566.36", "572.16", "576.88", "582.78", "621.01",
                                                         "570.124.04", "580.196.07")],
                         [565, 570, 575, 580, 620, 570, 580])

    def test_names(self):
        self.assertEqual([rc.scenario(gpu("7.5", d))["name"] for d in DRIVERS.values()], ["A", "B", "C"])
        self.assertIn("R580", rc.scenario(gpu("6.1", PASCAL_C))["text"])

    def test_pascal_driver_past_r580_is_an_anomaly(self):
        self.assertEqual(rc.anomalies(gpu("6.1", PASCAL_C)), [])
        self.assertEqual(len(rc.anomalies(gpu("6.1", "590.10"))), 1)
        self.assertEqual(rc.anomalies(gpu("7.5", DRIVERS["C"])), [])


def report(driver: str, observed: dict, created: str) -> dict:
    g = gpu("7.5", driver)
    routes = {}
    for route, obs in observed.items():
        pred = rc.predict(route, g, "win32")
        fields = {"driver_version": driver, "pci": g["pci"], "os_build": "1", "packages": {}}
        routes[route] = {"predicted": pred, "observed": {"verdict": obs},
                         "verdict_key": {"fields": fields, "hash": driver}}
    return {"created": created, "gpu": g, "scenario": rc.scenario(g), "routes": routes}


class Compare(unittest.TestCase):
    def test_driver_update_fixes_cu13_as_predicted(self):
        before = report(DRIVERS["B"], {"cuda-cu13": "fail", "cuda-cu12": "pass"}, "2026-01-01T00:00:00")
        after = report(DRIVERS["C"], {"cuda-cu13": "pass", "cuda-cu12": "pass"}, "2026-01-02T00:00:00")
        step = rc.compare_pair(before, after)
        self.assertTrue(step["routes"]["cuda-cu13"]["outcome"].startswith("as predicted"))
        self.assertEqual(step["routes"]["cuda-cu12"]["outcome"], "no change")
        self.assertTrue(step["routes"]["cuda-cu12"]["verdict_key_changed"])
        self.assertEqual(step["routes"]["cuda-cu12"]["key_fields_changed"], ["driver_version"])

    def test_route_that_passed_before_the_update_is_a_wrong_prediction(self):
        before = report(DRIVERS["A"], {"cuda-cu12": "pass"}, "2026-01-01T00:00:00")
        after = report(DRIVERS["B"], {"cuda-cu12": "pass"}, "2026-01-02T00:00:00")
        self.assertTrue(rc.compare_pair(before, after)["routes"]["cuda-cu12"]["outcome"].startswith("prediction wrong"))

    def test_update_that_does_not_fix_is_flagged(self):
        before = report(DRIVERS["B"], {"cuda-cu13": "fail"}, "2026-01-01T00:00:00")
        after = report(DRIVERS["C"], {"cuda-cu13": "fail"}, "2026-01-02T00:00:00")
        self.assertTrue(rc.compare_pair(before, after)["routes"]["cuda-cu13"]["outcome"].startswith("NOT"))


class DriverLinks(unittest.TestCase):
    def test_every_family_and_os_has_https_links_for_each_scenario(self):
        for family, by_os in rc.DRIVERS.items():
            for osk, rows in by_os.items():
                self.assertEqual(sorted(rows), ["A", "B", "C"], (family, osk))
                for name, entries in rows.items():
                    self.assertTrue(entries, (family, osk, name))
                    for version, _, _, url in entries:
                        self.assertTrue(url.startswith("https://www.nvidia.com/"), url)
                        if not version[0].isdigit():
                            continue  # a generic entry, for example "older than R525"
                        branch = rc.driver_branch(version.split()[0])
                        expected = next(n for limit, n, _ in rc.SCENARIOS if branch < limit)
                        self.assertEqual(expected, name, (family, osk, version))

    def test_pascal_links_never_pass_r580(self):
        for rows in rc.DRIVERS["pascal"].values():
            for entries in rows.values():
                for version, *_ in entries:
                    if not version[0].isdigit():
                        continue
                    self.assertLessEqual(rc.driver_branch(version.split()[0]), 580, version)

    def test_guide_marks_the_installed_scenario_and_gives_the_next_step(self):
        text = "\n".join(rc.driver_guide(gpu("7.5", DRIVERS["B"]), "win32"))
        self.assertIn("Scenario B (R525 to R579)  <- installed", text)
        self.assertIn("install a scenario C driver", text)
        self.assertIn(rc.DRIVERS["turing"]["win32"]["C"][0][3], text)
        text = "\n".join(rc.driver_guide(gpu("6.1", PASCAL_C), "linux"))
        self.assertIn("R580 is the last driver branch", text)
        self.assertIn("install a scenario A or B driver", text)
        self.assertEqual(rc.driver_guide(None, "win32"), ["Driver test: no NVIDIA GPU found."])


class Matching(unittest.TestCase):
    def test_match(self):
        self.assertEqual(rc.match("ok", "pass"), "yes")
        self.assertEqual(rc.match("update-driver", "fail"), "yes")
        self.assertEqual(rc.match("unsupported", "pass"), "NO")
        self.assertEqual(rc.match("experimental", "fail"), "informational")
        self.assertEqual(rc.match("ok", "error"), "n/a")


if __name__ == "__main__":
    unittest.main()
