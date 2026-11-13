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
# Freqtrade refuses a strategy whose warm-up exceeds 5x the 999 candles Binance serves per request
# (4999 on 1h); H-006 needed 5520 and never ran. Stay clear of that edge with a margin.
MAX_STARTUP_CANDLES = 4500
# Sibling modules in user_data/strategies/ a strategy may import. Nothing else local is allowed.
ALLOWED_LOCAL_MODULES = frozenset({"regime_filter"})
FORBIDDEN_METHODS = frozenset({"leverage", "custom_stake_amount", "adjust_trade_position"})

FORBIDDEN_STRINGS = ("enter_short", "exit_short")

FILE_STEM = re.compile(r"^[A-Za-z][A-Za-z0-9]*_H(\d{3})_v\d+$")


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _constant(node: ast.AST) -> object:
    return node.value if isinstance(node, ast.Constant) else object()


def _screen_tree(tree: ast.AST, *, allow_short: bool = False) -> list[str]:
    """AST allow-list shared by strategy files and the sibling helper modules."""
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in ALLOWED_LOCAL_MODULES and alias.name.split(".")[0] not in ALLOWED_IMPORT_ROOTS:
                    found.append(f"line {node.lineno}: import of '{alias.name}' is not allowed")
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module in ALLOWED_LOCAL_MODULES:
                continue
            if node.level or (node.module or "").split(".")[0] not in ALLOWED_IMPORT_ROOTS:
                found.append(f"line {node.lineno}: import from '{node.module}' is not allowed")
        elif isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else None
            if name in FORBIDDEN_CALLS:
                found.append(f"line {node.lineno}: call to '{name}' is not allowed")
        elif isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_ATTRS:
                found.append(f"line {node.lineno}: attribute '.{node.attr}' is not allowed")
            elif _is_dunder(node.attr):
                found.append(f"line {node.lineno}: dunder attribute '.{node.attr}' is not allowed")
        elif isinstance(node, ast.Name):
            if _is_dunder(node.id):
                found.append(f"line {node.lineno}: name '{node.id}' is not allowed")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            for forbidden in () if allow_short else FORBIDDEN_STRINGS:
                if forbidden in node.value:
                    found.append(f"line {node.lineno}: '{forbidden}' (shorting) is not allowed")
    return found


def check_helper_module_source(path: Path) -> list[str]:
    """Same AST screen for an allowed sibling module (e.g. regime_filter.py): no class contract."""
    if path.stem not in ALLOWED_LOCAL_MODULES:
        return [f"'{path.stem}' is not in ALLOWED_LOCAL_MODULES"]
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as error:
        return [f"does not parse: {error}"]
    problems = _screen_tree(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and any(
            isinstance(b, ast.Name) and b.id == "IStrategy" for b in node.bases
        ):
            problems.append("a helper module must not define an IStrategy class")
    return problems


def check_strategy_source(
    path: Path,
    *,
    expected_hypothesis_id: str | None = None,
    allowed_timeframes: tuple[str, ...] = ("1h",),
    lane: str = "spot",
) -> list[str]:
    """Violations found in a strategy file; an empty list means it passed. In the futures lane (docs/faixa-futuros.md)
    `can_short` may be True and the short signal columns are allowed; `leverage()` stays forbidden, so trades are 1x."""
    allow_short = lane == "futures"
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

    problems += _screen_tree(tree, allow_short=allow_short)

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

    startup = assigned.get("startup_candle_count")
    if not isinstance(startup, int) or isinstance(startup, bool):
        problems.append("class must set startup_candle_count to an integer constant")
    elif startup > MAX_STARTUP_CANDLES:
        problems.append(
            f"startup_candle_count {startup} is above {MAX_STARTUP_CANDLES}: Freqtrade cannot load more "
            "than about 4999 candles of 1h history, so the backtest would never start"
        )
    if allow_short:
        if not isinstance(assigned.get("can_short"), bool):
            problems.append("class must set can_short to True or False (futures lane)")
    elif assigned.get("can_short") is not False:
        problems.append("class must set can_short = False (spot, long only)")
    if assigned.get("INTERFACE_VERSION") != 3:
        problems.append("class must set INTERFACE_VERSION = 3")
    if assigned.get("timeframe") not in allowed_timeframes:
        problems.append(f"class must set timeframe to one of {list(allowed_timeframes)}")
    return problems


# --- warm-up advice (a warning, never a violation) -------------------------------------------

# EMA, RSI (Wilder) and ATR (Wilder) are recursive: the value at a candle depends on all earlier
# history with geometrically decaying weight, so a short warm-up leaves a residual error.
# Rule (step 0.3): startup_candle_count >= WARMUP_FACTOR * P for the largest period P, and never
# below WARMUP_MIN. TA-Lib defaults apply when the period is not given.
RECURSIVE_INDICATORS = {"EMA": 30, "RSI": 14, "ATR": 14}
WARMUP_FACTOR = 3
WARMUP_MIN = 400


def _module_int_constants(tree: ast.Module) -> dict[str, int]:
    constants: dict[str, int] = {}
    for statement in tree.body:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, int)
            and not isinstance(statement.value.value, bool)
        ):
            constants[statement.targets[0].id] = statement.value.value
    return constants


