"""Treina o modelo e mede quanto ele se aproxima da Understat (só La Liga e Serie A).

Memória desta frente: CLAUDE.md + modelo_xg/CONSENSO.md e ESTADO.md.
Não é a planilha nem a rodada (isso é AGENTS.md / o outro agente).

Duas provas, sem tocar na Ligue 1 nem em 25/26:
  tempo   treina 20/21 a 23/24 nas duas ligas, testa 24/25
  liga    treina numa liga e testa na outra, que o modelo nunca viu (simula Portugal)

Versões do modelo de chute (histórico das tentativas):
  v0  só lugar e tipo do chute
  v1  v0 + placar, minuto, mando, quem chuta e histórico dos times
  v2  v1 + jogo aéreo: cabeçadas do jogador; cabeçadas, escanteios, cruzamentos e
      duelos aéreos dos times (ideia do usuário: time que cruza, centroavante que cabeceia)
  v3  v2 + fatos do lance: no alvo, bloqueado, trave, gol
  v4  v3 + onde cruzou a linha do gol e estatísticas do próprio jogo (grandes chances etc.)
  v5  v4 + grande chance quase chute a chute, pelas estatísticas de cada jogador
  v6  v5 + força da escalação de ataque e de defesa, jogador por jogador (não ajudou)
  v7  v5 + grande chance marcada chute a chute pela qualidade do chute
  v8  v7 + ajuste por jogo: um segundo modelo corrige o xG somado de cada time no jogo
      com as estatísticas do jogo inteiro. No treino, o xG somado que ele recebe vem
      de previsões feitas sem a própria temporada (senão ele aprenderia a corrigir um
      modelo que já viu as respostas).
Pênalti não passa pelo modelo de chute: vale o número fixo da liga de treino.

Métricas (modelo contra Understat), todas por jogo:
  jogo      xG de cada time: correlação, nível (média) e dispersão (desvio)
  gatilhos  com os jogos ANTERIORES, como no motor, sem vermelhos nem odds; o jogo
            dispara se qualquer um dos dois times disparar. Concordância = de todos os
            jogos em que Understat ou modelo dispararam, em quantos os dois dispararam.
            LAY-over defesa    (gols sofridos - xGA)/xGA >= limiar na janela da liga
            LAY-over completo  defesa, sem a exclusão de ataque ((xG - gols)/xG >= 0,35
                               nos 4 anteriores)
            LAY-under          maior (xG - gols)/xG dos dois nos 3 anteriores >= limiar

Uso (da raiz do projeto):
  python modelo_xg/treina_avalia.py
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

LAY_OVER = {"La_liga": (3, 0.45), "Serie_A": (2, 0.45)}
LAY_UNDER = {"La_liga": 0.35, "Serie_A": 0.30}
V0 = ["x", "y", "distancia", "angulo", "parte", "lance"]
V1 = V0 + ["saldo", "minuto", "mandante", "conv_jogador", "ch_ant",
           "atq_gf_ant", "atq_gs_ant", "atq_cf_ant", "atq_cs_ant",
           "def_gf_ant", "def_gs_ant", "def_cf_ant", "def_cs_ant"]
V2 = V1 + ["cab_parcela_jogador", "cab_conv_jogador",
           "atq_hf_ant", "atq_hs_ant", "atq_ef_ant", "atq_es_ant", "atq_xf_ant", "atq_xs_ant", "atq_ap_ant",
           "def_hf_ant", "def_hs_ant", "def_ef_ant", "def_es_ant", "def_xf_ant", "def_xs_ant", "def_ap_ant"]
V3 = V2 + ["no_alvo", "bloqueado", "trave", "gol"]
V4 = V3 + ["gol_y", "gol_z", "jg_grandes", "jg_grandes_perdidas", "jg_chutes_area", "jg_cruz", "jg_escanteios",
           "jga_grandes", "jga_chutes_area"]
V5 = V4 + ["grande_chance"]
V6 = V5 + ["esc_atq_gols_90", "esc_atq_chutes_90", "esc_atq_gc_perdidas_90", "esc_atq_criadas_90", "esc_atq_rodizio",
           "esc_def_aereos_90", "esc_def_acoes_def_90", "esc_def_driblado_90", "esc_def_erros_90",
           "esc_gk_defesa_pct", "esc_def_rodizio"]
V7 = V5 + ["gc_marcada"]
# TESTE autorizado pelo usuário em 14/09 (não muda a regra): xG da Opta com e sem as grandes chances
GRANDES = ["jg_grandes", "jg_grandes_perdidas", "jga_grandes", "grande_chance", "gc_marcada"]
V9A = V7 + ["xg_opta"]
V9B = [v for v in V7 if v not in GRANDES] + ["xg_opta"]
V10 = V7 + ["jog_aereos_ganhos", "jog_aereos_disputados", "adv_cortes_cabeca"]   # pistas de cabeçada disputada
# TESTES de 17/09 (autorizados pelo usuário): execução do chute = xGOT menos o xG da Opta, e
# tirar onde a bola cruzou o gol, que é execução pura e a Understat não enxerga
V11 = V7 + ["exec_chute"]
V12 = [v for v in V7 if v not in ("gol_y", "gol_z")]
V13 = V12 + ["exec_chute"]
# Correção por jogo (v14): o xG somado do time mais o que só faz sentido com o jogo pronto —
# xGOT do jogo, execução (xGOT menos o xG da Opta) e gols contra o xGOT
JOGO = ["xg_soma", "chutes", "cabecadas", "gc_marcadas", "no_alvo", "bloqueados", "penaltis", "gols", "mandante",
        "jg_grandes", "jg_grandes_perdidas", "jg_chutes_area", "jg_cruz", "jg_escanteios", "jga_grandes", "jga_chutes_area",
        "xgot_jogo", "exec_jogo", "gols_menos_xgot"]
CATEGORICAS = ["parte", "lance"]
CATEGORIAS = {"parte": ["Header", "LeftFoot", "OtherBodyParts", "RightFoot"],
              "lance": ["FastBreak", "FreeKick", "FromCorner", "IndividualPlay", "Penalty",
                        "RegularPlay", "SetPiece", "ThrowInSetPiece"]}


def codifica(df, cols):
    # Categóricas com a MESMA lista de categorias no treino e no teste; senão os códigos
    # mudam de significado quando uma categoria falta num dos lados
    x = df[cols].copy()
    for c in CATEGORICAS:
        if c in x:
            x[c] = pd.Categorical(x[c], categories=CATEGORIAS[c])
    return x


def gbm():
    return HistGradientBoostingRegressor(max_iter=600, learning_rate=0.05, max_leaf_nodes=31,
                                         min_samples_leaf=40, categorical_features="from_dtype",
                                         early_stopping=True, validation_fraction=0.1, random_state=0)


def treina(tr, cols):
    # Modelo de chute; alvo = xG da Understat do chute
    return gbm().fit(codifica(tr, cols), tr.xg_understat)


def preve(m, te, cols, penalti):
    p = np.clip(m.predict(codifica(te, cols)), 0.001, 0.99)
    return np.where(te.lance == "Penalty", penalti, p)


def tabela_jogo(c, col):
    # Uma linha por time em cada jogo: xG somado do modelo de chute, contagens do lance,
    # estatísticas do jogo, o xG da Understat (alvo) e os gols do placar oficial (com gol contra)
    g = c.assign(_cab=c.parte == "Header", _pen=c.lance == "Penalty").groupby(
        ["liga", "season", "f_arq", "data", "time", "adversario"])
    j = g.agg(xg_soma=(col, "sum"), xg_u=("xg_understat", "sum"), chutes=("gol", "size"), cabecadas=("_cab", "sum"),
              gc_marcadas=("gc_marcada", "sum"), no_alvo=("no_alvo", "sum"), bloqueados=("bloqueado", "sum"),
              penaltis=("_pen", "sum"), gols=("gols_time_jogo", "first"), mandante=("mandante", "first"),
              xgot_jogo=("xgot", "sum"), exec_jogo=("exec_chute", "sum"),
              **{k: (k, "first") for k in JOGO if k.startswith("jg")})
    j["gols_menos_xgot"] = j.gols - j.xgot_jogo
    return j.reset_index()


def previsoes_fora_da_temporada(tr, cols, penalti):
    # xG de chute para o treino do ajuste: cada temporada prevista por um modelo que não a viu.
    # `penalti` recebe o recorte e devolve o valor do pênalti de cada chute
    tr = tr.copy()
    tr["xg_modelo"] = np.nan
    base = tr[tr.lance != "Penalty"]
    for s in sorted(tr.season.unique()):
        m = treina(base[base.season != s], cols)
        sel = tr.season == s
        tr.loc[sel, "xg_modelo"] = preve(m, tr[sel], cols, penalti(tr[sel]))
    return tr


def gatilhos(j, col, liga):
    # Por jogo, com os jogos ANTERIORES de cada time: LAY-over (defesa e completo) e LAY-under
    w, lim = LAY_OVER[liga]
    sofr = j.rename(columns={"time": "adversario", "adversario": "time", col: "xga", "gols": "gs"})[["f_arq", "time", "xga", "gs"]]
    t = j[["f_arq", "data", "time", col, "gols"]].rename(columns={col: "xg"}).merge(sofr, on=["f_arq", "time"]).sort_values("data")
    g = t.groupby("time")
    ant = lambda s, n: s.rolling(n).mean().shift(1)
    xga_w, gs_w = g.xga.transform(lambda s: ant(s, w)), g.gs.transform(lambda s: ant(s, w))
    xg4, gl4 = g.xg.transform(lambda s: ant(s, 4)), g.gols.transform(lambda s: ant(s, 4))
    xg3, gl3 = g.xg.transform(lambda s: ant(s, 3)), g.gols.transform(lambda s: ant(s, 3))
    t["defesa"] = (gs_w - xga_w) / xga_w >= lim
    t["ataque"] = ((xg4 - gl4) / xg4 >= 0.35) & (xg4 > gl4)
    t["gap_under"] = (xg3 - gl3) / xg3
    t["ok"] = xga_w.notna() & xg4.notna()
    m = t.groupby("f_arq").agg(defesa=("defesa", "any"), ataque=("ataque", "any"), gap_under=("gap_under", "max"), ok=("ok", "all"))
    m = m[m.ok]
    return pd.DataFrame({"LAY-over defesa": m.defesa, "LAY-over completo": m.defesa & ~m.ataque,
                         "LAY-under": m.gap_under >= LAY_UNDER[liga]})


def mede(j, col_modelo, nome):
    linhas = []
    for liga, x in j.groupby("liga"):
        a, b = x.xg_u, x[col_modelo]
        l = dict(prova=nome, liga=liga, corr_jogo=a.corr(b), nivel=b.mean() / a.mean(), dispersao=b.std() / a.std())
        gu, gm = gatilhos(x, "xg_u", liga), gatilhos(x, col_modelo, liga)
        gu, gm = gu.align(gm, join="inner")
        for k in gu:
            u, m = gu[k], gm[k]
            l[k] = f"{(u & m).sum() / max((u | m).sum(), 1):.1%} ({int(u.sum())}/{int(m.sum())})"
        linhas.append(l)
    return linhas


def prova(c, treino, teste, pen_teste, nome):
    # v7 (soma dos chutes) e v8 (soma corrigida pelo ajuste por jogo) na mesma prova
    base = c[treino & (c.lance != "Penalty")].dropna(subset=["xg_understat"])
    pen = c[treino & (c.lance == "Penalty")].dropna(subset=["xg_understat"]).groupby("liga").xg_understat.median()
    m = treina(base, V7)
    te = c[teste].dropna(subset=["xg_understat"]).copy()
    te["xg_modelo"] = preve(m, te, V7, pen_teste(pen, te))
    jt = tabela_jogo(te, "xg_modelo")
    # ajuste por jogo treinado com previsões feitas fora da temporada
    tr = previsoes_fora_da_temporada(c[treino].dropna(subset=["xg_understat"]), V7, lambda df: pen_teste(pen, df))
    jtr = tabela_jogo(tr, "xg_modelo")
    aj = gbm().fit(jtr[JOGO], jtr.xg_u)
    jt["xg_ajustado"] = np.clip(aj.predict(jt[JOGO]), 0.0, None)
    return mede(jt, "xg_soma", f"v7 {nome}") + mede(jt, "xg_ajustado", f"v8 {nome}")


def main():
    c = pd.read_pickle("modelo_xg/dados/variaveis.pkl")
    r = prova(c, c.season <= 2023, c.season == 2024, lambda pen, df: df.liga.map(pen), "tempo (testa 24/25)")
    for a, b in (("La_liga", "Serie_A"), ("Serie_A", "La_liga")):
        r += prova(c, c.liga == a, c.liga == b, lambda pen, df, a=a: pen[a], f"liga (treina {a})")
    pd.set_option("display.width", 250)
    print("gatilhos: concordância (disparos Understat / disparos modelo)")
    print(pd.DataFrame(r).to_string(index=False, float_format=lambda v: f"{v:.3f}"))


if __name__ == "__main__":
    main()
