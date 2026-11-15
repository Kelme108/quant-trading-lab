# Plano: day trade em índices no portal (15/11/2026)

## Objetivo

Ver no portal (`python -m lab.dashboard serve`, http://127.0.0.1:8765) tudo o que hoje só aparece em arquivos e no terminal:

- a pesquisa nos mercados substitutos do WIN/WDO (US500, USTEC, US30, US2000, DE40);
- o programa de agentes que propõe regras sozinho;
- as medições que decidem o que vale testar.

Hoje o portal mostra só o laboratório de cripto (hipóteses H-\*, ciclos, dry-run).

## Situação de hoje

| O quê | Onde está | Tamanho |
|---|---|---|
| Leituras (regra × mercado × etapa) | `research/proxies/ledger.jsonl` | 67 leituras, 62 combinações em exploração, 10 regras |
| Resultado de cada leitura (métricas por cenário de custo, por ano, motivos dos gates) | `research/proxies/results/*.json` | 67 arquivos, 0,3 MB |
| Funil | ledger | exploração 62 → 3 passaram; validação 3 → 2; teste final 2 → 0 |
| Propostas dos agentes | `research/proxies/proposals/P-NNN.json` | P-008 a P-011 (P-010 com erro) |
| Ciclos do pipeline e custo dos agentes | `research/proxies/pipeline_log.jsonl`, `ops/state/proxy-cycle.log` | US$ 6,05 até agora |
| Limites e prazos do programa | `b3/config/proxy_program.json`, `python -m b3.proxy_program status` | 3 por semana; parada 15 regras; 14/12; dados de bolsa 28/11 |
| Mercados, custos e escopo | `b3/markets.py`, `b3/config/scope_proxies.json` | 9 mercados, 5 no escopo |
| Medições | `research/proxies/anatomy.json`, `event_anatomy.json`, `tick_fidelity.json`, `data_quality.json`, `failure_anatomy.json` | — |

**O que falta para alguns gráficos:** as leituras guardam só as métricas, não a lista de operações. Sem ela não dá para desenhar a curva de capital nem cruzar por hora ou dia da semana (decisão D2).

**Limite atual do portal:** `/api/state` já leva 27 s e tem 16,9 MB. Os dados novos não entram nele: vão num endereço próprio e leve.

## O que o portal vai mostrar

Novo grupo no menu: **"Índices (WIN/WDO)"**, com 5 páginas. Cada página abre com a conclusão numa frase simples, como as páginas de Resultados.

### 1. Visão geral (`#/indices`)

- **Frase de abertura**, por exemplo: "Nenhuma regra aprovada. 10 regras em 62 combinações; 3 passaram a exploração, 2 a validação, 0 o teste final. Programa ativo: 0 de 3 regras nesta semana."
- **Números-chave:**
  - regras testadas e combinações;
  - régua atual de retorno líquido (hoje 7,1%, sobe 0,1 ponto a cada combinação);
  - gasto com agentes;
  - dias até a parada do projeto (14/12);
  - dias até o prazo dos dados de bolsa (28/11).
- **Funil:** exploração → validação → teste final, por combinação.
- **Cartão "Programa de agentes":**
  - estado (ativo, no limite da semana, pausado ou encerrado) e o motivo, com o texto de `proxy_program.status`;
  - próximo ciclo previsto;
  - os dois critérios de parada com o progresso (por exemplo "4 de 15 regras sem passar a validação").
- **Avisos que pedem você:**
  - regra que passou a validação e espera o desbloqueio do teste final;
  - pipeline pausado após erros, com o comando para retomar;
  - prazo vencido.

### 2. Placar (`#/indices-placar`)

- Tabela regra × mercado: tempo gráfico, operações por ano, ganho bruto por operação e em múltiplos do custo, líquido no custo base e no conservador, pior queda, anos positivos e a decisão em cada etapa (exploração, validação, teste final).
- Os motivos de reprovação aparecem em texto ao passar o mouse.
- Filtros: mercado, decisão, origem (regras escritas à mão P-001 a P-007, ou propostas dos agentes), tempo gráfico.
- Ordena por qualquer coluna.
- Gráfico de dispersão "ganho bruto por operação × operações por ano", com as linhas de 1x e de 3x o custo. Mostra de relance que quase tudo fica abaixo de 3x.

### 3. Relatório de uma regra (`#/indices-regra/P-NNN`)

- **A ideia:**
  - título e mecanismo ("quem está do outro lado");
  - a regra exata, os parâmetros e as fontes, com links;
  - por que deveria ganhar 3x o custo.
- **Esperado × observado:** operações por ano, duração mediana e ganho por operação.
- **Prova de que foi registrada antes do teste:** commit e hora do registro × hora de cada leitura.
- **Por mercado e etapa:**
  - métricas nos 4 cenários de custo;
  - barras de retorno por ano;
  - compra × venda;
  - motivos de saída;
  - critérios que reprovaram.
- **Com a lista de operações (D2):** curva de capital, queda desde o pico e resultado por hora de entrada e dia da semana.
- Caminho do arquivo da regra e do teste.

### 4. Ciclos dos agentes (`#/indices-ciclos`)

- Linha do tempo dos ciclos: proposta → implementação → verificações → exploração → validação, ou erro, ou "limite da semana".
- Custo por agente e acumulado, por dia e por semana.
- Erros com o texto (por exemplo o limite de uso de 5 horas que derrubou a P-010).
- Estado do arquivo de pausa e o comando para retomar.
- As últimas linhas de `ops/state/proxy-cycle.log`.

### 5. Mercados, custos e medições (`#/indices-mercados`)

- **Os 9 mercados:**
  - o que cada um substitui e o horário do pregão;
  - custo base e conservador, deslizamento no stop;
  - se está no escopo, e o motivo quando não está.
- **Qualidade dos dados:** dias completos e dias pulados pela regra dos 90%.
- **Tamanho do movimento × custo:** 1, 5, 15, 30 e 60 min, por mercado. É a tabela 1 do veredito, saída de `anatomy.json`.
- **Eventos:** FOMC, inflação (CPI) e emprego (NFP) — quanto o preço anda e o resultado das 5 regras medidas, com a fonte das datas.
- **Fidelidade em ticks:** spread e saltos do preço.

### Mudanças nas páginas que já existem

- **Início:** cartão "Day trade em índices" com a frase da visão geral e o link.
- **Alertas do topo:** os mesmos avisos da visão geral.
- **Busca rápida:** as regras P-NNN e as 5 páginas novas.

## Como será feito

### Servidor (somente leitura, como o resto do portal)

1. Novo módulo `lab/indices_portal.py`, que monta um único JSON a partir dos arquivos acima:
   - `program`: estado, limites e prazos, usando `b3.proxy_program.status` (só leitura);
   - `funnel`, `placar`, `rules` (proposta + leituras), `cycles` e `costs`;
   - `markets`, `measurements`, `alerts`.
   - O texto escrito por agentes vai cortado em tamanho máximo e é tratado como não confiável.
2. Novo endereço `GET /api/indices` com cache próprio de 30 s. Meta: menos de 1 s e menos de 1 MB.
3. A página busca esse JSON só ao abrir uma página de Índices. O `export` (arquivo único) passa a embutir esse JSON.
4. `INDICES_CONTRACT`: a lista de campos que a página lê. Um teste mantém servidor e página em sincronia, como já faz o `STATE_CONTRACT`.
5. Os alertas de Índices entram em `_attention` sem pesar o `/api/state`: só contagens e textos curtos.

### Página

6. Novo arquivo `lab/dashboard_assets/indices.js`, embutido no script da página como o `results.js`. Mesmos auxiliares (`h`, `card`, `dataTable`, `badge`, `term`), mesmo visual e mesmas regras:
   - texto só via textContent;
   - nada carregado de fora;
   - CSP com nonce.
7. Rotas e grupo no `ROUTES` do `index.html`, com ícones, e explicações de termos para as palavras técnicas: régua, variante, exploração, validação, teste final, múltiplo do custo.

### Dados novos na pesquisa (`b3/`)

8. **(D2)** `b3/proxy_research.py` passa a gravar, em cada leitura, a lista de operações (entrada, saída, lado, bruto, líquido, motivo) em `research/proxies/trades/<mesmo nome>.json`, com cerca de 50 KB por leitura.
9. O pipeline grava um resumo por ciclo (regra, resultado, custo total, duração), para a linha do tempo não depender de remontar o log.

## Testes e critérios de pronto

| Teste | Critério |
|---|---|
| Unitários do montador (`tests/test_lab_indices_portal.py`, dados sintéticos) | Funil, placar, régua, avisos e estado do programa batem com os arquivos. Ledger vazio e proposta com erro não quebram nada |
| Contrato servidor × página | Todo campo lido pela página existe no JSON |
| Segurança | O texto de agentes não vira HTML. Nenhum endereço externo carregado. `/api/indices` só aceita GET em loopback |
| Desempenho | `/api/indices` abaixo de 1 s e de 1 MB com os dados atuais; `/api/state` não cresce mais de 2% |
| JavaScript | `node --check` em `indices.js`, como já se faz com `portal.js` e `results.js` |
| Navegador de verdade (`research/tools/portal_e2e.mjs` estendido) | As 5 páginas abrem sem erro no console, as tabelas ordenam, o link P-NNN abre o relatório. Largura de celular sem rolagem lateral |
| Conferência com a fonte | Os números do placar batem com `research/proxies/SCOREBOARD.md` em todas as linhas |
| Suíte inteira | `python -m pytest tests -q` sem falhas novas |

## Fases

| Fase | Entrega | Pronto quando |
|---|---|---|
| 0 | Resolver o trabalho pendente do portal (D1) | Árvore do portal limpa ou commitada |
| 1 | Montador + `/api/indices` + testes | Testes unitários, contrato e desempenho passam |
| 2 | Visão geral e Placar | As duas páginas abrem no navegador e batem com o SCOREBOARD |
| 3 | Relatório da regra (+ lista de operações, se D2 = sim) | Abre para P-001 a P-011; curva aparece nas leituras com operações |
| 4 | Ciclos dos agentes + alertas no topo e no Início | O erro da P-010 e o limite da semana aparecem como aconteceram |
| 5 | Mercados, custos e medições | Tabelas iguais às do veredito de 14/11 |
| 6 | Teste no navegador, busca, guia de uso, reinício do portal | Todos os critérios da tabela acima |

Cada fase vira um commit próprio, e só com os arquivos dela.

## Riscos e cuidados

- **Trabalho pendente de outra sessão:** 7 arquivos do portal com cerca de 1.040 linhas não commitadas (`lab/dashboard.py`, `index.html`, `portal.js`, `dryrun_live.js`, `trades_view.js` e dois testes). As rotas novas precisam editar `dashboard.py` e `index.html`, os mesmos arquivos. Ver D1.
- **O pipeline roda a cada 3 horas e aborta o ciclo se arquivos do repositório mudarem enquanto um agente trabalha.**
  - Até domingo, 21:00, os ciclos param no limite da semana, sem agentes, então dá para trabalhar na pasta principal.
  - A partir de segunda, o trabalho vai numa cópia separada (git worktree) e só entra na principal entre ciclos.
- **O portal em execução precisa ser reiniciado** para carregar o código novo. Ele foi aberto hoje às 12:28.
- **Leituras antigas não têm lista de operações:**
  - recalcular a validação ou o teste final para desenhar a curva seria ler de novo uma etapa que se lê uma vez só;
  - por isso só a exploração pode ser recalculada, marcada como "recalculada com o motor atual". Os números mudam um pouco por causa do deslizamento no stop adicionado em 14/11.

## Decisões do dono

| Decisão | Opções | Recomendação |
|---|---|---|
| D1. Trabalho pendente no portal | (a) Conferir que os testes passam e commitar como está, num commit separado, antes de começar; (b) construir por cima sem commitar o que é da outra sessão; (c) esperar a outra sessão terminar | (a): é o que destrava o resto sem misturar autorias |
| D2. Lista de operações | (a) Gravar daqui em diante e recalcular só a exploração das regras antigas, marcada; (b) gravar só daqui em diante; (c) não gravar (sem curva nem horários) | (a) |
| D3. Lugar no menu | (a) Grupo próprio "Índices (WIN/WDO)"; (b) dentro de "Laboratório" | (a): é outra frente de pesquisa, com outro mercado e outros custos |
| D4. Escopo da primeira entrega | (a) As 5 páginas; (b) só Visão geral + Placar + Ciclos, o resto depois | (a), entregue fase a fase |
