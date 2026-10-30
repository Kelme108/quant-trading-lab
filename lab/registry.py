"""SQLite registry: the single source of truth for hypotheses, experiments,
metrics, and decisions.

research/hypothesis-ledger.md is synchronized FROM this database (see
sync_ledger_markdown below); the database is authoritative, the Markdown
file is a human-readable export. Never hand-edit the ledger to add a row
that bypasses the database.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).parents[1] / "research" / "lab.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS hypotheses (
    id TEXT PRIMARY KEY,                 -- e.g. "H-004"
    family TEXT NOT NULL,
    ex_ante_rule TEXT NOT NULL,
    proposed_at_utc TEXT NOT NULL,
    data_visible_at_proposal TEXT NOT NULL,  -- what data window was visible when the rule was fixed
    status TEXT NOT NULL,                -- e.g. "proposed", "frozen reference", "candidate", "rejected"
    notes TEXT
);

CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,                 -- experiment id, e.g. "2026-10-27-donchian-h002-explore"
    hypothesis_id TEXT NOT NULL REFERENCES hypotheses(id),
    strategy_file TEXT NOT NULL,
    strategy_sha256 TEXT NOT NULL,
    cost_scenario TEXT NOT NULL,         -- optimistic | base | conservative | stress
    pair TEXT NOT NULL DEFAULT 'BTC/USDT',
    split TEXT NOT NULL,                 -- exploration | validation | final_test
    command TEXT NOT NULL,               -- exact argv, space-joined, for the record
    artifact_path TEXT,
    status TEXT NOT NULL,                -- pending | running | completed | failed
    created_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT NOT NULL REFERENCES experiments(id),
    name TEXT NOT NULL,
    value REAL,
    text_value TEXT,                     -- for non-numeric metrics (e.g. has_bias, notes)
    UNIQUE(experiment_id, name)
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL,
    hypothesis_id TEXT,
    purpose TEXT NOT NULL,
    status TEXT NOT NULL,                -- completed | failed | guard_violation
    cost_usd REAL,
    num_turns INTEGER,
    duration_s REAL,
    session_id TEXT,
    result_excerpt TEXT,
    started_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT NOT NULL REFERENCES experiments(id),
    decision TEXT NOT NULL,              -- rejected | inconclusive | candidate_for_portfolio
    reasons_json TEXT NOT NULL,
    gates_sha256 TEXT NOT NULL,
    decided_at_utc TEXT NOT NULL
);
"""


