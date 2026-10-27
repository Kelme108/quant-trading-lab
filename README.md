# Trading Lab

Laboratório reproduzível para pesquisa de estratégias de criptomoedas spot com Freqtrade.

> **Estado de segurança:** este projeto permanece em `dry_run`. Não contém chaves privadas, não usa margem/alavancagem e não envia ordens reais.

## Decisão inicial

O motor principal é o **Freqtrade via Docker Compose**, porque reúne estratégia Python, download de OHLCV, backtesting, dry-run e FreqUI em um fluxo open source. A instalação nativa não foi escolhida neste ambiente: o host é Windows/MSYS2 e o WSL Kali fornece Docker Engine. O laboratório fica em `D:\Trade-Initial` (montado no WSL como `/mnt/d/Trade-Initial`), onde há espaço suficiente para a imagem e os dados.

A estratégia inicial é [SmaTrendBaseline.py](user_data/strategies/SmaTrendBaseline.py): SMA(20)/SMA(50), filtro de regime SMA(200), saída pelo cruzamento contrário e stop-loss fixo de 10%. Os parâmetros são uma **baseline ex-ante**, não uma recomendação nem um resultado de rentabilidade.

## Diagnóstico do ambiente

Executado em 20/10/2026:

- Diretório: `/mnt/d/Trade-Initial` no WSL; projeto no host em `D:\Trade-Initial`.
- WSL 2, distribuição Kali Linux Rolling 2025.2.
- Host Windows 11 Home, acesso via MSYS2/Git Bash no VS Code.
- Python 3.13.3, Git 2.47.2, Docker 28.3.3, Compose v2.39.1.
- Carteira hipotética local: 100 USDT na configuração de dry-run; o limite futuro de R$ 500 continua apenas uma hipótese, sem depósito ou recomendação.
- Espaço livre na unidade `D:`: aproximadamente 120 GB no diagnóstico.
- O arquivo experimental anterior `bot.py` foi preservado e não participa do laboratório Freqtrade.

## Estrutura

```text
.
├── docs/                         # pesquisa, decisões e procedimento
├── research/                     # registros de experimentos
├── reports/                      # relatórios exportados/interpretados
├── tests/                        # testes da baseline
├── user_data/
│   ├── backtest_results/
│   ├── data/
│   ├── strategies/
│   └── config.dryrun.json        # sem credenciais; dry_run=true
├── docker-compose.yml
└── README.md
```

## Guia para iniciantes

O procedimento completo, com comandos, explicação de backtest, lookahead, recursive,
dry-run, custos, benchmarks, manifestos e critérios de decisão está em
[docs/guia-utilizacao-freqtrade.md](docs/guia-utilizacao-freqtrade.md).


Execute os comandos a partir do WSL, não do Git Bash, para usar o Docker Engine Linux:

```bash
cd /mnt/d/Trade-Initial
docker compose version
```

Se o Compose estiver disponível, obtenha a imagem oficial e valide o layout:

```bash
docker compose pull
docker compose run --rm freqtrade list-strategies \
  --config user_data/config.dryrun.json
```

O `docker-compose.yml` monta somente `user_data` no container. Não há segredo no arquivo de configuração. Antes do pull, libere espaço em `C:` ou mova o armazenamento do Docker/WSL.

## Baixar dados públicos

A Binance é somente a origem dos candles neste experimento; isso não cria conta nem exige saldo. O endpoint usado deve ser público e as restrições regionais da Binance precisam ser verificadas no momento da execução.

Para um ensaio inicial reproduzível de 365 dias:

```bash
docker compose run --rm freqtrade download-data \
  --config user_data/config.dryrun.json \
  --exchange binance \
  --pairs BTC/USDT \
  --timeframes 1h \
  --timerange 20251020-20261020 \
  --data-format-ohlcv feather

docker compose run --rm freqtrade list-data \
  --exchange binance \
  --datadir user_data/data \
  --show-timerange \
  --data-format-ohlcv feather
```

A data final deve ser registrada pelo comando `list-data`; verifique lacunas relevantes e confirme que existe pelo menos o período de startup de 200 candles antes da janela analisada.

## Primeiro backtest de referência

O período abaixo é um exemplo operacional; registre a data efetivamente disponível antes de interpretar os resultados. Não ajuste os parâmetros depois de observar o resultado deste primeiro ensaio:

