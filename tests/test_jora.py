from __future__ import annotations
import tempfile
import unittest
import zipfile
from pathlib import Path
from duckos.jora.catalog import PARAMETERS, catalog_payload
from duckos.jora.engine import FormulaError, build_application, build_graph, normalize_formula, validate_package, write_package

class JoraFormulaTests(unittest.TestCase):
    def test_registry_has_unique_ids_and_seed_variants(self):
        ids=[item["id"] for item in PARAMETERS]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(catalog_payload()["schema"],"jora.parameter-registry.v1")
        self.assertGreaterEqual(len(PARAMETERS),20)
        self.assertGreaterEqual(sum(len(item["variants"]) for item in PARAMETERS),50)
    def test_multilingual_formula_normalizes(self):
        components=normalize_formula("текстовый редактор + audio editor + переводчик")
        self.assertEqual([item["id"] for item in components],["text_editor","audio_editor","translator"])
        self.assertEqual(components[0]["role"],"primary")
    def test_unknown_duplicate_conflict_and_bounds_are_rejected(self):
        for formula in ("text editor + mystery widget","translator + переводчик","offline mode + cloud translation","x"*2049):
            with self.subTest(formula=formula[:60]),self.assertRaises(FormulaError): normalize_formula(formula)
    def test_three_component_formula_builds_integrated_triad(self):
        graph=build_graph(normalize_formula("text editor + audio editor + translator"))
        self.assertEqual(len([e for e in graph["edges"] if e["kind"]=="domain_synergy"]),3)
        app=build_application("text editor + audio editor + translator")
        self.assertEqual(app["manifest"]["app"]["display_name"],"Слововолна")
        self.assertIn("source/main.rpr",app["files"])
    def test_real_catalogue_supports_large_clustered_formulas(self):
        formula = "text editor + audio editor + translator + subtitles + notes + task board + calendar + text to speech + speech to text + code editor + spreadsheet + image editor + video editor"
        components = normalize_formula(formula)
        self.assertEqual(len(components), 13)
        graph = build_graph(components)
        self.assertEqual(graph["topology"], "clustered-hub")
        self.assertLessEqual(len(graph["edges"]), len(components) * 3 + len(graph["clusters"]))
        self.assertGreaterEqual(len(graph["clusters"]), 5)

class JoraPackageTests(unittest.TestCase):
    def test_directory_and_zip_packages_validate(self):
        app=build_application("текстовый редактор + аудиоредактор + переводчик")
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            write_package(app,root/"package")
            write_package(app,root/"package.zip")
            for target in (root/"package",root/"package.zip"):
                result=validate_package(target,check_reaper=False)
                self.assertTrue(result["valid"])
                self.assertEqual(result["app_id"],"slovovolna")
                self.assertFalse(result["execution_performed"])
    def test_validation_rejects_traversal_and_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            unsafe=root/"unsafe.zip"
            with zipfile.ZipFile(unsafe,"w") as archive: archive.writestr("../escape.txt","bad")
            with self.assertRaises(ValueError): validate_package(unsafe,check_reaper=False)
            package=root/"tampered"
            write_package(build_application("translator"),package)
            (package/"source/main.rpr").write_text("emit 7\n",encoding="utf-8")
            with self.assertRaises(ValueError): validate_package(package,check_reaper=False)
    def test_output_is_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary)/"package"
            write_package(build_application("notes"),target)
            with self.assertRaises(ValueError): write_package(build_application("notes"),target)

if __name__=="__main__": unittest.main()
