# Plano: histórico de ticks com agressor e regras de fluxo (WIN/WDO)

Escrito em 17/11/2026 para sua aprovação. **Nada aqui foi executado, comprado ou lido.**
Depende de duas decisões suas (seção 4).

## 1. Por que

Depois de cerca de 1.000 tentativas com candles de 1 e 5 minutos no WIN (buscas A, B, C, regras dos agentes e o estudo de saídas), nenhuma passa com os custos medidos. O sinal mais forte até agora vem do **fluxo de agressão**: desfazer o desequilíbrio entre compra e venda agressoras dos últimos 15 minutos, cerca de 960 operações por ano, +0,094% bruto por operação. Mas isso foi lido em só 20 pregões, e o Sharpe deflacionado deu 0,22 (mínimo 0,95).

O gargalo é **a quantidade de dados**: o terminal da Clear guarda só cerca de 3 meses de ticks. Até 31/12 teremos uns 50 pregões, o que não decide nada. Cinco anos de ticks permitiriam testar em anos, não em semanas.

## 2. Parte A: histórico de ticks com agressor

**O que existe (levantado hoje, preços não verificados):**

| Fornecedor | O que oferece | Agressor | Preço |
|---|---|---|---|
| Nelogica (Base Histórica) | Tick a tick de WINFUT e WDOFUT desde 2012, um registro por negócio, CSV por sFTP em até 48 horas úteis depois do pagamento | Sim, segundo a página de vendas | Só sob orçamento, sem tabela |
| Portara (CQG) | WIN "trades only" desde 2008 | Não | Não levantado |
| NegocIA | WIN com preço, volume e book | Não verificado | Não levantado, histórico desde 2024 |
| Benfeitoria | Campanha de compra coletiva (WIN desde 2010, WDO desde 2012) | Não verificado | Não levantado, não sei se ainda está ativa |
| B3 (UP2DATA) | Não encontrei canal de ticks de futuros | Não | Não encontrei |

O que **não** foi verificado: preço, licença de uso, lista exata de campos e se cobre todos os contratos de WIN/WDO desde 2012. A página da Nelogica diz que os dados servem para backtest e pesquisa, mas não lista restrições de licença.

**Passos propostos (nenhum gasta dinheiro sem seu aval):**
1. Você decide se quer pedir orçamento. Eu preparo a lista do que pedir: WINFUT e WDOFUT, 2021-11-16 até hoje, negócio a negócio, com o lado agressor e o campo de contrato, e uma amostra gratuita de uma semana, se possível.
2. Quando o arquivo chegar, **antes de qualquer teste de estratégia**, faço uma conferência de qualidade:
   - compara os dias que se sobrepõem com os ticks que a Clear gravou: mesmas quantidades de negócios, mesmo agressor na maior parte, horários batendo;
   - confere buracos, sessões incompletas e o fuso horário.
3. Só depois disso, o protocolo de divisão dos dados (seção 3).

**Custo e risco:** o preço é desconhecido e a compra é decisão sua. Se a conferência de qualidade falhar, o dado não serve e não se usa.

## 3. Parte B: regras de fluxo

**O que muda em relação ao projeto de hoje:**
- Hoje uma regra enxerga só candles: `time, open, high, low, close, volume`. Isso explicou várias das regras perdidas pelos agentes.
- O programa de ticks já tem candles de 1 minuto com fluxo (compra agressora, venda agressora, negócios grandes, rajadas), em `user_data/data/b3/clear/tickbars/`.
- A proposta é um **segundo tipo de regra**, de fluxo, que enxerga esses candles, e um **robô de demo** capaz de montar os mesmos candles de fluxo a partir dos ticks ao vivo.

**Divisão dos dados (a aprovar, só vale depois da conferência de qualidade):**
- **Exploração:** 2021-11-16 a 2024-06-30, a mesma janela das regras de candle.
- **Validação:** 2024-07-01 a 2025-09-30, lida **uma vez** por candidata.
- **Teste final:** a partir de 2025-10-01 e os ticks que o gravador guarda daqui para frente, **trancado** até você liberar.
- Os ticks que a Clear já gravou (ago/2026 em diante) ficam como parte do teste final e não são lidos antes.

**Critério de aprovação:** o mesmo do projeto, 500 operações por ano, lucro positivo no custo medido e no conservador, Sharpe deflacionado de pelo menos 0,95 contando todas as tentativas, probabilidade de sobreajuste de no máximo 0,3.

**Os agentes:**
- Só voltam a propor regras de fluxo depois que o histórico existir. Sem ele, só haveria uns 50 pregões para testar.
- O agente de propostas passa a ver as colunas de fluxo. As regras de candle antigas não voltam.
- A parada de 15 regras continua. Hoje são 10, com a P-031 fora da conta; as regras de fluxo seriam um programa novo, com contagem própria, a decidir com você.

**Trabalho de engenharia (eu faço, com testes):**
1. Ler o arquivo comprado e gerar os candles de fluxo no mesmo formato.
2. Passar as colunas de fluxo para as regras no teste e no robô.
3. Montar os candles de fluxo ao vivo e comprovar, com um teste de paridade, que dão o mesmo resultado do histórico.

## 4. Decisões suas

1. **Pedir orçamento do histórico de ticks?** Eu monto o pedido e você contata o fornecedor, ou me diz como prefere. Não compro nada em seu nome.
2. **Aprova a direção das regras de fluxo**, com a divisão de dados da seção 3, a valer só se o dado passar na conferência?

## 5. Enquanto isso

- **Demo:** rodando normal, com os 11 robôs e o registro de maior lucro e maior perda por operação.
- **Gravador de ticks:** todo dia útil às 19:05. Cada dia gravado conta para o teste final do programa de ticks.
- **Agentes de candle:** pausados, com 5 regras até a parada.
- **Leitura semanal do programa de ticks:** só para acompanhar; a decisão só vale depois de 31/12.

## Fontes

- [Nelogica, Base Histórica](https://use.nelogica.com.br/pr-capt-lp-bases-historicas): tick a tick de WINFUT e WDOFUT desde 2012, agressor, CSV por sFTP, preço sob orçamento.
- [Portara, WIN tick trades only](https://portaracqg.com/futures/tto/win): WIN desde 2008, sem agressor.
- [B3, dados disponíveis do UP2DATA](https://b3.com.br/en_us/market-data-and-indices/data-services/up2data/available-data/): não encontrei canal de ticks de futuros.