```bash
docker compose run --rm freqtrade backtesting \
  --config user_data/config.dryrun.json \
  --strategy SmaTrendBaseline \
  --strategy-path user_data/strategies \
  --timeframe 1h \
  --pairs BTC/USDT \
  --timerange 20251020-20261020 \
  --dry-run-wallet 100 \
  --fee 0.001 \
  --export trades \
  --export-filename user_data/backtest_results/sma-baseline-20251020-20261020.json \
  --backtest-directory user_data/backtest_results \
  --breakdown day month
```

O arquivo de saída e a tabela do terminal são a fonte dos números. Este repositório não inventa métricas: retorno, drawdown, Sharpe, Sortino, profit factor, expectativa e número de operações só serão reportados depois da execução.

Para análise de look-ahead após os dados existirem:

```bash
docker compose run --rm freqtrade lookahead-analysis \
  --config user_data/config.dryrun.json \
  --strategy SmaTrendBaseline \
  --strategy-path user_data/strategies \
  --timeframe 1h \
  --pairs BTC/USDT \
  --timerange 20251020-20261020 \
  --minimum-trade-amount 1
```

## FreqUI local (optional)

A API fica **desabilitada por padrão** em `user_data/config.dryrun.json`. Para uma
sessão local deliberada, crie uma cópia não versionada da configuração, habilite a API,
configure credenciais fortes e use `listen_ip_address: "0.0.0.0"` somente dentro do
container. O host deve continuar publicando somente `127.0.0.1:8080`.

Não preencha credenciais no arquivo versionado. Nunca publique a porta na LAN ou na
Internet.

```bash
# somente depois de editar uma cópia local não versionada
# api_server.enabled=true
# api_server.listen_ip_address="0.0.0.0"
docker compose config --quiet
docker compose ps
curl -I http://127.0.0.1:8080/
```

O `docker-compose.yml` usa uma versão fixa do Freqtrade e não reinicia o bot
automaticamente; iniciar o serviço é uma ação deliberada de forward test em dry-run.

Cada experimento deve ter um manifesto em `research/manifests/` contendo a versão do
runtime, hashes do código e dos dados, intervalo efetivo, parâmetros, custos, comando e
resultado. O template está em `research/experiment-manifest.yaml`. Gere um manifesto
antes de interpretar qualquer novo resultado e preserve os artefatos anteriores.

Validações locais:

```bash
python3 research/validate_ohlcv.py user_data/data/binance/BTC_USDT-1h.feather
python3 -m unittest discover -s tests -v
```

A baseline `SmaTrendBaseline` permanece congelada. Qualquer mudança de regra deve ser
uma nova estratégia/versionamento e não uma alteração retrospectiva da referência.

## Dry-run

Depois de revisar os logs e os resultados do backtest:

```bash
docker compose up -d freqtrade
docker compose logs -f freqtrade
```

O `dry_run` continua `true`, `trading_mode` é `spot`, `can_short` é falso e a whitelist contém apenas BTC/USDT. Não altere para live, não adicione chaves privadas e não habilite saque. O dry-run é forward testing, não prova de execução futura.

## Qualidade e critérios

A baseline será considerada apenas uma referência de infraestrutura. Antes de qualquer decisão posterior, compare cronologicamente exploração, validação e teste final; inclua taxas e slippage conservador, benchmarks comprar-e-manter e ficar em caixa, regimes distintos, sensibilidade dos parâmetros/custos e walk-forward. Um resultado negativo ou inconclusivo é aceitável e deve ser preservado.

## Fontes oficiais consultadas

- [Freqtrade stable](https://www.freqtrade.io/en/stable/)
- [Installation](https://docs.freqtrade.io/en/stable/installation/)
- [Docker quickstart](https://www.freqtrade.io/en/stable/docker_quickstart/)
- [Strategy customization](https://docs.freqtrade.io/en/stable/strategy-customization/)
- [Backtesting](https://docs.freqtrade.io/en/latest/backtesting/)
- [Data download](https://docs.freqtrade.io/en/stable/data-download/)
- [FreqUI](https://docs.freqtrade.io/en/latest/freq-ui/)
- [Exchanges](https://www.freqtrade.io/en/stable/exchanges/)
- [Binance Spot API](https://github.com/binance/binance-spot-api-docs)
- [Atlas Studio](https://www.mind-vest.io/studio)
- [MetaTrader 5](https://www.metatrader5.com/)
