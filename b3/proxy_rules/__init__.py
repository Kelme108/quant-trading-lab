"""Registry of the proxy-market rules: P-001..P-007 (b3/strategies/proxies.py) plus one file per later rule in
this package, `p<NNN>_<snake_name>.py`, each with a module constant RULE_ID = "P-<NNN>" and exactly one
ProxyStrategy subclass (screened by b3.strategy_check.check_proxy_rule_source before it is loaded by the
pipeline). A rule file enters only after its proposal is written in research/proxies/proposals/ (ex ante).
"""

from __future__ import annotations

import importlib
import inspect
import re
from pathlib import Path

from b3.markets import ProxyStrategy
from b3.strategies.proxies import RULES as BUILTIN_RULES

HERE = Path(__file__).resolve().parent
FILE = re.compile(r"^p(\d{3})_[a-z0-9_]+$")


def rule_files(folder: Path = HERE) -> list[Path]:
    return sorted(p for p in folder.glob("p*.py") if FILE.match(p.stem))


def load_module_rule(module) -> tuple[str, type[ProxyStrategy]]:
    classes = [c for _, c in inspect.getmembers(module, inspect.isclass)
               if issubclass(c, ProxyStrategy) and c is not ProxyStrategy and c.__module__ == module.__name__]
    if len(classes) != 1:
        raise ValueError(f"{module.__name__}: expected exactly one ProxyStrategy subclass, found {len(classes)}")
    rule_id = getattr(module, "RULE_ID", None)
    m = FILE.match(module.__name__.rsplit(".", 1)[-1])
    if not isinstance(rule_id, str) or not m or rule_id != f"P-{m.group(1)}":
        raise ValueError(f"{module.__name__}: RULE_ID must be 'P-<NNN>' matching the file name")
    return rule_id, classes[0]


def discover() -> dict[str, type[ProxyStrategy]]:
    rules = dict(BUILTIN_RULES)
    for path in rule_files():
        rule_id, cls = load_module_rule(importlib.import_module(f"{__name__}.{path.stem}"))
        if rule_id in rules:
            raise ValueError(f"{rule_id} is registered twice")
        rules[rule_id] = cls
    return dict(sorted(rules.items()))


RULES = discover()
