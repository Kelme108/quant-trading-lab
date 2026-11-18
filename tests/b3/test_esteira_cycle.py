"""Conveyor cycle (b3/esteira_cycle.py): limits, ids and the checks of an agent's file. No market data."""

from __future__ import annotations

from datetime import datetime, timezone

from b3 import esteira as es
from b3 import esteira_cycle as cy

TODAY = datetime.now(timezone.utc).isoformat(timespec="seconds")   # now, so it is today in Sao Paulo too
CFG = {"limits": {"max_families_per_day": 40, "max_agent_cost_usd_per_day": 15.0}}


def test_the_assistant_batch_passes_the_static_check():
    src = (es.FAMILY_DIR / "e001_batch1.py").read_text(encoding="utf-8")
    assert cy.static_problems(src) == []


def test_static_check_refuses_files_network_and_dunder():
    bad = {
        "import os\n": "import os",
        "from pathlib import Path\n": "from pathlib",
        "x = open('a')\n": "name open",
        "import numpy as np\nnp.load('a')\n": "attribute load",
        "import pandas as pd\npd.read_csv('a')\n": "attribute read_csv",
        "y = (1).__class__\n": "attribute __class__",
        "from b3.esteira import Ctx\n": "only Family",
        "from b3.costs import x\n": "from b3.costs",
        "def f(:\n": "syntax error",
    }
    for src, expected in bad.items():
        probs = cy.static_problems(src)
        assert any(expected in p for p in probs), (src, probs)
    assert cy.static_problems("import numpy as np\nimport math\nfrom b3.esteira import Family\nz = np.zeros(3).sum()\n") == []


def test_room_stops_on_the_family_and_cost_limits():
    done = {f"E-{i:03d}": {"screened_at_utc": TODAY} for i in range(30)}
    k, why = cy.room(CFG, done=done, rows=[])
    assert k == 10 and why == []
    done |= {f"E-{i:03d}": {"screened_at_utc": TODAY} for i in range(30, 37)}
    k, why = cy.room(CFG, done=done, rows=[])
    assert k == 0 and "family limit" in why[0]
    rows = [{"event": "agent", "at_utc": TODAY, "cost_usd": 12.5}]
    k, why = cy.room(CFG, done={}, rows=rows)
    assert k == 0 and "agent cost" in why[0]
    old = [{"event": "agent", "at_utc": "2020-01-01T03:00:00+00:00", "cost_usd": 99.0}]
    assert cy.room(CFG, done={}, rows=old)[0] == 10


def test_precheck_rejects_a_peeking_family_and_keeps_a_causal_one(tmp_path, monkeypatch):
    src = '''
from __future__ import annotations
import numpy as np
from b3.esteira import Family

def _ok(ctx, p):
    return np.nan_to_num(np.sign(ctx.c - ctx.prev(ctx.c, p["n"]))).astype(int)

def _peek(ctx, p):
    nxt = np.r_[ctx.c[1:], ctx.c[-1]]
    return np.sign(nxt - ctx.c).astype(int)

FAMILIES = [
    Family("E-901", "ok", "h", {"n": [2, 3]}, _ok, author="agent"),
    Family("E-902", "peek", "h", {"n": [1]}, _peek, author="agent"),
]
'''
    f = tmp_path / "b099_agent.py"
    f.write_text(src, encoding="utf-8")
    monkeypatch.setattr(es, "FAMILY_DIR", tmp_path)
    res = cy.precheck(f, ["E-901", "E-902"])
    assert res["file"] == []
    assert res["families"]["E-901"] == []
    assert res["families"]["E-902"] and res["families"]["E-902"][0].startswith("look-ahead")
    res = cy.precheck(f, ["E-901", "E-902", "E-903"])
    assert any("differ" in p for p in res["file"])


def test_usage_limit_is_recognised_and_never_pauses(tmp_path, monkeypatch):
    from b3 import esteira_cycle as cy
    assert cy.is_usage_limit("You've hit your 5-hour limit · resets 3:40pm (America/Sao_Paulo)")
    assert not cy.is_usage_limit("SyntaxError: invalid syntax")
    monkeypatch.setattr(cy, "STOP_FILE", tmp_path / "STOP")
    monkeypatch.setattr(cy, "LOCK", tmp_path / "lock")
    monkeypatch.setattr(cy, "log", lambda *a, **k: None)

    def boom():
        raise cy.UsageLimit("You've hit your 5-hour limit")
    monkeypatch.setattr(cy, "cycle", boom)
    for _ in range(3):
        assert cy.main(["cycle", "--max", "1"]) == 0
    assert not (tmp_path / "STOP").exists()
