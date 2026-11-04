# Relatório da auditoria das estratégias do Trading Lab

Data: 2026-11-04. Escopo: BTC/USDT, ETH/USDT e BNB/USDT, 1h, somente long, somente dry-run. Nenhuma ordem real, chave ou conta foi usada.

**Todas as decisões abaixo são PROVISÓRIAS.** `lab/config/gates.json` e `portfolio.json` continuam com `_status: PROPOSED` (decisão do usuário na Fase 0). Os arquivos de configuração e os protegidos por SHA não foram editados. `final_test_unlocked` continua `false`; o holdout prospectivo (desde 2026-10-21) não foi lido.

## 1. Veredito

**Nenhuma estratégia está aprovada para a carteira.** O `orchestrator portfolio` produziu uma carteira vazia (`research/portfolio/20261104T152035Z.json`).

- **H-009** (WeeklyBreakoutRegime) é a única candidata em exploração. Passou nos gates nos três pares, mas:
  - a validação não foi lida;
  - o maior trade do BNB responde por 80% do lucro;
  - o IC95% do retorno total inclui zero em ETH e BNB;
  - em Sharpe com custo 2x, só vence o buy-and-hold e a `Sma200Baseline` no BTC;
  - tem 89–93% de sobreposição em posição com a `Sma200Baseline`.
  - Isso é indício, não evidência fora da amostra. **Não declaro sucesso.**
- **H-016** (TSMOM N30) e **H-008** (VolSqueeze com 20% de exposição) já usaram a leitura da validação e não foram aprovadas. O lucro por dia caiu de 63% a 96% da exploração para a validação.
- **H-017** (melhoria da H-009) foi rejeitada na exploração e é redundante: correlação diária de 0,86 a 0,98 com a H-009, sem ganho de Sharpe.
- As demais foram rejeitadas, inválidas ou descartadas por terem menos de 30 trades.
- Nenhuma estratégia sobrevive para o dry-run congelado. O holdout só poderia ser avaliado a partir de 2027-04-21 e com pelo menos 30 trades fechados.

## 2. Inventário final

Fonte: `research/lab.sqlite` (hipóteses, decisões, arquivamento) e `research/hypothesis-ledger.md`.

| ID | Família (variantes) | Local | Exploração BTC / ETH / BNB | Validação | Classe (provisória) |
|---|---|---|---|---|---|
| H-001 | SmaTrend (1) | ativa, baseline protegida | rej. / rej. / rej. | não lida | rejeitada |
| H-002 | Donchian (1) | ativa, baseline protegida | rej. / rej. / rej. | não lida | rejeitada |
| H-003 | Bollinger (1) | ativa, baseline protegida | rej. / rej. / rej. | não lida | rejeitada |
| H-004 | SlowTSMOM (1) | removida (só no git, `544a3d5`) | rej. mas implementação inválida | não lida | inválida |
| H-005 | VolSqueeze (2) | `_archive/` | rej. / rej. / rej. | não lida | rejeitada |
| H-006 | RegimeGatedPullback (1) | removida (só no git) | nunca rodou (warm-up 5520 > 4500) | não lida | inválida |
| H-007 | RisingTrendBreakout (1) | `_archive/` | rej. / rej. / rej. | não lida | rejeitada |
| H-008 | VolSqueeze (2) | `_archive/` | cand. / cand. / cand. | **lida**: rej. / inconclusiva (ETH) / rej. | rejeitada |
| H-009 | WeeklyBreakout (2) | **ativa** | cand. / cand. / cand. | não lida | **candidata_exploração** |
| H-010 | UptrendPullback (1) | `_archive/` | rej. / rej. / rej. | não lida | rejeitada |
| H-011 | TripleBottom (2) | `_archive/` | descartada: 9 / 5 / 6 trades na calibração | não lida | inconclusiva |
| H-012 | EMASnapback (2) | `_archive/` | rej. / rej. / rej. | não lida | rejeitada |
| H-013 | TripleBottom 4h | `_archive/` | descartada: 5 / 3 / 1 trades | não lida | inconclusiva |
| H-014 | EMASnapback 4h | `_archive/` | descartada: 33 / 27 / 32 trades (ETH < 30) | não lida | inconclusiva |
| H-015 | TSMOM (2), grid de 10 | `_archive/` | célula N30 escolhida (DSR 0,999, PBO 0,31) | via H-016 | rejeitada (família) |
| H-016 | TSMOM (2) | `_archive/` | cand. / cand. / cand. | **lida**: rej. / cand. (ETH) / rej. | rejeitada |
| H-017 | WeeklyBreakout (2) | `_archive/` | cand. / **rej.** / cand. | não lida | rejeitada, redundante |

