# Manual completo do Trading Lab com Freqtrade

Este manual foi escrito para quem está começando do zero com Freqtrade e com pesquisa
quantitativa. Ele explica o que cada parte faz, quais comandos executar, como interpretar
os resultados e como validar uma estratégia sem confundir um backtest com uma promessa de
lucro.

> **Escopo de segurança deste projeto**
>
> Este laboratório usa somente **spot**, somente posições **long**, somente **dry-run** e
> não possui chaves privadas de exchange. Não habilite live trading, margem, futuros,
> alavancagem, short ou saques como parte deste manual.

---

## Sumário

1. [O que é o Freqtrade](#1-o-que-é-o-freqtrade)
2. [O que este laboratório faz](#2-o-que-este-laboratório-faz)
3. [Conceitos básicos](#3-conceitos-básicos)
4. [Estrutura do projeto](#4-estrutura-do-projeto)
5. [Instalação e ambiente](#5-instalação-e-ambiente)
6. [Primeira verificação segura](#6-primeira-verificação-segura)
7. [Dados OHLCV](#7-dados-ohlcv)
8. [Estratégias implementadas](#8-estratégias-implementadas)
9. [Testes locais](#9-testes-locais)
10. [Como registrar um experimento](#10-como-registrar-um-experimento)
11. [Como executar um backtest](#11-como-executar-um-backtest)
12. [Como validar uma estratégia](#12-como-validar-uma-estratégia)
13. [Lookahead analysis](#13-lookahead-analysis)
14. [Recursive analysis](#14-recursive-analysis)
15. [Métricas e interpretação](#15-métricas-e-interpretação)
16. [Custos, spread e slippage](#16-custos-spread-e-slippage)
17. [Benchmarks](#17-benchmarks)
18. [Exploração, validação e teste final](#18-exploração-validação-e-teste-final)
19. [Walk-forward e robustez](#19-walk-forward-e-robustez)
20. [Dry-run](#20-dry-run)
21. [FreqUI opcional](#21-frequi-opcional)
22. [Como criar uma nova estratégia](#22-como-criar-uma-nova-estratégia)
23. [Esteira de validação](#23-esteira-de-validação)
24. [Erros comuns](#24-erros-comuns)
25. [Critérios de decisão](#25-critérios-de-decisão)
26. [Checklist completo](#26-checklist-completo)
27. [Glossário](#27-glossário)
28. [Próximos passos](#28-próximos-passos)

---

# 1. O que é o Freqtrade

O Freqtrade é um software open source que organiza um bot de pesquisa e execução para
mercados de criptomoedas. Neste projeto ele é usado como **laboratório**, não como
sistema de operação real.

Ele oferece comandos para:

- baixar dados históricos;
- carregar estratégias Python;
- simular estratégias com backtesting;
- executar um acompanhamento em tempo real sem ordens reais, chamado dry-run;
- verificar possíveis vieses de look-ahead;
- verificar dependência excessiva do histórico inicial;
- exibir resultados por período;
- expor uma API/FreqUI opcional.

O Freqtrade não elimina os problemas de pesquisa quantitativa. Ele não consegue, usando
apenas candles OHLCV históricos:

- reconstruir perfeitamente o spread histórico;
- saber a fila de uma ordem limit;
- garantir preenchimento parcial;
- conhecer a latência real de cada ordem;
- descobrir o caminho exato do preço dentro de uma vela;
- provar que uma estratégia terá desempenho futuro.

Por isso, o Freqtrade é o motor da pesquisa, mas o protocolo estatístico e o controle dos
experimentos continuam sendo responsabilidade do laboratório.

Fontes técnicas principais:

- [Documentação oficial do Freqtrade](https://www.freqtrade.io/en/stable/)
- [Backtesting](https://www.freqtrade.io/en/stable/backtesting/)
- [Strategy customization](https://www.freqtrade.io/en/latest/strategy-customization/)
- [Lookahead analysis](https://www.freqtrade.io/en/stable/lookahead-analysis/)
- [Recursive analysis](https://www.freqtrade.io/en/stable/recursive-analysis/)

---

# 2. O que este laboratório faz

O fluxo do projeto é:

```text
candles públicos
      ↓
validação dos dados
      ↓
estratégia Python
      ↓
backtesting histórico
      ↓
lookahead + recursive analysis
      ↓
custos + benchmarks + robustez
      ↓
forward test em dry-run
```

O fluxo **não** é:

```text
backtest positivo → operar com dinheiro real
```

Um resultado histórico positivo é somente uma observação. Para ser considerado uma
hipótese de pesquisa razoável, ele precisa também ser:

- reproduzível;
- causal;
- resistente a custos;
- comparado a benchmarks;
- estável em períodos diferentes;
- testado fora da amostra;
- compatível com uma execução plausível.

## 2.1 Níveis de utilização

### Nível A — execução manual

Você executa cada comando individualmente e analisa os resultados. É o nível atual do
projeto.

### Nível B — esteira reproduzível

Um conjunto de comandos executa validação, backtests, análises e geração de relatórios de
forma padronizada. O projeto tem parte dos componentes, mas ainda depende de execução e
interpretação manuais.

### Nível C — pipeline automatizado

Um comando ou CI executa tudo, preserva artefatos e bloqueia resultados inválidos. Este
nível ainda não deve ser considerado concluído. Primeiro é preciso executar uma rodada
manual completa e verificar se o protocolo está correto.

---

# 3. Conceitos básicos

## 3.1 Par

Um par representa dois ativos negociados entre si:

```text
BTC/USDT
```

Neste caso:

- BTC é o ativo comprado/vendido;
- USDT é a moeda de cotação;
- uma posição long spot compra BTC usando USDT.

## 3.2 Candle

Um candle resume o comportamento do preço durante um intervalo. No projeto, o intervalo
é de uma hora (`1h`). Cada candle possui, normalmente:

- `open`: preço de abertura;
- `high`: maior preço do intervalo;
- `low`: menor preço do intervalo;
- `close`: preço de fechamento;
- `volume`: volume negociado;
- `date`: início do intervalo.

Um candle de 1h não informa a ordem dos eventos entre `high` e `low`. Se a máxima ocorreu
antes ou depois da mínima, essa informação não está no OHLCV.

## 3.3 Timeframe

O timeframe é o tamanho de cada candle:

- `5m`: cinco minutos;
- `1h`: uma hora;
- `4h`: quatro horas;
- `1d`: um dia.

Mudar o timeframe muda a hipótese. Uma estratégia em 1h não é automaticamente a mesma
estratégia em 15m ou 4h.

## 3.4 Estratégia

Uma estratégia é uma classe Python que define, pelo menos:

1. indicadores;
2. condições de entrada;
3. condições de saída;
4. stoploss e outras regras de risco;
5. timeframe e período inicial necessário.

## 3.5 Indicador

Um indicador é uma transformação dos dados disponíveis até determinado momento. Exemplos:

- SMA: média móvel simples;
- RSI: índice de força relativa;
- ATR: medida de amplitude/volatilidade;
- banda de Bollinger;
- canal de Donchian.

O indicador precisa ser calculado de forma causal: para decidir no candle `t`, ele só pode
usar informação disponível até `t`.

## 3.6 Sinal

Um sinal é a condição que a estratégia marca em determinado candle. No Freqtrade atual,
as colunas comuns são:

- `enter_long`: entrada comprada;
- `exit_long`: saída da posição comprada;
- `enter_tag`: explicação textual da entrada;
- `exit_tag`: explicação textual da saída.

## 3.7 Startup candles

Indicadores precisam de histórico antes de produzir valores confiáveis. A estratégia SMA
usa uma SMA de 200 candles e, por isso, define:

```python
startup_candle_count = 200
```

Esses candles iniciais servem para aquecer os indicadores e não devem ser interpretados
como parte normal da janela de resultado.

## 3.8 Backtest

Backtest é uma simulação sobre dados históricos. Ele é útil para encontrar bugs, comparar
hipóteses e estudar comportamento. Ele não é execução real.

## 3.9 Dry-run

Dry-run acompanha o mercado atual e simula ordens sem enviar ordens reais à exchange. Ele
é um forward test operacional, não uma prova de rentabilidade futura.

## 3.10 Live trading

Live trading enviaria ordens reais. **Não faz parte deste projeto e não deve ser habilitado.**

---

# 4. Estrutura do projeto

```text
.
├── README.md
├── docker-compose.yml
├── docs/
│   ├── research-decision.md
│   └── guia-utilizacao-freqtrade.md
├── research/
│   ├── command-log.md
│   ├── experiment-manifest.yaml
│   ├── hypothesis-ledger.md
│   ├── validation-protocol.md
│   ├── validation-protocol-v2.md
│   ├── validation-run-2026-10-20.md
│   ├── validate_ohlcv.py
│   └── manifests/
├── reports/
│   ├── initial-experiment-status.md
│   └── generated/
├── tests/
│   ├── test_strategy.py
│   └── test_safety_configuration.py
└── user_data/
    ├── config.dryrun.json
    ├── data/
    ├── backtest_results/
    └── strategies/
```

## 4.1 O que não deve ser editado casualmente

- a baseline congelada;
- dados de um experimento concluído;
- resultados antigos;
- manifestos preenchidos;
- relatórios históricos.

Se uma regra mudar, crie uma nova estratégia ou nova versão. Não reaproveite o mesmo nome
para uma regra diferente.

## 4.2 O que é gerado

Normalmente são gerados:

- arquivos de trades;
- arquivos `.zip` de backtest;
- metadados JSON;
- logs;
- relatórios de lookahead;
- relatórios de recursive;
- banco SQLite do dry-run.

Cada execução precisa de um identificador único. Nunca substitua silenciosamente um
artefato anterior.

---

# 5. Instalação e ambiente

O ambiente recomendado é:

- Windows como sistema hospedeiro;
- WSL2 com uma distribuição Linux;
- Docker Engine acessível dentro do WSL;
- Docker Compose;
- Python local no WSL somente para os testes e ferramentas auxiliares.

## 5.1 Abrir o WSL

Abra o terminal da distribuição Linux e entre no projeto:

```bash
cd /mnt/d/Trade-Initial
```

O caminho do Windows é:

```text
D:\Trade-Initial
```

O caminho equivalente dentro do WSL é:

```text
/mnt/d/Trade-Initial
```

## 5.2 Conferir versões

```bash
docker --version
docker compose version
python3 --version
```

O projeto foi documentado com Freqtrade `2026.9` na imagem Docker. O Docker Compose é
responsável por usar essa imagem, portanto não é necessário instalar Freqtrade
manualmente no sistema hospedeiro.

## 5.3 Ambiente Python para ferramentas locais

Os testes de estratégias usam `pandas`. O validador Feather normalmente precisa de
`pyarrow`.

Crie um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pandas pyarrow
```

Para sair do ambiente virtual:

```bash
deactivate
```

O ambiente virtual não deve ser commitado.

## 5.4 Verificar o Compose sem iniciar o bot

```bash
docker compose config --quiet
```

Esse comando apenas verifica a configuração do Compose. Ele não executa backtest nem
inicia o bot.

Se houver erro, não prossiga. Leia a mensagem e corrija a configuração.

---

# 6. Primeira verificação segura

Antes de qualquer comando que inicie o Freqtrade, confira o arquivo:

[user_data/config.dryrun.json](../user_data/config.dryrun.json)

Os valores essenciais devem ser:

```json
"dry_run": true,
"trading_mode": "spot",
"max_open_trades": 1
```

As credenciais da exchange devem estar vazias:

```json
"key": "",
"secret": ""
```

A API deve estar desabilitada por padrão:

```json
"enabled": false
```

## 6.1 Por que não há chaves

O download de candles públicos não precisa de chave privada. O backtest também não
precisa. O dry-run deste projeto não deve usar uma conta real.

Não coloque no projeto:

- API key;
- API secret;
- senha de exchange;
- chave de saque;
- token privado;
- credencial em comentário ou relatório.

## 6.2 Teste automatizado de segurança

```bash
python3 -m unittest tests.test_safety_configuration -v
```

Esse teste verifica, entre outras coisas:

- dry-run;
- spot;
- ausência de chaves;
- API desabilitada;
- bind de loopback;
- imagem Docker pinada;
- ausência de reinício automático.

## 6.3 Validar JSON

```bash
python3 -m json.tool user_data/config.dryrun.json > /dev/null
```

Se o comando não produzir erro, o arquivo é JSON sintaticamente válido. Isso não significa
que todos os valores sejam adequados; por isso também usamos o teste de segurança e o
validador do Freqtrade.

## 6.4 Validar estratégias no container

```bash
docker compose run --rm freqtrade list-strategies \
  --config user_data/config.dryrun.json
```

O comando deve listar as estratégias carregáveis. `--rm` remove o container temporário ao
final; os arquivos montados em `user_data` permanecem no projeto.

---

# 7. Dados OHLCV

## 7.1 Dados existentes

O laboratório possui um arquivo Feather para:

```text
Binance / BTC/USDT / spot / 1h
```

A cobertura e a quantidade efetivas devem ser confirmadas pelo comando `list-data` e pelo
validador. O número registrado anteriormente não deve ser tratado como garantia permanente
se o arquivo for baixado novamente.

## 7.2 Listar os dados disponíveis

```bash
docker compose run --rm freqtrade list-data \
  --exchange binance \
  --datadir user_data/data \
  --show-timerange \
  --data-format-ohlcv feather
```

Procure:

- par;
- timeframe;
- tipo de mercado/candle;
- primeira data;
- última data;
- formato.

## 7.3 Baixar uma nova série

Exemplo:

```bash
docker compose run --rm freqtrade download-data \
  --config user_data/config.dryrun.json \
  --exchange binance \
  --pairs BTC/USDT \
  --timeframes 1h \
  --timerange 20240101-20261020 \
  --data-format-ohlcv feather
```

A data final do comando é uma solicitação. O arquivo real pode terminar antes, dependendo
da disponibilidade no momento do download. Sempre execute `list-data` depois.

## 7.4 Validar o arquivo

```bash
python3 research/validate_ohlcv.py \
  user_data/data/binance/BTC_USDT-1h.feather
```

O resultado é JSON. Guarde-o junto ao manifesto.

O validador verifica:

- colunas necessárias;
- timestamps convertíveis para UTC;
- ordem temporal;
- timestamps duplicados;
- gaps maiores que uma hora;
- NaN nas colunas essenciais;
- preços positivos;
- coerência de OHLC;
- volume não negativo;
- SHA-256 do arquivo.

## 7.5 O que fazer quando há gap

Não faça isto automaticamente:

```text
preencher o gap por interpolação e continuar o backtest
```

Primeiro descubra:

- se o gap é uma falha do download;
- se o exchange não possui aquele intervalo;
- se houve mudança de símbolo;
- se o arquivo foi corrompido;
- se a estratégia deveria ficar sem sinal durante o gap.

Registre a decisão. Um dataset com gap não explicado deve bloquear a interpretação.

## 7.6 Candles incompletos

O candle mais recente em uma API ao vivo pode ainda estar em formação. Não use um candle
incompleto como se fosse fechado.

Para backtest, registre:

- horário do download;
- último timestamp disponível;
- política para o último candle;
- se ele foi removido ou se o estado ficou desconhecido.

---

# 8. Estratégias implementadas

## 8.1 SmaTrendBaseline

Arquivo:

[user_data/strategies/SmaTrendBaseline.py](../user_data/strategies/SmaTrendBaseline.py)

Regras:

- SMA rápida: 20 candles;
- SMA lenta: 50 candles;
- regime: SMA 200;
- entrada quando a SMA 20 cruza acima da SMA 50;
- entrada exige fechamento acima da SMA 200;
- saída quando a SMA 20 cruza abaixo da SMA 50;
- stoploss fixo de 10%;
- spot long-only;
- ROI mínimo em 100% para não dominar as saídas.

Essa é a baseline congelada. Ela existe para ser referência, não para ser otimizada depois
do resultado histórico.

## 8.2 DonchianBreakoutBaseline

Arquivo:

[user_data/strategies/DonchianBreakoutBaseline.py](../user_data/strategies/DonchianBreakoutBaseline.py)

Regras:

- máxima dos 20 candles anteriores;
- entrada quando o fechamento rompe essa máxima;
- mínima dos 10 candles anteriores para saída;
- saída quando o fechamento rompe essa mínima;
- stoploss fixo de 10%;
- spot long-only.

A máxima e a mínima são deslocadas com `shift(1)`, portanto não incluem o candle atual.

## 8.3 BollingerMeanReversionBaseline

Arquivo:

[user_data/strategies/BollingerMeanReversionBaseline.py](../user_data/strategies/BollingerMeanReversionBaseline.py)

Regras pretendidas:

- banda de Bollinger de 20 períodos;
- entrada abaixo da banda inferior;
- RSI 14 abaixo de 30;
- fechamento acima da SMA 200;
- saída acima da banda média;
- stoploss fixo de 10%;
- spot long-only.

### Atenção sobre a especificação

A documentação original menciona “banda anterior”, enquanto a implementação calcula a banda
usando também o fechamento do candle atual. Isso pode ser causal quando o sinal só é decidido
no fechamento, mas representa uma definição diferente.

Antes de comparar versões, registre qual definição será usada. Não corrija a estratégia
silenciosamente depois de olhar o resultado.

### Atenção sobre o teste do RSI

Os testes locais substituem o RSI por um mock constante em algumas situações. Isso permite
que os testes rodem sem TA-Lib, mas não exercita completamente a condição `RSI < 30`.

Portanto, a estratégia precisa ser validada também dentro do container Freqtrade, onde a
implementação real dos indicadores estará disponível.

## 8.4 Estado das estratégias

“Carregável” significa que o Freqtrade consegue importar a classe. Não significa:

- que a estratégia foi validada;
- que tem vantagem;
- que é robusta;
- que supera o benchmark;
- que deve ser usada em dry-run por longo prazo.

---

# 9. Testes locais

## 9.1 Executar todos os testes

```bash
python3 -m unittest discover -s tests -v
```

## 9.2 O que os testes verificam

Os testes atuais verificam:

- interface v3;
- estratégia spot-only;
- ausência de short;
- stoploss negativo;
- ROI fixo;
- deslocamento causal do canal Donchian;
- estabilidade dos indicadores anteriores quando candles futuros são alterados;
- volume zero sem sinal;
- ausência de sinal no startup;
- colunas de sinal binárias;
- configuração segura;
- imagem Docker fixada;
- restart automático desabilitado.

## 9.3 O que esses testes não verificam

Eles não substituem uma simulação completa. Ainda não provam:

- preço real de entrada no candle seguinte;
- comportamento de saída no candle seguinte;
- stoploss intrabar;
- preenchimento limit;
- timeout;
- spread;
- slippage;
- preenchimento parcial;
- banco SQLite;
- diferenças entre backtest e dry-run;
- candles incompletos recebidos em tempo real.

---

# 10. Como registrar um experimento

Toda pesquisa começa antes do comando de backtest.

## 10.1 Registrar a hipótese

Abra:

[research/hypothesis-ledger.md](../research/hypothesis-ledger.md)

Adicione uma linha antes de executar. Registre:

- identificador;
- data UTC;
- estratégia;
- regra formal;
- parâmetros;
- dataset que será usado;
- quantidade de hipóteses anteriores;
- estado inicial, normalmente `candidate` ou `frozen reference`.

Exemplo conceitual:

```text
H-004 | 2026-10-20 | Donchian | breakout 20 / saída 10 / stop -10% | dataset D001 | 3 | candidate
```

Se você mudar qualquer regra depois, crie `H-005`. Não edite H-004 para esconder a versão
anterior.

## 10.2 Criar o manifesto

Copie o modelo:

```bash
cp research/experiment-manifest.yaml \
  research/manifests/2026-10-20-e004-donchian.yaml
```

O manifesto deve registrar:

- código;
- hash da estratégia;
- hash da configuração;
- versão do Freqtrade;
- imagem Docker;
- digest da imagem, quando disponível;
- exchange;
- par;
- timeframe;
- origem dos dados;
- hash do dataset;
- período;
- startup candles;
- parâmetros;
- taxa;
- slippage;
- spread;
- wallet;
- stake;
- posições máximas;
- comandos;
- resultado;
- decisão.

Preencha o máximo possível antes de interpretar o terminal. Se um campo ainda não é
conhecido, escreva `pending` ou `unknown`, não invente um valor.

## 10.3 Calcular hashes

No WSL:

```bash
sha256sum \
  user_data/strategies/SmaTrendBaseline.py \
  user_data/config.dryrun.json \
  user_data/data/binance/BTC_USDT-1h.feather \
  docker-compose.yml
```

O hash identifica o conteúdo exato naquele momento. Se o arquivo mudar, o hash mudará e o
experimento antigo não deve ser descrito como se fosse o novo.

---

# 11. Como executar um backtest

## 11.1 O comando geral

A forma geral é:

```bash
docker compose run --rm freqtrade backtesting \
  --config user_data/config.dryrun.json \
  --strategy NOME_DA_ESTRATEGIA \
  --strategy-path user_data/strategies \
  --timeframe 1h \
  --pairs BTC/USDT \
  --timerange DATA_INICIAL-DATA_FINAL \
  --dry-run-wallet 100 \
  --fee 0.001 \
  --export trades \
  --backtest-directory user_data/backtest_results
```

## 11.2 Explicação de cada parte

### `docker compose run --rm freqtrade`

Executa um container temporário usando o serviço `freqtrade` do Compose. O container é
removido ao final, mas os arquivos montados no `user_data` permanecem.

### `backtesting`

É o subcomando que simula a estratégia sobre candles históricos.

### `--config`

Indica o arquivo de configuração usado pelo Freqtrade.

### `--strategy`

Indica o nome da classe Python, sem `.py`.

### `--strategy-path`

Indica onde o Freqtrade deve procurar os arquivos das estratégias.

### `--timeframe`

Indica o timeframe do backtest. Neste projeto, `1h`.

### `--pairs`

Indica os pares. Neste projeto, `BTC/USDT`.

### `--timerange`

Indica a janela histórica solicitada. O período efetivo pode começar depois por causa de
`startup_candle_count`.

### `--dry-run-wallet`

Define a carteira hipotética do backtest. Não é dinheiro real e não cria uma conta.

### `--fee 0.001`

Define uma taxa de 0,1% por lado. A taxa de entrada e a taxa de saída precisam ser
consideradas na interpretação.

### `--export trades`

Pede a exportação das operações simuladas.

### `--backtest-directory`

Define onde guardar os artefatos do backtest.

## 11.3 Backtest da SMA

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
  --export-filename user_data/backtest_results/e004-sma-20251020-20261020.json \
  --backtest-directory user_data/backtest_results \
  --breakdown day month
```

## 11.4 Backtest do Donchian

```bash
docker compose run --rm freqtrade backtesting \
  --config user_data/config.dryrun.json \
  --strategy DonchianBreakoutBaseline \
  --strategy-path user_data/strategies \
  --timeframe 1h \
  --pairs BTC/USDT \
  --timerange 20251020-20261020 \
  --dry-run-wallet 100 \
  --fee 0.001 \
  --export trades \
  --export-filename user_data/backtest_results/e004-donchian-20251020-20261020.json \
  --backtest-directory user_data/backtest_results \
  --breakdown day month
```

## 11.5 Backtest da Bollinger

```bash
docker compose run --rm freqtrade backtesting \
  --config user_data/config.dryrun.json \
  --strategy BollingerMeanReversionBaseline \
  --strategy-path user_data/strategies \
  --timeframe 1h \
  --pairs BTC/USDT \
  --timerange 20251020-20261020 \
  --dry-run-wallet 100 \
  --fee 0.001 \
  --export trades \
  --export-filename user_data/backtest_results/e004-bollinger-20251020-20261020.json \
  --backtest-directory user_data/backtest_results \
  --breakdown day month
```

## 11.6 O que copiar do resultado

Copie para o manifesto e para um relatório:

- estratégia;
- timeframe;
- período solicitado;
- período efetivo;
- quantidade de trades;
- vencedoras, perdedoras e empates;
- retorno absoluto;
- retorno percentual;
- saldo final;
- drawdown máximo;
- duração do drawdown;
- duração média das operações;
- exposição;
- custos;
- saída por motivo;
- avisos do Freqtrade;
- nome do artefato exportado.

Não copie somente a linha de retorno. O contexto completo é necessário para interpretar o
resultado.

## 11.7 Resultado de backtest não é aprovação

Uma estratégia com retorno positivo pode ser rejeitada se:

- houver poucos trades;
- o retorno vier de um único movimento;
- o custo base eliminar o resultado;
- o resultado ocorrer apenas em um período;
- houver look-ahead;
- o preenchimento for irrealista;
- a regra tiver sido escolhida depois de ver o resultado.

---

# 12. Como validar uma estratégia

A validação completa possui várias camadas. Nenhuma camada isolada é suficiente.

## Camada 1 — validação sintática

Pergunta:

> O código e a configuração podem ser carregados?

Comandos:

```bash
python3 -m json.tool user_data/config.dryrun.json > /dev/null
docker compose config --quiet
docker compose run --rm freqtrade list-strategies \
  --config user_data/config.dryrun.json
```

## Camada 2 — validação unitária

Pergunta:

> As regras básicas do código obedecem ao contrato esperado?

```bash
python3 -m unittest discover -s tests -v
```

## Camada 3 — validação dos dados

Pergunta:

> Os candles são temporalmente e numericamente coerentes?

```bash
python3 research/validate_ohlcv.py \
  user_data/data/binance/BTC_USDT-1h.feather
```

## Camada 4 — validação de causalidade

Pergunta:

> A estratégia usa informação que não estaria disponível no instante da decisão?

Use:

- inspeção do código;
- teste de alteração de candles futuros;
- `lookahead-analysis`;
- revisão de timeframes informativos, se usados.

## Camada 5 — validação de startup

Pergunta:

> O indicador depende demais da quantidade de histórico inicial?

Use `recursive-analysis`.

## Camada 6 — validação de execução

Pergunta:

> O modelo de entrada, saída, stop, taxas e preenchimento é plausível?

Compare:

- ordens market e limit;
- custos otimistas e conservadores;
- `timeframe-detail`, quando disponível;
- dry-run posterior.

## Camada 7 — validação estatística

Pergunta:

> Há observações suficientes e estabilidade fora da amostra?

Analise:

- número de trades;
- divisão temporal;
- subperíodos;
- walk-forward;
- sensibilidade;
- Monte Carlo apenas quando houver amostra suficiente;
- múltiplos testes.

## Camada 8 — validação operacional

Pergunta:

> O bot consegue acompanhar dados atuais sem divergências graves?

Use dry-run, ainda sem ordens reais.

---

# 13. Lookahead analysis

## 13.1 O que é

Look-ahead bias ocorre quando o backtest usa dados futuros sem que a estratégia pudesse
conhecê-los no momento da decisão.

Exemplos de risco:

```python
dataframe["close"].shift(-1)
dataframe["close"].mean()  # média global sem janela
iloc[-1] em lógica que deveria ser histórica
```

O Freqtrade oferece `lookahead-analysis` para procurar alterações suspeitas nos resultados
quando sinais são analisados em condições controladas.

## 13.2 Comando

```bash
docker compose run --rm freqtrade lookahead-analysis \
  --config user_data/config.dryrun.json \
  --strategy SmaTrendBaseline \
  --strategy-path user_data/strategies \
  --timeframe 1h \
  --pairs BTC/USDT \
  --timerange 20251020-20261020 \
  --minimum-trade-amount 1 \
  --lookahead-analysis-exportfilename reports/generated/lookahead-e004-sma.txt
```

Repita trocando a estratégia:

- `DonchianBreakoutBaseline`;
- `BollingerMeanReversionBaseline`.

## 13.3 Como interpretar

Resultado favorável:

```text
has_bias: No
```

Isso significa que nenhum viés foi detectado pelo procedimento executado. Não significa
que todo erro possível esteja descartado.

A ferramenta pode alterar condições para reduzir falsos positivos, incluindo ordem market,
wallet maior e máximo de posições diferente. Portanto, o resultado do comando deve ser
arquivado como um artefato de auditoria separado do backtest comparável.

## 13.4 Se aparecer viés

Pare a interpretação econômica. Faça:

1. preservar o relatório;
2. identificar o indicador/sinal marcado;
3. revisar `shift`, `iloc`, agregações e loops;
4. criar uma nova versão da estratégia se a correção mudar a regra;
5. rodar os testes novamente;
6. repetir a análise.

Não apague o resultado enviesado.

---

# 14. Recursive analysis

## 14.1 O que é

Alguns indicadores dependem de valores anteriores. Se receberem pouco histórico inicial,
podem produzir valores diferentes do que produziriam ao vivo depois de muito tempo.

`recursive-analysis` compara indicadores com diferentes quantidades de startup candles.

## 14.2 Comando

```bash
docker compose run --rm freqtrade recursive-analysis \
  --config user_data/config.dryrun.json \
  --strategy SmaTrendBaseline \
  --strategy-path user_data/strategies \
  --timeframe 1h \
  --pairs BTC/USDT \
  --timerange 20251020-20261020 \
  --startup-candle 199 200 399 499 999 1999
```

Repita para Donchian e Bollinger.

## 14.3 Como interpretar

- valores muito próximos de zero são tranquilizadores;
- `nan` pode indicar histórico insuficiente;
- diferença material exige investigação;
- a ferramenta olha principalmente indicadores, não todo o efeito nos trades;
- recursive analysis não substitui backtesting nem lookahead analysis.

Se o indicador muda com o startup, não conclua que o resultado é reproduzível.

---

# 15. Métricas e interpretação

## 15.1 Métricas principais

### Retorno líquido

Quanto a carteira variou depois de taxas simuladas. Deve ser apresentado em valor absoluto e
percentual.

### Drawdown máximo

Maior queda da curva de capital desde um pico até um vale posterior.

### Duração do drawdown

Quanto tempo a carteira permaneceu abaixo do pico anterior.

### Número de trades

Quantidade de operações fechadas. É fundamental para julgar a incerteza.

### Exposição

Percentual de tempo em que a estratégia permaneceu posicionada.

### Custos

Taxas e outras penalidades de execução. Sem custos explícitos, o retorno não é comparável.

### Duração

Tempo médio, mediano e máximo das posições.

## 15.2 Métricas secundárias

- volatilidade;
- downside deviation;
- Sharpe;
- Sortino;
- Calmar;
- profit factor;
- expectativa;
- win rate;
- payoff ratio;
- pior trade;
- pior sequência de perdas;
- turnover;
- concentração por mês;
- desempenho por regime.

## 15.3 Poucos trades

Com uma única operação, não interprete como evidência:

- Sharpe;
- Sortino;
- profit factor;
- win rate;
- payoff ratio;
- expectativa;
- retorno anualizado;
- Calmar.

Nesse caso, a decisão correta é:

```text
inconclusive — insufficient trades
```

Isso não significa que a estratégia é boa ou ruim. Significa que o experimento não
respondeu à pergunta.

## 15.4 Não anualizar automaticamente

Anualizar um retorno de poucos trades pode produzir um número visualmente preciso, mas
estatisticamente enganoso. Só anualize quando o protocolo definir a medida e houver
histórico suficiente para justificá-la.

---

# 16. Custos, spread e slippage

## 16.1 Taxa

No comando:

```bash
--fee 0.001
```

`0.001` representa 0,1% por lado. Uma operação de compra e venda paga custo nos dois
lados.

## 16.2 Spread

Spread é a diferença entre o preço de compra disponível e o preço de venda disponível.
Candles OHLCV normalmente não informam o spread histórico.

## 16.3 Slippage

Slippage é a diferença entre o preço esperado e o preço efetivamente obtido.

O backtest com candles não reconstrói completamente:

- latência;
- fila;
- liquidez;
- preenchimento parcial;
- impacto da ordem;
- caminho intrabar.

## 16.4 Cenários mínimos

Use cenários declarados, sem afirmar que sejam medições históricas:

| Cenário | Fee por lado | Slippage por lado | Spread adicional |
|---|---:|---:|---:|
| Otimista | 0,10% | 0 bps | 0 bps |
| Base | 0,10% | 5 bps | 5 bps |
| Conservador | 0,10% | 10–20 bps | 10 bps |
| Stress | pelo menos 0,10% | 25–50 bps | 25 bps |

A opção `--fee` modela a taxa informada ao Freqtrade. Os cenários de slippage e spread
precisam ser registrados e aplicados por um procedimento de pesquisa separado ou por um
modelo que seja explicitamente documentado. Não escreva no relatório que `--fee` modela
slippage; ele não faz isso.

## 16.5 Ordens limit

A configuração atual usa ordens limit para entrada e saída no dry-run. Em backtest, uma
ordem pode ser considerada preenchida porque o preço apareceu no intervalo da vela. Isso
não garante que teria havido liquidez ou posição na fila.

Por isso, compare pelo menos:

- modelo de ordem definido no experimento;
- modelo market como sensibilidade;
- custo conservador;
- comportamento posterior no dry-run.

---

# 17. Benchmarks

Uma estratégia não deve ser avaliada somente contra zero.

## 17.1 Caixa

A carteira permanece em USDT durante todo o período. Mede se a estratégia acrescenta algo
além de não assumir exposição.

## 17.2 Comprar e manter

Compra BTC no início e mantém até o fim, usando a mesma janela e custos declarados.

Esse benchmark pode ter risco diferente da estratégia, mas mostra a contribuição da simples
exposição direcional.

## 17.3 Baseline simples

Uma regra simples previamente aprovada pode responder se a complexidade adicional realmente
ajuda.

## 17.4 Comparação justa

Todos devem usar:

- mesma janela;
- mesmo dataset;
- mesmo timeframe;
- mesmo capital inicial;
- mesma taxa;
- mesma política para o último candle;
- mesma moeda de referência.

Não escolha o benchmark depois de ver qual faz a estratégia parecer melhor.

---

# 18. Exploração, validação e teste final

## 18.1 Por que separar

Se você usa todo o histórico para escolher a estratégia e depois mede no mesmo histórico,
o resultado tende a ser otimista. O período usado para escolher não é um teste independente.

## 18.2 Exploração

Pode ser usada para:

- entender o formato dos dados;
- localizar bugs;
- testar se os comandos funcionam;
- criar hipóteses.

Não deve ser chamada de prova fora da amostra.

## 18.3 Validação

Serve para comparar hipóteses que já foram registradas. Você pode rejeitar regras, corrigir
bugs e planejar a próxima fase, mas deve registrar quantas tentativas foram feitas.

## 18.4 Teste final

O teste final é reservado. Não use seus resultados para escolher:

- parâmetros;
- stop;
- indicador;
- timeframe;
- par;
- cenário de custo;
- estratégia vencedora.

Leia-o apenas quando o protocolo estiver congelado. Se depois mudar a estratégia, o teste
anterior deixa de ser um teste final válido para a nova versão.

## 18.5 Forward test

Depois do teste histórico, o dry-run pode acompanhar novos candles. Ele serve para medir:

- sinais detectados;
- atrasos;
- timeout;
- diferenças de preço;
- reinícios;
- falhas de conexão;
- divergência do backtest.

Ainda não é operação real.

---

# 19. Walk-forward e robustez

## 19.1 O que é walk-forward

Em vez de escolher uma regra em todo o histórico, você simula decisões sequenciais:

```text
janela histórica → próximo período de teste
janela histórica expandida → próximo período de teste
janela histórica expandida → próximo período de teste
```

Nenhuma janela de teste deve ser usada para alterar decisões anteriores.

## 19.2 Rolling e expanding

### Expanding

A janela de pesquisa cresce com o tempo.

### Rolling

A janela mantém tamanho fixo e se desloca.

A escolha depende da hipótese e deve ser feita antes da análise dos resultados.

## 19.3 Sensibilidade

Teste uma pequena vizinhança previamente definida, por exemplo, somente para saber se há um
planalto de estabilidade. Não faça uma busca de centenas de combinações.

O objetivo é responder:

> Pequenas mudanças razoáveis destroem completamente o resultado?

Se sim, a hipótese é frágil.

## 19.4 Regimes

Separe o resultado por condições de mercado, por exemplo:

- alta;
- baixa;
- lateralização;
- volatilidade alta;
- volatilidade baixa.

Não defina os regimes depois de observar qual separação favorece a estratégia.

## 19.5 Monte Carlo

Com trades suficientes, pode-se reordenar ou reamostrar resultados para estudar drawdown e
sequências de perdas. Com uma única operação, isso não fornece evidência útil.

---

# 20. Dry-run

## 20.1 O que o dry-run faz

O dry-run inicia o bot e acompanha dados atuais, mantendo uma carteira hipotética. Ele não
deve enviar ordens reais quando `dry_run` está `true`.

## 20.2 Iniciar em primeiro plano

```bash
docker compose up freqtrade
```

Os logs aparecem no terminal. Para interromper, use `Ctrl+C`.

## 20.3 Iniciar em segundo plano

```bash
docker compose up -d freqtrade
```

Acompanhe:

```bash
docker compose logs -f freqtrade
```

Verifique o estado:

```bash
docker compose ps
```

Parar:

```bash
docker compose down
```

## 20.4 O que observar no dry-run

Registre:

- horário do sinal;
- timestamp do candle;
- estratégia;
- entrada esperada;
- entrada simulada;
- saída esperada;
- saída simulada;
- preço estimado;
- timeout;
- erro de conexão;
- reinício do processo;
- diferenças entre backtest e comportamento atual.

## 20.5 Banco SQLite

O dry-run mantém estado no banco configurado. Um banco antigo pode conter trades e estado
de uma sessão anterior. Antes de interpretar uma nova sessão, registre:

- se o banco foi reutilizado;
- se era uma sessão limpa;
- data de início;
- estratégia;
- configuração;
- período forward.

Não apague o banco de uma execução histórica sem antes preservá-lo e registrar a decisão.

---

# 21. FreqUI opcional

A API está desabilitada por padrão em:

[user_data/config.dryrun.json](../user_data/config.dryrun.json)

Isso é intencional e mais seguro.

## 21.1 Quando não usar

Não habilite FreqUI somente para executar backtest. Os comandos de terminal são mais
reproduzíveis e funcionam sem API.

## 21.2 Habilitar com segurança

Se for necessário usar a interface:

1. faça uma cópia local não versionada da configuração;
2. não coloque credenciais no arquivo versionado;
3. gere username, password e JWT fortes;
4. habilite a API somente durante a sessão;
5. dentro do container, use o bind exigido pelo Docker;
6. mantenha a porta publicada no host somente em `127.0.0.1`;
7. não publique na LAN ou Internet;
8. desabilite novamente ao terminar;
9. não registre senha ou JWT em relatório.

Nunca habilite a API com credenciais vazias.

## 21.3 Por que o bind pode ser diferente

O processo dentro do container pode precisar escutar em `0.0.0.0` para aceitar a interface
interna do Docker, enquanto o host publica somente:

```text
127.0.0.1:8080:8080
```

Essas duas camadas não são a mesma coisa. O bind interno não autoriza publicar o host para
a rede.

---

# 22. Como criar uma nova estratégia

Criar uma estratégia significa formular uma hipótese, não adicionar indicadores ao acaso.

## 22.1 Antes de escrever código

Escreva:

1. hipótese econômica ou comportamental;
2. informação permitida;
3. regra de entrada;
4. regra de saída;
5. stoploss;
6. timeframe;
7. startup candles;
8. parâmetros fixos;
9. condições em que deve funcionar;
10. condições em que pode falhar;
11. custo esperado;
12. critério de rejeição.

## 22.2 Criar nova classe

Não altere a baseline. Use um novo nome, por exemplo:

```text
SmaTrendVolatilityFilterV1
```

Mantenha:

- `INTERFACE_VERSION = 3`;
- `can_short = False`;
- `timeframe = "1h"`, salvo hipótese aprovada;
- sinais vetorizados;
- sem acesso a dados futuros;
- parâmetros fixos nesta fase.

## 22.3 Evitar look-ahead

Evite:

```python
dataframe.shift(-1)
dataframe.iloc[-1]
dataframe.mean()  # quando deveria ser rolling
```

Prefira janelas causais:

```python
dataframe["mean"] = dataframe["close"].rolling(20).mean()
```

Se o indicador precisa representar somente o passado anterior ao candle atual, use o
`shift(1)` de forma explícita e documentada.

## 22.4 Testar a nova estratégia

Adicione testes para:

- startup;
- volume zero;
- NaN;
- sinal esperado;
- sinal não esperado;
- ausência de dependência em candles futuros;
- entrada e saída;
- tags;
- conflito de condições;
- comportamento específico do indicador.

Depois rode:

```bash
python3 -m unittest discover -s tests -v
```

E:

```bash
docker compose run --rm freqtrade list-strategies \
  --config user_data/config.dryrun.json
```

---

# 23. Esteira de validação

## 23.1 Esteira manual atual

Execute nesta ordem:

```text
1. conferir segurança
2. validar JSON
3. validar Compose
4. validar Python
5. validar dataset
6. listar estratégias
7. registrar hipótese
8. criar manifesto
9. executar backtest
10. salvar trades e logs
11. executar lookahead
12. executar recursive
13. comparar benchmarks
14. aplicar cenários de custo
15. analisar subperíodos
16. registrar decisão
```

## 23.2 Comandos de pré-voo

```bash
cd /mnt/d/Trade-Initial
source .venv/bin/activate

python3 -m json.tool user_data/config.dryrun.json > /dev/null
python3 -m unittest discover -s tests -v
python3 research/validate_ohlcv.py \
  user_data/data/binance/BTC_USDT-1h.feather
docker compose config --quiet
docker compose run --rm freqtrade list-strategies \
  --config user_data/config.dryrun.json
```

Se qualquer comando falhar, a esteira deve parar.

## 23.3 Comparação das três estratégias

Execute o backtest da:

1. `SmaTrendBaseline`;
2. `DonchianBreakoutBaseline`;
3. `BollingerMeanReversionBaseline`.

Use exatamente:

- mesmo dataset;
- mesmo timerange;
- mesma taxa;
- mesma wallet;
- mesmo stake;
- mesmo `max_open_trades`;
- mesmo runtime;
- mesmo modelo de exportação.

A comparação deve gerar três manifestos e três conjuntos de artefatos.

## 23.4 Esteira automatizada futura

Uma futura automação deverá falhar se:

- `dry_run` não for `true`;
- `trading_mode` não for `spot`;
- houver chave de exchange;
- API estiver exposta além do loopback;
- dataset não passar na validação;
- estratégia não carregar;
- lookahead indicar viés;
- manifesto estiver incompleto;
- artefato de saída já existir;
- imagem não estiver pinada;
- estratégia não estiver registrada no ledger.

A automação deve produzir:

- logs;
- hashes;
- manifestos;
- backtests;
- análises de viés;
- tabela consolidada;
- decisão marcada como `continue`, `investigate`, `reject` ou `inconclusive`.

---

# 24. Erros comuns

## “Docker não foi encontrado”

Causa provável: Docker não está disponível no shell atual. Abra o WSL com Docker Engine
funcionando e repita.

## “pandas não foi encontrado”

Ative o ambiente virtual e instale as dependências:

```bash
source .venv/bin/activate
python -m pip install pandas pyarrow
```

## “stake amount is too large”

A carteira hipotética disponível ficou menor que o stake, possivelmente por causa de
`tradable_balance_ratio`. Não altere a configuração sem registrar a mudança. Para uma
execução de pesquisa, use valores compatíveis e preserve o experimento anterior.

## “A estratégia não aparece”

Verifique:

- nome da classe;
- caminho `--strategy-path`;
- erro de importação;
- dependências;
- sintaxe Python;
- nome do arquivo.

## “Há somente uma operação”

Não é erro necessariamente. Pode significar que a regra é rara ou que o período é curto.
O resultado deve ser classificado como inconclusivo para inferência estatística.

## “ROI encerrou imediatamente”

Verifique `minimal_roi`. Uma configuração como `{"0": 0.0}` pode tornar o ROI elegível
imediatamente. A baseline usa `{"0": 100.0}` para que o ROI não substitua a hipótese de
saída nesta fase.

## “Lookahead não encontrou viés”

Isso é bom, mas não é uma prova absoluta. Ainda é necessário revisar o código, startup,
execução, custos e dados.

## “Backtest e dry-run diferem”

Isso pode ocorrer por:

- preço atual diferente do OHLC histórico;
- spread;
- timeout;
- latência;
- order book;
- candle incompleto;
- banco persistente;
- ordem limit não preenchida;
- timing do processo.

Registre a divergência; não escolha automaticamente o resultado mais favorável.

## “Quero escolher a estratégia que teve maior retorno”

Não faça isso isoladamente. Primeiro compare:

- número de trades;
- exposição;
- drawdown;
- custos;
- benchmarks;
- subperíodos;
- estabilidade;
- quantidade de hipóteses tentadas.

---

# 25. Critérios de decisão

Use quatro estados.

## `continue`

A hipótese passou pelos bloqueios técnicos e pode seguir para a próxima etapa. Isso não
significa que tenha vantagem estatística.

## `investigate`

Existe comportamento interessante, mas ainda há uma divergência ou incerteza que precisa
de estudo.

## `reject`

Existe motivo objetivo para interromper:

- viés confirmado;
- dados inválidos;
- indicador instável;
- custos que eliminam o resultado;
- execução claramente irrealista;
- fragilidade extrema;
- dependência de uma escolha retrospectiva.

## `inconclusive`

A execução foi tecnicamente válida, mas não há observações suficientes para responder à
pergunta.

A baseline SMA atual permanece nesse estado por causa do número mínimo de operações.

## 25.1 O que não é critério suficiente

Não aprove uma estratégia somente porque ela tem:

- maior retorno;
- maior win rate;
- maior Sharpe;
- melhor curva visual;
- menor número de perdas;
- mais trades;
- resultado positivo em uma janela escolhida depois.

---

# 26. Checklist completo

## Antes de iniciar

- [ ] estou no WSL correto;
- [ ] Docker está disponível;
- [ ] Compose está disponível;
- [ ] `dry_run` está `true`;
- [ ] `trading_mode` é `spot`;
- [ ] chaves da exchange estão vazias;
- [ ] API está desabilitada;
- [ ] a porta do host está restrita a loopback;
- [ ] a imagem está pinada;
- [ ] não há live, margem, futuros, alavancagem ou short;
- [ ] o período foi definido antes de olhar o resultado;
- [ ] a hipótese está no ledger;
- [ ] o manifesto foi criado;
- [ ] o artefato de destino ainda não existe.

## Validar ambiente

- [ ] JSON passou;
- [ ] Compose passou;
- [ ] testes passaram;
- [ ] `list-strategies` passou;
- [ ] Freqtrade carregou a estratégia correta.

## Validar dados

- [ ] fonte registrada;
- [ ] par registrado;
- [ ] timeframe registrado;
- [ ] timezone registrado;
- [ ] hash salvo;
- [ ] timestamps ordenados;
- [ ] duplicatas verificadas;
- [ ] gaps investigados;
- [ ] NaN verificado;
- [ ] OHLC coerente;
- [ ] volume verificado;
- [ ] última vela tratada conforme política.

## Executar pesquisa

- [ ] backtest normal executado;
- [ ] trades exportados;
- [ ] logs salvos;
- [ ] período efetivo anotado;
- [ ] `lookahead-analysis` executado;
- [ ] `recursive-analysis` executado;
- [ ] taxa anotada;
- [ ] slippage anotado;
- [ ] spread anotado;
- [ ] benchmarks comparados;
- [ ] subperíodos analisados;
- [ ] exposição analisada;
- [ ] duração analisada;
- [ ] quantidade de hipóteses atualizada.

## Depois

- [ ] manifesto completado;
- [ ] decisão registrada;
- [ ] resultado negativo preservado;
- [ ] teste final continua bloqueado;
- [ ] nenhuma regra foi alterada com o mesmo ID;
- [ ] nenhum segredo foi registrado;
- [ ] nenhum live trading foi habilitado.

---

# 27. Glossário

**Backtest** — simulação histórica.

**Candle** — resumo OHLCV de um intervalo.

**Dry-run** — acompanhamento em tempo atual sem ordens reais.

**Entry** — sinal de entrada.

**Exit** — sinal de saída normal.

**Fee** — taxa cobrada pela exchange.

**Forward test** — teste prospectivo com dados que chegam depois da definição da hipótese.

**Look-ahead bias** — uso indevido de informação futura.

**Long** — posição que se beneficia de alta do ativo; no spot, normalmente significa
comprar o ativo.

**OHLCV** — open, high, low, close e volume.

**Pair** — par de negociação, como BTC/USDT.

**ROI** — regra de retorno mínimo por tempo de permanência.

**Slippage** — diferença entre preço esperado e efetivo.

**Spot** — compra e venda do ativo sem contrato futuro ou margem.

**Startup candles** — candles usados para aquecer indicadores antes do início efetivo.

**Stoploss** — limite de perda definido pela estratégia.

**Timeframe** — duração de cada candle.

**Walk-forward** — validação sequencial em que cada período futuro é testado sem ser usado
para tomar decisões anteriores.

---

# 28. Próximos passos

A próxima rodada recomendada é a comparação controlada das três estratégias já existentes:

1. validar o ambiente no WSL;
2. validar os candles;
3. registrar a hipótese e o dataset;
4. criar um manifesto para cada estratégia;
5. executar SMA;
6. executar Donchian;
7. executar Bollinger;
8. rodar lookahead nas três;
9. rodar recursive nas três;
10. comparar caixa e buy-and-hold;
11. aplicar cenários de custos;
12. analisar subperíodos;
13. registrar uma decisão para cada uma;
14. preservar todos os artefatos.

Depois disso, e somente se houver histórico e trades suficientes:

```text
walk-forward
→ sensibilidade limitada
→ stress de execução
→ dry-run monitorado
→ uma nova hipótese por vez
```

Não adicione ainda machine learning, hyperopt, dezenas de combinações, funding, open
interest, alavancagem, margem ou live trading.

O objetivo do Trading Lab é produzir evidência auditável e reproduzível. Um resultado
negativo ou inconclusivo é um resultado válido. A qualidade do laboratório é medida pela
capacidade de descobrir isso sem esconder erros, custos ou incerteza.
