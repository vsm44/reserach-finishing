"""Casa cada chute da Understat com o mesmo chute no FotMob (La Liga e Serie A).

Jogos: casados pelo calendário. Primeiro por data e placar, quando há candidato
único, o que ensina o id do FotMob de cada nome da Understat; depois pelos dois
times e data até 1 dia de diferença. Chutes: dentro do jogo e do lado
(mandante/visitante), pela menor combinação de diferença de minuto e distância
de posição no campo. A Understat conta o minuto a partir de 0 e o FotMob soma o
acréscimo à parte; as coordenadas têm a mesma orientação (conferido: espelhando
o eixo Y, a taxa cai de 96% para 45%). Gols contra ficam fora, porque não são chute de quem os
marca. 2019/20 fica fora porque o FotMob não tem mapa de chutes nessa temporada.

Uso (da raiz do projeto):
  python modelo_xg/pareia_chutes.py
Grava modelo_xg/dados/chutes_pareados.pkl e imprime a taxa de pareamento.
"""
import glob
import gzip
import json
import os

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

LIGAS = {"La_liga": "la_liga", "Serie_A": "serie_a"}
TEMPORADAS = range(2020, 2025)          # 20/21 a 24/25; 25/26 é holdout
SAIDA = "modelo_xg/dados/chutes_pareados.pkl"
MAX_MINUTO = 3                           # diferença máxima de minuto aceita
MAX_METROS = 8.0                         # distância máxima entre as posições


def ler(caminho):
    with gzip.open(caminho) as f:
        return json.load(f)


def jogos_understat(liga, ano):
    # Lista de jogos encerrados da temporada, com data UTC e placar
    d = ler(f"data/bruto/understat/{liga}/{ano}/liga.json.gz")
    return pd.DataFrame([dict(u_id=j["id"], data=pd.Timestamp(j["datetime"]).normalize(),
                              hg=int(j["goals"]["h"]), ag=int(j["goals"]["a"]),
                              u_home=j["h"]["title"], u_away=j["a"]["title"])
                         for j in d["dates"] if j["isResult"]])


def jogos_fotmob(pasta, ano):
    # Cabeçalho de cada jogo baixado: data UTC, placar e ids dos times
    linhas = []
    for f in glob.glob(f"data/bruto/fotmob/{pasta}/{ano}/*.json.gz"):
        if f.endswith("liga.json.gz"):
            continue
        d = ler(f)
        g, h = d["general"], d["header"]["teams"]
        linhas.append(dict(f_arq=f, data=pd.Timestamp(g["matchTimeUTC"]).tz_localize(None).normalize(),
                           hg=h[0].get("score"), ag=h[1].get("score"),
                           f_home=g["homeTeam"]["id"], f_away=g["awayTeam"]["id"]))
    return pd.DataFrame(linhas)


def casa_jogos(u, f):
    # 1ª passada: mesma data e placar com candidato único; cada casamento vota no id
    # do FotMob para os nomes da Understat. 2ª passada: os dois times pelo id votado
    # e data até 1 dia de diferença.
    votos = {}
    for j in u.itertuples(index=False):
        c = f[(f.hg == j.hg) & (f.ag == j.ag) & (f.data == j.data)]
        if len(c) == 1:
            for nome, fid in ((j.u_home, c.f_home.iloc[0]), (j.u_away, c.f_away.iloc[0])):
                votos.setdefault(nome, {}).setdefault(fid, 0)
                votos[nome][fid] += 1
    mapa = {nome: max(v, key=v.get) for nome, v in votos.items()}
    pares = []
    for j in u.itertuples(index=False):
        c = f[(f.f_home == mapa.get(j.u_home)) & (f.f_away == mapa.get(j.u_away))
              & ((f.data - j.data).abs() <= pd.Timedelta(days=1))]
        if len(c) == 1 and c.hg.iloc[0] == j.hg and c.ag.iloc[0] == j.ag:
            pares.append((j.u_id, c.f_arq.iloc[0], c.f_home.iloc[0]))
    return pares


def casa_chutes(u_chutes, f_chutes):
    # Custo = diferença de minuto + distância em metros/4; atribuição de menor custo total
    if not len(u_chutes) or not len(f_chutes):
        return []
    ux = np.array([(float(s["X"]) * 105, float(s["Y"]) * 68,
                    float(s["minute"]) + 1) for s in u_chutes])  # Understat conta o minuto a partir de 0
    fx = np.array([(s["x"], s["y"], s["min"] + (s["minAdded"] or 0)) for s in f_chutes])  # acréscimo somado
    dmin = np.abs(ux[:, 2][:, None] - fx[:, 2][None, :])
    dist = np.hypot(ux[:, 0][:, None] - fx[:, 0][None, :], ux[:, 1][:, None] - fx[:, 1][None, :])
    custo = dmin + dist / 4
    custo[(dmin > MAX_MINUTO) | (dist > MAX_METROS)] = 1e6
    li, co = linear_sum_assignment(custo)
    return [(i, j, dist[i, j], dmin[i, j]) for i, j in zip(li, co) if custo[i, j] < 1e6]


def main():
    linhas, resumo = [], []
    for liga, pasta in LIGAS.items():
        for ano in TEMPORADAS:
            u, f = jogos_understat(liga, ano), jogos_fotmob(pasta, ano)
            pares = casa_jogos(u, f)
            n_u = n_par = 0
            for u_id, f_arq, f_home in pares:
                ud, fd = ler(f"data/bruto/understat/{liga}/{ano}/{u_id}.json.gz"), ler(f_arq)
                fs = [s for s in (fd["content"].get("shotmap") or {}).get("shots") or [] if not s["isOwnGoal"]]
                for lado in ("h", "a"):
                    us = [s for s in ud["shots"][lado] if s["result"] != "OwnGoal"]
                    fl = [s for s in fs if (s["teamId"] == f_home) == (lado == "h")]
                    n_u += len(us)
                    for i, j, dist, dm in casa_chutes(us, fl):
                        n_par += 1
                        linhas.append(dict(liga=liga, season=ano, u_match=u_id, f_arq=os.path.basename(f_arq),
                                           h_a=lado, dist_par=dist, dmin_par=dm,
                                           **{f"u_{k}": v for k, v in us[i].items()},
                                           **{f"f_{k}": v for k, v in fl[j].items() if not isinstance(v, dict)}))
            resumo.append(dict(liga=liga, season=ano, jogos_u=len(u), jogos_casados=len(pares),
                               chutes_u=n_u, chutes_pareados=n_par, taxa=n_par / max(n_u, 1)))
    return pd.DataFrame(linhas), pd.DataFrame(resumo)


if __name__ == "__main__":
    import sys
    chutes, resumo = main()
    print(resumo.to_string(index=False, formatters={"taxa": "{:.1%}".format}))
    print(f"distância média do par: {chutes.dist_par.mean():.2f} m | minuto igual: {(chutes.dmin_par == 0).mean():.1%}")
    if "--grava" in sys.argv:
        os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
        chutes.to_pickle(SAIDA)
