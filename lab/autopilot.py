"""Autopilot: the owner's standing policy that lets an exploration candidate reach DRY-RUN without a per-hypothesis
approval. It never reaches real money.

Policy (lab/config/autopilot.json, written by the owner, never by an agent):
  - a hypothesis that is `candidate_for_portfolio` on every pair in exploration gets its single validation read,
    at the exposure calibrated on exploration (nothing is tuned);
  - every pair whose validation decision is `candidate_for_portfolio` gets a dry-run bot: per-pair overlay,
    its own compose file, a freeze by hash, and `docker compose up -d`;
  - pairs that were rejected or inconclusive get nothing; a calibrated stake below the exchange minimum gets nothing.

Each step is recorded as an approval by `autopilot-policy` (with the policy's owner and date in the note), so the
ledger shows that a policy, not a person, approved it. Real money stays behind every lock in docs/runbook-ao-vivo.md:
the overlays written here never touch `dry_run`, the base config (protected) keeps `dry_run: true`, and a policy file
whose `real_money` is anything but false is refused.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from lab import experiment, forward, orchestrator, registry, runner

ROOT = Path(__file__).parents[1]
POLICY_PATH = ROOT / "lab" / "config" / "autopilot.json"
ACTOR = "autopilot-policy"
CANDIDATE = "candidate_for_portfolio"


class PolicyError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_policy(path: Path = POLICY_PATH) -> dict:
    policy = json.loads(path.read_text(encoding="utf-8"))
    if policy.get("real_money") is not False:
        raise PolicyError("autopilot.json: real_money must be false; the autopilot never trades real money")
    for key in ("enabled", "auto_validation", "auto_dryrun"):
        if not isinstance(policy.get(key), bool):
            raise PolicyError(f"autopilot.json: '{key}' must be true or false")
    return policy


def calibrated_exposure(conn, hypothesis_id: str) -> float | None:
    """The exposure lab/calibrate.py recorded in the notes ('Calibrated exposure: 0.2 ...'); the last one wins."""
    row = registry.get_hypothesis(conn, hypothesis_id)
    found = re.findall(r"Calibrated exposure: ([0-9]*\.?[0-9]+)", str(row["notes"] or "")) if row else []
    return float(found[-1]) if found else None


def exploration_passed(conn, hypothesis_id: str, pairs: list[str]) -> bool:
    latest = {r["pair"]: r["decision"] for r in registry.list_latest_decisions(conn)
              if r["hypothesis_id"] == hypothesis_id and r["split"] == "exploration"}
    return all(latest.get(p) == CANDIDATE for p in pairs)


def validation_status(decisions: dict[str, str]) -> str:
    values = set(decisions.values())
    if values == {CANDIDATE}:
        return "validation: candidate"
    if "rejected" in values or "inconclusive" in values:
        return "not approved at validation"
    return "validation: mixed"


def read_validation(conn, hypothesis_id: str, exposure: float, *, root: Path = ROOT, pairs: list[str] | None = None,
                    run_experiment=experiment.run_experiment, decide=experiment.decide_experiment,
                    version: str | None = None) -> dict[str, str]:
    """The single validation read (shared by research/tools/validate_once.py). {pair: decision}.

    Refuses unless exploration is a candidate on every pair, a `validation` approval is recorded, and the
    validation split was never read for this hypothesis."""
    pairs = pairs or runner.enabled_pairs()
    if not exploration_passed(conn, hypothesis_id, pairs):
        raise PolicyError(f"{hypothesis_id}: exploration is not a candidate on every pair; validation not read")
    if not registry.has_approval(conn, hypothesis_id, "validation"):
        raise PolicyError(f"{hypothesis_id}: no validation approval is recorded")
    if registry.latest_experiments(conn, hypothesis_id, "validation"):
        raise PolicyError(f"{hypothesis_id}: the validation split was already read; it is never read twice")
    strategy = forward.find_strategy(hypothesis_id, root)
    name, strategy_file = strategy.stem, str(strategy.relative_to(root)).replace("\\", "/")
    timeframe = orchestrator.strategy_timeframe(strategy)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    splits, version = runner.load_splits(), version or experiment.freqtrade_version()
    decisions = {}
    for pair in pairs:
        experiment_id = run_experiment(
            conn, hypothesis_id=hypothesis_id, strategy_name=name, strategy_file=strategy_file, pair=pair,
            split_name="validation", timestamp=stamp, splits=splits, version=version,
            notes=f"single validation read, exposure {exposure} (calibrated on exploration)",
            exposure=exposure, timeframe=timeframe,
        )
        decisions[pair], _ = decide(conn, experiment_id, hypothesis_id)
    registry.set_hypothesis_status(conn, hypothesis_id, validation_status(decisions))
    return decisions


# -- dry-run files -------------------------------------------------------------------------------------------------

KEY_OF = {pair: key for key, pair in forward.PAIR_KEYS.items()}


def compose_name(hypothesis_id: str) -> str:
    return f"docker-compose.forward.{forward.tag(hypothesis_id)}.yml"


def write_forward_files(hypothesis_id: str, pairs: list[str], exposure: float, strategy_class: str,
                        root: Path = ROOT, image: str = "freqtradeorg/freqtrade:2026.9") -> list[str]:
    """Per-pair overlays and the hypothesis' own compose file, in the shape of the H-016 ones. Returns the paths."""
    tag = forward.tag(hypothesis_id)
    written = []
    services = []
    for pair in pairs:
        key = KEY_OF[pair]
        overlay = {
            "bot_name": f"forward-{tag}-{key}",
            "strategy": strategy_class,
            "db_url": f"sqlite:///{forward.database_path(hypothesis_id, key)}",
            "tradable_balance_ratio": exposure,
            "exchange": {"pair_whitelist": [pair]},
        }
        path = root / forward.overlay_path(hypothesis_id, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(overlay, indent=2) + "\n", encoding="utf-8")
        written.append(forward.overlay_path(hypothesis_id, key))
        services.append(
            f"  forward-{tag}-{key}:\n"
            f"    image: {image}\n"
            f"    restart: \"no\"\n"
            f"    container_name: forward-{tag}-{key}\n"
            f"    volumes:\n"
            f"      - \"./user_data:/freqtrade/user_data\"\n"
            f"      - \"./forward:/freqtrade/forward:ro\"\n"
            f"    command: >-\n"
            f"      trade --config /freqtrade/user_data/config.dryrun.json --config /freqtrade/forward/config.{tag}.{key}.json\n"
            f"      --strategy-path /freqtrade/user_data/strategies --logfile /freqtrade/user_data/logs/forward-{tag}-{key}.log\n"
        )
    header = (
        f"# Dry-run evidence collection for {hypothesis_id} ({strategy_class}), written by the autopilot policy\n"
        f"# (lab/autopilot.py, lab/config/autopilot.json) on the pairs whose single validation read was a candidate:\n"
        f"# {', '.join(pairs)}. Exposure {exposure} is the one calibrated on exploration. Same rules as\n"
        f"# docker-compose.forward.yml: base config first, the overlay changes only bot name, strategy, database,\n"
        f"# exposure and pair. No API server, no exchange keys, no real money.\n"
        f"# Check the freeze first:  python research/tools/forward_freeze.py {hypothesis_id} --check\n"
        f"name: trading-lab-forward-{tag}\n\nservices:\n"
    )
    (root / compose_name(hypothesis_id)).write_text(header + "".join(services), encoding="utf-8")
    written.append(compose_name(hypothesis_id))
    return written


