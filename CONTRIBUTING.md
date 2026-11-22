# Como contribuir

Este projeto pesquisa estratégias de day trade (WIN e WDO da B3) e roda robôs **só em conta demo**. Várias pessoas, e várias sessões do Claude Code, trabalham no mesmo repositório. Estas regras existem para ninguém quebrar a pesquisa dos outros.

## 1. Antes de qualquer coisa

1. Rode `python bootstrap.py` (cria o `.venv` e instala as dependências) e depois `python bootstrap.py --check`.
2. Leia o cofre de notas: [docs/cerebro/00-LEIA-PRIMEIRO.md](docs/cerebro/00-LEIA-PRIMEIRO.md). Ele abre como cofre no Obsidian (pasta `docs/cerebro/`) e também lê direto no GitHub.
3. Leia [docs/cerebro/Regras-inviolaveis.md](docs/cerebro/Regras-inviolaveis.md). Se for usar o Claude Code, o [CLAUDE.md](CLAUDE.md) já aponta para ele.

## 2. Segredos e dados pessoais

- **Nunca** faça commit de senha, chave, número de conta, e-mail, caminho com seu usuário do Windows ou log de sessão. Credenciais ficam em `live/.env` (ignorado pelo git; modelo em `live/.env.example`).
- Robôs da demo **não usam senha**: anexam ao terminal MetaTrader 5 já logado na conta demo.
- **Não há dinheiro real aqui.** `allow_real` fica `false`. Operar na conta real é decisão do dono do projeto, por escrito.
- Dados de mercado, bancos SQLite, logs e estado (`ops/state/`, `live/state/`, `live/journal*.sqlite`) **não vão para o git**. O `.gitignore` já cobre; confira com `git status` antes de `git add`.

## 3. Branches, commits e PRs

- Trabalhe numa branch (`feat/...`, `fix/...`, `docs/...`, `exp/...`) e abra um PR para `main`. Nada de push direto em `main` nem de `--force`.
- Mensagem de commit curta e específica. O histórico usa prefixos como `exp(esteira):`, `feat(live):`, `fix(...)`, `docs(...)`.
- **Faça commit só dos seus arquivos.** Se `git status` mostra coisas que você não mexeu, são de outra pessoa ou sessão: deixe.
- Antes do PR: `python -m pytest tests/b3 tests/live tests/test_cerebro_vault.py -q` e confira o **código de saída** (não filtre com `| tail`). A suíte completa leva uns 10 minutos.

## 4. Regras da pesquisa (valem para todos)

- **Pré-registro antes de ler resultado.** Configs em `b3/config/*.json` marcadas `approved_by_owner` só mudam com aprovação do dono; qualquer mudança vira uma rodada nova, com as variantes contadas de novo.
- **Validação lê-se uma vez por regra e mercado; o teste final está trancado.** Não destrave.
- **Toda variante testada é uma tentativa.** Não rode "só mais uma variação" sem registrar.
- **Demo não é evidência.** Servir para observar, não para aprovar regra.
- **Agentes de IA escrevem texto e código; os portões em código decidem.** Não afrouxe gates (`lab/config/gates.json`, `b3/config/gates_b3.json`) nem splits.
- **Calendário de feriados da B3**: só a partir do Ofício Circular oficial, nunca de memória.

## 5. Quem roda o quê (importante)

- **Um único computador** roda, ao mesmo tempo, a esteira (`TradeInitial-EsteiraCycle`) e os robôs da demo. Se dois rodarem, a evidência duplica e as filas colidem. Combine antes e, ao assumir, avise no PR ou no chat.
- A esteira tem um **guard**: se um arquivo rastreado mudar durante o ciclo, ele derruba o ciclo. Para editar o repositório na máquina que roda a esteira, crie `ops/state/STOP_ESTEIRA`, espere a trava `%TEMP%\trade-initial-esteira-cycle.lock` sumir, edite, e apague o arquivo depois. Em outra máquina isso não se aplica.
- Tarefas agendadas do Windows são do dono da máquina: quem precisar de uma entrega o script `.ps1` em `ops/windows/` e a própria pessoa roda.
- Mudou o motor ao vivo (`live/`)? Robôs em execução só carregam o código novo ao reiniciar. Avise.

## 6. Como manter o cofre de notas

- Uma ideia por nota, em português, com `atualizado:` no topo e `[[links]]`. Decisão nova: copie `docs/cerebro/modelos/modelo-decisao.md` e ligue no `Decisoes-indice`.
- O **código manda**: se uma nota divergir do arquivo, corrija a nota e anote a data.
- `tests/test_cerebro_vault.py` falha se um `[[link]]` quebrar ou se aparecer algo que parece segredo. Rode antes do PR.

## 7. Windows, Linux e macOS

- A pesquisa (`b3/`, `lab/`) e os testes rodam em qualquer sistema. O **MetaTrader 5** (dados da B3 e robôs) só roda no Windows.
- Os scripts `ops/windows/*.cmd` descobrem sozinhos a raiz do repositório e o Python (`.venv` → `C:\Python314` → `python` do PATH).
- Linha cripto (Freqtrade) precisa de Docker; está pausada. Veja `docs/migracao-linux.md`.