Nota: H-009 e H-017 são a mesma família (`WeeklyBreakoutRegime`), 2 de 3 variantes. `Sma200Baseline` é referência protegida e não recebe decisão de gates.

## 3. Total de configurações testadas

Cada célula de grid e cada cenário de custo conta como teste. Fonte: `research/lab.sqlite` e `research/experiments/`.

| Item | Quantidade |
|---|---:|
| Hipóteses registradas (H-001 a H-017) | 17 |
| Células do grid da H-015 (uma delas é a H-016) | 10 |
| Variantes de sensibilidade (`sens-*`: 9 EMASnapback, 8 TripleBottom) | 17 |
| Variantes da ablação do filtro de regime | 4 |
| **Regras distintas (aprox., sem contar H-016 duas vezes)** | **≈ 47** |

Cada regra foi rodada em 3 pares e em 2 a 4 cenários de custo. A multiplicidade é alta: com ≈ 47 regras testadas sobre o mesmo histórico, um resultado isolado positivo tem pouca força como evidência.

## 4. Métricas padrão por estratégia

Exploração (IS) cobre cerca de 2017-08 a 2024-07 por par. As tabelas A a D vêm de `audit_exploration.py`. **Não estão incluídas as janelas OOS (validação) nem os últimos 12 meses (semi-contaminados) para nenhuma estratégia, porque a validação só foi lida para H-008 e H-016** (veja a seção 5). As janelas dos ciclos são recortadas no fim da exploração.

### Tabela A — métricas padrão, exploração (IS), custo base

Fonte: `research/audit/<H>-exploration-metrics.json` (gerado por `research/tools/audit_exploration.py`); DD gate e decisão: `research/lab.sqlite`. `exp.` = exposição calibrada. DD gate = trades fechados; DD m2m = marcado a mercado (informativo).

