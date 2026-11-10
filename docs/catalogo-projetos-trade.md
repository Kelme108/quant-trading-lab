# Catálogo de projetos de trade no GitHub (pesquisa de 10/11/2026)

Escrito para: o dono do projeto, para saber o que foi pesquisado e como isso entra no lab.

## O que foi feito
Busquei no GitHub (API pública) por tópicos como trading-bot, algorithmic-trading, freqtrade-strategies, ai-trading, quantitative-trading, day-trading, reinforcement-learning e llm trading. Saíram **196 repositórios** com mais de 150 estrelas. Separei os que trazem regras de estratégia ou métodos reaproveitáveis. O resultado, para os agentes, está em `research/sources-queue.md`: uma fila de fontes que o scout (Opus) percorre antes das buscas genéricas, reescrevendo cada regra com palavras próprias, sem copiar código.

## O que há lá fora
| Grupo | Exemplos | Serve para |
|---|---|---|
| Bots com estratégias prontas | freqtrade-strategies, pycryptobot, binance-trading-bot, Crypto-Signal | Regras que já rodam em bots (breakout, pivot, volume, queda em tendência) |
| Pesquisa quantitativa | je-suis-tm/quant-trading, QuantConnect Lean, awesome-systematic-trading | Regras intradiárias bem descritas (London Breakout, Dual Thrust, padrões) e mapa de artigos |
| Conceitos ICT / smart money | OpenMobius-skill | Varreduras de liquidez, fair value gaps, killzones, em forma de regra |
| Day trade com IA | day-trader-skill (o que você me passou) | Já estudado: Time Machine, faixa de abertura, limites do dia |
| Machine learning | intelligent-trading-bot, ML for Trading (Stefan Jansen), mlfinlab | Features, rótulos "triple barrier" e meta-labeling (filtro de ML sobre sinais de regras) |
| Agentes de IA / LLM | TradingAgents, Vibe-Trading, ai-hedge-fund-crypto, nof0 | Ideias de arquitetura; quase nenhum publica regras testáveis |
| Não aproveitável agora | bibliotecas de execução, market making, bolsa chinesa | O lab opera spot a mercado |

## Como isso vira validação
1. O scout lê a fila, extrai regras e escreve ideias.
2. A triagem descarta as que não têm movimento esperado de pelo menos 0,45% por trade (nova regra de 10/11).
3. O research formaliza, o developer implementa e os gates decidem, como sempre.
4. Os projetos de ML ficam como base do **piloto de filtro com ML** (meta-labeling), que só começa quando existir uma estratégia com vantagem bruta real.

## Limites honestos
- A popularidade de um repositório não é evidência de que a regra funciona. Muitos desses bots têm resultados anunciados que nunca foram validados fora da amostra; o lab ignora esses números.
- Projetos de ações e de outros mercados só valem se o mecanismo se sustenta em cripto.
- Agentes de LLM que "negociam sozinhos" não trazem regra testável; entram como referência de arquitetura, não como fonte de estratégia.
