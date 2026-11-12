# Modelo Finishing — leia isto primeiro

Atualizado em 12/11/2026. O histórico detalhado, em ordem cronológica, está em PLANEJAMENTO.md.

## O que é
Reproduzir o xG e o xGA por time que a Understat publicava, usando dados que ainda existem
(FotMob/Opta). A Understat saiu do ar; o projeto de apostas do usuário dependia dela.
O projeto de apostas em si fica FORA deste repositório e não deve ser discutido aqui.

## Como trabalhar com o usuário
Regras registradas a partir das sessões de 09 a 12/11/2026. O usuário pode substituir esta seção
pelo texto que usa nos outros projetos.

- Responder em português. Nunca chutar: se não sabe, dizer "não sei".
- Apresentar dados e evidências; conclusões e recomendações só quando pedidas.
- Uma dúvida por vez, mensagens curtas. Devagar, passo a passo.
- Pedir permissão antes de agir. Antes de mover, alterar ou deletar, listar o que será afetado.
- Nunca fazer commit sem autorização. Mensagens de commit datadas e aprovadas.
- Não elogiar, não criticar, não se despedir.
- Os créditos do usuário são limitados: não refazer o que já foi medido (ver "Já testado").
- O usuário sobe arquivos pelo site do GitHub, na raiz. Depois, mover com `git mv`.
  Nunca usar "Rename" do site em arquivo grande: ele corrompe o conteúdo.
- Régua do usuário: importa o ERRO GRAVE (mais de 0,50 no xG de um time). O erro médio é
  secundário. Saber qual time foi superior não importa.
- O usuário conhece futebol e revisa lances em vídeo; a modelagem fica por conta do assistente.

## Estado atual
Modelo de uso em `scripts/`, só com dados da FotMob, em duas etapas:

1. xG por finalização: posição, parte do corpo, tipo de lance, grande chance (escolhida pelo
   maior xG da Opta), se foi gol. Rebotes do mesmo minuto são unidos. Pênalti = valor fixo da liga.
2. Correção do total do time com dados do jogo (gols, total do adversário, contagens, xG da Opta).

Erros acima de 0,50, por time-jogo:

| Onde | Erros graves |
|---|---|
| Histórico (5.778 time-jogos, fora da amostra) | 2,6% |
| Temporada 2026/27 (382) | 4,7% (era 6,5% só com a primeira etapa) |
| Contra o modelo antigo (V7), nos mesmos 3.039 jogos | 1,81% contra 1,94% do V7 |

Onde erra: times com xG acima de 2,0 (cerca de 10%). Até 1,0, praticamente nunca.
Com poucos gols o modelo é muito melhor; 2026/27 tem média de gols alta.

## Como usar
```
python3 scripts/baixa_fotmob.py fotmob/la_liga/2026
python3 scripts/roda_modelo.py fotmob/la_liga/2026 La_liga saida.csv
python3 scripts/treina_modelo.py
```
O primeiro baixa os jogos encerrados; o segundo calcula o xG e o xGA; o terceiro refaz o modelo
a partir de `data/treino`. Ligas: La_liga, Serie_A, Ligue_1, EPL, Bundesliga. Número de cada uma
na FotMob, para o download: 87, 55, 53, 47, 54.

## Onde está cada coisa
| Pasta | Conteúdo |
|---|---|
| `scripts/` | modelo, treino, download da FotMob, PDF de análise de um jogo |
| `data/understat/` | bruto de 5 ligas (até 2025/26) e planilhas de 2026/27 (total por time) |
| `data/fotmob/` | jogos por liga e temporada |
| `data/whoscored/` | páginas salvas à mão (48 jogos) |
| `data/treino/` | tabelas de treino das duas etapas |
| `analises/` | scripts de cada teste, descritos em `analises/LEIA-ME.md` |
| `relatorios/` | previsões fixadas antes de ver o gabarito, PDFs, planilha dos 20 gols |
| `legado/` | projeto antigo (V7), só para consulta |

## Já testado e descartado (não refazer)
- xGOT e xG da Opta, direto ou misturados ao modelo: pioram ou não mudam.
- Treinar com mais ligas e temporadas, ou só com temporadas recentes: não muda.
- Ajuste de escala nos jogos altos: o erro não tem direção.
- Pé dominante: a Understat não ajusta por ele. Técnica (voleio): sem apoio.
- Histórico dos times e dos jogadores, força de escalação: ganho mínimo.
- Posição dos defensores (StatsBomb): ajuda 17%, mas não existe para jogos atuais.

## Fatos sobre os dados
- Understat: pênalti tem valor por liga (0,7433 a 0,7613); o xG do time une os rebotes por
  1 − (1−a)(1−b); gol contra vale 0; às vezes o xG vem sem o ponto decimal (1031 = 1,031).
- FotMob: as páginas públicas trazem os dados completos. Não tem mapa antes de 2020/21.
- WhoScored: tem grande chance por finalização e a jogada anterior, mas recusa acesso
  automático. Páginas salvas à mão (Ctrl+S "somente HTML", ou SingleFile sem remover scripts).
  Conferir com `grep -c matchCentreData arquivo.html` (precisa dar 1 ou mais).
- `scripts/modelo_fotmob.pkl` só abre com a mesma versão do scikit-learn que o treinou (1.9.1);
  em outra máquina, rodar `treina_modelo.py`.

## Em aberto
1. Teste do WhoScored com amostra maior, que o usuário vai salvar (rodadas inteiras de 2025/26).
   Se reduzir os erros graves, escrever um script que comanda o navegador do usuário, sem disfarces.
2. Teste cego dos palpites do usuário: `relatorios/teste_palpites_20_gols.xlsx`.
3. Lista de lances a conferir por rodada (times com xG acima de 2,0 ou 4+ grandes chances).
4. Não testado: força acumulada do time (xGD) como entrada; Premier League e Bundesliga
   como validação; liga russa.
