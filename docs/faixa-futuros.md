# Faixa de futuros perpétuos em dry-run (decisão do dono D2, 13/11/2026)

Especificação pré-registrada, escrita **antes de qualquer backtest de futuros**. Até agora o único backtest de futuros é a conferência da referência congelada SmaTrendBaseline (seção 6), que não é hipótese; nenhuma hipótese foi testada em futuros. Dinheiro real continua bloqueado (`real_money: false`). O spot continua como está.

## 1. O que muda e o que não muda

| Item | Spot (hoje) | Faixa de futuros |
|---|---|---|
| Mercado | Binance spot, 26 pares `X/USDT` | Binance USDⓈ-M perpétuos, os mesmos 26 pares `X/USDT:USDT` |
| Lados | Só compra | Compra **e venda**, com as duas regras escritas antes do teste |
| Alavancagem | - | **1x fixa**. A estratégia não pode definir `leverage()` (o padrão do Freqtrade é 1); a checagem estática recusa quem definir |
| Margem | - | Isolada. A 1x isolada, a liquidação de uma posição comprada exige queda perto de 100%; numa vendida, alta perto de 100%. O stop continua obrigatório |
| Funding | - | Cobrado pelo backtest a partir do histórico de funding da Binance (baixado junto com os candles) |
| Gates, amplitude 16/26, penalidade por variantes | Iguais | Iguais. Hipóteses de futuros entram no mesmo contador do DSR |
| Holdout (>= 2027-04-21) | Trancado | Trancado, o mesmo |

## 2. Custos (mesmo modelo do spot, só a taxa muda)

