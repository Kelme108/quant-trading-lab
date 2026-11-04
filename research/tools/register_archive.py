"""One-off: record the step 0.2 archive in the registry (no decision or status is changed)."""
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from lab import registry  # noqa: E402
from rerun_archived import manifest_hashes, sha256_file  # noqa: E402

ARCHIVED = {
    "H-005": "VolatilitySqueezeBreakout_H005_v1",
    "H-007": "RisingTrendBreakoutGate_H007_v1",
    "H-008": "VolatilitySqueezeBreakout_H008_v1",
    "H-010": "UptrendPullbackRecovery_H010_v1",
    "H-011": "TripleBottomReversal_H011_v1",
    "H-012": "EMASnapbackATR_H012_v1",
    "H-013": "TripleBottomReversal_H013_v1",
    "H-014": "EMASnapbackATR_H014_v1",
    "H-015": "TimeSeriesMomentum_H015_v1",
    "H-016": "TimeSeriesMomentum_H016_v1",
}


def main() -> None:
    conn = registry.connect()
    now = datetime.now(timezone.utc).isoformat()
    existing = {r["hypothesis_id"] for r in registry.list_archived_strategies(conn)}
    for hyp, cls in ARCHIVED.items():
        if hyp in existing:
            continue
        path = ROOT / "user_data" / "strategies" / "_archive" / f"{cls}.py"
        sha = sha256_file(path)
        recorded = manifest_hashes(cls)
        if recorded and recorded != {sha}:
            raise SystemExit(f"{hyp}: manifest sha {recorded} != file {sha}")
        registry.add_archived_strategy(
            conn, hypothesis_id=hyp, strategy_class=cls,
            original_path=f"user_data/strategies/{cls}.py",
            archive_path=f"user_data/strategies/_archive/{cls}.py",
            strategy_sha256=sha, sha256_source="manifest" if recorded else "file_at_archive_time",
            archived_at_utc=now,
        )
        print(hyp, cls, sha[:12], "manifest" if recorded else "file_at_archive_time")
    registry.sync_ledger_markdown(conn)
    registry.dump_sql(conn)


if __name__ == "__main__":
    main()