def running_forward_bots(root: Path = ROOT) -> int:
    """Bots already frozen for dry-run (one per pair in every freeze record)."""
    total = 0
    for path in sorted((root / "research" / "forward").glob("H-*-freeze.json")):
        total += len(json.loads(path.read_text(encoding="utf-8")).get("databases", {}))
    return total


def start_bots(compose: str, root: Path = ROOT) -> tuple[bool, str]:
    done = subprocess.run(["docker", "compose", "-f", compose, "up", "-d"], cwd=root, capture_output=True, text=True)
    return done.returncode == 0, (done.stdout + done.stderr)[-400:]


def freeze(conn, hypothesis_id: str, root: Path = ROOT) -> dict:
    path = forward.freeze_path(hypothesis_id, root)
    if path.exists():
        raise PolicyError(f"{hypothesis_id}: already frozen; a change is a new hypothesis")
    frozen = forward.build_freeze(hypothesis_id, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(frozen, indent=2, ensure_ascii=False), encoding="utf-8")
    conn.execute("UPDATE hypotheses SET notes = COALESCE(notes, '') || ' ' || ? WHERE id = ?", (
        f"[Frozen for dry-run by the autopilot policy {frozen['frozen_at_utc']}, commit {frozen['git_commit'][:10]}, "
        f"strategy sha256 {frozen['strategy']['sha256'][:12]}; {forward.LABEL}]", hypothesis_id))
    conn.commit()
    return frozen


