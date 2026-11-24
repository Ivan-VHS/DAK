from __future__ import annotations

import json
import tempfile
import unittest
from jsonschema import Draft202012Validator, FormatChecker
from pathlib import Path

from duckos.jora.engine import (
    FormulaError,
    analyze_formula,
    build_graph,
    normalize_formula,
    select_languages,
)
from duckos.jora.packages import PackageError, generate_package, publish_package, verify_package


class PassingReaper:
    available = True

    def check(self, source: Path):
        text = source.read_text(encoding="utf-8")
        return {
            "ok": "make app_name :=" in text and 'emit "Jora application: "' in text,
            "exit_code": 0,
            "result": {"diagnostics": []},
            "stderr": "",
        }


class FormulaEngineTests(unittest.TestCase):
    def test_aliases_resolve_and_trio_has_stable_identity(self) -> None:
        result = analyze_formula("текстовый редактор + аудиоредактор + переводчик")
        self.assertEqual(
            result["formula"]["component_ids"],
            ["text_editor", "audio_editor", "translator"],
        )
        self.assertEqual(result["identity"]["display_name"], "Слововолна")
        self.assertEqual(result["identity"]["slug"], "slovovolna")
        self.assertEqual(result["languages"]["languages"][0]["language"], "Reaper")

    def test_role_and_weight_are_normalized(self) -> None:
        result = normalize_formula("основной: текстовый редактор + фоновый: заметки x2")
        self.assertEqual(result["components"][0]["role"], "primary")
        self.assertEqual(result["components"][1]["role"], "background")
        self.assertEqual(result["components"][1]["weight"], 2)
        self.assertEqual(result["complexity"], 3)

    def test_duplicate_component_is_rejected(self) -> None:
        with self.assertRaisesRegex(FormulaError, "Повторяющиеся"):
            normalize_formula("заметки + notes")

    def test_offline_and_cloud_components_conflict_is_rejected(self) -> None:
        with self.assertRaisesRegex(FormulaError, "несовместим"):
            normalize_formula("строго офлайн + облачный стриминг")
        with self.assertRaisesRegex(FormulaError, "несовместим"):
            normalize_formula("строго офлайн + облачная синхронизация")

    def test_unknown_component_has_suggestions(self) -> None:
        with self.assertRaisesRegex(FormulaError, "Возможные варианты"):
            normalize_formula("аудиоредакторр")

    def test_graph_is_bounded_and_clustered(self) -> None:
        formula = normalize_formula(
            "текстовый редактор + аудиоредактор + переводчик + глоссарий + "
            "субтитры + заметки + канбан + календарь"
        )
        graph = build_graph(formula, max_neighbors=2)
        self.assertEqual(graph["topology"], "bounded_hub_cluster")
        self.assertEqual(graph["node_count"], len(formula["components"]) + 1)
        self.assertLessEqual(graph["edge_count"], len(formula["components"]) * 3)
        self.assertEqual(graph["complexity"]["edge_growth"], "O(N*M)")
        self.assertGreaterEqual(len(graph["clusters"]), 3)

    def test_language_selection_is_deterministic_and_availability_aware(self) -> None:
        formula = normalize_formula("аудиоредактор + переводчик")
        plan = select_languages(formula, profile="desktop", toolchain={"python": "/python", "rust": None, "c": None})
        self.assertEqual([item["language"] for item in plan["languages"]], ["Reaper", "Python"])
        self.assertTrue(any("DSP" in item for item in plan["warnings"]))


class PackageTests(unittest.TestCase):
    def test_package_is_generated_with_manifest_graph_and_coherent_demo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "slovovolna.jora"
            created = generate_package("текстовый редактор + аудиоредактор + переводчик", output)
            self.assertTrue(created["created"])
            self.assertTrue((output / "source" / "main.rpr").is_file())
            self.assertTrue((output / "architecture" / "graph.json").is_file())
            self.assertTrue((output / "content" / "demo-project.json").is_file())
            manifest = json.loads((output / "jora.manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["app"]["display_name"], "Слововолна")
            self.assertIn("source/main.rpr", manifest["files"])
            demo = json.loads((output / "content" / "demo-project.json").read_text(encoding="utf-8"))
            self.assertEqual(len(demo["segments"]), 4)
            self.assertTrue(demo["audio_assets"][0]["generated"])
            self.assertTrue((output / "content" / "audio" / "demo.wav").is_file())
            self.assertEqual((output / "content" / "audio" / "demo.wav").read_bytes()[:4], b"RIFF")

    def test_generated_manifest_matches_the_versioned_json_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "schema-check.jora"
            generate_package("текстовый редактор + аудиоредактор + переводчик", output)
            manifest = json.loads((output / "jora.manifest.json").read_text(encoding="utf-8"))
            schema = json.loads((Path(__file__).resolve().parents[1] / "schemas" / "jora-app-package.v1.schema.json").read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema, format_checker=FormatChecker()).validate(manifest)

    def test_integrity_verification_and_reaper_static_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "voice.jora"
            generate_package("переводчик + глоссарий", output)
            result = verify_package(output, reaper_workbench=PassingReaper())
            self.assertTrue(result["ok"])
            self.assertEqual(result["verification"]["status"], "verified_preview")
            self.assertTrue(result["verification"]["source_check"]["passed"])
            self.assertFalse(result["verification"]["source_check"]["source_executed"])

    def test_tampered_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "voice.jora"
            generate_package("переводчик + глоссарий", output)
            (output / "README.md").write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(PackageError, "Integrity check failed"):
                verify_package(output, reaper_workbench=PassingReaper())

    def test_output_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "existing.jora"
            output.mkdir()
            with self.assertRaisesRegex(PackageError, "already exists"):
                generate_package("заметки", output)

    def test_local_catalog_publish_is_not_public_store_publish(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "notes.jora"
            generate_package("заметки", output)
            catalog_path = Path(directory) / "catalog.json"
            result = publish_package(output, channel="experimental", catalog_path=catalog_path)
            self.assertTrue(result["published"])
            self.assertEqual(result["scope"], "current_user_local")
            self.assertFalse(result["public_store"])
            self.assertTrue(catalog_path.is_file())
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            self.assertEqual(len(catalog["applications"]), 1)


if __name__ == "__main__":
    unittest.main()
