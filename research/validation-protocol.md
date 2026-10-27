# Protocolo de validação de estratégias

Este laboratório usa a tabela do contato apenas como inspiração para organizar hipóteses. Os números e rótulos de MNQ não são evidência para BTC/USDT: são outro mercado, outro instrumento, outra granularidade, outros custos e permitem short. Nenhuma regra foi inferida das imagens, porque as condições estavam ocultas.

## Catálogo inicial

| Estratégia | Família | Hipótese | Entrada | Saída | Estado |
|---|---|---|---|---|---|
| `SmaTrendBaseline` | tendência | persistência após cruzamento e regime positivo | SMA20 cruza acima da SMA50 e close > SMA200 | cruzamento contrário ou stop -10% | referência congelada |
| `DonchianBreakoutBaseline` | breakout | fechamento acima da máxima recente pode iniciar tendência | close > máxima anterior de 20 candles | close < mínima anterior de 10 candles ou stop -10% | candidata fixa |
| `BollingerMeanReversionBaseline` | mean reversion | excesso de venda pode retornar à média em regime positivo | close abaixo da banda inferior de 20, RSI14 < 30 e close > SMA200 | close acima da banda média ou stop -10% | candidata fixa |

Os parâmetros são hipóteses ex-ante. Não serão ajustados para escolher a melhor curva histórica nesta rodada.

## Execução comparável

Toda comparação deve usar o mesmo:

- par, mercado, timeframe e origem de dados;
- janela temporal e dados congelados;
- saldo, limite de posições e taxa;
- definição de candle fechado e execução seguinte;
- formato de exportação e versão do Freqtrade;
- slippage ou cenário de custos explicitamente registrado.

O comando em lote economiza tempo, mas não transforma estratégias diferentes em observações independentes. Estratégias que usam o mesmo histórico compartilham risco de descoberta e múltiplos testes.

## Divisão temporal

Para o primeiro arquivo disponível, a janela efetiva começa após o startup de 200 candles. O primeiro backtest completo é uma referência exploratória, não um teste final. A próxima rodada deve congelar uma divisão cronológica, por exemplo:

1. exploração: primeira parte do histórico;
2. validação: trecho seguinte, nunca usado para escolher parâmetros;
3. teste final: período mais recente reservado até o protocolo ser congelado.

A divisão exata deve ser registrada antes de qualquer leitura de resultados da rodada correspondente. Walk-forward deve ser usado quando houver histórico e número de operações suficiente.

## Portão de qualidade

Uma estratégia não é aprovada por retorno total positivo. Antes de avançar, verificar:

- `lookahead-analysis` sem viés;
- `recursive-analysis` sem instabilidade relevante de indicadores;
- quantidade de trades suficiente para a pergunta;
- desempenho por subperíodo e regime;
- taxas e slippage conservador;
- comparação com ficar em caixa e comprar-e-manter;
- estabilidade a pequenas mudanças ex-ante de parâmetros;
- drawdown, concentração e exposição compatíveis com o objetivo;
- dry-run como forward test, sem promessa de desempenho.

Não há limiar universal de lucro. Com uma operação, como na baseline atual, Sharpe, Sortino, profit factor e win rate não sustentam inferência; o resultado é **inconclusivo**.

## Busca em massa e overfitting

O lote é limitado a hipóteses interpretáveis. Cada execução deve guardar estratégia, código, versão, dados, custos, janela e configuração. Não usar hyperopt antes de validar a infraestrutura e o protocolo. Quando hyperopt for autorizado em fase posterior:

- limitar espaços e número de tentativas;
- separar exploração de validação e teste final;
- não selecionar pelo melhor resultado isolado;
- relatar quantas variantes foram testadas;
- repetir o teste fora da amostra;
- rejeitar instabilidade e dependência de um único período.

Um catálogo grande com resultados históricos positivos pode ser apenas seleção entre muitas tentativas. A hipótese nula de que a descoberta é acaso precisa permanecer plausível até haver validação independente.

## Segurança operacional

- spot somente;
- `dry_run: true` por padrão;
- sem chaves privadas e sem saque;
- sem margem, futuros ou short;
- FreqUI somente em loopback;
- nenhuma estratégia nova substitui a estratégia ativa sem revisão explícita;
- nenhum resultado autoriza operação real.