def connect(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Bring a database created by an older schema up to date.

    CREATE TABLE IF NOT EXISTS leaves an existing table untouched, so columns
    added later must be added here. Rows that predate a column get its
    DEFAULT, which for `pair` is the only pair the lab used before multi-pair
    support (BTC/USDT).
    """
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(experiments)")}
    if "pair" not in columns:
        conn.execute(
            "ALTER TABLE experiments ADD COLUMN pair TEXT NOT NULL DEFAULT 'BTC/USDT'"
        )
        conn.commit()


# --- hypotheses -----------------------------------------------------------

def add_hypothesis(
    conn: sqlite3.Connection,
    *,
    hypothesis_id: str,
    family: str,
    ex_ante_rule: str,
    proposed_at_utc: str,
    data_visible_at_proposal: str,
    status: str = "proposed",
    notes: str = "",
) -> None:
    conn.execute(
        "INSERT INTO hypotheses ("
        "  id, family, ex_ante_rule, proposed_at_utc, data_visible_at_proposal, status, notes"
        ") VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            hypothesis_id,
            family,
            ex_ante_rule,
            proposed_at_utc,
            data_visible_at_proposal,
            status,
            notes,
        ),
    )
    conn.commit()


def set_hypothesis_status(conn: sqlite3.Connection, hypothesis_id: str, status: str) -> None:
    conn.execute("UPDATE hypotheses SET status = ? WHERE id = ?", (status, hypothesis_id))
    conn.commit()


def get_hypothesis(conn: sqlite3.Connection, hypothesis_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM hypotheses WHERE id = ?", (hypothesis_id,)
    ).fetchone()


def count_variants_in_family(conn: sqlite3.Connection, family: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM hypotheses WHERE family = ?", (family,)
    ).fetchone()
    return int(row["n"])


def count_prior_variants(conn: sqlite3.Connection, hypothesis_id: str) -> int:
    """Hypotheses in the same family registered BEFORE `hypothesis_id`.

    This is the `variants_tested_in_family` input to gates.decide(): the
    multiple-testing penalty counts what was already tried, not the
    hypothesis being judged. Registration order (rowid) is the order of
    testing, because a hypothesis is registered before its first test.
    """
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM hypotheses "
        "WHERE family = (SELECT family FROM hypotheses WHERE id = ?) "
        "AND rowid < (SELECT rowid FROM hypotheses WHERE id = ?)",
        (hypothesis_id, hypothesis_id),
    ).fetchone()
    return int(row["n"])


def next_hypothesis_id(conn: sqlite3.Connection) -> str:
    rows = conn.execute("SELECT id FROM hypotheses").fetchall()
    max_n = 0
    for row in rows:
        try:
            n = int(row["id"].split("-")[1])
        except (IndexError, ValueError):
            continue
        max_n = max(max_n, n)
    return f"H-{max_n + 1:03d}"


# --- experiments ------------------------------------------------------------

def add_experiment(
    conn: sqlite3.Connection,
    *,
    experiment_id: str,
    hypothesis_id: str,
    strategy_file: str,
    strategy_sha256: str,
    cost_scenario: str,
    split: str,
    command: str,
    created_at_utc: str,
    artifact_path: str | None = None,
    status: str = "pending",
    pair: str = "BTC/USDT",
) -> None:
    conn.execute(
        "INSERT INTO experiments ("
        "  id, hypothesis_id, strategy_file, strategy_sha256, cost_scenario, pair, split,"
        "  command, artifact_path, status, created_at_utc"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            experiment_id,
            hypothesis_id,
            strategy_file,
            strategy_sha256,
            cost_scenario,
            pair,
            split,
            command,
            artifact_path,
            status,
            created_at_utc,
        ),
    )
    conn.commit()


def set_experiment_status(
    conn: sqlite3.Connection,
    experiment_id: str,
    status: str,
    artifact_path: str | None = None,
) -> None:
    if artifact_path is not None:
        conn.execute(
            "UPDATE experiments SET status = ?, artifact_path = ? WHERE id = ?",
            (status, artifact_path, experiment_id),
        )
    else:
        conn.execute(
            "UPDATE experiments SET status = ? WHERE id = ?", (status, experiment_id)
        )
    conn.commit()


def get_experiment(conn: sqlite3.Connection, experiment_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM experiments WHERE id = ?", (experiment_id,)
    ).fetchone()


def latest_experiments(
    conn: sqlite3.Connection, hypothesis_id: str, split: str
) -> dict[str, sqlite3.Row]:
    """The latest completed experiment per pair for a hypothesis and split."""
    rows = conn.execute(
        "SELECT * FROM experiments WHERE hypothesis_id = ? AND split = ? AND status = 'completed' "
        "ORDER BY created_at_utc, rowid",
        (hypothesis_id, split),
    ).fetchall()
    return {row["pair"]: row for row in rows}


def list_experiments_for_hypothesis(
    conn: sqlite3.Connection, hypothesis_id: str
) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM experiments WHERE hypothesis_id = ? ORDER BY created_at_utc",
        (hypothesis_id,),
    ).fetchall()


# --- metrics ----------------------------------------------------------------

def record_metric(
    conn: sqlite3.Connection,
    experiment_id: str,
    name: str,
    value: float | None = None,
    text_value: str | None = None,
) -> None:
    conn.execute(
        "INSERT INTO metrics (experiment_id, name, value, text_value) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(experiment_id, name) DO UPDATE SET value = excluded.value, "
        "text_value = excluded.text_value",
        (experiment_id, name, value, text_value),
    )
    conn.commit()


def record_metrics(conn: sqlite3.Connection, experiment_id: str, metrics: dict) -> None:
    """Store a dict of metrics; numeric values go in `value`, everything else
    is stringified into `text_value` (JSON-encoded if it's a dict/list/bool)."""
    for name, raw_value in metrics.items():
        if isinstance(raw_value, bool):
            record_metric(conn, experiment_id, name, text_value=json.dumps(raw_value))
        elif isinstance(raw_value, (int, float)):
            record_metric(conn, experiment_id, name, value=float(raw_value))
        elif isinstance(raw_value, (dict, list)):
            record_metric(conn, experiment_id, name, text_value=json.dumps(raw_value))
        elif raw_value is None:
            record_metric(conn, experiment_id, name, value=None, text_value=None)
        else:
            record_metric(conn, experiment_id, name, text_value=str(raw_value))


def get_metrics(conn: sqlite3.Connection, experiment_id: str) -> dict:
    rows = conn.execute(
        "SELECT name, value, text_value FROM metrics WHERE experiment_id = ?",
        (experiment_id,),
    ).fetchall()
    result = {}
    for row in rows:
        if row["value"] is not None:
            result[row["name"]] = row["value"]
        elif row["text_value"] is not None:
            try:
                result[row["name"]] = json.loads(row["text_value"])
            except (json.JSONDecodeError, TypeError):
                result[row["name"]] = row["text_value"]
        else:
            result[row["name"]] = None
    return result


# --- decisions ---------------------------------------------------------------

def record_decision(
    conn: sqlite3.Connection,
    *,
    experiment_id: str,
    decision: str,
    reasons: list[str],
    gates_sha256: str,
    decided_at_utc: str,
) -> None:
    conn.execute(
        "INSERT INTO decisions (experiment_id, decision, reasons_json, gates_sha256, decided_at_utc) "
        "VALUES (?, ?, ?, ?, ?)",
        (experiment_id, decision, json.dumps(reasons), gates_sha256, decided_at_utc),
    )
    conn.commit()


def get_latest_decision(conn: sqlite3.Connection, experiment_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM decisions WHERE experiment_id = ? ORDER BY id DESC LIMIT 1",
        (experiment_id,),
    ).fetchone()


# --- agent runs ----------------------------------------------------------------

def record_agent_run(
    conn: sqlite3.Connection,
    *,
    agent: str,
    purpose: str,
    status: str,
    started_at_utc: str,
    hypothesis_id: str | None = None,
    cost_usd: float | None = None,
    num_turns: int | None = None,
    duration_s: float | None = None,
    session_id: str | None = None,
    result_excerpt: str | None = None,
) -> None:
    conn.execute(
        "INSERT INTO agent_runs (agent, hypothesis_id, purpose, status, cost_usd, num_turns, "
        "duration_s, session_id, result_excerpt, started_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (agent, hypothesis_id, purpose, status, cost_usd, num_turns, duration_s, session_id,
         (result_excerpt or "")[:2000], started_at_utc),
    )
    conn.commit()


def agent_cost_since(conn: sqlite3.Connection, since_utc: str) -> float:
    row = conn.execute(
        "SELECT COALESCE(SUM(cost_usd), 0) AS total FROM agent_runs WHERE started_at_utc >= ?",
        (since_utc,),
    ).fetchone()
    return float(row["total"])


def list_hypotheses(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM hypotheses ORDER BY rowid").fetchall()


def list_latest_decisions(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """One row per experiment that has a decision: its latest one.

    Joined with the hypothesis so a caller (portfolio.py) can group by
    hypothesis, pair and split without issuing a query per experiment.
    """
    return conn.execute(
        "SELECT e.id AS experiment_id, e.hypothesis_id, h.family, e.strategy_file, "
        "       e.pair, e.split, e.artifact_path, d.decision, d.reasons_json, d.decided_at_utc "
        "FROM experiments e "
        "JOIN hypotheses h ON h.id = e.hypothesis_id "
        "JOIN decisions d ON d.experiment_id = e.id "
        "WHERE d.id = (SELECT MAX(id) FROM decisions WHERE experiment_id = e.id) "
        "ORDER BY e.hypothesis_id, e.pair, e.split, e.created_at_utc"
    ).fetchall()


# --- ledger sync -------------------------------------------------------------

LEDGER_PATH = Path(__file__).parents[1] / "research" / "hypothesis-ledger.md"

LEDGER_HEADER = """# Hypothesis ledger

This ledger records research attempts so selection bias remains visible.
It is generated from research/lab.sqlite; the database is the source of
truth. Do not hand-edit the table below, edit the database through
lab/registry.py instead.

| ID | Proposed UTC | Strategy / family | Ex-ante rule | Data visible at proposal | Prior tests | Decision | Notes |
|---|---|---|---|---|---:|---|---|
"""

LEDGER_RULES = """
## Rules

- Add a row before running a new hypothesis.
- Do not edit a rule after observing its result; create a new ID.
- Record rejected and negative hypotheses.
- Count parameter variants and cost scenarios as tests.
- The final test period stays locked until the protocol explicitly permits one read.
"""


def sync_ledger_markdown(conn: sqlite3.Connection, ledger_path: Path = LEDGER_PATH) -> None:
    """Regenerate the Markdown ledger from the database.

    This does not touch H-001/H-002/H-003's original rows unless they were
    themselves imported into the database; it always reflects exactly what
    is in `hypotheses`, nothing more.
    """
    rows = conn.execute(
        "SELECT * FROM hypotheses ORDER BY proposed_at_utc, id"
    ).fetchall()

    lines = [LEDGER_HEADER.rstrip("\n")]
    for row in rows:
        experiment_count = conn.execute(
            "SELECT COUNT(*) AS n FROM experiments WHERE hypothesis_id = ?",
            (row["id"],),
        ).fetchone()["n"]
        lines.append(
            "| {id} | {proposed} | {family} | {rule} | {data_visible} | {tests} | {status} | {notes} |".format(
                id=row["id"],
                proposed=row["proposed_at_utc"],
                family=row["family"],
                rule=row["ex_ante_rule"],
                data_visible=row["data_visible_at_proposal"],
                tests=experiment_count,
                status=row["status"],
                notes=(row["notes"] or "").replace("\n", " "),
            )
        )
    lines.append(LEDGER_RULES.rstrip("\n"))
    ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
