"""Contracts for the static-site validator and the authored content tree."""
from pathlib import Path
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_site", ROOT / "scripts/check_site.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class SiteContracts(unittest.TestCase):
    def test_external_link_is_not_treated_as_local(self):
        self.assertIsNone(module.local_target("https://github.com/mapseekai/geoledger", "https://docs.example/a/", "https://docs.example/", ROOT))

    def test_subpath_resolution(self):
        path, fragment = module.local_target("../merge/#conflicts", "https://docs.example/gl/docs/overview/", "https://docs.example/gl/", ROOT)
        self.assertEqual(path, ROOT / "docs/merge/index.html")
        self.assertEqual(fragment, "conflicts")

    def test_deployment_prefix_escape_is_rejected(self):
        with self.assertRaises(ValueError):
            module.local_target("/docs/", "https://docs.example/gl/", "https://docs.example/gl/", ROOT)

    def test_anchor_and_image_metadata(self):
        parser = module.Inspector()
        parser.feed('<html lang="zh-CN"><title>Test</title><h1 id="top">Title</h1><img src="a.png" alt="diagram" width="10" height="20">')
        self.assertIn("top", parser.document.ids)
        self.assertTrue(parser.document.language)
        self.assertEqual(parser.document.h1_count, 1)
        self.assertEqual(parser.document.image_errors, [])

    def test_missing_image_accessibility_is_reported(self):
        parser = module.Inspector()
        parser.feed('<img src="missing.png">')
        self.assertEqual(len(parser.document.image_errors), 2)

    def test_screenshot_files_match_provenance(self):
        import hashlib
        entries = json.loads((ROOT / "data/screenshots.json").read_text())
        self.assertGreaterEqual(len(entries), 4)
        for name, metadata in entries.items():
            data = (ROOT / "static/images/screenshots" / name).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), metadata["sha256"])
            self.assertIn("visible_version", metadata)
            self.assertIn("captured_at", metadata)
            self.assertEqual(metadata["alterations"], "none")

    def test_project_version_is_explicit(self):
        data = json.loads((ROOT / "data/project.json").read_text())
        self.assertEqual(data["storage_format"], 19)
        self.assertRegex(data["source_commit"], r"^[a-f0-9]{40}$")
        self.assertEqual(data["theme"]["version"], "v1.4.0")

    def test_tutorial_checks_out_documented_source(self):
        commit = json.loads((ROOT / "data/project.json").read_text())["source_commit"]
        quickstart = (ROOT / "content/docs/start/quickstart.md").read_text()
        self.assertIn(f"git checkout {commit}", quickstart)

    def test_document_examples_have_valid_syntax(self):
        for path in (ROOT / "content/docs").rglob("*.md"):
            blocks = re.findall(r"^```(json|python|sh)\n(.*?)^```", path.read_text(), re.M | re.S)
            for language, code in blocks:
                with self.subTest(page=str(path.relative_to(ROOT)), language=language):
                    if language == "json":
                        json.loads(code)
                    elif language == "python":
                        compile(code, str(path), "exec")
                    else:
                        result = subprocess.run(["bash", "-n"], input=code, text=True, capture_output=True)
                        self.assertEqual(result.returncode, 0, result.stderr)

    def test_three_top_level_sections(self):
        for path in ("content/_index.md", "content/docs/_index.md", "content/blog/_index.md"):
            self.assertTrue((ROOT / path).is_file(), path)

    def test_instruction_file_is_a_relative_symlink(self):
        import os
        self.assertTrue((ROOT / "CLAUDE.md").is_symlink())
        self.assertEqual(os.readlink(ROOT / "CLAUDE.md"), "AGENTS.md")

    def test_draft_credentials_are_not_in_public_sources(self):
        pattern = __import__("re").compile(r"glk_[a-f0-9]{64}")
        for directory in ("content", "layouts", "data", "assets", "static"):
            for path in (ROOT / directory).rglob("*"):
                if path.is_file() and path.suffix in (".md", ".html", ".json", ".css", ".svg", ".js"):
                    self.assertIsNone(pattern.search(path.read_text()), str(path))


if __name__ == "__main__":
    unittest.main()
