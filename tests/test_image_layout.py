from __future__ import annotations

import unittest

from dakos.image_layout import LayoutError, plan_image, validate_layout


class ImageLayoutTests(unittest.TestCase):
    def test_plans_aligned_non_overlapping_regions(self):
        plan = plan_image([
            {"name": "efi", "type": "system", "size_bytes": 64 * 1024 * 1024},
            {"name": "boot", "type": "boot", "size_bytes": 128 * 1024 * 1024},
            {"name": "rootfs", "type": "linux", "size_bytes": 2 * 1024 * 1024 * 1024},
        ])
        self.assertTrue(validate_layout(plan))
        self.assertEqual(plan["partitions"][0]["start_byte"], 1024 * 1024)
        self.assertGreaterEqual(plan["partitions"][1]["start_byte"], plan["partitions"][0]["end_byte_exclusive"])
        self.assertFalse(plan["write_performed"])

    def test_rejects_duplicate_names_and_invalid_alignment(self):
        with self.assertRaises(LayoutError):
            plan_image([{"name": "boot", "size_bytes": 100}, {"name": "boot", "size_bytes": 200}])
        with self.assertRaises(LayoutError):
            plan_image([{"name": "boot", "size_bytes": 100}], alignment_bytes=3000)

    def test_rejects_tampered_derived_partition_metadata(self):
        plan = plan_image([{"name": "boot", "type": "boot", "size_bytes": 1_000_000}])
        plan["partitions"][0]["start_sector"] += 1
        with self.assertRaisesRegex(LayoutError, "start sector"):
            validate_layout(plan)

        plan = plan_image([{"name": "boot", "type": "boot", "size_bytes": 1_000_000}])
        plan["partitions"][0]["size_bytes"] -= 512
        with self.assertRaisesRegex(LayoutError, "partition size"):
            validate_layout(plan)

    def test_rejects_unknown_fields_and_false_bootability_claims(self):
        plan = plan_image([{"name": "boot", "size_bytes": 1_000_000}])
        altered = dict(plan)
        altered["trusted"] = True
        with self.assertRaises(LayoutError):
            validate_layout(altered)
        altered = dict(plan)
        altered["bootability_verified"] = True
        with self.assertRaisesRegex(LayoutError, "dry-run"):
            validate_layout(altered)

    def test_rejects_non_integer_and_unbounded_image_size(self):
        plan = plan_image([{"name": "boot", "size_bytes": 1_000_000}])
        plan["image_size_bytes"] = True
        with self.assertRaises(LayoutError):
            validate_layout(plan)
        plan["image_size_bytes"] = 64 * 1024 * 1024 * 1024 + 1
        with self.assertRaises(LayoutError):
            validate_layout(plan)

    def test_rejects_overlap_in_external_plan(self):
        plan = plan_image([{"name": "boot", "size_bytes": 1_000_000}, {"name": "rootfs", "size_bytes": 1_000_000}])
        plan["partitions"][1]["start_byte"] = plan["partitions"][0]["start_byte"]
        with self.assertRaises(LayoutError):
            validate_layout(plan)


if __name__ == "__main__":
    unittest.main()
