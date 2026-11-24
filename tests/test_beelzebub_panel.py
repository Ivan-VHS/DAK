from __future__ import annotations
import unittest
from pathlib import Path
from duckos.desktop.beelzebub_panel import build_scan_options

class BeelzebubPanelConfigTests(unittest.TestCase):
    def test_signed_feed_requires_all_three_files(self):
        with self.assertRaises(ValueError):
            build_scan_options(hashdb="feed.json")

    def test_yara_requires_binary_and_rules_together(self):
        with self.assertRaises(ValueError):
            build_scan_options(yara_bin="/usr/bin/yara-x")

    def test_default_configuration_is_explicit(self):
        result = build_scan_options()
        self.assertEqual(result["clam_port"], 3310)
        self.assertIsNone(result["hashdb"])
        self.assertIsNone(result["signature"])
        self.assertIsNone(result["public_key"])
        self.assertIsNone(result["yara_bin"])
        self.assertIsNone(result["yara_rules"])

    def test_complete_configuration_is_converted_to_paths(self):
        result = build_scan_options(hashdb="feed.json", signature="feed.sig", public_key="feed.pub",
            clam_port="3311", yara_bin="/usr/bin/yara-x", yara_rules="rules.yar")
        self.assertEqual(result["hashdb"], Path("feed.json"))
        self.assertEqual(result["signature"], Path("feed.sig"))
        self.assertEqual(result["public_key"], Path("feed.pub"))
        self.assertEqual(result["clam_port"], 3311)
        self.assertEqual(result["yara_bin"], Path("/usr/bin/yara-x"))
        self.assertEqual(result["yara_rules"], Path("rules.yar"))

    def test_invalid_clam_port_is_rejected(self):
        with self.assertRaises(ValueError):
            build_scan_options(clam_port="65536")

if __name__ == "__main__":
    unittest.main()
