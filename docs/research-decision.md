# Pesquisa e decisão inicial

## Famílias consideradas

| Família | Hipótese formalizável | Riscos | Testes necessários |
|---|---|---|---|
| Trend/momentum | Persistência de retornos: comprar após tendência confirmada por médias, momentum ou canais | whipsaw, atraso, dependência de regime e custos | períodos de alta/baixa/lateralização, custos, sensibilidade e walk-forward |
| Mean reversion | Retorno a uma média após desvio de z-score/banda | tendência continua e a posição acumula perdas | stop, limite de tempo, filtros de regime, caudas e stress |
| Breakout | Rompimentos de máximas/mínimas carregam informação sobre nova tendência | falsos rompimentos, slippage e gaps intrabar | confirmação, volatilidade, custos e detalhe intrabar |
| Opening Range Breakout | Movimento após uma abertura definida persiste | cripto não tem abertura única; UTC arbitrário cria viés | só usar se uma sessão for definida ex-ante e comparar com baseline 24/7 |
| ML/IA | variáveis históricas classificam regime ou estimam retorno futuro | leakage, não-estacionariedade, múltiplos testes e baixa interpretabilidade | split temporal, teste fora da amostra, embargo, benchmark simples e estabilidade |

## Decisão

Escolhi um cruzamento SMA(20)/SMA(50) com filtro SMA(200) como baseline. A escolha não se apoia em superioridade publicada ou promessa de lucro: é barata, interpretável, determinística e adequada para validar dados, sinais, custos, stop-loss, exportação e FreqUI. O filtro de regime e o stop são hipóteses fixas; eles não devem ser tratados como parâmetros otimizados.

A estratégia exclui ML na primeira rodada. IA pode ajudar a documentar, testar e revisar, mas não gera sinais. ORB fica fora porque BTC/USDT negocia 24/7 e não há abertura universalmente natural. Mean reversion e breakout serão comparados somente depois que a baseline estiver congelada.

## Comparação de motores

- **Freqtrade:** melhor primeiro motor para este escopo: Python, spot cripto, Binance/CCXT, download, backtesting, dry-run, API e FreqUI integrados. A principal cautela é que backtest simula a ordem intrabar e não substitui forward testing.
- **MT5 + Expert Advisors/MQL5:** forte para corretoras e mercados oferecidos pelo MT5, mas introduz terminal, MQL5 e dependência de broker; não é o caminho mínimo para BTC/USDT spot via exchange cripto.
- **MT5 + Python:** útil quando a conta e execução são no MT5, porém exige terminal, integração e as mesmas dependências do broker; não oferece vantagem para a primeira validação de exchange spot.
- **VectorBT:** excelente biblioteca de pesquisa vetorizada e exploração rápida, mas não substitui sozinho a operação/dry-run/FreqUI de um bot.
- **Backtrader:** framework Python flexível para backtests e brokers, porém demanda mais integração e configuração para o fluxo de exchange spot escolhido.

Esses quatro ficam como alternativas de comparação, sem instalação simultânea.

## Dados e evidência

A Binance foi escolhida apenas como fonte inicial de candles porque o Freqtrade documenta suporte spot e o download público usa o identificador `binance`. A origem, o período, o formato e a taxa precisam ser registrados. Restrições regionais e disponibilidade devem ser rechecadas na data de execução. Nenhuma conta, chave ou API privada é necessária para esta fase.

Não há resultado próprio neste registro até que o container consiga baixar os dados e executar o comando. Resultados publicados não foram usados para afirmar rentabilidade da baseline; qualquer número futuro precisa vir do arquivo exportado pelo Freqtrade.

## Atlas Studio

A página consultada descreve ferramentas editáveis e dashboards e lista conectores, mas não lista Binance ou MetaTrader 5. Não há base para presumir suporte nativo a execução Python contínua, Binance ou MT5. Portanto, Atlas não é dependência desta etapa e nenhum segredo será enviado a ele.