| Hip. | Par | exp. | Decisão (gates) | Trades | Lucro (ROI %) | Sem o melhor | DD gate | DD m2m | WR [Wilson 95%] | PF | Expectância % | Payoff | Maior seq. perdas | Sharpe | Sortino | Calmar | Tempo em posição |
|---|---|--:|---|--:|--:|--:|--:|--:|---|--:|--:|--:|--:|--:|--:|--:|--:|
| H-001 | BTC | 1.0 | rej. | 383 | 186.5 (186%) | 112.2 | 50.4% | 62% | 33% [28%–37%] | 1.12 | 0.40 | 2.65 | 18 | 0.59 | 1.01 | 0.27 | 31% |
| H-001 | ETH | 1.0 | rej. | 388 | 759.6 (760%) | 502.5 | 46.5% | 48% | 34% [30%–39%] | 1.21 | 0.77 | 2.77 | 11 | 0.88 | 1.54 | 0.76 | 31% |
| H-001 | BNB | 1.0 | rej. | 366 | 2529.8 (2530%) | 1263.4 | 44.0% | 50% | 39% [34%–44%] | 1.26 | 1.41 | 2.81 | 9 | 1.01 | 2.16 | 1.25 | 31% |
| H-002 | BTC | 1.0 | rej. | 787 | -51.7 (-52%) | -91.8 | 79.8% | 81% | 33% [29%–36%] | 0.96 | -0.01 | 2.06 | 31 | -0.01 | -0.01 | -0.12 | 41% |
| H-002 | ETH | 1.0 | rej. | 819 | -28.8 (-29%) | -71.3 | 73.6% | 80% | 35% [32%–38%] | 0.98 | 0.08 | 1.94 | 14 | 0.18 | 0.32 | -0.06 | 41% |
| H-002 | BNB | 1.0 | rej. | 835 | 61.0 (61%) | -352.9 | 88.6% | 90% | 32% [29%–36%] | 1.01 | 0.32 | 2.49 | 12 | 0.44 | 0.93 | 0.08 | 41% |
| H-003 | BTC | 1.0 | rej. | 71 | -14.8 (-15%) | -25.4 | 31.9% | 35% | 55% [43%–66%] | 0.82 | -0.18 | 0.68 | 4 | -0.17 | -0.21 | -0.07 | 2% |
| H-003 | ETH | 1.0 | rej. | 61 | -19.9 (-20%) | -24.1 | 42.7% | 43% | 62% [50%–73%] | 0.72 | -0.30 | 0.47 | 4 | -0.22 | -0.26 | -0.07 | 2% |
| H-003 | BNB | 1.0 | rej. | 50 | 48.7 (49%) | 24.3 | 17.7% | 19% | 64% [50%–76%] | 1.60 | 0.90 | 1.06 | 4 | 0.52 | 0.96 | 0.31 | 1% |
| H-005 | BTC | 1.0 | rej. | 31 | 520.4 (520%) | 112.3 | 50.1% | 67% | 29% [16%–47%] | 1.89 | 10.90 | 8.02 | 7 | 0.86 | 1.30 | 0.45 | 33% |
| H-005 | ETH | 1.0 | rej. | 36 | 507.2 (507%) | 94.9 | 50.6% | 61% | 31% [18%–47%] | 1.57 | 10.87 | 7.45 | 8 | 0.79 | 1.21 | 0.49 | 30% |
| H-005 | BNB | 1.0 | rej. | 36 | 879.2 (879%) | 255.2 | 42.9% | 59% | 22% [12%–38%] | 2.63 | 21.16 | 17.94 | 10 | 0.84 | 1.50 | 0.68 | 33% |
| H-007 | BTC | 1.0 | rej. | 23 | 563.3 (563%) | 197.5 | 36.7% | 54% | 35% [19%–55%] | 2.36 | 13.08 | 8.96 | 7 | 1.02 | 1.69 | 0.58 | 19% |
| H-007 | ETH | 1.0 | rej. | 27 | 329.5 (330%) | 88.6 | 44.7% | 59% | 22% [11%–41%] | 2.00 | 9.88 | 13.03 | 12 | 0.72 | 1.10 | 0.40 | 16% |
| H-007 | BNB | 1.0 | rej. | 36 | 163.3 (163%) | -48.6 | 25.1% | 58% | 22% [12%–38%] | 1.59 | 9.46 | 11.27 | 7 | 0.51 | 0.99 | 0.27 | 15% |
| H-008 | BTC | 0.2 | cand. | 31 | 78.3 (78%) | 34.2 | 12.2% | 25% | 29% [16%–47%] | 2.76 | 10.90 | 8.02 | 7 | 0.77 | 1.14 | 0.34 | 33% |
| H-008 | ETH | 0.2 | cand. | 36 | 87.4 (87%) | 21.4 | 12.5% | 20% | 31% [18%–47%] | 2.58 | 10.87 | 7.45 | 8 | 0.71 | 1.05 | 0.48 | 30% |
| H-008 | BNB | 0.2 | cand. | 36 | 171.5 (172%) | 30.5 | 10.3% | 30% | 22% [12%–38%] | 4.11 | 21.16 | 17.94 | 10 | 0.68 | 1.45 | 0.53 | 33% |
| H-009 | BTC | 0.25 | cand. | 58 | 113.8 (114%) | 89.3 | 7.2% | 11% | 38% [27%–51%] | 2.93 | 5.62 | 5.81 | 9 | 1.19 | 2.08 | 1.10 | 18% |
| H-009 | ETH | 0.25 | cand. | 81 | 61.8 (62%) | 38.6 | 18.5% | 25% | 31% [22%–42%] | 1.74 | 2.62 | 4.37 | 14 | 0.67 | 1.09 | 0.29 | 17% |
| H-009 | BNB | 0.25 | cand. | 80 | 133.6 (134%) | 27.0 | 14.5% | 32% | 31% [22%–42%] | 2.26 | 5.62 | 6.60 | 11 | 0.63 | 1.27 | 0.42 | 18% |
| H-010 | BTC | 0.1 | rej. | 145 | -1.7 (-2%) | -4.1 | 8.1% | 9% | 41% [34%–50%] | 0.96 | -0.11 | 1.36 | 7 | -0.08 | -0.11 | -0.03 | 21% |
| H-010 | ETH | 0.1 | rej. | 187 | -9.1 (-9%) | -11.1 | 15.5% | 16% | 35% [29%–42%] | 0.84 | -0.50 | 1.54 | 13 | -0.37 | -0.51 | -0.09 | 22% |
| H-010 | BNB | 0.1 | rej. | 173 | -1.6 (-2%) | -4.4 | 14.5% | 15% | 36% [29%–43%] | 0.97 | -0.07 | 1.75 | 16 | -0.05 | -0.08 | -0.02 | 22% |
| H-012 | BTC | 0.2 | rej. | 121 | -7.3 (-7%) | -8.7 | 10.2% | 10% | 56% [47%–65%] | 0.65 | -0.31 | 0.50 | 7 | -0.64 | -0.78 | -0.11 | 1% |
| H-012 | ETH | 0.2 | rej. | 114 | -9.5 (-10%) | -10.5 | 11.2% | 11% | 59% [50%–67%] | 0.59 | -0.43 | 0.41 | 8 | -0.72 | -0.82 | -0.13 | 2% |
| H-012 | BNB | 0.2 | rej. | 129 | -15.4 (-15%) | -16.1 | 16.4% | 17% | 50% [42%–59%] | 0.42 | -0.65 | 0.42 | 7 | -1.23 | -1.39 | -0.15 | 2% |
| H-016 | BTC | 0.15 | cand. | 94 | 150.2 (150%) | 91.1 | 14.0% | 24% | 37% [28%–47%] | 3.12 | 7.54 | 5.86 | 10 | 1.16 | 1.84 | 0.59 | 54% |
| H-016 | ETH | 0.15 | cand. | 89 | 115.2 (115%) | 83.0 | 11.4% | 25% | 35% [26%–45%] | 2.93 | 6.29 | 5.73 | 12 | 0.83 | 1.20 | 0.47 | 54% |
| H-016 | BNB | 0.15 | cand. | 96 | 517.0 (517%) | 283.7 | 9.7% | 48% | 42% [32%–52%] | 4.12 | 16.59 | 8.77 | 6 | 1.02 | 1.98 | 0.65 | 56% |
| H-017 | BTC | 0.3 | cand. | 54 | 73.7 (74%) | 58.1 | 7.6% | 12% | 35% [24%–49%] | 2.25 | 3.65 | 4.62 | 7 | 0.87 | 1.41 | 0.71 | 15% |
| H-017 | ETH | 0.3 | rej. | 70 | 61.4 (61%) | 34.4 | 20.3% | 27% | 31% [22%–43%] | 1.73 | 2.58 | 4.30 | 11 | 0.64 | 1.05 | 0.26 | 15% |
| H-017 | BNB | 0.3 | cand. | 62 | 171.3 (171%) | 44.6 | 11.0% | 34% | 34% [23%–46%] | 2.60 | 7.35 | 7.41 | 6 | 0.68 | 1.39 | 0.47 | 16% |

