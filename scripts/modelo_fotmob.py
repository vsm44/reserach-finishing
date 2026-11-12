"""Modelo novo, nível só FotMob: xG de cada finalização e total por time, no padrão da Understat.

Entradas por finalização: posição (X, Y), parte do corpo, tipo de lance, grande chance
(escolhida pelo maior xG da Opta entre as finalizações do jogador ou do time) e se foi gol.
O total do time une as finalizações do mesmo minuto quando a anterior foi defendida,
bloqueada ou bateu na trave (rebote). Pênalti vale o número fixo da liga.

Segunda etapa: o total de cada time é corrigido com dados do jogo inteiro (gols, total do
adversário, contagens das finalizações e xG da Opta por time).
"""
import gzip, json, pickle, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
PENALTI = {"La_liga": 0.7433, "Bundesliga": 0.7578, "Ligue_1": 0.7601, "EPL": 0.7612, "Serie_A": 0.7613}
COLS = ["X", "Y", "parte", "lance", "big", "gol"]


def finalizacoes(d):
    """Finalizações de um jogo da FotMob (sem gol contra), com a grande chance marcada."""
    casa = d["general"]["homeTeam"]["id"]
    sh = [s for s in (d["content"].get("shotmap") or {}).get("shots") or [] if not s["isOwnGoal"]]
    r = pd.DataFrame([dict(lado="h" if s["teamId"] == casa else "a", jog=s["playerId"], jogador=s.get("fullName") or s.get("playerName"),
                           minute=s["min"], acr=s.get("minAdded") or 0, fid=s["id"], X=s["x"] / 105, Y=s["y"] / 68,
                           parte=s["shotType"], lance=s["situation"], gol=int(s["eventType"] == "Goal"), ev=s["eventType"],
                           bloq=int(bool(s["isBlocked"])), alvo=int(bool(s["isOnTarget"])), xg_opta=s.get("expectedGoals") or 0.0,
                           xgot=s.get("expectedGoalsOnTarget")) for s in sh])
    if not len(r):
        return r
    r["big"] = 0
    perd = {}
    for pl in (d["content"].get("playerStats") or {}).values():
        bc = pm = 0
        for grp in pl.get("stats") or []:
            for v in (grp.get("stats") or {}).values():
                if v.get("key") == "big_chance_missed_title":
                    bc = (v.get("stat") or {}).get("value") or 0
                elif v.get("key") == "missed_penalty":
                    pm = (v.get("stat") or {}).get("value") or 0
        perd[pl["id"]] = max(bc - pm, 0)
    tot = estatisticas(d)
    np_ = r[r.lance != "Penalty"]
    for jog, k in perd.items():
        r.loc[np_[(np_.jog == jog) & (np_.gol == 0)].sort_values("xg_opta", ascending=False).index[:int(k)], "big"] = 1
    for i, lado in enumerate(("h", "a")):
        conv = (tot[i].get("big_chance") or 0) - (tot[i].get("big_chance_missed_title") or 0) - int(((r.lado == lado) & (r.lance == "Penalty") & (r.gol == 1)).sum())
        if not np.isnan(conv):
            r.loc[np_[(np_.lado == lado) & (np_.gol == 1)].sort_values("xg_opta", ascending=False).index[:max(int(conv), 0)], "big"] = 1
    return r


def _num(v):
    if v is None:
        return np.nan, np.nan
    if isinstance(v, (int, float)):
        return float(v), np.nan
    s = str(v)
    try:
        if "(" in s:
            a, b = s.split("(")
            return float(a), float(b.strip(" %)")) / 100
        return float(s), np.nan
    except ValueError:
        return np.nan, np.nan


def estatisticas(d):
    """Estatísticas do jogo inteiro por time: [mandante, visitante]."""
    out = [{}, {}]
    for grp in (((d["content"].get("stats") or {}).get("Periods") or {}).get("All") or {}).get("stats", []):
        for s in grp["stats"]:
            k, st = s.get("key"), s.get("stats")
            if not k or not st or len(st) != 2 or st[0] is None:
                continue
            for i in (0, 1):
                a, b = _num(st[i])
                out[i][k] = a
                if not np.isnan(b):
                    out[i][k + "_pct"] = b
    return out


def codifica(d, cats):
    d = d[COLS].copy()
    for c, lista in cats.items():
        d[c] = pd.Categorical(d[c].where(d[c].isin(lista), lista[0]), categories=lista)
    return d


def treina(tabela):
    from sklearn.ensemble import HistGradientBoostingRegressor
    cats = {c: sorted(tabela[c].unique()) for c in ("parte", "lance")}
    m = HistGradientBoostingRegressor(max_iter=600, learning_rate=0.06, max_leaf_nodes=47, min_samples_leaf=20,
                                      categorical_features="from_dtype", early_stopping=True, random_state=0)
    m.fit(codifica(tabela, cats), tabela.xg_understat)
    return dict(modelo=m, cats=cats)


