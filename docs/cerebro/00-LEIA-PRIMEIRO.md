---
tipo: entrada
atualizado: 2026-11-19
tags: [cerebro, entrada]
---

# Leia primeiro

Este cofre é o **segundo cérebro** do projeto: tudo que o dono e as sessões do Claude decidiram, descobriram e deixaram pendente, em Markdown com `[[links]]`. Abre como cofre no **Obsidian** (aponte para a pasta `docs/cerebro/`) e também lê normalmente no GitHub.

## O projeto em dez linhas

1. É um **laboratório de pesquisa de estratégias de trading** feito para não se enganar com o próprio backtest.
2. Linha principal desde 2026-11-16: **WIN e WDO da B3**, dados de 5 anos da Clear, candles de 1 e 5 minutos (15 também). Ver [[B3-WIN-WDO]].
3. Uma **esteira** de agentes gera famílias de regras simples e um filtro leve as seleciona. Ver [[Esteira]].
4. Cada regra selecionada passa pelo **menu de saídas** (stop e alvo em unidades de volatilidade). Ver [[Menu-de-saidas]].
5. As melhores vão para **robôs na conta demo**, que operam 1 contrato. Ver [[Robos-demo]] e [[Engine-live]].
6. A demo é **observação, não evidência**. Validação lê-se uma vez e o teste final está trancado. Ver [[Regras-inviolaveis]].
7. Nenhuma regra tem hoje evidência fora da amostra que justifique dinheiro real. Ver [[Resultados-B3]].
8. A linha antiga de **cripto (Freqtrade)** está pausada. Ver [[Cripto-Freqtrade]].
9. Um **portal** local mostra pesquisa, demo e gráficos. Ver [[Portal]].
10. O dono decide tudo que envolve dinheiro, gates e splits. Os agentes só escrevem texto e código.

## Ordem de leitura para um Claude novo

| Passo | Nota | Para quê |
|---|---|---|
| 0 | [[Onboarding-equipe]] | Do clone ao primeiro resultado (comandos, o que funciona em cada nível de acesso) |
| 1 | [[Regras-inviolaveis]] | O que nunca fazer |
| 2 | [[Estado-atual]] | Onde o trabalho parou |
| 3 | [[Mapa-do-repositorio]] | Onde está cada coisa |
| 4 | [[Como-rodar-em-outro-ambiente]] | Montar o ambiente |
| 5 | [[Glossario]] | Termos (esteira, V, S1..S4, DSR, PBO...) |
| 6 | [[Pendencias-e-calendario]] | O que vence e o que espera decisão |
| 7 | Áreas e decisões abaixo | Aprofundar |

## Índice por área

- **Linha B3**: [[B3-WIN-WDO]] · [[Esteira]] · [[Menu-de-saidas]] · [[Dados]]
- **Execução**: [[Engine-live]] · [[Robos-demo]] · [[Operacao-Windows]]
- **Pesquisa e agentes**: [[Lab-de-pesquisa]] · [[Agentes-e-skills]] · [[Portal]]
- **Linha antiga**: [[Cripto-Freqtrade]]
- **Resultados**: [[Resultados-B3]] · [[Demo-diario]]
- **Decisões do dono**: [[Decisoes-indice]]

## Como manter o cofre

- **Uma ideia por nota**, em português, com `atualizado:` no topo e `[[links]]` para as vizinhas.
- Decisão nova: copie [[modelo-decisao]] para `decisoes/AAAA-MM-DD-assunto.md` e ligue no [[Decisoes-indice]].
- **O código manda.** Se uma nota divergir do arquivo, o arquivo está certo: corrija a nota e anote a data.
- **Nunca coloque** senha, chave, número de conta, e-mail ou dados pessoais aqui. O cofre vai para o GitHub.
- A pasta `arquivo/memoria-claude/` guarda as notas originais da memória do Claude, só para consulta histórica.
