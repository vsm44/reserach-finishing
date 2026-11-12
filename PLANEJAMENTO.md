# Planejamento — 10/11/2026

## Prioridade 1 — Organizar o repositório
Restaurar os 5 arquivos da Understat (vazios desde o rename), padronizar `data/`, mover o trabalho
anterior para `legado/`. Sem isso, nada começa.

## Etapa 1 — Inventário dos brutos
Por fonte, liga e temporada: jogos, finalizações, dados por time e por jogador (ataque e defesa),
campos disponíveis e lacunas.

## Etapa 2 — Regras fixas da Understat
Documentar e testar no bruto inteiro. Listar as exceções. Ver "Observações já conferidas".
Verificar também como npxG, PPDA, deep, xPTS, xGChain e xGBuildup se relacionam com os dados do jogo.

## Etapa 3 — Pareamento
Ligar cada finalização da FotMob à mesma finalização da Understat, a partir dos dois brutos.
Saída: taxa de pareamento e lista do que não pareou, dos dois lados.

## Etapa 4 — Diferenças entre as fontes
Nas finalizações pareadas: posição, minuto, situação, parte do corpo e resultado. No jogo inteiro:
o que cada fonte registra de defesa, por time e por jogador.

## Etapa 5 — Quem defende e como defende
Verificar no bruto se o xG que a Understat dá a uma finalização muda conforme o time que defende, os
jogadores em campo e o comportamento defensivo. Testar a tese de deep, deep sofrido e buildup.

## Etapa 6 — xG por finalização
Alvo: xG da Understat. Posição da FotMob. Variáveis a definir com base nas etapas 4 e 5.

## Etapa 7 — xG e xGA por jogo
Aplicar as regras da Etapa 2 sobre o xG por finalização.

## Etapa 8 — Medição
Erro por finalização e por jogo, em todos os dados, com temporadas e ligas que o modelo não viu.
Sem métricas de aposta nesta etapa.

## Etapa 9 — Depois
Aplicar no projeto de apostas; outras ligas; melhorias próprias.

## Observações já conferidas no bruto (09/11/2026)
Bruto da Understat: 5 ligas, 15.257 jogos com finalizações, 381.984 finalizações.

1. **Rebote e xG do time.** A soma simples das finalizações bate com o xG publicado do time em 65,6%
   dos 30.426 time-jogos. Unindo cada finalização com última ação "Rebound" à anterior do mesmo time
   por 1 − (1−a)×(1−b), e depois somando, bate em 30.425 de 30.426. Há 17.359 rebotes; rebote de
   rebote entra no mesmo grupo. Exceção: Sheffield United × Everton, 26/12/2020 (causa desconhecida).
2. **Gol contra.** 1.246 no bruto, todos com xG 0. Não entram no xG de nenhum time.
3. **Pênalti.** Sempre na coordenada X 0,885 / Y 0,5. Valor quase constante por liga, igual em todas
   as temporadas: La Liga 0,7433; Bundesliga 0,7578; Ligue 1 0,7601; EPL 0,7612; Serie A 0,7613.
   Três exceções. Por que varia por liga: desconhecido. Na Opta (FotMob) o pênalti é 0,7884.
4. **Lacunas.** Serie A 2018 (100 de 380 jogos), Ligue 1 2019 (279 com resultado), Bundesliga 2024
   (305 de 306).
5. **FotMob, La Liga 2021–2025.** 1.900 jogos, 46.284 finalizações. Traz estatísticas de time e de
   jogador, escalação e xG da Opta. Não traz a última ação antes da finalização nem a assistência.

## Descobertas de 10/11/2026

Detalhes e scripts em `analises/`. Amostras pequenas estão indicadas; nada aqui é conclusão final.

1. **Os campos publicados não determinam o xG da Understat.** Com posição, parte do corpo, situação
   e última ação (375 mil finalizações), o erro médio é 0,043 por finalização e 0,24 por time-jogo.
   Finalizações com campos idênticos raramente têm o mesmo xG. Liga, temporada, mando e minuto não
   acrescentam nada. A última ação ajuda.
2. **A posição da defesa e do goleiro reduz o erro em 17%** (de 0,240 para 0,200 por time-jogo).
   Medido na La Liga 2015/16 com o conjunto aberto da StatsBomb, 8.880 finalizações pareadas.
