# Decisões do usuário (Etapa 0 de docs/prompt-execucao-tempo-real.md)

Registradas em 2026-11-04. Só o usuário altera este arquivo.

| Item | Decisão |
|---|---|
| Plataforma | MetaTrader 5 instalado; conta de teste/demo. Corretora e servidor: **a confirmar** com `live/tools/probe_mt5.py` (precisa listar WIN/WDO e ser conta netting) |
| Modalidade | Day-trade, **somente comprado** (sem short, sem overnight) |
| Perda diária máxima | R$ 300 |
| Perda semanal máxima | R$ 900 |
| Contratos máx. por ativo | 2 |
| Operações máx. por dia | 10 |
| Alertas / kill switch | Log + arquivo-sentinela (`live/STOP`); sem Telegram por enquanto |
| Dinheiro real | Bloqueado (Etapa 5). `allow_real=false` |

## Pendências
- Corretora/servidor/tipo de conta (saída do probe).
- Capital hipotético da demo.
- Horário de zeragem antes do fechamento (default proposto: 10 min antes do limite da corretora).

## Verificação da conta (2026-11-04, via senha de investidor, somente leitura)
- Terminal: `C:\Program Files\MetaTrader 5`, build 6295. API Python conecta (`initialize` com `path`, `login`, `password`, `server`).
- Conta de teste no servidor `MetaQuotes-Demo`: demo, **hedging** (`margin_mode=2`), moeda USD, saldo 100.000.
- **Não serve para B3.** Nenhum futuro WIN/WDO: `WIN*` devolve só ações dos EUA (WINA, WING, WINN) e `WDO*` nada; 12.197 símbolos, nenhum de B3. Conta hedging também difere do netting exigido para os futuros.
- Uso restante: testar a conexão, os dados e os `retcode` do adaptador MT5 (Etapa 2) com símbolos de outro mercado. Não valida custos, contratos, tick, vencimentos nem sessão da B3.
- Credenciais nunca vão para o repositório. Apareceram no chat; trocar as senhas se a conta passar a ser usada além do teste.