Taxa de taker da Binance para usuário comum: 0,05% por lado; 0,045% pagando em BNB (desconto de 10%; [FAQ da Binance](https://www.binance.com/support/faq/360033544231)). O spot usa a taxa com desconto BNB, então futuros também. Derrapagem e spread: os mesmos valores do spot.

| Cenário | Taxa/lado | Derrapagem/lado | Spread total | Ida e volta | Spot hoje |
|---|--:|--:|--:|--:|--:|
| Otimista | 0,045% | 0 | 0 | 0,09% | 0,15% |
| Base | 0,045% | 0,05% | 0,05% | 0,24% | 0,30% |
| Conservador | 0,045% | 0,10% | 0,10% | 0,39% | 0,45% |
| Estresse | 0,045% | 0,25% | 0,25% | 0,84% | 0,90% |

**Atenção, para não criar expectativa errada:** com o modelo de derrapagem do lab, o ganho de custo é de só 0,06 ponto por ida e volta. O número de 0,15% usado no placar supunha derrapagem e spread bem menores que os do modelo (0,05 ponto por ida e volta, contra 0,15 do cenário base). A medição de hoje sugere que o spread real é pequeno (seção 2.2 do plano), mas a derrapagem por atraso nas barras de gatilho não foi medida. O ganho principal da faixa de futuros é **poder vender**, o que ataca as perdas de 2022-2024 de todas as regras de momentum só compradas. O custo só deve mudar de novo quando houver custo medido em bots rodando.

**Funding (medido na conferência de 13/11, seção 6):** a referência SmaTrendBaseline, comprada em BTC durante 2021, pagou 0,38% do valor da posição por trade em funding (posições de ~57 h, cerca de 0,05% a cada 8 h, num ano de alta). Num day trade comprado de ~10 h, isso seria 0,05 a 0,1% por trade em anos assim: o mesmo tamanho da economia de taxa. Em posição vendida, o funding costuma ser receita nesses anos. Conclusão: em futuros, uma regra comprada pode custar MAIS que no spot em mercado de alta. O backtest já cobra o funding real de cada hora, então isso aparece nos resultados sem ajuste manual.

## 3. Dados

- Candles de 1h e 15m, mark price e funding, por `freqtrade download-data --trading-mode futures`, em `user_data/data/binance/futures/` (fora do git, como os dados do spot).
- Início do histórico de futuros (Binance, conferido em 13/11/2026): BTC dez/2019; a maioria jan-out/2020; HBAR mar/2021; OP jun/2022; INJ ago/2022; APT out/2022; ARB mar/2023; SUI mai/2023. A exploração de futuros é mais curta que a do spot: BTC tem cerca de 4,5 anos em vez de 7.

## 4. Divisões de exploração e validação (confirmado pelo dono em 13/11/2026: "faça o ideal")

Proposta: **as mesmas datas do spot.** A exploração de cada par vai do primeiro candle de futuros até 04/07/2024 19:00 UTC, e a validação vai de 04/07/2024 20:00 a 20/10/2026 16:00. Assim nenhum período é escolhido olhando resultado.

Ressalva honesta: o preço de futuros quase não difere do spot, e a validação do spot já foi lida para cerca de 10 hipóteses (H-016, H-024, H-043 e outras). Essas hipóteses **não podem ser validadas de novo em futuros**, porque a validação delas não seria fora da amostra. Para hipóteses novas, o período de validação nunca foi visto por elas, e a regra "lida uma vez" continua valendo, agora por hipótese e por faixa.

Alternativa mais rígida: validar futuros só em dados depois de 20/10/2026. Hoje isso dá menos de 1 mês, então nenhuma hipótese teria 30 trades por par. Não recomendo.

## 5. Etapas de implementação

1. Dados dos 26 pares (rodando em 13/11).
2. `user_data/config.futures.dryrun.json`: dry_run, `trading_mode: futures`, `margin_mode: isolated`, pares `:USDT`. Arquivo novo; `config.dryrun.json` (protegido) não muda.
3. Lab: o runner aceita a faixa (config e pasta de dados); cenários de custo de futuros em `lab/costs.py`; `splits` de futuros num arquivo novo com as datas da seção 4; a checagem estática aceita `can_short = True` só na faixa de futuros e recusa `leverage()`.
4. Agentes: o pesquisador pode propor regras de futuros declarando o lado vendido ex ante; o desenvolvedor gera a estratégia com `can_short`.
5. Primeiro teste de conferência: uma regra simples e conhecida (por exemplo, a referência SMA) em futuros só comprada, conferida à mão contra o spot (mesmo sinal, diferença só de taxa e funding).
6. Dry-run: compose e congelamento da faixa de futuros, com a mesma regra de atividade (D1).

Critério de aceite: o teste de conferência da etapa 5 bate com o cálculo manual; a suíte passa; nenhum arquivo protegido muda; `real_money` continua false.

## 6. Andamento (13/11/2026)

| Etapa | Estado |
|---|---|
| 1. Dados | Feito: 26 pares, candles 1h e 15m, mark e funding (104 arquivos) |
| 2. Config | Feito: `user_data/config.futures.dryrun.json` (dry-run, futures, isolated, sem chaves, banco próprio) |
| 3. Lab | Feito. Faixa e custos por faixa; divisões em `lab/config/splits_futures.json`, geradas por `research/tools/build_futures_splits.py` (a opção `--check` confere o arquivo contra a regra). A estratégia declara a faixa com `LAB_MARKET = "futures"`, e checagens, calibração, experimentos e validação seguem a faixa (o registro marca `futures:` no cenário de custo). Um futuros de família com validação spot já lida, ou de família cujo nome estende uma dessas (H-104 `HourlyWilliamsVolBreakoutRVol` estende H-043 `HourlyWilliamsVolBreakout`), não lê a validação (`autopilot.family_spot_validations`); a comparação por prefixo pode barrar de mais um nome parecido, nunca de menos. Placar, curva de patrimônio (DSR) e MAE/MFE tratam vendas com o sinal certo. Teste real no Docker com uma estratégia descartável comprada e vendida: lookahead e recursive limpos em BTC, ETH e BNB; 21 de 42 trades vendidos, todos com alavancagem 1,0, funding cobrado |
| 4. Agentes | Feito. Pesquisador: campo opcional `"market": "futures"` com a linha obrigatória `Short side: ...`, custos e funding explicados. Desenvolvedor: `LAB_MARKET`, `can_short` e colunas de venda só nessa faixa. Direção do dono de 13/11 em `research/guidance.md` |
| 5. Conferência | Feito. SmaTrendBaseline, BTC, 2021, só comprada, custo base. 44 das 47 entradas de futuros no mesmo horário do spot; as outras 3 deslocadas 1 hora pela pequena diferença de preço. Funding cobrado de 0,38% por trade (ver seção 2). Nenhuma posição vendida, como esperado |
| 6. Dry-run | Feito no código: bot multi-par com pares `:USDT` e `config.futures.dryrun.json`; a config de futuros entra nos hashes do congelamento; o banco do bot é lido pela chave do par; a derrapagem de venda tem o sinal invertido; o registro de atividade (D1) usa as divisões de futuros. O primeiro bot só nasce quando uma hipótese de futuros passar exploração e validação |
