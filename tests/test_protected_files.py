"""Guard the frozen files: baselines, dry-run config, and Compose definition.

These hashes are recorded once, right after the files were reviewed and
committed (see research/command-log.md, 2026-10-27 entry). If any of these
tests fail, a protected file changed on disk and the change must be reviewed
manually before anything else proceeds. Do not update a hash here just to
make the test pass; that defeats the purpose of the guard.
"""

import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]

# Recorded 2026-10-27, right after user_data/config.dryrun.json was reverted
# to its safe defaults (api_server disabled, loopback bind, blank credentials)
# and the initial git commit was made.
PROTECTED_SHA256 = {
    "user_data/strategies/SmaTrendBaseline.py": (
        "0edc921c5e0b507dcf7b9128aeebb54e624d68d6e4f5d13e8874218e6fadebcc"
    ),
    "user_data/strategies/DonchianBreakoutBaseline.py": (
        "2eca97e49b1a0b048dd35ac1aec5be7155b8f390f7ee32f05d1616a42305ce0e"
    ),
    "user_data/strategies/BollingerMeanReversionBaseline.py": (
        "da38ebf7d4db29c44a2a6b1d3f146ac3b07cf5dda2ca6ddcc6478375a873c75a"
    ),
    "user_data/config.dryrun.json": (
        "e7c86f0ba71900e1c0e7ef1169253d3068ae90a8d02dbf1913a3f3e936bb667b"
    ),
    "docker-compose.yml": (
        "3ac6f17b2459a54f3ebf8310b58097987a53972e83cb433af0203d77b2e598a7"
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ProtectedFilesTests(unittest.TestCase):
    def test_protected_files_are_unchanged(self) -> None:
        for relative_path, expected_sha256 in PROTECTED_SHA256.items():
            path = ROOT / relative_path
            with self.subTest(file=relative_path):
                self.assertTrue(path.is_file(), f"missing protected file: {relative_path}")
                actual_sha256 = sha256_file(path)
                self.assertEqual(
                    actual_sha256,
                    expected_sha256,
                    f"{relative_path} changed on disk; protected files must not be edited "
                    "after freezing. If this change is intentional, it requires explicit "
                    "user approval before the recorded hash is updated.",
                )

    def test_every_protected_file_exists(self) -> None:
        for relative_path in PROTECTED_SHA256:
            self.assertTrue((ROOT / relative_path).is_file(), relative_path)


if __name__ == "__main__":
    unittest.main()
