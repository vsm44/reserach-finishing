Atualizado em 14/11/2026

# Modelo Finishing — Expected Goals

## O que é
Projeto para medir o xG e o xGA de partidas já disputadas da forma como a Understat mede (ou media, caso não volte), usando os dados de fontes como Fotmob/Opta, WhoScored, FM-INSIDE e outros que se mostrarem necessários. A ideia é entender as diferenças que dos modelos de fontes de dados tidas como mais modernas e, aplicando informações de outras fontes de dados, emular o número de xG/XGA que a Understat daria para um jogo.


## Por quê
- A Understat é a fonte de dados principal para um projeto de apostas do proprietário do repositório.
- Um modelo próprio remove essa dependência e permite cobrir ligas que a Understat não cobre.
- O modelo da Understat é pioneiro, mais simples e funciona para o nosso propósito.

## O que NÃO é
Não é engenharia reversa para lançar um serviço. Serve só ao nosso projeto. 

## Vocabulário
- **Finalização**, não "chute". Os modelos chamam tudo de chute (shot), mas o conjunto inclui
  cabeceios e outras partes do corpo. Daí o nome do projeto.
- **Rebote**: finalização que nasce de outra finalização na mesma jogada.
- **Gol contra**: não é finalização de quem o marca.
- **xGA** de um time num jogo é o xG do adversário nesse jogo. São duas medidas do mesmo jogo
  (ataque de um, defesa do outro), e as duas precisam ser entendidas.

## Como trabalhamos
1. O bruto é a referência. Trabalho anterior é registro, não verdade.
2. Sem inferência, presunção, aproximação ou correlação sem evidência. O que não se sabe se escreve
   como "não sei".
3. Regra fixa da fonte é descoberta e fixada como regra, não aproximada por estatística.
4. Há julgamento humano na anotação das duas fontes. Diferenças são estudadas, não correlacionadas.
5. Na dúvida, mesmo pequena, ou quando algo do futebol real não estiver claro, perguntar: o olho
   humano muitas vezes resolve.
6. Uma dúvida por vez, mensagens curtas. Dados e evidências sem conclusões, salvo quando pedidas.
7. Nada é alterado, movido, deletado ou commitado sem lista do que é afetado e autorização.
8. Primeiro acertar nos dados como um todo; a aplicação no projeto de apostas vem depois.
9. Devagar, passo a passo. Se preciso, começar por um único jogo. Deixar passar algo importante
   custa muito trabalho perdido lá na frente, e os créditos são limitados. Pressa só prejudica.

## Dados
- `data/understat/` — bruto da Understat, 5 ligas.
- `data/fotmob/` — bruto da FotMob.
- `legado/` — trabalho anterior, só para consulta.

Papel de cada dado:
- Posição das finalizações: a da FotMob/Opta.
- xG, xGA e xGOT da própria Opta: comparação e referência. Dificilmente entrada.
- deep, deep sofrido, buildup e afins da Understat: tese de que podem ser entrada, a testar.

## Horizonte (secundário)
Se a estratégia se provar no mercado, fora da amostra, evoluir para um modelo próprio de previsão.
Não faz parte da fase atual.

## Estado
O estado atual, resumido, está em CLAUDE.md. O histórico detalhado está em PLANEJAMENTO.md.
