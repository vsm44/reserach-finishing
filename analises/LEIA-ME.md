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
| `le_ods.py` | Lê planilhas .ods sem biblioteca extra |
| `rebote_fotmob.py` | Deduz rebotes só com a FotMob e mede o efeito de uni-los |
| `pe_dominante.py` | Testa se a Understat ajusta o xG pelo pé dominante do jogador |
| `xgot_gol.py` | Testa o xGOT e a informação de gol como entradas |
| `combinado.py` | Mede juntos: foi gol e rebotes do mesmo minuto |
| `teste2026.py` | Testa o modelo só FotMob na La Liga 2026/27 contra a planilha da Understat |
| `retreina.py` | Pareia a La Liga 2025/26, retreina de várias formas e testa de novo |
| `cego.py` | Teste cego na Serie A 2026/27, níveis WhoScored e só FotMob |
| `cego_r1.py` | Teste cego da rodada 1 da Serie A, nível só FotMob |
| `sorteia_gols.py` | Sorteia os 20 gols do teste cego dos palpites e gera a planilha |
| `treina_final.py` | Treino do modelo final na pasta de trabalho (a versão de uso é `scripts/treina_modelo.py`) |
| `roda_liga.py` | Roda o modelo numa pasta de jogos (a versão de uso é `scripts/roda_modelo.py`) |
| `casa_prev.py` | Casa as linhas de um arquivo de jogos com as previsões, só por data e nomes dos times |
| `compara.py` | Compara as previsões gravadas com um arquivo de xG da Understat |
| `amplia_treino.py` | Pareia temporadas novas, retreina com mais ligas e mede em 2026/27 (piloto de 12/11) |
| `etapa2.py` | Segunda etapa: corrige o total do time com dados do jogo; treina no histórico e mede em 2026/27 |
| `v7_vs_novo.py` | Compara o V7, a primeira etapa e a segunda etapa nos mesmos jogos da La Liga |
| `fm_le_bruto.py` | Lê o bruto do FMInside (fichas do Football Manager) e monta a tabela única de jogadores |
| `fm_monta.py` | Junta as notas do Football Manager (finalizador, goleiro, zagueiros) às finalizações de 5 temporadas |
| `fm_teste.py` | Primeira etapa com e sem as notas do Football Manager, validação cruzada por jogo (13/11) |
| `fm_etapa2.py` | Desvio nos seis times de elite antes e depois da segunda etapa |

Fontes externas usadas e não guardadas aqui: conjunto aberto da StatsBomb
(github.com/statsbomb/open-data), La Liga 2015/16.