def preve(mod, s, liga):
    s = s.copy()
    s["p"] = np.where(s.lance == "Penalty", PENALTI[liga], np.clip(mod["modelo"].predict(codifica(s, mod["cats"])), 0, 1)) if len(s) else []
    return s


def total(g):
    """Total do time, unindo rebotes do mesmo minuto."""
    if not len(g):
        return 0.0
    g = g.sort_values(["minute", "acr", "fid"])
    ok = ((g.alvo.shift() == 1) | (g.bloq.shift() == 1) | (g.ev.shift() == "Post")) & (g.gol.shift() == 0)
    reb = ((g.minute + g.acr) == (g.minute + g.acr).shift()) & ok
    return float(g.groupby((~reb).cumsum()).p.apply(lambda v: 1 - np.prod(1 - v.values)).sum())


COLS2 = ["m", "m_adv", "soma", "n_fin", "n_big", "p_big", "p_max", "n_cab", "n_alvo", "n_bloq", "n_pen", "opta_fin", "xgot_fin",
         "mandante", "gols", "gols_adv", "f_expected_goals", "f_expected_goals_open_play", "f_expected_goals_set_play",
         "f_expected_goals_non_penalty", "f_expected_goals_on_target", "a_expected_goals"]


def linhas_time(d, s):
    """Dados de cada time no jogo para a segunda etapa: [mandante, visitante]."""
    h = d["header"]["teams"]
    st = estatisticas(d)
    out = []
    for i, lado in enumerate(("h", "a")):
        t, o = (s[s.lado == lado], s[s.lado != lado]) if len(s) else (s, s)
        r = dict(m=total(t), m_adv=total(o), soma=float(t.p.sum()) if len(t) else 0.0, n_fin=len(t),
                 n_big=int(t.big.sum()) if len(t) else 0, p_big=float(t[t.big == 1].p.sum()) if len(t) else 0.0,
                 p_max=float(t.p.max()) if len(t) else 0.0, n_cab=int((t.parte == "Header").sum()) if len(t) else 0,
                 n_alvo=int(t.alvo.sum()) if len(t) else 0, n_bloq=int(t.bloq.sum()) if len(t) else 0,
                 n_pen=int((t.lance == "Penalty").sum()) if len(t) else 0, opta_fin=float(t.xg_opta.sum()) if len(t) else 0.0,
                 xgot_fin=float(t.xgot.fillna(0).sum()) if len(t) else 0.0, mandante=int(i == 0),
                 gols=float(h[i].get("score") or 0), gols_adv=float(h[1 - i].get("score") or 0))
        for k, v in st[i].items():
            r["f_" + k] = v
        for k, v in st[1 - i].items():
            r["a_" + k] = v
        out.append(r)
    return out


def treina2(tabela):
    """Segunda etapa: aprende a diferença entre o xG da Understat e o total da primeira etapa."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    m = HistGradientBoostingRegressor(max_iter=250, learning_rate=0.04, max_leaf_nodes=6, min_samples_leaf=40,
                                      l2_regularization=2.0, early_stopping=False, random_state=0)
    m.fit(tabela[COLS2], tabela.u - tabela.m)
    return m


def jogo(mod, d, liga):
    """Linha-resumo de um jogo. xg_m e xg_v: xG final do mandante e do visitante (com a segunda etapa,
    se o modelo a tiver). xg1_m e xg1_v: total da primeira etapa. opta_m e opta_v: xG publicado pela Opta."""
    h = d["header"]["teams"]
    s = preve(mod, finalizacoes(d), liga)
    lt = linhas_time(d, s)
    x1 = [lt[0]["m"], lt[1]["m"]]
    if mod.get("etapa2") is not None:
        aj = mod["etapa2"].predict(pd.DataFrame(lt).reindex(columns=COLS2))
        xf = [max(float(x1[i] + aj[i]), 0.0) for i in (0, 1)]
    else:
        xf = x1
    return dict(id=d["general"]["matchId"], data=d["general"]["matchTimeUTCDate"][:10], mandante=h[0]["name"], visitante=h[1]["name"],
                gols_m=h[0].get("score"), gols_v=h[1].get("score"), xg_m=xf[0], xg_v=xf[1], xg1_m=x1[0], xg1_v=x1[1],
                opta_m=lt[0].get("f_expected_goals", np.nan), opta_v=lt[1].get("f_expected_goals", np.nan),
                fin_m=lt[0]["n_fin"], fin_v=lt[1]["n_fin"], gc_m=lt[0]["n_big"], gc_v=lt[1]["n_big"]), s


def le(caminho):
    with gzip.open(caminho) as f:
        return json.load(f)
