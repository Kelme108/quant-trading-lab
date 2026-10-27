import tempfile
import unittest
from pathlib import Path

from lab import manifest


class ManifestRenderTests(unittest.TestCase):
    def test_skeleton_has_every_template_section(self) -> None:
        data = manifest.default_manifest_skeleton()
        self.assertEqual(
            set(data),
            {"experiment_id", "created_at_utc", "code", "runtime", "market", "data", "backtest", "validation", "result"},
        )

    def test_render_quotes_strings_and_leaves_numbers_bare(self) -> None:
        data = manifest.default_manifest_skeleton()
        data["experiment_id"] = "exp-001"
        data["data"]["candle_count"] = 8778
        rendered = manifest.render_manifest(data)
        self.assertIn('experiment_id: "exp-001"', rendered)
        self.assertIn("candle_count: 8778", rendered)

    def test_render_null_for_none(self) -> None:
        data = manifest.default_manifest_skeleton()
        rendered = manifest.render_manifest(data)
        self.assertIn("git_commit: null", rendered)

    def test_render_inline_parameters_mapping(self) -> None:
        data = manifest.default_manifest_skeleton()
        data["backtest"]["parameters"] = {"0": 100.0, "fast_sma": 20}
        rendered = manifest.render_manifest(data)
        self.assertIn('parameters: {"0": 100.0, "fast_sma": 20}', rendered)

    def test_render_escapes_embedded_quotes(self) -> None:
        data = manifest.default_manifest_skeleton()
        data["result"]["notes"] = 'Contains a "quoted" phrase'
        rendered = manifest.render_manifest(data)
        self.assertIn('\\"quoted\\"', rendered)


class WriteManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.manifests_dir = Path(self._tmp.name)

    def test_write_creates_file_at_expected_path(self) -> None:
        data = manifest.default_manifest_skeleton()
        data["experiment_id"] = "exp-abc"
        path = manifest.write_manifest("exp-abc", data, self.manifests_dir)
        self.assertEqual(path, self.manifests_dir / "exp-abc.yaml")
        self.assertTrue(path.is_file())

    def test_write_refuses_to_overwrite_existing_manifest(self) -> None:
        data = manifest.default_manifest_skeleton()
        manifest.write_manifest("exp-dup", data, self.manifests_dir)
        with self.assertRaises(FileExistsError):
            manifest.write_manifest("exp-dup", data, self.manifests_dir)


if __name__ == "__main__":
    unittest.main()