3. **A grande chance é a variável de maior efeito.** No legado (91 mil finalizações, dados da FotMob),
   posição, parte, situação e grande chance levam o erro por time-jogo de 0,270 para 0,136; o modelo
   antigo completo (V7) chega a 0,122. O resultado da finalização quase não pesa.
4. **A FotMob só informa a grande chance por jogador no jogo.** O legado estimava qual finalização
   recebia a marca, e errava em parte dos casos (exemplo conferido: Ibañez, Empoli × Roma).
5. **O WhoScored traz a grande chance por finalização**, e também a jogada anterior. Em 18 jogos
   salvos à mão (416 finalizações), todas casaram com as da Understat; a posição é idêntica em 71%.
   Sem a marca, o xG médio da Understat é 0,056; com a marca, 0,448. Das 59 finalizações com xG de
   0,20 ou mais, 55 têm a marca.
6. **Modelo com a marca do WhoScored, nesses 18 jogos:** erro médio de 0,017 por finalização; por
   time-jogo, médio 0,122 e mediano 0,054. Nas finalizações sem a marca, o erro médio é 0,010.
   Os erros grandes vêm de 10 finalizações em que a marca e a Understat se desencontram.
7. **O acesso automático ao WhoScored foi recusado pelo site** (uma tentativa, não contornada).
   As páginas foram salvas à mão pelo navegador.
8. **Pênalti na Understat** varia por liga (item 3 das observações de 09/11); a versão divulgada
   de 0,76 fixo não se confirma no bruto.

Diretrizes do usuário registradas no dia:
- A marcação humana (grande chance, assistência, rebote) varia e erra. A grande chance entra como
  variável que o modelo pesa, não como verdade copiada.
- Uma grande chance depende mais da defesa e de como a chance foi criada do que do chute em si.
- Estilo de jogo é característica do clube; médias entre clubes diferentes escondem isso.
- Um erro no xG de um time é também um erro no xGA do adversário.

## Patamar medido e decisão (10/11/2026, fim do dia)

Erro no xG de um time num jogo, contra o xG publicado pela Understat. O xG típico de um time é 1,3.

| Nível | Erro médio | Metade dos casos até | Acima de 0,50 | Base |
|---|---|---|---|---|
| Só FotMob: posição, parte, lance, grande chance | 0,140 | 0,095 | 3,1% | 7.592 time-jogos |
| + jogada anterior e união de rebotes (o que o WhoScored acrescenta) | 0,120 | 0,078 | 2,0% | 7.592 time-jogos |
| Com o WhoScored de verdade, sem nada da Understat | 0,11 | 0,08 | 0 de 30 | 30 time-jogos |

- No segundo nível a jogada anterior usada foi a da própria Understat, como substituta da do WhoScored;
  a derivada do WhoScored coincide com ela em 84% das finalizações.
- Na FotMob, a finalização que recebe a grande chance é escolhida pelo maior xG da Opta (ideia do
  usuário). É melhor que a escolha por geometria e coincide com a marca do WhoScored em 45 de 53 casos.
- O modelo aprende com a posição da própria fonte. Treinar com a posição da Understat e aplicar na da
  FotMob criava desvio para cima.
- O xG da Opta e o xGOT como entradas não reduziram o erro total. O xGOT acima de 0,98 identifica os
  lances de gol desprotegido (Understat média 0,76), mas são 278 casos em 91 mil.
- O WhoScored registra quem foi driblado antes da finalização, inclusive o goleiro (conferido em 2
  lances, um deles revisto em vídeo pelo usuário).

De onde vem o erro que sobra (legado, 91 mil finalizações):

| Grupo | Parcela das finalizações | Parcela do erro |
|---|---|---|
| Nem grande chance, nem xG alto na Understat | 84,0% | 41,7% |
| Grande chance e xG alto (concordam) | 13,3% | 33,2% |
| Grande chance, mas xG baixo na Understat | 1,7% | 15,6% |
| Sem grande chance, mas xG alto na Understat | 1,0% | 9,4% |

Os dois grupos de desencontro são 2,7% das finalizações e um quarto do erro. Nenhuma fonte testada
os explica.

