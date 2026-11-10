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