### Tabela B — custo 1x (base) vs 2x (`base_2x`) e referências, exploração

Referências na mesma janela, custo e exposição da estratégia: buy-and-hold (B&H) e `Sma200Baseline` (Sma). Sharpe anualizado em retornos diários.

| Hip. | Par | Lucro base | Lucro 2x | Sharpe base | Sharpe 2x | B&H Sharpe (2x) | Sma Sharpe (2x) | B&H retorno | Corr. diária com Sma | Sobreposição com Sma |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| H-001 | BTC | 186.5 | -25.1 | 0.59 | 0.07 | 0.89 | 0.77 | 1250% | 0.43 | 55% |
| H-001 | ETH | 759.6 | 120.6 | 0.88 | 0.47 | 0.83 | 0.80 | 928% | 0.41 | 59% |
| H-001 | BNB | 2529.8 | 629.6 | 1.01 | 0.73 | 1.32 | 0.99 | 32966% | 0.50 | 58% |
| H-002 | BTC | -51.7 | -94.5 | -0.01 | -0.71 | 0.89 | 0.77 | 1250% | 0.45 | 52% |
| H-002 | ETH | -28.8 | -94.5 | 0.18 | -0.50 | 0.83 | 0.80 | 928% | 0.44 | 55% |
| H-002 | BNB | 61.0 | -91.3 | 0.44 | -0.11 | 1.32 | 0.99 | 32966% | 0.53 | 55% |
| H-003 | BTC | -14.8 | -33.6 | -0.17 | -0.51 | 0.89 | 0.77 | 1250% | 0.12 | 60% |
| H-003 | ETH | -19.9 | -35.3 | -0.22 | -0.50 | 0.83 | 0.80 | 928% | 0.08 | 56% |
| H-003 | BNB | 48.7 | 24.9 | 0.52 | 0.32 | 1.32 | 0.99 | 32966% | 0.03 | 54% |
| H-005 | BTC | 520.4 | 457.1 | 0.86 | 0.82 | 0.89 | 0.77 | 1250% | 0.65 | 81% |
| H-005 | ETH | 507.2 | 435.8 | 0.79 | 0.75 | 0.83 | 0.80 | 928% | 0.68 | 88% |
| H-005 | BNB | 879.2 | 763.9 | 0.84 | 0.81 | 1.32 | 0.99 | 32966% | 0.76 | 83% |
| H-007 | BTC | 563.3 | 513.2 | 1.02 | 0.98 | 0.89 | 0.77 | 1250% | 0.64 | 98% |
| H-007 | ETH | 329.5 | 291.2 | 0.72 | 0.69 | 0.83 | 0.80 | 928% | 0.52 | 95% |
| H-007 | BNB | 163.3 | 132.1 | 0.51 | 0.47 | 1.32 | 0.99 | 32966% | 0.72 | 99% |
| H-008 | BTC | 78.3 | 74.6 | 0.77 | 0.74 | 0.89 | 0.64 | 1250% | 0.61 | 81% |
| H-008 | ETH | 87.4 | 82.8 | 0.71 | 0.68 | 0.83 | 0.67 | 928% | 0.68 | 88% |
| H-008 | BNB | 171.5 | 164.5 | 0.68 | 0.67 | 1.32 | 0.76 | 32966% | 0.73 | 83% |
| H-009 | BTC | 113.8 | 103.2 | 1.19 | 1.11 | 0.89 | 0.66 | 1250% | 0.48 | 90% |
| H-009 | ETH | 61.8 | 50.5 | 0.67 | 0.58 | 0.83 | 0.71 | 928% | 0.43 | 89% |
| H-009 | BNB | 133.6 | 117.6 | 0.63 | 0.59 | 1.32 | 0.81 | 32966% | 0.71 | 93% |
| H-010 | BTC | -1.7 | -6.5 | -0.08 | -0.33 | 0.89 | 0.57 | 1250% | 0.48 | 93% |
| H-010 | ETH | -9.1 | -14.7 | -0.37 | -0.63 | 0.83 | 0.57 | 928% | 0.27 | 87% |
| H-010 | BNB | -1.6 | -7.2 | -0.05 | -0.30 | 1.32 | 0.63 | 32966% | 0.24 | 87% |
| H-012 | BTC | -7.3 | -14.8 | -0.64 | -1.31 | 0.89 | 0.64 | 1250% | 0.09 | 64% |
| H-012 | ETH | -9.5 | -16.4 | -0.72 | -1.27 | 0.83 | 0.67 | 928% | 0.09 | 59% |
| H-012 | BNB | -15.4 | -22.7 | -1.23 | -1.81 | 1.32 | 0.76 | 32966% | 0.07 | 66% |
| H-016 | BTC | 150.2 | 137.8 | 1.16 | 1.10 | 0.89 | 0.61 | 1250% | 0.57 | 64% |
| H-016 | ETH | 115.2 | 105.2 | 0.83 | 0.78 | 0.83 | 0.63 | 928% | 0.60 | 69% |
| H-016 | BNB | 517.0 | 485.6 | 1.02 | 0.99 | 1.32 | 0.71 | 32966% | 0.62 | 67% |
| H-017 | BTC | 73.7 | 63.9 | 0.87 | 0.78 | 0.89 | 0.68 | 1250% | 0.55 | 97% |
| H-017 | ETH | 61.4 | 49.8 | 0.64 | 0.54 | 0.83 | 0.73 | 928% | 0.46 | 93% |
| H-017 | BNB | 171.3 | 154.1 | 0.68 | 0.64 | 1.32 | 0.84 | 32966% | 0.72 | 96% |

