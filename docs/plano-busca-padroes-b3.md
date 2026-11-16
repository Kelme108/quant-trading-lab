# Plano: busca de padrões no WIN e no WDO, com bastante operações

16/11/2026. Pedido do dono: "quero regras com bastante trades" e "quero ver um plano de busca de padrões". Nada aqui começa sem a sua escolha nas decisões da seção 5.

## 1. Resumo

- **Recomendo o caminho B:** um sinal simples que opera muito, mais um filtro de aprendizado de máquina que aprende **quais** desses sinais costumam dar certo. Ele junta frequência e controle do risco de achar coincidência.
- **O caminho A**, uma biblioteca de padrões testada de forma sistemática, vem antes e fornece os sinais de base do B.
- **O caminho C**, prever o próximo movimento a cada candle, opera mais, mas tem o maior risco de achar coincidência.
- **O caminho D**, um agente de IA decidindo as ordens, eu **não recomendo**. Os motivos estão na seção 4.
- **Duas travas antes de começar:**
  - **A régua de lucro mínimo hoje é 26,6%.** Uma busca de padrões nunca passa nela. É preciso trocar a forma de contar tentativas para o programa de busca (decisão D2).
  - **Focar no WIN.** No WDO, regras frequentes são quase impossíveis com o custo atual (seção 2).

## 2. O ponto de partida, em números

Todos os números são da exploração (nov/2021 a jun/2024). Os dados de validação e de teste final não foram abertos para isto.

| | WIN | WDO |
|---|---|---|
| Custo de ida e volta (base) | 0,011% | 0,0235% |
| Ganho bruto médio necessário por operação (3× o custo) | 0,033% | 0,070% |
| Movimento mediano em 15 min | 0,088% | 0,066% |
| Movimento mediano em 30 min | 0,125% | 0,091% |
| Movimento mediano em 60 min | 0,181% | 0,131% |

**O que isto quer dizer.** O preço anda bem mais que o custo. O difícil é acertar a **direção** com frequência. Com ganhos e perdas do mesmo tamanho, a taxa de acerto mínima para chegar a 3× o custo é aproximadamente esta:

| Tempo da operação | WIN | WDO |
|---|---|---|
| 15 min | ~69% | ~100% (impossível) |
| 30 min | ~63% | ~88% |
| 60 min | ~59% | ~77% |

Conclusões:

- Uma regra frequente no **WIN** precisa segurar a posição por **30 a 60 minutos** e acertar cerca de 60% das vezes. Também serve acertar menos, com ganhos maiores que as perdas.
- Com 2 a 4 operações por pregão, isso dá **500 a 1.000 operações por ano**.
- No **WDO**, o custo come o movimento. Lá, só vale testar regras raras e de movimento grande.

**O que já foi tentado.**

| Regra | Operações/ano no WIN | Ganho bruto por operação | Resultado |
|---|---|---|---|
| P-005 (VWAP, 1 min) | ~4.480 | −0,014% | −85% |
| P-003 (área de ruído) | ~420 | +0,003% | ~0% |
| P-004 (fim do dia) | ~246 | +0,031% | +20% na exploração, reprovou na validação |

Regras que viram a mão a cada sinal pequeno perdem tudo no custo.

**A régua.** Hoje uma regra nova precisa ganhar mais de 26,6% na exploração. A conta é 1% × (1 + 0,1 × 256 tentativas), e 256 tentativas vieram da triagem das 128 estratégias de cripto. Isso foi feito de propósito, para punir quem testa muito. Só que essa régua cresce em linha reta com o número de testes, e uma busca de padrões testa milhares de variações. Com ela, nenhuma busca passa, nem uma boa.

## 3. Proteções comuns a todos os caminhos

1. **Os dados de validação** (jul/2024 a set/2025) são lidos **uma única vez** por família de padrões, só para as finalistas.
2. **O teste final** (out/2025 em diante) continua trancado até você liberar.
3. **Dentro da exploração, a busca se valida sozinha.** Ela usa janelas que andam no tempo: treina num pedaço e testa no seguinte, que nunca viu.
4. **Toda variação testada é contada.** O resultado é descontado pelo número de tentativas, com os dois testes que o projeto já tem:
   - o **Sharpe deflacionado** (DSR), que pergunta se o resultado ainda é bom depois de descontar quantas variações foram testadas;
   - a **probabilidade de sobreajuste** (PBO), que pergunta com que frequência a melhor variação no passado vira uma das piores logo depois.
