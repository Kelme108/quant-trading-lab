---
tipo: decisao
data: 2026-11-20
atualizado: 2026-11-20
tags: [cerebro, decisao, saidas, stop, alvo]
---

# Saídas em reais: alvo R$ 35 e stop R$ 90

**Data:** 2026-11-20  ·  **Quem pediu:** o dono ("vamos começar a testar estratégias com take profit e stop loss... ganho de R$ 30, R$ 35, pode ser R$ 35, e perda de R$ 90, o que me diz?")

## O que foi decidido

Testar, na exploração de WIN, as entradas que já existem com uma saída **fixa em reais**: alvo R$ 35, stop R$ 90, no máximo 60 minutos. Config pré-registrada: `b3/config/exit_brl.json` (saída **B1**). Código: o mesmo [[Menu-de-saidas]] (`python -m b3.exit_menu run --config b3/config/exit_brl.json ...`).

Em WIN 1 contrato: 1 ponto = R$ 0,20 e o tick (5 pontos) = R$ 1. Então **alvo = 175 pontos** e **stop = 450 pontos**.

## A opinião dada ao dono

- **Vale testar, mas o perfil é exigente.** Ganhar R$ 35 para arriscar R$ 90 (razão 2,6 para 1 contra) só fecha com **~73% de acertos** no custo medido (R$ 1,30 por trade); ~74% no custo pessimista (R$ 3,00). A melhor saída de alta taxa do menu anterior (S2) acertou 65–68%.
- **Um ponto só não prova nada.** Por isso o teste inclui os vizinhos: alvo 30 e 40, stop 80 e 100 (B2–B5). Uma regra só vale se o resultado for parecido nos vizinhos (planalto), não se só a combinação 35/90 fechar.
- **Risco de cauda.** Com perda diária máxima de R$ 300 no robô, três stops de R$ 90 encerram o dia. Muitos ganhos pequenos e poucas perdas grandes parecem bons até a primeira sequência ruim.
- **Só WIN.** Em WDO, R$ 35 são 7 ticks e o custo medido é ~20% do alvo.

## Erro registrado (errata)

O texto de comentário `honesty` em `exit_brl.json` cita "R$ 3,67 por ida e volta". **Está errado**: esse número é da base de custo da linha de substitutos. A simulação usa o custo **medido** da esteira (`b3/config/pattern_search_b3.json`, `cost_reevaluation.measured`): taxas R$ 0,25 por lado + 0,4 tick de slippage por lado = **R$ 1,30 por trade**. Só o comentário está errado; o arquivo não foi editado depois da rodada porque o hash dele ficou registrado no relatório (`config_sha256`).

Pelo mesmo erro, o resumo da demo de 2026-11-19 estimou o líquido com R$ 3,70 por trade. Corrigido em [[Demo-diario]].

## Escopo da primeira rodada

76 famílias que já tiveram ao menos uma candidata no menu de saídas por V (lista em `research/b3/exit_brl/families.txt`). É uma **prévia da mesma base de dados**, não uma busca cega. Contam como tentativas: **6.160 versões** (variante × saída), registradas em `research/b3/exit_brl/ledger.jsonl`.

## Resultado (rodada de 2026-11-20, só exploração, custo medido)

Relatório: `research/b3/exit_brl/20261120T175450Z.json`.

- **887 versões candidatas** em 64 das 76 famílias; **29 famílias** têm uma melhor versão com lucro também no custo pessimista (p90).
- **A base do dono (B1) não foi a melhor para a maioria.** Melhor saída por família: B1 em 10, B2 (alvo 30) em 13, B3 (alvo 40) em 16, B4 (stop 80) em 7, **B5 (stop 100) em 18**. Alvo e stop mais largos tendem a se sair um pouco melhor.
- **Taxa de acerto das melhores versões: 61% a 75% (mediana 67%).** Ficou abaixo dos ~73% que alvo 35 / stop 90 exigiriam se toda saída fosse alvo ou stop; fecha porque parte dos trades termina pelo relógio de 60 min, perto do zero.
- **Lucro por trade das melhores:** +R$ 2 a +R$ 4,5 no custo medido. É parecido com o do menu por V (S2/S3), não melhor.

Melhores com lucro no p90 (por trade, p90, trades/ano, bate o aleatório em todas):

| Família (variante) | Saída | Acerto | Por trade | p90 | Trades/ano |
|---|---|---|---|---|---|
| E-286 (1m, k=1,5, win=10) | B5 | 72,1% | +R$ 4,48 | +3,18 | 515 |
| E-156 (1m, k=1,25, win=30) | B5 | 72,0% | +R$ 4,14 | +2,84 | 449 |
| E-118 (5m, win=10, k=1) | B3 | 68,8% | +R$ 4,09 | +2,78 | 374 |
| E-062 (5m, run=3, k=0,8) | B3 | 63,8% | +R$ 3,73 | +2,37 | 261 |
| E-377 (1m, stay=15, k=1) | B3 | 67,2% | +R$ 3,44 | +2,12 | 287 |
| E-362 (1m, win=10, k=1,5) | B5 | 69,1% | +R$ 3,10 | +1,79 | 446 |
| E-193 (5m, step=0,33, k=0) | B4 | 65,7% | +R$ 2,91 | +1,58 | 587 |

**Ressalvas.** (1) Estas famílias já tinham sido escolhidas por resultado bom nesta mesma exploração: o ganho aparente soma duas seleções. (2) Mais de 26 mil versões lidas no total entre os menus. (3) **Nenhuma foi ligada na demo.** A demo é que separa sorte de edge.

## Como aplicar

- Candidata só vira robô da demo se passar nos mesmos filtros do menu **e** tiver lucro no custo pessimista (p90).
- Para rodar um robô com saída em reais, `b3/esteira_live.py` precisa aprender o tipo `["brl", valor]` (hoje só lê saídas em V). **Ainda não implementado.**
- Validação continua intocada; o teste final, trancado ([[Regras-inviolaveis]]).