### Tabela C — retorno por ciclo de mercado, exploração, custo base (retorno da estratégia / buy-and-hold)

| Hip. | Par | 2018 | 2019 | 2020-21 | 2022 | 2023+ |
|---|---|--:|--:|--:|--:|--:|
| H-001 | BTC | -7% / -73% | 26% / 94% | 26% / 544% | -30% / -65% | 19% / 252% |
| H-001 | ETH | 93% / -82% | 3% / -2% | 170% / 2753% | -17% / -68% | 36% / 160% |
| H-001 | BNB | 51% / -27% | 54% / 127% | 733% / 3633% | -27% / -52% | 12% / 129% |
| H-002 | BTC | -62% / -73% | 30% / 94% | 15% / 544% | -52% / -65% | -10% / 252% |
| H-002 | ETH | -64% / -82% | -13% / -2% | 517% / 2753% | -40% / -68% | -40% / 160% |
| H-002 | BNB | 3% / -27% | 63% / 127% | 82% / 3633% | -49% / -52% | -45% / 129% |
| H-003 | BTC | -1% / -73% | -1% / 94% | -15% / 544% | -13% / -65% | -4% / 252% |
| H-003 | ETH | -13% / -82% | 2% / -2% | -23% / 2753% | 2% / -68% | 7% / 160% |
| H-003 | BNB | 34% / -27% | 23% / 127% | -6% / 3633% | -6% / -52% | -4% / 129% |
| H-005 | BTC | -19% / -73% | 115% / 94% | 106% / 544% | -18% / -65% | 49% / 252% |
| H-005 | ETH | -23% / -82% | 43% / -2% | 678% / 2753% | -36% / -68% | 11% / 160% |
| H-005 | BNB | -47% / -27% | 46% / 127% | 919% / 3633% | -31% / -52% | 79% / 129% |
| H-007 | BTC | 0% / -73% | 94% / 94% | 252% / 544% | 0% / -65% | 4% / 252% |
| H-007 | ETH | -3% / -82% | 12% / -2% | 345% / 2753% | 0% / -68% | -5% / 160% |
| H-007 | BNB | -8% / -27% | -11% / 127% | 330% / 3633% | -4% / -52% | -22% / 129% |
| H-008 | BTC | -4% / -73% | 26% / 94% | 28% / 544% | -4% / -65% | 11% / 252% |
| H-008 | ETH | -5% / -82% | 8% / -2% | 92% / 2753% | -8% / -68% | 3% / 160% |
| H-008 | BNB | -12% / -27% | 13% / 127% | 151% / 3633% | -7% / -52% | 16% / 129% |
| H-009 | BTC | -2% / -73% | 21% / 94% | 32% / 544% | 0% / -65% | 9% / 252% |
| H-009 | ETH | 9% / -82% | 10% / -2% | 36% / 2753% | -2% / -68% | 0% / 160% |
| H-009 | BNB | -5% / -27% | 26% / 127% | 115% / 3633% | -7% / -52% | -2% / 129% |
| H-010 | BTC | -1% / -73% | 3% / 94% | -1% / 544% | -1% / -65% | -0% / 252% |
| H-010 | ETH | -4% / -82% | 2% / -2% | 1% / 2753% | -3% / -68% | -2% / 160% |
| H-010 | BNB | 1% / -27% | 2% / 127% | -1% / 3633% | -4% / -52% | -0% / 129% |
| H-012 | BTC | -0% / -73% | -2% / 94% | -4% / 544% | -3% / -65% | -1% / 252% |
| H-012 | ETH | -0% / -82% | 1% / -2% | -5% / 2753% | -4% / -68% | -2% / 160% |
| H-012 | BNB | -4% / -27% | -4% / 127% | -4% / 3633% | -3% / -52% | -2% / 129% |
| H-016 | BTC | -11% / -73% | 17% / 94% | 62% / 544% | -7% / -65% | 24% / 252% |
| H-016 | ETH | -2% / -82% | -0% / -2% | 84% / 2753% | -4% / -68% | 10% / 160% |
| H-016 | BNB | -7% / -27% | 63% / 127% | 177% / 3633% | -5% / -52% | 15% / 129% |
| H-017 | BTC | -2% / -73% | 26% / 94% | 38% / 544% | 0% / -65% | 4% / 252% |
| H-017 | ETH | 11% / -82% | 14% / -2% | 32% / 2753% | 0% / -68% | -1% / 160% |
| H-017 | BNB | 1% / -27% | 24% / 127% | 128% / 3633% | -3% / -52% | -2% / 129% |

