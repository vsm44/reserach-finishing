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

## Em aberto
- Como identificar rebote com os dados da FotMob, que não traz a última ação.
- Se PPDA, deep e buildup podem ser reproduzidos com o que a FotMob fornece.
- Quais variáveis entram no xG por finalização.
- Como medir o erro, por finalização e por jogo.
- Quais ligas e temporadas da FotMob entram (hoje: La Liga 2021–2025).
- Fonte e rotina de atualização para jogos novos.
