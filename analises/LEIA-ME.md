# Análises de 10/11/2026

Scripts usados nos testes do dia. Foram escritos para rodar numa pasta de trabalho temporária
(primeiro argumento de cada um), com o bruto já extraído. Ficam aqui como registro do método;
para rodar de novo é preciso ajustar os caminhos.

| Script | O que faz |
|---|---|
| `carrega.py` | Lê o bruto da Understat e monta as tabelas de jogos e de finalizações |
| `h1.py` | Mede quanto do xG da Understat se explica pelos campos que ela publica |
| `sb_extrai.py` | Extrai as finalizações (com posição dos jogadores) de um arquivo de eventos da StatsBomb |
| `sb_par.py` | Casa jogos e finalizações da StatsBomb com os da Understat |
| `sb_teste.py` | Mede o efeito da posição da defesa e do goleiro sobre o erro |
| `v7_jogo.py` | Reproduz o modelo antigo (V7) para um jogo, a partir do legado |
| `v7_tudo.py` | Mede as versões do modelo antigo no legado inteiro |
| `ws_lote.py` | Lê as páginas salvas do WhoScored e casa as finalizações com as da Understat |
| `ws_teste.py` | Primeiro piloto do efeito da marca de grande chance nos jogos do WhoScored |
| `ws_pseudo.py` | Ensina o efeito da grande chance com o bruto da Understat e aplica nos jogos do WhoScored |
| `ponta_a_ponta_1.py` | Três versões sem nenhuma entrada da Understat: só WhoScored, só FotMob, e mista |
| `ponta_a_ponta_2.py` | As mesmas versões com o xG da Opta e o xGOT como entradas, treinando com a posição de cada fonte |
| `legado_fotmob.py` | Mede o nível só FotMob no legado inteiro (7.592 time-jogos) |
| `disseca.py` | Separa o erro conforme a grande chance concorda ou não com a Understat |
| `jogada_anterior.py` | Mede o ganho da jogada anterior e da união de rebotes no legado inteiro |

Fontes externas usadas e não guardadas aqui: conjunto aberto da StatsBomb
(github.com/statsbomb/open-data), La Liga 2015/16.