`2023+` termina no fim da exploração de cada par (jul/2024); não inclui a validação.

### Tabela D — bootstrap dos trades (blocos de 3, 4000 reamostras, semente fixa), custo base, exploração

| Hip. | Par | Trades | Retorno médio por trade (IC95%) | Retorno total (IC95%) |
|---|---|--:|---|---|
| H-001 | BTC | 383 | 0.40% [-0.12%; 0.99%] | 186% [-57%; 2338%] |
| H-001 | ETH | 388 | 0.77% [0.09%; 1.50%] | 758% [-24%; 10977%] |
| H-001 | BNB | 366 | 1.41% [0.32%; 2.70%] | 2521% [20%; 88183%] |
| H-002 | BTC | 787 | -0.01% [-0.30%; 0.31%] | -52% [-95%; 433%] |
| H-002 | ETH | 819 | 0.08% [-0.26%; 0.44%] | -29% [-95%; 1009%] |
| H-002 | BNB | 835 | 0.32% [-0.20%; 0.87%] | 61% [-95%; 5412%] |
| H-003 | BTC | 71 | -0.18% [-0.97%; 0.54%] | -15% [-52%; 43%] |
| H-003 | ETH | 61 | -0.30% [-1.25%; 0.56%] | -20% [-56%; 38%] |
| H-003 | BNB | 50 | 0.90% [-0.53%; 2.06%] | 49% [-26%; 162%] |
| H-005 | BTC | 31 | 10.90% [-1.49%; 25.59%] | 519% [-54%; 9818%] |
| H-005 | ETH | 36 | 10.87% [-2.07%; 33.35%] | 506% [-62%; 51648%] |
| H-005 | BNB | 36 | 21.16% [-2.20%; 61.67%] | 878% [-67%; 123610%] |
| H-007 | BTC | 23 | 13.08% [-0.66%; 31.63%] | 562% [-27%; 10212%] |
| H-007 | ETH | 27 | 9.88% [-1.98%; 30.04%] | 329% [-48%; 11436%] |
| H-007 | BNB | 36 | 9.46% [-3.25%; 33.75%] | 163% [-72%; 15375%] |
| H-008 | BTC | 31 | 10.90% [-1.49%; 25.59%] | 79% [-10%; 292%] |
| H-008 | ETH | 36 | 10.87% [-2.07%; 33.35%] | 87% [-15%; 613%] |
| H-008 | BNB | 36 | 21.16% [-2.20%; 61.67%] | 171% [-16%; 1746%] |
| H-009 | BTC | 58 | 5.62% [1.41%; 8.48%] | 114% [21%; 220%] |
| H-009 | ETH | 81 | 2.62% [0.12%; 5.76%] | 62% [-0%; 195%] |
| H-009 | BNB | 80 | 5.62% [-0.28%; 15.52%] | 133% [-8%; 916%] |
| H-010 | BTC | 145 | -0.11% [-1.15%; 1.09%] | -2% [-16%; 17%] |
| H-010 | ETH | 187 | -0.50% [-1.45%; 0.60%] | -9% [-24%; 11%] |
| H-010 | BNB | 173 | -0.07% [-1.15%; 1.13%] | -2% [-18%; 21%] |
| H-012 | BTC | 121 | -0.31% [-0.65%; 0.03%] | -7% [-15%; 1%] |
| H-012 | ETH | 114 | -0.43% [-0.92%; -0.02%] | -10% [-19%; -1%] |
| H-012 | BNB | 129 | -0.65% [-1.05%; -0.32%] | -15% [-24%; -8%] |
| H-016 | BTC | 94 | 7.54% [0.48%; 15.71%] | 150% [4%; 568%] |
| H-016 | ETH | 89 | 6.29% [0.93%; 12.84%] | 115% [11%; 383%] |
| H-016 | BNB | 96 | 16.59% [1.23%; 35.85%] | 516% [15%; 4365%] |
| H-017 | BTC | 54 | 3.65% [0.74%; 7.81%] | 74% [10%; 232%] |
| H-017 | ETH | 70 | 2.58% [-0.39%; 5.78%] | 61% [-10%; 203%] |
| H-017 | BNB | 62 | 7.35% [0.09%; 19.94%] | 171% [-0%; 1348%] |

