# Binance Spot Testnet: ensaio da mecânica de ordens

Este ambiente envia **ordens reais ao servidor de testes da Binance** (`testnet.binance.vision`). Os preços, os saldos e a liquidez de lá são fictícios, e não há dinheiro envolvido.

Ele serve para testar a parte que o dry-run não cobre:
- chaves de API;
- ordens limit que de fato chegam à corretora;
- `stoploss_on_exchange`;
- rejeições, `min_notional` e filtros de lote;
- reinício do bot com ordem ou posição aberta.

**Não serve para avaliar estratégia.** A evidência de estratégia vem só do dry-run com preço real (H-009 e H-016).

A estratégia [strategies/TestnetMechanics.py](strategies/TestnetMechanics.py) é um exercitador de ordens. Ela abre uma posição por hora e a fecha 15 minutos depois, com stop de -3% na corretora. Fica fora de `user_data/strategies/` de propósito, para o laboratório nunca a tratar como pesquisa.

## Preparação (uma vez)

1. Entre em https://testnet.binance.vision, faça login com o GitHub e clique em **Generate HMAC_SHA256 Key**. A chave criada é só da testnet.
2. Copie `testnet/.env.example` para `testnet/.env` e preencha `FREQTRADE__EXCHANGE__KEY` e `FREQTRADE__EXCHANGE__SECRET`. O `.env` é ignorado pelo git. **Não cole as chaves no chat.**
3. Rode `python -m pytest tests/test_live_readiness_safety.py -q`. O resultado deve dar verde.
4. Suba o bot com `docker compose -f docker-compose.testnet.yml up -d`.
5. Acompanhe com `docker logs -f testnet-mechanics` ou pelo arquivo `user_data/logs/testnet-mechanics.log`.

O banco de trades fica em `user_data/tradesv3.testnet.sqlite`, separado dos bancos de dry-run.

## Roteiro de testes de falha (checklist C e D)

Anote o resultado de cada teste em `research/forward/failure-tests.md`, com data, trecho do log e conclusão.

| # | Teste | Como provocar | Esperado |
|---|---|---|---|
| T1 | Conexão e chaves | Subir o bot | O log mostra `sandbox: True` e nenhum erro de autenticação; o saldo de USDT da testnet aparece |
| T2 | Ciclo completo | Esperar o candle das :00 | Ordem limit de entrada → fill → stop criado **na corretora** → saída no candle das :15 |
| T3 | Stop na corretora | Durante a posição aberta, conferir as ordens abertas (log ou site da testnet) | Existe uma ordem stop-loss do lado da Binance, não só no processo |
| T4 | Queda com posição aberta | `docker stop testnet-mechanics` com a posição aberta, esperar 5 min e rodar `up -d` | O bot reconhece o trade aberto no banco, mantém ou recria o stop e sai normalmente |
| T5 | Perda de rede | `docker network disconnect trading-lab-testnet_default testnet-mechanics` por cerca de 2 min e depois `connect` | Erros de rede no log, nenhuma ordem duplicada, recuperação sozinha |
| T6 | Ordem pequena demais | Parar o bot, mudar `stake_amount` para 1, subir, observar e depois voltar para 20 | A entrada é recusada por `min_notional` com mensagem clara, sem travar o bot |
| T7 | Saldo insuficiente | Parar o bot, mudar `stake_amount` para um valor acima do saldo de USDT da testnet, subir e depois voltar ao normal | A entrada é recusada com log claro |
| T8 | Chave inválida | Trocar um caractere do secret no `.env` e subir | O bot falha ao iniciar com erro de autenticação e não fica em loop silencioso |
| T9 | Parada de emergência | Com a posição aberta, rodar `docker compose -f docker-compose.testnet.yml down` | `cancel_open_orders_on_exit` cancela as ordens pendentes; registrar o que acontece com a posição e com o stop |

Nos testes T6 e T7, desfaça a mudança em `config.testnet.json` assim que terminar. O teste `tests/test_live_readiness_safety.py` continua valendo durante todo o processo.
