"""Static screen for B3 strategy files (b3/strategies/), in the spirit of lab/strategy_check.py.

The same AST allow-list (no file or network access, no dynamic code, no introspection), adapted to
the B3 contract: one B3Strategy subclass named like the file, `root`, `name`, `timeframe_min` and
`warmup` as constants, and no backwards-looking violations that are visible statically (negative
shift, centered windows). It is a screen, not a sandbox.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from lab.strategy_check import FORBIDDEN_ATTRS, FORBIDDEN_CALLS, _is_dunder

ALLOWED_IMPORT_ROOTS = frozenset({"__future__", "math", "typing", "datetime", "functools", "numpy", "pandas"})
ALLOWED_FROM_MODULES = frozenset({"b3.strategy", "b3.calendar", "live.core.models"})
FILE_STEM = re.compile(r"^[A-Za-z][A-Za-z0-9]*_B(\d{3})_v\d+$")
ALLOWED_TIMEFRAMES = (1, 5, 15, 30, 60)
MAX_WARMUP = 20_000


def _negative(node: ast.AST) -> bool:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return True
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and node.value < 0


def _screen(tree: ast.AST) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_IMPORT_ROOTS:
                    found.append(f"line {node.lineno}: import of '{alias.name}' is not allowed")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level or (mod not in ALLOWED_FROM_MODULES and mod.split(".")[0] not in ALLOWED_IMPORT_ROOTS):
                found.append(f"line {node.lineno}: import from '{mod}' is not allowed")
        elif isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else None
            if name in FORBIDDEN_CALLS:
                found.append(f"line {node.lineno}: call to '{name}' is not allowed")
            attr = func.attr if isinstance(func, ast.Attribute) else None
            if attr == "shift":
                periods = node.args[:1] + [kw.value for kw in node.keywords if kw.arg == "periods"]
                if any(_negative(a) for a in periods):
                    found.append(f"line {node.lineno}: shift with a negative period looks into the future")
            if attr in ("rolling", "ewm"):
                for kw in node.keywords:
                    if kw.arg == "center" and not (isinstance(kw.value, ast.Constant) and kw.value.value is False):
                        found.append(f"line {node.lineno}: centered windows look into the future")
        elif isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_ATTRS:
                found.append(f"line {node.lineno}: attribute '.{node.attr}' is not allowed")
            elif _is_dunder(node.attr):
                found.append(f"line {node.lineno}: dunder attribute '.{node.attr}' is not allowed")
        elif isinstance(node, ast.Name) and _is_dunder(node.id):
            found.append(f"line {node.lineno}: name '{node.id}' is not allowed")
    return found


def check_b3_strategy_source(path: Path, expected_hypothesis_id: str | None = None) -> list[str]:
    problems: list[str] = []
    m = FILE_STEM.match(path.stem)
    if not m:
        problems.append(f"file name '{path.name}' must look like <Family>_B<NNN>_v<N>.py")
    elif expected_hypothesis_id is not None and f"B-{m.group(1)}" != expected_hypothesis_id:
        problems.append(f"file name says B-{m.group(1)} but the hypothesis is {expected_hypothesis_id}")
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as error:
        return problems + [f"does not parse: {error}"]
    problems += _screen(tree)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)
               and any(isinstance(b, ast.Name) and b.id == "B3Strategy" for b in n.bases)]
    if len(classes) != 1:
        return problems + [f"expected exactly one B3Strategy subclass, found {len(classes)}"]
    cls = classes[0]
    if cls.name != path.stem:
        problems.append(f"class '{cls.name}' must be named like the file ('{path.stem}')")
    consts = {}
    for st in cls.body:
        if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
            consts[st.targets[0].id] = st.value.value if isinstance(st.value, ast.Constant) else object()
    if consts.get("root") not in ("WIN", "WDO"):
        problems.append("class must set root = 'WIN' or 'WDO'")
    if not isinstance(consts.get("name"), str) or not consts.get("name"):
        problems.append("class must set name to a non-empty string")
    if consts.get("timeframe_min") not in ALLOWED_TIMEFRAMES:
        problems.append(f"class must set timeframe_min to one of {list(ALLOWED_TIMEFRAMES)}")
    warmup = consts.get("warmup")
    if not isinstance(warmup, int) or isinstance(warmup, bool) or not 1 <= warmup <= MAX_WARMUP:
        problems.append(f"class must set warmup to an integer constant between 1 and {MAX_WARMUP}")
    if "rules" not in consts:
        problems.append("class must state its own session rules (rules = SessionRules(...))")
    return problems
