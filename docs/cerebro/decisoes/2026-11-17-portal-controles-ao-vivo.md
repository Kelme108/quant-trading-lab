---
tipo: decisao
data: 2026-11-17
atualizado: 2026-11-19
tags: [cerebro, decisao]
---

# Seção 'ao vivo' do portal com botões de risco

**Data:** 2026-11-17

O dono quer uma seção separada **Ao vivo (conta real)** com botões **Fechar posição**, **Pausar/Retomar entradas** e **Fechar e parar**, para administrar o risco manualmente. Os robôs **não** operam dinheiro real ainda; só a interface.

Desenho: `POST /api/control` → `live/commands/<robô>.json` → o próprio motor executa (`live/core/control.py`) e registra no journal. **Nunca feche por fora**: fechar direto na corretora levou a P-017 a `safe_mode` e o portal a mostrar posição velha. Os robôs reais usarão `live/config/live-b3-*.json` (journal e magic próprios); a demo fica só leitura. Credenciais só no `live/.env`, digitadas pelo dono.

Estado: branch `feat/portal-controls` (worktree separado) até o dono aprovar o merge. Robôs em execução precisam reiniciar para carregar o motor novo. Ver [[Portal]] e [[Engine-live]].
