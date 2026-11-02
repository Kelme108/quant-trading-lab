import subprocess
import unittest

from lab import experiment


class _Result:
    def __init__(self, stdout: str) -> None:
        self.stdout = stdout


class RuntimeFingerprintTest(unittest.TestCase):
    def test_compose_image_is_pinned(self) -> None:
        self.assertNotIn(":stable", experiment.compose_image())
        self.assertTrue(experiment.compose_image().startswith("freqtradeorg/freqtrade:"))

    def test_reads_digest_and_ccxt_version(self) -> None:
        def fake(argv, **kwargs):
            return _Result("sha256:abc" if argv[1] == "image" else "4.4.1\n")

        result = experiment.runtime_fingerprint(fake)
        self.assertEqual(result, {"docker_image_digest": "sha256:abc", "ccxt_version": "4.4.1"})

    def test_failure_leaves_values_empty_and_does_not_raise(self) -> None:
        def boom(argv, **kwargs):
            raise subprocess.CalledProcessError(1, argv)

        self.assertEqual(experiment.runtime_fingerprint(boom), {"docker_image_digest": "", "ccxt_version": ""})


if __name__ == "__main__":
    unittest.main()