def _period(node: ast.AST | None, constants: dict[str, int]) -> int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    return None


def recursive_indicator_periods(source: str) -> list[tuple[str, int | None, int]]:
    """(indicator, period or None when not a constant, line) for every EMA/RSI/ATR use.

    Recognises `ta.EMA(df, timeperiod=P)` / `EMA(df, P)` (TA-Lib) and `.ewm(span=P)` (pandas).
    Periods given as module-level integer constants are resolved.
    """
    tree = ast.parse(source)
    constants = _module_int_constants(tree)
    found: list[tuple[str, int | None, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else None
        keywords = {kw.arg: kw.value for kw in node.keywords}
        if name in RECURSIVE_INDICATORS:
            expr = keywords.get("timeperiod")
            if expr is None and len(node.args) > 1:
                expr = node.args[1]
            period = RECURSIVE_INDICATORS[name] if expr is None else _period(expr, constants)
            found.append((name, period, node.lineno))
        elif name == "ewm" and "span" in keywords:
            found.append(("ewm(span)", _period(keywords["span"], constants), node.lineno))
    return found


def warmup_warnings(path: Path) -> list[str]:
    """Advice when startup_candle_count is too small for the strategy's recursive indicators."""
    try:
        source = path.read_text(encoding="utf-8")
        uses = recursive_indicator_periods(source)
        tree = ast.parse(source)
    except SyntaxError:
        return []
    if not uses:
        return []
    startup = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for statement in node.body:
                if (
                    isinstance(statement, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "startup_candle_count" for t in statement.targets)
                    and isinstance(statement.value, ast.Constant)
                ):
                    startup = statement.value.value
    warnings = [
        f"line {line}: period of {name} is not a constant; cannot check the warm-up"
        for name, period, line in uses
        if period is None
    ]
    periods = [period for _, period, _ in uses if period is not None]
    if periods and isinstance(startup, int):
        biggest = max(periods)
        needed = max(WARMUP_MIN, WARMUP_FACTOR * biggest)
        if startup < needed:
            names = ", ".join(sorted({f"{n}({p})" for n, p, _ in uses if p is not None}))
            warnings.append(
                f"startup_candle_count {startup} < {needed} (max({WARMUP_MIN}, {WARMUP_FACTOR} x {biggest})) "
                f"for recursive indicators {names}: the first values carry a residual warm-up error"
            )
    return warnings


if __name__ == "__main__":  # python -m lab.strategy_check <file>...
    import sys

    for argument in sys.argv[1:]:
        for message in warmup_warnings(Path(argument)):
            print(f"WARNING {argument}: {message}")