5. **Custo conservador** (o dobro do base) e 1 tick a mais em todo stop.
6. **A finalista vai para a demo da Clear** antes de qualquer conversa sobre dinheiro real, como a P-004 hoje.

## 4. Os caminhos

### A. Biblioteca de padrões testada de forma sistemática
- **Como funciona:** escrevo de 15 a 25 famílias de padrões intradiários conhecidos, cada uma com poucos números para variar. Exemplos:
  - rompimento da máxima ou da mínima dos últimos N minutos;
  - afastamento da VWAP;
  - candle com volume anormal;
  - falha de rompimento;
  - reversão depois de um movimento rápido;
  - horários de leilão e de abertura do mercado à vista;
  - o mini dólar como sinal para o mini índice.

  Todas rodam em 1 e 5 min no motor da B3 e são ranqueadas pelo DSR.
- **Operações:** as famílias são escolhidas para dar 500 a 3.000 operações por ano.
- **Custo:** 1 a 2 dias de trabalho meu e algumas horas de computador. Não gasta com agentes.
- **Risco:** médio, controlado pelo DSR e pelo PBO. Com algumas milhares de variações, a chance de uma ser boa por acaso é alta, e por isso esses dois testes decidem.
- **Minha opinião:** vale fazer, sobretudo como fonte de sinais para o B.

### B. Sinal frequente com filtro de aprendizado de máquina (recomendado)
- **Como funciona:** um sinal do caminho A que opera muito e quase empata no bruto passa a ser a "base". Um modelo de árvores aprende **quais** desses sinais dão certo, olhando:
  - horário;
  - volatilidade das últimas horas;
  - movimento do dia;
  - distância da VWAP;
  - volume;
  - o que o WDO está fazendo;
  - se é véspera ou dia de evento dos EUA.

  O robô só opera os sinais que o modelo aprova. O treino é sempre em janelas que andam no tempo, dentro da exploração. A validação é lida uma vez.
- **Operações:** depende do corte do filtro. Fixamos antes um mínimo de 500 por ano, e o filtro não pode cortar abaixo disso.
- **Custo:** 3 a 5 dias, depois do A. Precisa instalar a biblioteca do modelo (scikit-learn ou LightGBM; nenhuma está instalada hoje). Computador: horas.
- **Risco:** menor que o do C, porque o modelo só escolhe entre sinais que já têm uma lógica. A literatura sobre esse método, a do "meta-rótulo", mostra ganhos reais, mas pequenos. O risco principal é o modelo usar sem querer informação do futuro, e a verificação de causalidade do projeto barra isso.
- **Minha opinião:** é o melhor equilíbrio entre bastante operações e chance de ser real. Em 13/11 você decidiu não fazer aprendizado de máquina por enquanto (D5). Na época, a ideia era usá-lo só depois de uma regra B3 provar vantagem bruta. Este plano antecipa isso, então precisa do seu sim (D1).

### C. Previsão direta a cada candle
- **Como funciona:** um modelo olha cada candle de 1 ou 5 min e prevê se o preço sobe ou desce nos próximos 30 a 60 minutos. Opera quando a confiança passa de um limite.
- **Operações:** a maior de todas; dá para regular de 500 a 5.000 por ano.
- **Custo:** cerca de 1 semana e algumas horas de computador.
- **Risco:** **alto.** Em índice, a chance de acertar a direção fica quase sempre entre 50% e 53%, e precisamos de ~60%. É o caminho em que um bom resultado no passado mais engana.
- **Minha opinião:** só depois do B, e só se o B mostrar que existem variáveis que ajudam a prever.

### D. Agente de IA (como o ChatGPT ou o Claude) decidindo as ordens
- **Como funciona:** a cada candle, um modelo de linguagem recebe o gráfico e as notícias e decide comprar, vender ou esperar.
- **Evidência:** já pesquisamos isto em 12/11 (`research/reviews/2026-11-12-pesquisa-direcao-day-trade.md`).
  - **Alpha Arena**, o torneio da nof1 com dinheiro real: 4 de 6 modelos perderam, e o resultado foi dominado pelo custo de operar demais. A mesma empresa foi do pior ao melhor lugar trocando de versão, o que indica sorte, não habilidade.
  - **Estudo de 6 meses com cerca de 500 agentes em produção** (arXiv 2609.05663):
    - nenhuma vantagem na direção;
    - 41% de acerto, contra 50% do investidor comum;
    - um stop e um alvo fixos teriam feito melhor que as decisões dos agentes.