## 5. IS → OOS (só onde a validação já foi lida) e últimos 12 meses

Lucro base por dia, exploração vs validação. Fonte: `research/lab.sqlite` (tabela `metrics`); dias de `lab/config/splits.json` (2513 e 837 para BTC e ETH; 2453 e 817 para BNB).

| Hipótese | Par | Trades IS → OOS | Lucro/dia IS | Lucro/dia OOS | Variação | Sem o melhor trade (OOS) |
|---|---|---|--:|--:|--:|--:|
| H-008 | BTC | 31 → 12 | 0,0312 | 0,0075 | −76% | −2,1 |
| H-008 | ETH | 36 → 10 | 0,0348 | 0,0082 | −76% | 0,0 |
| H-008 | BNB | 36 → 8 | 0,0699 | 0,0126 | −82% | −0,5 |
| H-016 | BTC | 94 → 43 | 0,0598 | 0,0023 | −96% | −5,2 |
| H-016 | ETH | 89 → 33 | 0,0458 | 0,0170 | −63% | +2,6 |
| H-016 | BNB | 96 → 43 | 0,2108 | 0,0076 | −96% | −3,2 |

- A janela de validação é semi-contaminada para ideias de tendência: H-008, H-016 e os ciclos da `Sma200Baseline` já a viram. Os últimos 12 meses (2025-10-21 a 2026-10-20) estão dentro dela e também são semi-contaminados.
- Esses números são do registro e não foram recalculados. **Para as demais estratégias, OOS e últimos 12 meses não foram lidos.**
- Os números de OOS têm 8–43 trades, então são ruidosos.

## 6. Antes × depois: H-009 → H-017

Mesma janela de exploração, mesmos custos, mesmos pares. A H-009 aparece na exposição oficial (0,25) e na da H-017 (0,30). A calibração de exposição é automática, por regra do lab (H-017: 0,30), então a comparação justa é a de mesma exposição.
Fontes: `research/audit/H-009-exploration-metrics.json`, `H-009x30-exploration-metrics.json`, `H-017-exploration-metrics.json`.

| Par | Config. | Trades | Lucro base / 2x | Sem o melhor | DD m2m | Sharpe base / 2x | PF | WR | Maior seq. perdas | IC95% retorno total |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|---|
| BTC | H-009 @0,25 | 58 | 113,8 / 103,2 | 89,3 | 11% | 1,19 / 1,11 | 2,93 | 38% | 9 | [0,21; 2,20] |
| BTC | H-009 @0,30 | 58 | 145,9 / 131,2 | 116,5 | 13% | 1,20 / 1,12 | 2,83 | 38% | 9 | [0,25; 2,98] |
| BTC | **H-017 @0,30** | 54 | 73,7 / 63,9 | 58,1 | 12% | 0,87 / 0,78 | 2,25 | 35% | 7 | [0,10; 2,32] |
| ETH | H-009 @0,25 | 81 | 61,8 / 50,5 | 38,6 | 25% | 0,67 / 0,58 | 1,74 | 31% | 14 | [−0,00; 1,95] |
| ETH | H-009 @0,30 | 81 | 76,1 / 61,6 | 45,9 | 29% | 0,68 / 0,58 | 1,70 | 31% | 14 | [−0,01; 2,60] |
| ETH | **H-017 @0,30** | 70 | 61,4 / 49,8 | 34,4 | 27% | 0,64 / 0,54 | 1,73 | 31% | 11 | [−0,10; 2,03] |
| BNB | H-009 @0,25 | 80 | 133,6 / 117,6 | 27,0 | 32% | 0,63 / 0,59 | 2,26 | 31% | 11 | [−0,08; 9,16] |
| BNB | H-009 @0,30 | 80 | 164,9 / 143,6 | 31,9 | 34% | 0,66 / 0,61 | 2,16 | 31% | 11 | [−0,10; 13,30] |
| BNB | **H-017 @0,30** | 62 | 171,3 / 154,1 | 44,6 | 34% | 0,68 / 0,64 | 2,60 | 34% | 6 | [−0,00; 13,48] |

