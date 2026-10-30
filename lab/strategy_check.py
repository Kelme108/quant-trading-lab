"""Static screen for strategy files written by the developer agent.

A strategy written by an LLM is executed inside the Freqtrade container, which
has network access and the user_data volume mounted read-write. So the file is
screened before it ever runs: an AST allow-list that rejects imports, calls and
attributes that a trading strategy has no reason to use (file and network I/O,
dynamic code, introspection), plus the project's contract (spot, long only,
1h, one IStrategy class named like the file).

This is a screen, not a sandbox. It narrows what generated code can do and
makes a deviation visible; it does not make hostile code safe. The strategy
still only ever runs through `docker compose run` against public candles with
no credentials in the container.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ALLOWED_IMPORT_ROOTS = frozenset(
    {"__future__", "math", "typing", "datetime", "functools", "numpy", "pandas", "talib",
     "freqtrade", "technical"}
)

FORBIDDEN_CALLS = frozenset(
    {"open", "exec", "eval", "compile", "__import__", "input", "globals", "locals", "vars",
     "getattr", "setattr", "delattr", "breakpoint", "exit", "quit"}
)

# File I/O and expression evaluation reachable through pandas / numpy objects.
FORBIDDEN_ATTRS = frozenset(
    {"load", "loads", "save", "savez", "savetxt", "fromfile", "tofile", "memmap",
     "read_csv", "read_pickle", "read_feather", "read_parquet", "read_json", "read_excel",
     "read_sql", "read_html", "read_table", "read_hdf", "to_pickle", "to_csv", "to_feather",
     "to_parquet", "to_json", "to_excel", "to_sql", "to_hdf", "to_clipboard", "eval", "query",
     "system", "popen"}
)

# Methods that would change position sizing or leverage, and so make trades
# incomparable across strategies and cost scenarios.
FORBIDDEN_METHODS = frozenset({"leverage", "custom_stake_amount", "adjust_trade_position"})

FORBIDDEN_STRINGS = ("enter_short", "exit_short")

FILE_STEM = re.compile(r"^[A-Za-z][A-Za-z0-9]*_H(\d{3})_v\d+$")


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _constant(node: ast.AST) -> object:
    return node.value if isinstance(node, ast.Constant) else object()


def check_strategy_source(
    path: Path,
    *,
    expected_hypothesis_id: str | None = None,
    allowed_timeframes: tuple[str, ...] = ("1h",),
) -> list[str]:
    """Violations found in a strategy file; an empty list means it passed."""
    problems: list[str] = []
    stem = path.stem

    match = FILE_STEM.match(stem)
    if not match:
        problems.append(f"file name '{path.name}' must look like <Family>_H<NNN>_v<N>.py")
    elif expected_hypothesis_id is not None and f"H-{match.group(1)}" != expected_hypothesis_id:
        problems.append(
            f"file name says H-{match.group(1)} but the hypothesis being implemented is "
            f"{expected_hypothesis_id}"
        )

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as error:
        return problems + [f"does not parse: {error}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_IMPORT_ROOTS:
                    problems.append(f"line {node.lineno}: import of '{alias.name}' is not allowed")
        elif isinstance(node, ast.ImportFrom):
            if node.level or (node.module or "").split(".")[0] not in ALLOWED_IMPORT_ROOTS:
                problems.append(f"line {node.lineno}: import from '{node.module}' is not allowed")
        elif isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else None
            if name in FORBIDDEN_CALLS:
                problems.append(f"line {node.lineno}: call to '{name}' is not allowed")
        elif isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_ATTRS:
                problems.append(f"line {node.lineno}: attribute '.{node.attr}' is not allowed")
            elif _is_dunder(node.attr):
                problems.append(f"line {node.lineno}: dunder attribute '.{node.attr}' is not allowed")
        elif isinstance(node, ast.Name):
            if _is_dunder(node.id):
                problems.append(f"line {node.lineno}: name '{node.id}' is not allowed")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            for forbidden in FORBIDDEN_STRINGS:
                if forbidden in node.value:
                    problems.append(f"line {node.lineno}: '{forbidden}' (shorting) is not allowed")

    classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and any(
            (isinstance(base, ast.Name) and base.id == "IStrategy")
            or (isinstance(base, ast.Attribute) and base.attr == "IStrategy")
            for base in node.bases
        )
    ]
    if len(classes) != 1:
        problems.append(f"expected exactly one IStrategy subclass, found {len(classes)}")
        return problems

    strategy = classes[0]
    if strategy.name != stem:
        problems.append(f"class '{strategy.name}' must be named like the file ('{stem}')")

    assigned: dict[str, object] = {}
    for statement in strategy.body:
        if isinstance(statement, ast.FunctionDef) and statement.name in FORBIDDEN_METHODS:
            problems.append(f"method '{statement.name}' is not allowed")
        targets: list[ast.expr] = []
        value: ast.AST | None = None
        if isinstance(statement, ast.Assign):
            targets, value = statement.targets, statement.value
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            targets, value = [statement.target], statement.value
        for target in targets:
            if isinstance(target, ast.Name):
                assigned[target.id] = _constant(value)

    if assigned.get("can_short") is not False:
        problems.append("class must set can_short = False (spot, long only)")
    if assigned.get("INTERFACE_VERSION") != 3:
        problems.append("class must set INTERFACE_VERSION = 3")
    if assigned.get("timeframe") not in allowed_timeframes:
        problems.append(f"class must set timeframe to one of {list(allowed_timeframes)}")
    return problems
