---
tipo: area
atualizado: 2026-11-22
tags: [cerebro, portal, dashboard]
---

# Portal

Painel local de acompanhamento: `python -m lab.dashboard serve --open` → `http://127.0.0.1:8765` (atualiza a cada 15 s). Código: `lab/dashboard.py`, `lab/dashboard_assets/`, `lab/universes.py`, `lab/indices_portal.py`, `lab/demo_b3.py`.

## Seções

- **Cripto**, **B3: WIN e WDO** e **Substitutos**: mesmas páginas de resultados e gráfico de candles (1/5/15 min por sessão; padrão o timeframe da regra).
- **Índices (WIN/WDO)** (`#/indices`, `#/indices-placar`, `#/indices-regra/P-NNN`, `#/indices-ciclos`, `#/indices-mercados`).
- **Demo B3** (`#/b3-demo`): robôs na demo com visão ao vivo 1/5/15 m (`live/feed.py`, a cada 5 s). Somente leitura.
- **Esteira** (`#/b3-esteira`, criada em 2026-11-22 a pedido do dono): estado do ciclo e pausa, **gasto da noite contra o teto**, triagem (por que as versões caem), melhores saídas por família (menus S1–S4 em V e B1–B5 em R$), saídas testadas, portão das regras P, selecionadas e últimos 40 ciclos. Só lê arquivos (`research/b3/esteira/`, `ops/state/exit_*`, configs); não lê validação nem teste final. Código: `lab/esteira_portal.py` (cache de 30 s, rota `GET /api/esteira`) e `lab/dashboard_assets/esteira.js`. Teste: `tests/test_lab_esteira_portal.py`. Ver [[Esteira]] e [[Menu-de-saidas]].
- **Ao vivo (conta real)**: botões **Fechar posição**, **Pausar/Retomar entradas**, **Fechar e parar**; escrevem o arquivo de comando do robô ([[Engine-live]]). Nenhum robô real ligado. Estado: branch `feat/portal-controls`, aguardando merge ([[2026-11-17-portal-controles-ao-vivo]]).

## Segurança

Escuta só em `127.0.0.1`, banco aberto `mode=ro`, aceita GET/HEAD, recusa `Host` desconhecido, CSP com nonce. Texto vindo de agente ou da web entra como texto puro. Sem CDN. Os botões da conta real são a única exceção de escrita, e passam pelo arquivo de comando.

## Como acrescentar uma seção

Cada seção tem quatro encaixes e **o menu lateral tem lista própria**:

1. leitor em Python (`lab/<nome>_portal.py`) e rota `GET /api/<nome>` em `lab/dashboard.py`;
2. página em `lab/dashboard_assets/<nome>.js`, incluída por um marcador `/*__NOME__*/` em `index.html` e no `render_page`;
3. entrada na lista `ROUTES` (a rota existe);
4. entrada na lista `NAV` (o **botão** do menu aparece). Esquecer a `NAV` deixa a página acessível só por `#/rota`.

## Dica

Quem reiniciar o portal é o dono: matar o processo dele pode ser bloqueado. O servidor lê os arquivos da página a cada pedido, então basta atualizar o navegador depois de mudar `index.html` ou um `.js`; mudança em `.py` pede reiniciar.