| Par | Correlação diária H-009 × H-017 | Tempo de H-017 em posição dentro do de H-009 | Tempo de H-009 em posição dentro do de H-017 |
|---|--:|--:|--:|
| BTC | 0,86 | 100% | 82% |
| ETH | 0,89 | 100% | 85% |
| BNB | 0,98 | 100% | 85% |

- **Resultado:** a correlação é maior que 0,7 e não há ganho de Sharpe (BTC piora, ETH empata, BNB sobe 0,03). A H-017 é redundante.
- **Gates:** a H-017 falhou no ETH por drawdown no cenário stress (25,5% > 25%).
- **Mecanismo visado:** a maior sequência de perdas caiu (9→7, 14→11, 11→6), mas o drawdown marcado a mercado não mudou de forma relevante.
- **Por ciclo:** a H-017 ajudou um pouco em 2022 (ETH −3% → 0%, BNB −9% → −3%) e perdeu em 2020–21 (ETH +44% → +32%, BNB +141% → +128%) e em 2023+ no BTC (+11% → +4%).
- **Não calculados:** DSR, PBO e platô. A proposta tinha uma célula só, então não são calculáveis.

## 7. Carteira

`python -m lab.orchestrator portfolio` → `research/portfolio/20261104T152035Z.json`: **carteira vazia**.

Nenhuma hipótese tem `candidate_for_portfolio` em todo par × split, pois exige exploração e validação. A H-009 só tem exploração; H-008 e H-016 foram rejeitadas na validação. Os critérios de consistência (≥ 0,25) e de correlação (≤ 0,7) nem chegaram a ser aplicados. Para referência, na exploração a consistência é 0,45 (H-009), 0,45 (H-008), 0,22 (H-016) e 0,35 (H-017).

## 8. Limitações e pendências

1. **Gates PROPOSED.** Se o usuário alterar os limites, as classificações devem ser reavaliadas.
2. **Drawdown dos gates ignora a posição aberta.** O DD marcado a mercado é maior (H-009 BNB: 14,5% → 32%; H-016 BNB: 9,7% → 48%). Por decisão do usuário, é só informativo; nenhum gate foi alterado.
3. **Três pares não são três amostras independentes.** Correlação diária com o BTC: 0,787 (ETH) e 0,635 (BNB), em `scenarios.json`.
4. **Faltam os arquivos de proposta** `research/proposals/H-008.json`, `H-009.json` e `H-016.json`. A regra desses está só no registro e na docstring da estratégia. Não foram criados retroativamente.
5. **H-004 e H-006** saíram do strategy path sem ir para `_archive/`. São recuperáveis do git (`544a3d5`), documentado como exceção.
6. **Revisões dos agentes:** validator, quant e risk rodaram para H-005, H-007, H-008, H-009 e H-016. As demais hipóteses só tiveram diagnóstico determinístico, e a H-004 só o validator.
7. **H-017 sem revisão dos agentes** e sem `grid_explore`, por já ter sido rejeitada.
8. **Fora do escopo desta auditoria:** existe código novo em `live/` e `tests/live/` (camada de execução em tempo real, com MetaTrader 5), criado por outra sessão. Não foi revisado nem commitado aqui.
9. **Famílias pendentes de `docs/prompt-proxima-etapa.md`** (Donchian 4h, Pullback MTF, RSI2) não entraram, por falta de aprovação.

## 9. Fontes

- Métricas: `research/audit/*-exploration-metrics.json` (`research/tools/audit_exploration.py`).
- Diagnóstico: `research/audit/fase2-diagnostico.md`; contexto da Fase 4: `research/audit/research-diagnosis.md`.
- Revisões: `research/experiments/H-005-exploration/`, `H-007-…`, `H-008-…`, `H-009-…`, `H-016-…`.
- Registro: `research/lab.sqlite`, `research/hypothesis-ledger.md`, `research/registry-dump.sql`, `research/command-log.md`.
- Grid: `research/grids/H-015-report.md`.
