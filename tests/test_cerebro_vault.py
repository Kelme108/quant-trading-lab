"""Guarda do cofre de notas (docs/cerebro/): todo [[link]] resolve, toda nota tem cabeçalho e nada parece segredo.

O cofre vai para o GitHub e é a porta de entrada de quem clona o projeto: um link quebrado ou uma senha esquecida
numa nota não pode passar despercebido.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "docs" / "cerebro"
ARCHIVE = VAULT / "arquivo"          # cópia histórica da memória do Claude: sem links internos garantidos

# padrões que só aparecem em segredo de verdade (nada de falso positivo com a palavra "senha" em prosa)
SECRET_PATTERNS = [
    re.compile(r"(?i)(password|passwd|senha|api[_-]?key|secret|token)[ \t]*[:=][ \t]*[\"']?[A-Za-z0-9/+_\-]{8,}"),
    re.compile(r"\b[\w.+-]+@[\w-]+\.(?:com|org|net|br)\b"),
    re.compile(r"(?i)\b(login|conta|account)\s*[:=#]?\s*\d{6,}"),
    re.compile(r"(?i)C:\\Users\\[^\\\s]+"),
]
ALLOWED_EMAILS = {"noreply@anthropic.com"}
ALLOWED_WHITESPACE = {"\n", "\t", "\r"}


def _notes(include_archive: bool = False) -> list[Path]:
    return [p for p in VAULT.rglob("*.md") if include_archive or ARCHIVE not in p.parents]


def _strip_code(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def test_vault_has_entry_points():
    for name in ("00-LEIA-PRIMEIRO.md", "Regras-inviolaveis.md", "Estado-atual.md", "Como-rodar-em-outro-ambiente.md"):
        assert (VAULT / name).is_file(), f"missing {name}"
    assert (ROOT / "CLAUDE.md").is_file()


def test_every_wikilink_resolves():
    stems = {p.stem for p in VAULT.rglob("*.md")}
    broken = {}
    for p in _notes():
        for m in re.findall(r"\[\[([^\]|#]+)", _strip_code(p.read_text(encoding="utf-8"))):
            if m.strip() not in stems:
                broken.setdefault(str(p.relative_to(ROOT)), set()).add(m.strip())
    assert not broken, f"broken [[links]]: {broken}"


def test_relative_markdown_links_resolve():
    broken = []
    for p in _notes():
        for m in re.findall(r"\]\((?!https?:|mailto:|#)([^)#\s]+)", _strip_code(p.read_text(encoding="utf-8"))):
            if not m.endswith(".md"):
                continue
            if not (p.parent / m).resolve().exists():
                broken.append(f"{p.relative_to(ROOT)} -> {m}")
    assert not broken, f"broken relative links: {broken}"


def test_every_note_has_front_matter_with_date():
    missing = []
    for p in _notes():
        if p.parent.name == "modelos":
            continue
        head = p.read_text(encoding="utf-8").split("\n", 8)
        if head[0].strip() != "---" or not any(line.startswith("atualizado:") or line.startswith("data:") for line in head[1:8]):
            missing.append(str(p.relative_to(ROOT)))
    assert not missing, f"notes without front matter/date: {missing}"


def test_vault_and_entry_files_have_no_secrets():
    files = _notes(include_archive=True) + [ROOT / "CLAUDE.md", ROOT / "CONTRIBUTING.md", ROOT / "live" / ".env.example"]
    hits = []
    for p in files:
        text = p.read_text(encoding="utf-8")
        for pat in SECRET_PATTERNS:
            for m in pat.finditer(text):
                if m.group(0) in ALLOWED_EMAILS:
                    continue
                hits.append(f"{p.relative_to(ROOT)}: {m.group(0)[:60]}")
    assert not hits, "possible secrets/personal data in the vault: " + "; ".join(hits)


def test_notes_have_no_control_characters():
    bad = []
    for p in _notes(include_archive=True):
        text = p.read_text(encoding="utf-8")
        if any(ord(c) < 32 and c not in ALLOWED_WHITESPACE for c in text):
            bad.append(str(p.relative_to(ROOT)))
    assert not bad, f"control characters (usually a lost backslash) in: {bad}"
