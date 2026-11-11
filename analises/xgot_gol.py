import sys, warnings, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
S=sys.argv[1]; PENL={'La_liga':0.7433,'Serie_A':0.7613}
x=pd.read_pickle(S+'/work/disseca.pkl'); x['xgot_gol']=np.where(x.gol==1,x.xgot.fillna(0),0.0)
c0=pd.read_pickle(S+'/dados/dados/variaveis.pkl'); pen=c0[c0.lance=='Penalty'].assign(p=lambda d:d.liga.map(PENL)).groupby(['f_arq','mandante']).p.sum()
uj=pd.read_pickle(S+'/work/u_jogos.pkl').set_index('match_id'); jm=x.groupby('f_arq').u_match.first()
CAT={k:sorted(x[k].unique()) for k in ('parte','lance')}
def cod(d,cols):
    d=d[cols].copy()
    for k in CAT: d[k]=pd.Categorical(d[k],categories=CAT[k])
    return d
B=['X','Y','parte','lance','big']
for nome,cols in (('base',B),('+ xGOT',B+['xgot']),('+ foi gol',B+['gol']),('+ foi gol + xGOT',B+['gol','xgot']),('+ xGOT só nos gols',B+['xgot_gol']),('+ foi gol + xGOT + xG da Opta',B+['gol','xgot','xg_opta'])):
    ps=[]
    for a,b in (('La_liga','Serie_A'),('Serie_A','La_liga')):
        m=HistGradientBoostingRegressor(max_iter=600,learning_rate=0.06,max_leaf_nodes=47,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0).fit(cod(x[x.liga==a],cols),x[x.liga==a].xg_understat)
        te=x[x.liga==b].copy(); te['p']=np.clip(m.predict(cod(te,cols)),0.001,0.99); ps.append(te)
    t=pd.concat(ps); s=t.groupby(['f_arq','mandante']).p.sum(); s=s.add(pen.reindex(s.index).fillna(0)); j=s.rename('m').reset_index()
    j['u']=[float(uj.loc[jm[a]].xg_h if md==1 else uj.loc[jm[a]].xg_a) for a,md in zip(j.f_arq,j.mandante)]; e=j.m-j.u; a_=e.abs(); g=t[t.gol==1]
    print(f'{nome:32s} time-jogo: médio {a_.mean():.3f} | mediano {a_.median():.3f} | acima de 0,30: {(a_>.3).mean():.1%} | acima de 0,50: {(a_>.5).mean():.1%} || nos gols: modelo {g.p.mean():.3f} x Understat {g.xg_understat.mean():.3f} | erro médio nos gols {(g.p-g.xg_understat).abs().mean():.3f}')
