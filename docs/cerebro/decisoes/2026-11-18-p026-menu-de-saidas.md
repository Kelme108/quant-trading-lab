---
tipo: decisao
data: 2026-11-18
atualizado: 2026-11-19
tags: [cerebro, decisao]
---

# Estudo da P-026, P-032 e menu de saídas

**Data:** 2026-11-18

O dono: "mais válido do que gerar muitas estratégias é uma que funciona e gere lucro"; a gestão de stop e alvo vale tanto quanto a entrada.

- **Estudo P-026** (`b3/config/p026_lab.json`, 720 versões, exploração): a P-026 original (seguir) é negativa em toda saída. O **fade** do fechamento de 1 min fora de uma caixa comprimida de 120 min passa em WIN (melhor BT: +R$ 2,37 por trade, p90 +0,67, 398/ano, ~R$ 940/ano por contrato, bate o aleatório). WDO: nenhuma. Validação intocada.
- Virou a regra **P-032** (`b3/proxy_rules/p032_win_box_fade_trailing.py`): 1871/1871 sinais iguais ao laboratório. Robô `demo-b3-p032-win`.
- O motor ganhou **MOVE_STOP** e `take_profit` no servidor.
- **Menu de saídas** sobre todas as famílias ([[Menu-de-saidas]]); 11 robôs da esteira ligados na demo ([[Robos-demo]]).
- Teto de agente subiu de US$ 30 para **US$ 50 por dia** (dono: "mude o teto de gasto de 30 para 50... agora é com você, deixe tudo ligado").
- O limite de uso do Claude passou a **pular a hora** em vez de pausar a esteira.

**Como aplicar:** relatar os trades da P-032 e dos E contra a pesquisa; qualquer passo para a conta real exige uma leitura da validação, uma só vez.
