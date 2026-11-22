#!/usr/bin/env python
"""Prepara um clone novo do repositório: ambiente virtual, dependências, pastas locais e um diagnóstico.

    python bootstrap.py              # cria .venv, instala requirements.txt, cria as pastas locais, mostra o diagnóstico
    python bootstrap.py --research   # idem + extras da pesquisa de padrões (requirements-research.txt)
    python bootstrap.py --test       # idem + roda a suíte rápida de sanidade (cofre, B3, motor ao vivo)
    python bootstrap.py --check      # só o diagnóstico (não instala nada)

Não toca em credenciais, não abre o MetaTrader e não envia ordens. O que ele NÃO traz do git (dados de mercado,
bancos, estado de execução) está explicado em docs/cerebro/Como-rodar-em-outro-ambiente.md.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
MIN_PY = (3, 13)
LOCAL_DIRS = ["ops/state", "live/logs", "live/state", "live/commands", "user_data/data", "user_data/data/b3/clear"]
QUICK_TESTS = ["tests/test_cerebro_vault.py", "tests/b3", "tests/live"]


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(cmd: list[str]) -> int:
    print("  $", " ".join(str(c) for c in cmd), flush=True)
    return subprocess.call([str(c) for c in cmd], cwd=ROOT)


def ensure_venv() -> None:
    if sys.version_info < MIN_PY:
        raise SystemExit(f"Python {MIN_PY[0]}.{MIN_PY[1]}+ é necessário (esta é {sys.version.split()[0]}).")
    if not venv_python().exists():
        print(f"Criando {VENV.relative_to(ROOT)} ...")
        venv.EnvBuilder(with_pip=True).create(VENV)


def install(research: bool) -> None:
    req = "requirements-research.txt" if research else "requirements.txt"
    print(f"Instalando {req} ...")
    if run([venv_python(), "-m", "pip", "install", "--upgrade", "pip"]) or run([venv_python(), "-m", "pip", "install", "-r", req]):
        raise SystemExit("Falha ao instalar as dependências (veja a mensagem acima).")


def make_dirs() -> None:
    for d in LOCAL_DIRS:
        (ROOT / d).mkdir(parents=True, exist_ok=True)


def doctor() -> None:
    def has(path: str) -> str:
        return "ok" if (ROOT / path).exists() else "FALTA"

    print("\nDiagnóstico")
    print(f"  Python do sistema ........ {sys.version.split()[0]} (mínimo {MIN_PY[0]}.{MIN_PY[1]})")
    print(f"  .venv .................... {'ok' if venv_python().exists() else 'não criado (rode sem --check)'}")
    print(f"  git ...................... {'ok' if shutil.which('git') else 'FALTA'}")
    print(f"  claude (CLI, p/ agentes) . {'ok' if shutil.which('claude') else 'ausente (só a esteira/pipeline precisam)'}")
    print(f"  docker (linha cripto) .... {'ok' if shutil.which('docker') else 'ausente (só a linha cripto precisa)'}")
    if os.name == "nt":
        mt5 = Path(r"C:\Program Files\Clear Investimentos MT5 Terminal\terminal64.exe").exists()
        print(f"  terminal Clear (MT5) ..... {'encontrado' if mt5 else 'ausente (robôs e dados da B3 precisam dele)'}")
    else:
        print("  MetaTrader 5 ............. só roda no Windows (robôs e dados da B3)")
    b3 = ROOT / "user_data/data/b3/clear"
    print(f"  dados B3 (WIN/WDO) ....... {'ok' if any(b3.glob('*')) else 'ausentes: baixe com o terminal Clear aberto (ver cofre)'}")
    print(f"  cofre de notas ........... {has('docs/cerebro/00-LEIA-PRIMEIRO.md')}")
    print(f"  live/.env ................ {'existe' if (ROOT / 'live/.env').exists() else 'não existe (normal: robôs de demo não usam senha)'}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--research", action="store_true", help="instala também LightGBM/scikit-learn/scipy")
    ap.add_argument("--test", action="store_true", help="roda a suíte rápida de sanidade no fim")
    ap.add_argument("--check", action="store_true", help="só mostra o diagnóstico")
    a = ap.parse_args()
    if not a.check:
        ensure_venv()
        install(a.research)
        make_dirs()
    doctor()
    if a.test and not a.check:
        print("\nRodando a suíte de sanidade (pode levar vários minutos) ...")
        if run([venv_python(), "-m", "pytest", "-q", *QUICK_TESTS]):
            print("\nAlgum teste falhou: leia a saída acima antes de seguir.")
            return 1
    act = r".venv\Scripts\activate" if os.name == "nt" else "source .venv/bin/activate"
    print(f"\nPronto. Ative o ambiente com:  {act}\nDepois leia docs/cerebro/00-LEIA-PRIMEIRO.md (e o CLAUDE.md, se for usar o Claude Code).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
