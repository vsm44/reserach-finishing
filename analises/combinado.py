import sys, warnings, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
S=sys.argv[1]; PENL={'La_liga':0.7433,'Serie_A':0.7613}
x=pd.read_pickle(S+'/work/disseca.pkl').sort_values(['f_arq','mandante','minuto','f_id']).reset_index(drop=True)
g=x.groupby(['f_arq','mandante']); ant_ok=((g.no_alvo.shift()==1)|(g.bloqueado.shift()==1)|(g.trave.shift()==1))&(g.gol.shift()==0); x['reb']=((x.minuto==g.minuto.shift())&ant_ok).fillna(False).astype(int)
c0=pd.read_pickle(S+'/dados/dados/variaveis.pkl'); pen=c0[c0.lance=='Penalty'].assign(p=lambda d:d.liga.map(PENL)).groupby(['f_arq','mandante']).p.sum()
uj=pd.read_pickle(S+'/work/u_jogos.pkl').set_index('match_id'); jm=x.groupby('f_arq').u_match.first()
CAT={k:sorted(x[k].unique()) for k in ('parte','lance')}
def cod(d,cols):
    d=d[cols].copy()
    for k in CAT: d[k]=pd.Categorical(d[k],categories=CAT[k])
    return d
B=['X','Y','parte','lance','big']
for nome,cols,une in (('base',B,False),('+ foi gol',B+['gol'],False),('+ unir rebotes do mesmo minuto',B,True),('+ foi gol + unir rebotes',B+['gol'],True),('+ foi gol + rebote como entrada + unir',B+['gol','reb'],True)):
    ps=[]
    for a,b in (('La_liga','Serie_A'),('Serie_A','La_liga')):
        m=HistGradientBoostingRegressor(max_iter=600,learning_rate=0.06,max_leaf_nodes=47,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0).fit(cod(x[x.liga==a],cols),x[x.liga==a].xg_understat)
        te=x[x.liga==b].copy(); te['p']=np.clip(m.predict(cod(te,cols)),0.001,0.99); ps.append(te)
    t=pd.concat(ps).sort_values(['f_arq','mandante','minuto','f_id'])
    if une:
        t['g']=(t.reb==0).groupby([t.f_arq,t.mandante]).cumsum(); s=t.groupby(['f_arq','mandante','g']).p.apply(lambda v:1-np.prod(1-v.values)).groupby(level=[0,1]).sum()
    else: s=t.groupby(['f_arq','mandante']).p.sum()
    s=s.add(pen.reindex(s.index).fillna(0)); j=s.rename('m').reset_index(); j['u']=[float(uj.loc[jm[a]].xg_h if md==1 else uj.loc[jm[a]].xg_a) for a,md in zip(j.f_arq,j.mandante)]; e=j.m-j.u; a_=e.abs()
    print(f'{nome:40s} médio {a_.mean():.4f} | mediano {a_.median():.3f} | 90% até {a_.quantile(.9):.3f} | acima de 0,30: {(a_>.3).mean():.1%} | acima de 0,50: {(a_>.5).mean():.2%} | acima de 0,70: {(a_>.7).mean():.2%} | desvio {e.mean():+.3f}')