**Decisão do usuário:** o modelo antigo (V7) fica só como registro em `legado/`. O trabalho continua
a partir do modelo novo, de poucas entradas, com análise conjunta dos lances.

## Achados de 11/11/2026

**Coleta.** A FotMob continua publicando, e as páginas públicas trazem os dados completos de cada
jogo. `scripts/baixa_fotmob.py` baixa os jogos encerrados de uma liga (testado: La Liga, 119 jogos;
Serie A, 110 jogos, temporada 2026/27). O acesso automático ao WhoScored segue recusado; as páginas
são salvas à mão.

**Modelo só FotMob, sete entradas:** posição (duas coordenadas), parte do corpo, tipo de lance,
grande chance escolhida pelo xG da Opta, se foi gol, e rebote do mesmo minuto; os totais unem os
rebotes. No legado (7.592 time-jogos): erro médio 0,135, mediano 0,091, 2,5% acima de 0,50, sem
desvio. O V7 antigo, na mesma régua: 0,127 e 2,3%. Com a jogada anterior e os rebotes ligados
(o que o WhoScored acrescenta): 0,120 e 2,0%.

**Testes em jogos nunca vistos**

| Teste | Time-jogos | Erro médio | Mediano | Acima de 0,50 |
|---|---|---|---|---|
| Serie A 2026/27, rodadas 1 a 3, cego, só FotMob | 60 | 0,148 | 0,095 | 2 |
| Serie A 2026/27, rodadas 2 e 3, cego, WhoScored | 40 | 0,141 | 0,098 | 2 |
| La Liga 2025/26 inteira, só FotMob | 760 | 0,160 | 0,112 | 3,8% |
| La Liga 2026/27, 78 jogos, só FotMob | 156 | 0,188 | 0,107 | 9,0% |

- Nos testes cegos, as previsões foram publicadas antes de o usuário revelar o xG da Understat.
- Usar o xG da Opta diretamente erra o dobro (0,28 a 0,29) e quase sempre para menos.
- Na La Liga 2026/27 o erro foi maior, e retreinar com 2025/26 não mudou isso. Uma linha da planilha
  (Villarreal × Deportivo, 05/09/2026: 3,64 e 2,44) está três vezes acima da Opta nos dois times e não
  bate com a avaliação do usuário sobre os gols; sem ela, o erro médio é 0,174. Causa não identificada.
- A temporada 2026/27 da La Liga tem 1,55 gol por time, a maior desde 2015.

**Onde o erro se concentra**

- O erro absoluto cresce com o xG do time: 0,08 até 1,0 e 0,23 acima de 2,2. Em proporção, cai de
  20% para 8%.
- Nos jogos altos o erro não tem direção: o modelo acerta a média e erra para os dois lados. Ajuste
  de escala não melhora.
- Jogos equilibrados têm o menor erro, mas quando a diferença real entre os times é menor que 0,3 o
  modelo aponta o time errado como superior em 20% a 40% dos casos.
- Seleção para conferência manual: rever os times em que o modelo dá mais de 2,0 ou que tiveram 4 ou
  mais grandes chances são cerca de 5 times e 18 lances por rodada de 10 jogos, com 73% dos erros
  acima de 0,50.

**Lances revistos em vídeo pelo usuário**

- Griezmann (Atlético × Betis, 18/05/2025): bicicleta contada pela FotMob como grande chance;
  a Understat deu 0,142 e estava mais perto do que aconteceu.
- Gueye (Villarreal × Sevilla, 25/05/2025): ângulo fechado e marcado; a Understat deu 0,519 e a Opta
  0,197, mais perto da avaliação do usuário.
- Gols de Villarreal × Deportivo (05/09/2026): avaliação do usuário próxima da Opta e do modelo.
- Nos desencontros entre as fontes, nenhuma está sempre mais perto do que o usuário vê.

**Em aberto**

- Se o palpite do usuário aproxima o modelo da Understat: teste cego em andamento. Os 20 gols estão em
  `relatorios/teste_palpites_20_gols.xlsx` (sorteados entre 184 gols de grande chance da La Liga, de
  01/03 a 24/05/2026, sem nenhum valor de xG). A chave para casar com as fontes está em
  `relatorios/teste_palpites_chave.csv`.
