# Primeiro experimento — status em 20/10/2026

## Escopo congelado

- Motor: Freqtrade `2026.9` via Docker Compose.
- Estratégia: `SmaTrendBaseline`.
- Mercado: spot, `BTC/USDT`, origem Binance.
- Timeframe: `1h`.
- Carteira hipotética local: 100 USDT em dry-run; o limite futuro de R$ 500 não foi usado nem representa depósito.
- Taxa do experimento: 0,001 por lado.
- Execução real: desabilitada (`dry_run: true`).
- API/FreqUI: habilitada somente localmente; o host publica `127.0.0.1:8080`.

## Ambiente e dados

- WSL Kali Linux 2025.2, WSL 2.
- Python 3.13.3, pip 25.1.1, Git 2.47.2.
- Docker 28.3.3 e Docker Compose v2.39.1.
- Espaço usado para o laboratório: unidade `D:`; aproximadamente 120 GB livres no diagnóstico.
- Binance: somente origem dos candles públicos; nenhuma conta ou chave privada foi usada.
- Arquivo: `user_data/data/binance/BTC_USDT-1h.feather`.
- Cobertura disponível: `2025-10-20 00:00 UTC` a `2026-10-20 17:00 UTC`.
- Candles disponíveis: 8.778.
- A janela efetiva do backtest começou em `2025-10-28 08:00 UTC` após o startup de 200 candles.

## Validações concluídas

- `docker compose config --quiet`: passou.
- `python3 -m json.tool user_data/config.dryrun.json`: passou.
- `python3 -m unittest discover -s tests -v`: 3 testes passaram.
- `freqtrade list-strategies`: `SmaTrendBaseline` apareceu como `OK`.
- `lookahead-analysis`: **sem viés detectado**; 20 sinais analisados, 0 entradas enviesadas, 0 saídas enviesadas e nenhum indicador enviesado.

## Backtest de referência válido

Arquivo exportado: `user_data/backtest_results/backtest-result-2026-10-20_18-08-58.zip`.

Parâmetros:

- `SMA(20)` cruza acima/abaixo da `SMA(50)`.
- Entrada exige fechamento acima da `SMA(200)` e volume positivo.
- Saída por cruzamento descendente ou stop-loss fixo de 10%.
- ROI mínimo configurado em 100% para não encerrar imediatamente por ROI; a saída da baseline é o cruzamento ou o stop.
- Uma posição máxima.
- Carteira inicial: 100 USDT.
- Taxa: 0,1% na entrada e 0,1% na saída.

Métricas observadas no terminal do Freqtrade:

- Período: `2025-10-28 08:00` a `2026-10-20 00:00` UTC.
- Operações: 1.
- Operações vencedoras/empates/perdedoras: 0/0/1.
- Retorno absoluto: `-1,534 USDT`.
- Retorno percentual: `-1,53%`.
- Saldo final: `98,466 USDT`.
- Drawdown fechado: `1,534 USDT (1,53%)`.
- Profit factor: `0,00`.
- Expectativa: `-1,53 USDT` por operação; razão `-1,00`.
- Sharpe de trades fechados: `-100,00`.
- Sortino de trades fechados: `-100,00`.
- Sharpe diário baseado na carteira: `-0,51`.
- Sortino diário baseado na carteira: `-0,06`.
- Mudança do mercado no período: `-28,57%`.
- Saída observada: `sma20_cross_down`.
- Duração média: 1 dia e 21 horas.

As métricas de Sharpe/Sortino e as demais razões são estatisticamente frágeis com apenas uma operação. Este resultado é uma validação do caminho técnico, não evidência de rentabilidade nem critério para operar.

## Primeiro comando inválido e correções

O primeiro backtest foi recusado porque `dry_run_wallet` de 100 multiplicado por `tradable_balance_ratio` de 0,99 produzia 99 USDT, menor que o `stake_amount` de 100. A razão foi corrigida para `1.0`.

Uma execução posterior com `minimal_roi: {"0": 0.0}` fechou a única operação imediatamente por ROI. Ela não foi usada como resultado. A baseline foi corrigida para `minimal_roi: {"0": 100.0}` e o backtest válido foi executado novamente.

## FreqUI e dry-run

O container está ativo e em modo dry-run, com `dry_run: true`, spot, sem chaves privadas e sem ordens reais. A configuração usa credenciais locais fortes ignoradas pelo Git.

A configuração atual precisa ser recriada para aplicar `listen_ip_address: "0.0.0.0"` dentro do container. Isso é necessário porque o Docker publica o host em `127.0.0.1:8080`, enquanto o processo no container precisa aceitar a interface interna. O host continua limitado ao loopback e não fica exposto à rede.

O comando de recriação foi bloqueado nesta sessão pela política local de segurança para exposição de serviços. Execute no WSL:

```bash
cd /mnt/d/Trade-Initial
docker compose up -d --force-recreate freqtrade
curl -I http://127.0.0.1:8080/
```

Depois, abra `http://127.0.0.1:8080/` no navegador. O usuário local é `localuser`; a senha foi gerada no arquivo ignorado `user_data/config.dryrun.json` e não é registrada neste relatório.

Verifique o estado com:

```bash
docker compose ps
docker compose logs --tail=50 freqtrade
```

## Próximos critérios

O resultado atual é inconclusivo devido a apenas uma operação. Antes de ajustar parâmetros ou considerar qualquer capital:

1. preservar esta baseline e seu período;
2. separar exploração, validação e teste final por tempo;
3. testar períodos com regimes de alta, baixa e lateralização;
4. repetir com slippage conservador e sensibilidade de taxas;
5. comparar com ficar em caixa e comprar-e-manter no mesmo intervalo;
6. executar walk-forward;
7. avaliar sensibilidade em torno de 20/50/200 sem escolher o melhor ponto retrospectivamente;
8. acompanhar dry-run como forward test, sem transformá-lo em live;
9. só então comparar breakout e mean reversion sob o mesmo protocolo.

Nenhuma decisão de operação real é recomendada por este experimento.
