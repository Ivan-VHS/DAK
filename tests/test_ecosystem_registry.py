from __future__ import annotations

import json
import unittest

from tools.validate_ecosystem import REGISTRY, validate_registry


class EcosystemRegistryTests(unittest.TestCase):
    def test_registry_is_valid(self) -> None:
        self.assertEqual(validate_registry(), [])

    def test_specialist_roles_are_not_mixed(self) -> None:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        roles = {item["id"]: item["role"] for item in data["projects"]}
        self.assertEqual(roles["pytyliki"], "processor_analysis")
        self.assertEqual(roles["reaper"], "language_toolchain")
        self.assertEqual(roles["oplague"], "driver_inspection")
        self.assertEqual(roles["ventusample"], "offline_audio")
        self.assertEqual(roles["beelzebul"], "security_gate")


if __name__ == "__main__":
    unittest.main()
