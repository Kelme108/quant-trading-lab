# Checklist de prontidão para operação real

Gerado a partir da auditoria de 2026-11-02. Nada aqui autoriza operação real: o laboratório continua em `dry_run` e só o usuário decide cada passo. Marque um item apenas com evidência registrada (arquivo, hash ou decisão no registry).

## A. Decisões do usuário (bloqueiam o resto)

- [ ] Arquitetura de risco: como conciliar saldo inteiro por trade com o gate de drawdown de 25% (gate maior, fração fixa via config, ou stop de portfólio).
- [ ] Aprovar e congelar `lab/config/gates.json` (hoje `PROPOSED`).
- [ ] Aprovar e congelar `lab/config/portfolio.json` e `lab/config/budget.json`.
- [ ] Medir e registrar as taxas reais da conta (tier, desconto em BNB) e rever os cenários de custo.
- [ ] Confirmar situação regulatória e fiscal para residente no Brasil (Binance, IN 1888, ganho de capital).

## B. Pesquisa e validação estatística

- [x] Motor de backtest conferido contra simulador independente (H-001; `research/engine-crosscheck-2026-11-02.md`).
- [x] Gate de drawdown passou a usar o drawdown relativo (pico a vale).

- [x] Reavaliar H-001 e as baselines no harness corrigido (stake `unlimited`).
- [ ] Investigar o sinal de lookahead da H-007 (lógica não reproduz o viés localmente; falta resolver no analisador) em BNB/USDT e o salto de preço de 23,5% nos dados da BNB.
- [ ] Pelo menos uma hipótese com `candidate_for_portfolio` na exploração, nos 3 pares.
- [ ] A mesma hipótese em `candidate_for_portfolio` na validação, nos 3 pares.
- [ ] Bootstrap de blocos / Monte Carlo (ferramenta pronta em `lab/bootstrap.py`; falta rodar numa candidata, H-005/H-007 deram P95 de 51% a 76%).
- [ ] Sensibilidade de parâmetros na vizinhança do valor escolhido.
- [ ] Walk-forward e leave-one-pair-out.
- [ ] Comparação com buy-and-hold e com uma baseline simples.
- [ ] Preencher `docker_image_digest` e `ccxt_version` nos manifestos (código pronto e testado com mock; falta confirmar num experimento real).

## C. Forward test (dry-run)

- [ ] Rodar `trade` em dry-run por 4 a 8 semanas ou mais, com a estratégia congelada (hash registrado).
- [ ] Comparar trades do dry-run com o que o backtest teria feito no mesmo período.
- [ ] Medir fills de ordem limit vs market e o slippage observado.
- [ ] Testes de falha: queda do bot, reinício, perda de conexão, ordem rejeitada, saldo insuficiente, `min_notional` e filtros de lote.

## D. Infraestrutura de produção

- [ ] Servidor 24/7 (não o PC com WSL), relógio sincronizado, logs com rotação, backup do DB.
- [ ] `stoploss_on_exchange` ligado e testado.
- [ ] `protections` de portfólio (`StoplossGuard`, `MaxDrawdown`) e limite de perda diária.
- [ ] Alertas (Telegram ou equivalente) e kill switch documentado.
- [ ] Chave de API sem permissão de saque, restrita por IP, fora do repositório (variável de ambiente ou secret).
- [x] Gabarito inerte em `docs/config.production.example.json`, com teste. Falta a config real, protegida por hash, depois das decisões do bloco A.

## E. Final test e piloto

- [ ] Dados futuros suficientes após 2026-10-21 (hoje cerca de 9 dias).
- [ ] Uma única leitura do final test, com tudo congelado (`final_test_unlocked`, só o usuário altera).
- [ ] Piloto com valor mínimo e critério de parada definido antes (perda máxima e desvio vs. dry-run).
- [ ] Regra de escala por escrito antes de aumentar capital.