- **Não dá para testar de forma honesta:** o modelo foi treinado com textos e preços desse mesmo período, então ele "lembra" o passado e qualquer teste histórico fica contaminado. A única prova possível seria meses ao vivo.
- **Também é caro e não se repete:** uma decisão a cada 5 min em 2 contratos são ~200 chamadas por dia, alguns dólares por dia. A mesma situação pode gerar decisões diferentes.
- **Minha opinião:** **não fazer.** A IA rende mais onde já está: pesquisar, propor e programar regras que são testadas de forma fixa.

## 5. Decisões para você

- **D1. Caminhos:** (a) **A e depois B (recomendado)**; (b) só A; (c) A, B e depois C; (d) nenhum por enquanto.
- **D2. Régua do programa de busca:** a régua em linha reta (26,6% hoje) inviabiliza qualquer busca. Proponho para este programa:
  - aprovar na exploração quem tiver DSR ≥ 0,95 contando **todas** as variações da busca;
  - PBO ≤ 0,3;
  - lucro líquido positivo no custo conservador;
  - pelo menos 500 operações por ano;
  - mais de 60% dos anos positivos.

  A validação continua sendo lida uma vez e o teste final continua trancado. As regras dos agentes ficam com a régua atual. Opções: (a) **sim (recomendado)**; (b) manter a régua atual para tudo.
- **D3. Mercados:** (a) **só WIN (recomendado)**; (b) WIN e WDO.
- **D4. Instalar a biblioteca de aprendizado de máquina** (scikit-learn ou LightGBM), só no ambiente local: (a) sim; (b) não, e o B fica de fora.

## 6. Cronograma, se você escolher D1 (a)

| Etapa | Duração | Entrega |
|---|---|---|
| A: registrar as famílias e as faixas de números antes de rodar | 0,5 dia | arquivo de configuração com tudo fixado, publicado antes de qualquer leitura |
| A: rodar a busca na exploração, DSR e PBO | 1 dia | ranking no portal (B3 → Ranking), com operações por ano e ganho por operação |
| B: base + filtro, treino em janelas que andam no tempo | 3 a 5 dias | as 3 a 5 finalistas |
| Validação (uma leitura) | 1 hora | aprovadas ou não |
| Demo da Clear com as aprovadas | 2 a 4 semanas | o mesmo acompanhamento ao vivo de hoje |

Os agentes continuam no ritmo de hoje, com no máximo 3 regras por semana e pelo menos 500 operações por ano, em paralelo.

## 7. Resultado (16/11/2026, só dados de exploração)

Você escolheu D1 (a), D2 (a), D3 (a) e D4 (a). O protocolo foi gravado e datado antes de qualquer leitura: `b3/config/pattern_search_b3.json`, commit `1388af8`.

**Conferência do simulador.** Antes de olhar qualquer resultado, o simulador rápido foi comparado com o motor oficial (`b3/backtest.py`) em 3 variações. As operações saíram **100% idênticas** nas três (4.888, 4.488 e 750 operações), comparando horário e preço de entrada e saída. O registro está em `research/b3/search/fidelity.json`.

**Caminho A: 552 variações** (16 famílias de padrões × 1 e 5 min × 6 saídas).

- Nenhuma passou.
- 388 variações operam 500 ou mais vezes por ano. Nenhuma ganhou no custo conservador, e só 2 ganharam no custo base.
- A melhor delas ganhou **+0,004% bruto por operação**. A meta era 0,033% (3 vezes o custo), e o custo sozinho é 0,011%.
- O maior Sharpe deflacionado foi 0,002, contra o mínimo de 0,95. A probabilidade de sobreajuste do programa foi 0,20.
- Os poucos padrões com ganho bruto bom (como volume anormal a favor) operam de 4 a 80 vezes por ano, longe das 500 pedidas.

**Caminho B: 3 bases × 3 cortes do filtro = 9 variações.**

- Previsões feitas de jan/2023 a jun/2024. O primeiro trimestre completo depois de 12 meses de treino foi 2023-T1.
- O filtro levou duas bases de −0,004% e −0,009% para +0,004% e +0,003% bruto por operação. Ainda fica 8 vezes abaixo da meta, e com acerto de 47% a 51%.
- Na terceira base, com o dólar como sinal, o filtro piorou o resultado.
- A probabilidade de sobreajuste foi 0,81, ou seja, o corte "bom" é coincidência.
- Nenhuma variação passou.