- (Feito em 12/11) xG da Understat da rodada 4 da Serie A, para fechar o teste cego do nível WhoScored.
- Ferramenta de uso: baixar e calcular xG e xGA por time já existem em `scripts/` (12/11). Falta a
  lista dos lances a conferir por rodada.
- Por que a La Liga 2026/27 tem erro maior que a Serie A da mesma temporada.

## Teste final na temporada 2026/27 (12/11/2026)

O modelo só FotMob foi rodado em todos os jogos encerrados de 2026/27 da La Liga, da Serie A e da
Ligue 1, e as previsões foram gravadas antes de abrir os valores da Understat (arquivos em
`relatorios/previsoes_2026-27/`). Os valores da Understat estão em `data/understat/`.

| Liga e jogos | Time-jogos | Erro médio | Mediano | Acima de 0,50 | Desvio | Cego? |
|---|---|---|---|---|---|---|
| Serie A, rodadas 1 a 3 | 60 | 0,148 | 0,095 | 3,3% | 0,000 | sim (11/11) |
| Serie A, rodadas 4 a 6 | 60 | 0,207 | 0,163 | 5,0% | −0,044 | sim (12/11) |
| La Liga, 78 jogos | 156 | 0,193 | 0,110 | 8,3% | −0,042 | não |
| Ligue 1, 53 jogos | 106 | 0,211 | 0,158 | 6,6% | +0,081 | não |

- xG da Opta usado direto, nos mesmos jogos: 0,313 (Serie A), 0,284 (La Liga), 0,248 (Ligue 1).
- Nível WhoScored, nos 30 jogos da Serie A com página salva: 0,165, igual ao só FotMob (0,165);
  a média dos dois níveis deu 0,149. Na rodada 4, cega para esse nível: 0,212 contra 0,216.
- **O erro cresce a cada temporada:** 0,135 a 0,140 no legado (2020 a 2024), 0,160 em 2025/26 e
  cerca de 0,19 em 2026/27. Causa não identificada; investigar exigiria as finalizações da Understat
  de 2026/27, e só há totais por time.
- A Ligue 1, que o modelo nunca viu no treino, teve o pior resultado e um desvio para cima.
- A Understat às vezes entrega o xG sem o ponto decimal (ex.: `1031` em vez de 1,031). Regra: xG de
  time acima de 8 é lido com três casas decimais e avisado. O bruto do repositório não tem nenhum caso.
- Na La Liga os valores usados foram os da planilha de 11/11; `la_liga_teste.csv` e
  `la_liga_understat.csv` vieram sem xG e são idênticos entre si.

**Modelo guardado para uso**

- `scripts/modelo_fotmob.py`: o modelo (leitura do jogo, grande chance, união de rebotes, total por time).
- `data/treino/treino_fotmob_2020-2025.csv.gz`: as 100.383 finalizações usadas no treino.
- `scripts/treina_modelo.py`: treina a partir dessa tabela e grava `scripts/modelo_fotmob.pkl`.
- `scripts/roda_modelo.py`: roda o modelo numa pasta de jogos baixada por `scripts/baixa_fotmob.py`.
- Conferido: treinando a partir do repositório, as previsões da La Liga e da Serie A saem idênticas
  às que foram fixadas.

**Sugestões do usuário ainda não testadas**

- Usar outras métricas da Opta e a força acumulada do time (xGD) como entradas.
- Treinar com as temporadas de 2015 a 2018 da Premier League, Bundesliga e Ligue 1, que estão no
  computador do usuário e não no repositório.

## Régua e caminhos fechados (12/11/2026)

**Régua definida pelo usuário:** o que importa é o erro grave (acima de 0,50 no xG de um time), que é
o que gera aposta ruim. O erro médio é secundário. Saber qual time foi superior não é o problema.

**Onde os erros graves acontecem** (pelo xG que o modelo dá ao time)

| xG do modelo | Legado | 2026/27 |
|---|---|---|
| até 1,0 | 0,4% | 0 em 100 |
| 1,0 a 2,0 | 2,2% | 4,8% |
| acima de 2,0 | 9,4% | 14,8% |
| Total | 3,1% | 6,5% (25 em 382) |

