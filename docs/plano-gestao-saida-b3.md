# Estudo de gestão de saída (WIN/WDO) — protocolo para aprovação

Escrito em 17/11/2026, **antes de qualquer leitura de dados com estas saídas**.
**Aprovado por você em 17/11/2026 ("aprovo, retire")**, e registrado neste commit antes de qualquer leitura.
Arquivo do protocolo: `b3/config/exit_study_b3.json`. Código: `b3/exit_study.py`. Resultados: `research/b3/exit_study/`.
A P-031 foi interrompida pela pausa e não entra no estudo.

## 1. A pergunta

As regras dos agentes decidem a saída só no fechamento do candle. Por isso uma operação pode chegar a +R$ 80 e devolver tudo. A pergunta é:

**Uma gestão de saída por lucro e perda, acompanhada minuto a minuto, transforma alguma dessas entradas em algo que ganha depois dos custos?**

As entradas não mudam. Cada regra continua entrando exatamente como foi registrada. Só a saída varia.

## 2. Quais entradas

São as regras já registradas e rodadas no WIN e no WDO que fazem pelo menos 500 operações por ano. A frequência já está no registro de resultados, então decidir quem entra não exige nenhuma leitura nova.

- **Regras dos agentes:** P-014, P-017, P-020, P-023, P-024, P-025, P-026, P-028 e P-030, além das próximas, desde que registradas antes da primeira leitura.
- **P-004 (WIN e WDO):** só na exploração. A validação da P-004 no WIN já foi lida uma vez e não pode ser lida de novo.
- **P-029 fica de fora:** faz 15 operações por ano, e trocar a saída não muda a frequência.

## 3. As saídas testadas (12 por regra)

Os valores são por contrato. No WIN, R$ 1 equivale a 5 pontos; no WDO, a 0,1 ponto.

| Código | Saída |
|---|---|
| X00 | A da regra, sem mudança (referência) |
| X01–X03 | Alvo de R$ 20 / 30 / 50, mantendo o stop e as demais saídas da regra |
| X04 | Alvo de R$ 30 e stop de R$ 30, ou o stop da regra se ele for menor |
| X05 | Alvo de R$ 50 e stop de R$ 50, ou o stop da regra se ele for menor |
| X06–X07 | Stop vai para o preço de entrada depois de +R$ 20 / +R$ 40 |
| X08–X10 | Stop móvel a R$ 20 / 30 / 50 do melhor preço, ligado quando o lucro atinge essa distância |
| X11 | Alvo de R$ 30, com o stop indo para a entrada depois de +R$ 20 |

O tempo máximo e o fechamento antes do fim do pregão continuam valendo em todas.

## 4. Como a simulação é feita (premissas conservadoras)

- **Candles de 1 minuto da exploração:** 16/11/2021 a 01/07/2024. Isso vale para todas as regras, inclusive as de 5 minutos. Assim, alvo e stop são acompanhados minuto a minuto, como faria o robô ao vivo.
- **Stop e alvo no mesmo minuto:** vale o **stop**, o pior caso.
- **Alvo:** é uma ordem limitada. Só conta como executado se o preço passar 1 tick além do alvo, porque só tocar o nível não garante execução. A execução é no nível do alvo.
- **Stop e stop móvel:** são executados no nível. O stop móvel só sobe com o melhor preço dos minutos **anteriores**, nunca com o do minuto que está sendo avaliado.
- **Custos:** os mesmos medidos na Clear e já registrados.
  - Base: 0,4 tick de deslizamento por lado, mais taxa.
  - Conservador: 1 tick por lado e taxa maior, no percentil 90.
- **Conferência do simulador:**
  - Com X00, o simulador precisa reproduzir o motor oficial das regras.
  - Com entradas sorteadas, sem nenhum sinal de estratégia, a ordem dentro do minuto é comparada com os ticks gravados.
  - Nenhuma regra é lida nos dados de ticks, porque eles caem no período do teste final, que está trancado.

## 5. Critério de aprovação (o mesmo do projeto)

- Pelo menos 500 operações por ano.
- Lucro líquido acima de zero no custo base **e** no conservador.
- Sharpe deflacionado de pelo menos 0,95, contando **todas** as tentativas já feitas no mercado. No WIN, são as 849 das buscas A, B e C, mais as deste estudo.
- Probabilidade de sobreajuste de no máximo 0,3, com 8 fatias.
- Cada combinação de regra e saída que passar é lida **uma vez** na validação (01/07/2024 a 01/10/2025). O teste final continua trancado até você liberar.

## 6. O que esperar, com honestidade

- As entradas dessas regras perdem **antes** do custo. Uma saída melhor muda o formato do resultado: menos devolução, perdas menores. Raramente transforma uma entrada sem vantagem em uma com vantagem.
- A chance de alguma combinação passar é baixa. Com as tentativas já acumuladas no WIN, a exigência é alta.
- Mesmo assim, o estudo responde à sua pergunta com números, em vez de impressão de uma ou duas operações.

## 7. Na demo, em paralelo

- **Sem limite de lucro:** os robôs voltam às saídas originais, ou seja, sem o limite de R$ 25 ou R$ 30.
- **Novo registro por operação:**
  - o **maior lucro**, chamado MFE;
  - a **maior perda**, chamada MAE;
  - quanto teria dado com cada uma das saídas X01 a X11.

  É só medição: o robô continua operando como a regra manda.
- **Uso desse registro:** é a mesma pergunta medida ao vivo, com execução real, e serve para conferir o simulador. Não decide aprovação: poucas semanas de demo são poucas operações.
