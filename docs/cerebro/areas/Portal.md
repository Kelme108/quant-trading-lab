---
tipo: area
atualizado: 2026-11-19
tags: [cerebro, portal, dashboard]
---

# Portal

Painel local de acompanhamento: `python -m lab.dashboard serve --open` → `http://127.0.0.1:8765` (atualiza a cada 15 s). Código: `lab/dashboard.py`, `lab/dashboard_assets/`, `lab/universes.py`, `lab/indices_portal.py`, `lab/demo_b3.py`.

## Seções

- **Cripto**, **B3: WIN e WDO** e **Substitutos**: mesmas páginas de resultados e gráfico de candles (1/5/15 min por sessão; padrão o timeframe da regra).
- **Índices (WIN/WDO)** (`#/indices`, `#/indices-placar`, `#/indices-regra/P-NNN`, `#/indices-ciclos`, `#/indices-mercados`).
- **Demo B3** (`#/b3-demo`): robôs na demo com visão ao vivo 1/5/15 m (`live/feed.py`, a cada 5 s). Somente leitura.
- **Ao vivo (conta real)**: botões **Fechar posição**, **Pausar/Retomar entradas**, **Fechar e parar**; escrevem o arquivo de comando do robô ([[Engine-live]]). Nenhum robô real ligado. Estado: branch `feat/portal-controls`, aguardando merge ([[2026-11-17-portal-controles-ao-vivo]]).

## Segurança

Escuta só em `127.0.0.1`, banco aberto `mode=ro`, aceita GET/HEAD, recusa `Host` desconhecido, CSP com nonce. Texto vindo de agente ou da web entra como texto puro. Sem CDN. Os botões da conta real são a única exceção de escrita, e passam pelo arquivo de comando.

## Dica

Quem reiniciar o portal é o dono: matar o processo dele pode ser bloqueado.