**Validação:** nenhuma finalista, então **não houve leitura**. Os dados de validação e de teste final continuam intactos.

**Conclusão.** Com preços de 1 e 5 minutos e operações de 15 a 60 minutos, padrões frequentes no WIN não têm vantagem de direção que pague o custo de entrar e sair. Isso vale até com um filtro de aprendizado de máquina. Os dados apontam três alavancas de outro tipo:

1. **Custo.** No WIN, cerca de 80% do custo é o deslizamento de 1 tick em cada ponta. Com ordens limitadas, ou medindo o deslizamento real na demo da Clear (as ordens da P-004 já mostram isso), a meta cai muito. O risco é que uma ordem limitada só é executada justo quando o preço vai contra você, e isso não dá para testar com candles: precisa de dados de tick ou da demo.
2. **Dados novos.** O fluxo de agressão, isto é, quem compra e quem vende a mercado, vem do histórico de ticks da B3 no MT5. É o tipo de informação de curtíssimo prazo que a literatura aponta como preditiva, e os candles não mostram.
3. **Menos operações, maiores.** Os únicos padrões com ganho bruto acima da meta foram os raros: volume anormal a favor (+0,10% por operação, 4 por ano) e afastamento da VWAP (+0,04%, 60 por ano).

## 8. Alavanca 1: custo real medido (16/11/2026)

**Medição.** Usei os ticks do WINZ26 na Clear, de 15/10 a 13/11/2026: 21 pregões e 7.751 minutos (`research/b3/execution_cost.json`). Foi medida só a execução, em horários fixos e sem nenhum sinal de estratégia, porque esse período fica dentro do teste final trancado. O histórico de ticks do terminal tem buracos (falta quase sempre o fim da tarde), então valem as horas cobertas, de 9h às 16h.

| | Modelo do backtest | Medido |
|---|---|---|
| Spread | — | 1 tick em 95% do tempo |
| Ordem a mercado (por ponta, contra a abertura do candle) | 1 tick | **0,39 tick** (p90: 1 tick) |
| Stop | 2 ticks além do nível | **≈ 0** (média 0,7 tick a favor, p95 0) |
| Ordem limitada no bid/ask | — | executa 86–92% das vezes em 15–60 s, mas 15–30 min depois rende 0,1–0,25 tick **pior** que a mercado (seleção adversa) |

**Conclusões da medição:**
- A ida e volta real é cerca de **metade** do que o modelo cobrava.
- Ordem limitada **não** ajuda.

**Reavaliação das 552 variações do caminho A com o custo medido.** A reavaliação foi gravada no protocolo antes de rodar (commit `fe93da7`). Os dois custos usados foram:
- custo médio medido: 0,4 tick por ponta e R$ 0,25 de taxa;
- custo do pior caso (p90): 1 tick por ponta e R$ 0,50 de taxa.

Resultado:
- 36 das 388 variações frequentes lucram no custo médio medido. A melhor é a rejeição da máxima/mínima do dia em 5 min, com cerca de 826 operações por ano e +13% em 2,6 anos (+0,007% por operação).
- Nenhuma lucra no custo do pior caso.
- O maior Sharpe deflacionado é 0,009, contra o mínimo de 0,95.
- A probabilidade de sobreajuste é 0,51: escolher a melhor é praticamente cara ou coroa.
- **Nenhuma passou**, e a validação continua sem leitura.

**Leitura.** O custo real deixa os padrões frequentes mais perto do empate, mas o lucro que aparece tem o tamanho que se espera do acaso depois de 552 tentativas. Os candles de 1 e 5 minutos não trazem informação de direção suficiente.

**Sobre a alavanca 2 (fluxo de agressão).**
- **Onde existe o lado do agressor:** só no contrato vigente. A série contínua WIN$N grava todos os negócios com a mesma marca e não diz quem agrediu.
- **Quanto histórico há:** o terminal guarda poucas semanas, e com buracos.
- **O que isso exige:** pesquisar fluxo de agressão significa **começar a gravar** os ticks desde agora, com um gravador simples e só de leitura, e esperar alguns meses até ter dados para explorar e validar.