- Com poucos gols o modelo é muito melhor: jogo sem gols tem 1,3% de erros graves; com 5 ou mais, 5,7%.
- A temporada 2026/27 tem média de gols alta (hipótese do usuário para a piora). Aplicando as taxas do
  legado à distribuição de jogos de 2026/27, os erros graves iriam de 3,1% para 3,9%; o observado é
  6,5%. A média de gols explica cerca de um quarto da piora.
- Nos jogos altos o erro não tem direção; ajuste de escala não corrige.

**Caminhos testados e fechados**

- **xGOT da Opta** (direto ou misturado ao modelo): piora em todas as faixas, mais ainda nos jogos altos.
- **xG da Opta misturado ao modelo:** não melhora.
- **Treinar com mais ligas e temporadas** (piloto: Ligue 1 2024/25 e 2025/26, Serie A 2025/26; 989
  jogos, 24 mil finalizações): os erros graves em 2026/27 ficam entre 6,3% e 6,8%, contra 6,5% da
  base. Treinar só com temporadas recentes piora. Os dados do piloto estão em `data/fotmob/` e
  `data/treino/treino_fotmob_piloto_ligue1_seriea.csv.gz`, mas não entraram no modelo de uso.
- **Pênalti:** já tratado (valor fixo; pênaltis descontados das grandes chances antes de distribuí-las).

**Caminhos de pé**

- Média do nível WhoScored com o só FotMob (0,149 contra 0,165 em 60 time-jogos; amostra pequena).
- Avaliação do usuário nas grandes chances: teste cego dos 20 gols, pendente.
- Não testado: outras estatísticas do jogo da FotMob e força acumulada do time (xGD) como entradas.

## Hipóteses, verificações e ideias guardadas

| | Descrição | Situação |
|---|---|---|
| H1 | O xG da Understat muda conforme a última ação | confirmada como efeito; falta detalhar por tipo |
| V2 | O que antecede cada "Rebound" no bruto | a fazer |
| H3 | O modelo antigo errava mais nos gols por usar o resultado | enfraquecida pelo teste |
| H4 | Erro maior do modelo antigo em contra-ataques | a fazer |
| H5 | Erro maior do modelo antigo nas grandes chances | explicada em parte pela marca mal atribuída |
| H6 | PPDA, gols e pontuação como perfil do clube | exploração inicial feita; a aprofundar |
| V7 | Persistência do PPDA de um clube entre temporadas | a fazer |
| H8 | Cabeçadas concentram divergência | a fazer |
| V9 | Indício de goleiro batido nos dados | conferida: o WhoScored registra quem foi driblado |
| H9 | As fontes usam informação sobre o goleiro que não publicam | a fazer |
| H10 | xGOT extremo, perto de 1, como sinal de gol desprotegido | confirmada nos lances; sem ganho no erro total |
| H11 | Drible em defensor e drible no goleiro valem diferente na Understat | a medir com mais jogos |
| H12 | Técnica da finalização (voleio, bicicleta) reduz o xG da Understat | sem apoio em 18 jogos; amostra pequena |
| H13 | A Understat ajusta o xG pelo pé dominante | não confirmada (40 mil finalizações de pé ruim) |
| V10 | StatsBomb aberta: 2015/16 completa em La Liga, Serie A, Premier League e Ligue 1 | conferida |
| V11 | Fonte com grande chance por finalização | conferida: WhoScored |
| I1 | Trava: limitar o desvio do nosso xG em relação ao da Opta | a testar; o xG da Opta já é usado para escolher a grande chance |
| I2 | Revisão humana só das finalizações em que os sinais se contradizem | a testar |

## Em aberto
- Como obter as páginas do WhoScored em volume (histórico para treino e rodadas novas).
- Por que a marca de grande chance e o xG da Understat se desencontram em parte das finalizações.
- Como identificar rebote com os dados da FotMob, que não traz a última ação.
- Se PPDA, deep e buildup podem ser reproduzidos com o que a FotMob fornece.
- Quais variáveis entram no xG por finalização.
- Como medir o erro, por finalização e por jogo.
- Quais ligas e temporadas da FotMob entram (hoje: La Liga 2021–2025).
- Fonte e rotina de atualização para jogos novos.
