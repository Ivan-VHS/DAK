from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"


class ContentRightsSchemaTests(unittest.TestCase):
    def test_rights_schemas_are_valid_draft_2020_12_documents(self) -> None:
        expected = {
            "entitlement.v1.schema.json",
            "content-manifest.v1.schema.json",
            "rights-transfer.v1.schema.json",
            "user-content-record.v1.schema.json",
        }
        found = {path.name for path in SCHEMA_DIR.glob("*rights*.schema.json")}
        found.update(path.name for path in SCHEMA_DIR.glob("*entitlement*.schema.json"))
        found.update(path.name for path in SCHEMA_DIR.glob("*content-manifest*.schema.json"))
        found.update(path.name for path in SCHEMA_DIR.glob("*user-content-record*.schema.json"))
        self.assertTrue(expected.issubset(found))
        for name in sorted(expected):
            with self.subTest(schema=name):
                schema = json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
                Draft202012Validator.check_schema(schema)


if __name__ == "__main__":
    unittest.main()