# -- the policy run ------------------------------------------------------------------------------------------------

def run(conn, hypothesis_id: str, *, commit: Callable[[list[str], str], None], root: Path = ROOT,
        policy: dict | None = None, read: Callable = read_validation, start: Callable = start_bots,
        pairs: list[str] | None = None) -> dict:
    """Apply the policy to one exploration candidate. {'outcome', 'detail', 'pairs'}; never raises for a policy
    refusal (it is reported), only for a broken repository."""
    policy = policy if policy is not None else load_policy(root / "lab" / "config" / "autopilot.json")
    if policy.get("real_money") is not False:
        raise PolicyError("real_money must be false")
    result = {"outcome": "candidate: awaiting the user's approval to read the validation", "detail": "", "pairs": []}
    if not (policy["enabled"] and policy["auto_validation"]):
        result["detail"] = "autopilot off"
        return result
    pairs = pairs or runner.enabled_pairs()
    note = f"standing policy of {policy.get('approved_by', '?')} ({policy.get('approved_at_utc', '?')}): {policy.get('note', '')}"[:300]

    exposure = calibrated_exposure(conn, hypothesis_id)
    if exposure is None:
        result["detail"] = "autopilot: no calibrated exposure in the notes"
        return result
    registry.add_approval(conn, hypothesis_id=hypothesis_id, stage="validation", approved_by=ACTOR, note=note,
                          created_at_utc=_now())
    decisions = read(conn, hypothesis_id, exposure, root=root, pairs=pairs)
    passed = [p for p in pairs if decisions.get(p) == CANDIDATE]
    summary = ", ".join(f"{p.split('/')[0]} {d}" for p, d in decisions.items())
    if not passed:
        result.update(outcome="validation read by the autopilot: no pair passed", detail=summary)
        return result
    result["pairs"] = passed
    if not policy["auto_dryrun"]:
        result.update(outcome=f"validation passed on {', '.join(passed)}; dry-run waits for the user", detail=summary)
        return result
    min_stake = float(policy.get("min_stake_quote", 10.0))
    wallet = float(policy.get("wallet_quote", 100.0))
    if exposure * wallet < min_stake:
        result.update(outcome=f"validation passed on {', '.join(passed)}; no dry-run (stake {exposure * wallet:g} "
                              f"below the minimum order {min_stake:g})", detail=summary)
        return result
    cap = int(policy.get("max_forward_bots", 12))
    if running_forward_bots(root) + len(passed) > cap:
        result.update(outcome=f"validation passed on {', '.join(passed)}; no dry-run (the {cap}-bot cap would be "
                              f"exceeded: ask the user)", detail=summary)
        return result

    registry.add_approval(conn, hypothesis_id=hypothesis_id, stage="dryrun", approved_by=ACTOR,
                          note=f"{note}; pairs {', '.join(passed)}"[:300], created_at_utc=_now())
    strategy = forward.find_strategy(hypothesis_id, root)
    files = write_forward_files(hypothesis_id, passed, exposure, strategy.stem, root)
    commit(files + [str(strategy.relative_to(root)).replace("\\", "/")],
           f"forward({hypothesis_id}): dry-run files written by the autopilot policy ({', '.join(passed)})")
    frozen = freeze(conn, hypothesis_id, root)
    registry.sync_ledger_markdown(conn, root / "research" / "hypothesis-ledger.md")
    registry.dump_sql(conn, root / "research" / "registry-dump.sql")
    commit([str(forward.freeze_path(hypothesis_id, root).relative_to(root)).replace("\\", "/"),
            "research/hypothesis-ledger.md", "research/registry-dump.sql"],
           f"forward({hypothesis_id}): freeze by the autopilot policy")
    problems = forward.check_freeze(hypothesis_id, root)
    if problems:
        result.update(outcome="dry-run frozen but NOT started: freeze check failed", detail="; ".join(problems)[:300])
        return result
    ok, output = start(compose_name(hypothesis_id), root)
    started = "started" if ok else "NOT started (docker failed: start it by hand)"
    result.update(outcome=f"dry-run {started} on {', '.join(passed)} by the autopilot",
                  detail=f"{summary}; exposure {exposure}; strategy sha256 {frozen['strategy']['sha256'][:12]}"
                         + ("" if ok else f"; {output[-160:]}"))
    return result
