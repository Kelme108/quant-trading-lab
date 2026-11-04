import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


def docker_ready() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        return subprocess.run(["docker", "image", "inspect", "freqtradeorg/freqtrade:2026.9"],
                              capture_output=True, timeout=60).returncode == 0
    except Exception:
        return False


@unittest.skipUnless(docker_ready() and (ROOT / "user_data" / "data" / "binance" / "BTC_USDT-1d.feather").exists(),
                     "needs Docker, the Freqtrade image and the BTC data")
class RegimeInformativeContainerTest(unittest.TestCase):
    def test_regime_merged_into_the_execution_timeframe_uses_closed_days_only(self):
        env = {**os.environ, "MSYS_NO_PATHCONV": "1"}
        result = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint", "python",
             "-v", f"{ROOT / 'user_data'}:/freqtrade/user_data",
             "-v", f"{ROOT / 'research' / 'tools'}:/chk:ro",
             "-e", "PYTHONPATH=/chk:/freqtrade/user_data/strategies",
             "freqtradeorg/freqtrade:2026.9", "/chk/check_regime_informative.py"],
            capture_output=True, text=True, timeout=900, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count(" OK"), 4, result.stdout)


if __name__ == "__main__":
    unittest.main()
