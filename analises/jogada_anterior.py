import sys, warnings, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
S=sys.argv[1]; PENL={'La_liga':0.7433,'Serie_A':0.7613}
x=pd.read_pickle(S+'/work/disseca.pkl'); x['la']=x.u_lastAction.fillna('None').astype(str); x['reb']=(x.la=='Rebound').astype(int); x['bloq']=x.bloqueado
c0=pd.read_pickle(S+'/dados/dados/variaveis.pkl'); pen=c0[c0.lance=='Penalty'][['f_arq','mandante','liga']].assign(p=lambda d:d.liga.map(PENL))
uj=pd.read_pickle(S+'/work/u_jogos.pkl').set_index('match_id'); jm=x.groupby('f_arq').u_match.first()
CAT={k:sorted(x[k].unique()) for k in ('parte','lance','la')}
def cod(d,cols):
    d=d[cols].copy()
    for k in CAT:
        if k in d: d[k]=pd.Categorical(d[k],categories=CAT[k])
    return d
B=['X','Y','parte','lance','big']
vers={'C base: posição, parte, lance, grande chance':(B,False),'+ bloqueada':(B+['bloq'],False),'+ jogada anterior':(B+['la'],False),'+ jogada anterior + bloqueada':(B+['la','bloq'],False),
      '+ jogada anterior + bloqueada, unindo rebotes':(B+['la','bloq'],True),'+ tudo isso + xG da Opta, unindo rebotes':(B+['la','bloq','xg_opta'],True)}
for nome,(cols,une) in vers.items():
    ps=[]
    for a,b in (('La_liga','Serie_A'),('Serie_A','La_liga')):
        m=HistGradientBoostingRegressor(max_iter=600,learning_rate=0.06,max_leaf_nodes=47,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0).fit(cod(x[x.liga==a],cols),x[x.liga==a].xg_understat)
        te=x[x.liga==b].copy(); te['p']=np.clip(m.predict(cod(te,cols)),0.001,0.99); ps.append(te)
    t=pd.concat(ps); t=t.sort_values(['f_arq','mandante','minuto','f_id'])
    if une:
        t['g']=(t.reb==0).groupby([t.f_arq,t.mandante]).cumsum(); s=t.groupby(['f_arq','mandante','g']).p.apply(lambda v:1-np.prod(1-v.values)).groupby(level=[0,1]).sum()
    else: s=t.groupby(['f_arq','mandante']).p.sum()
    j=s.rename('m').reset_index().merge(pen.groupby(['f_arq','mandante']).p.sum().rename('pen').reset_index(),how='left',on=['f_arq','mandante']); j['m']+=j.pen.fillna(0)
    j['u']=[float(uj.loc[jm[a]].xg_h if md==1 else uj.loc[jm[a]].xg_a) for a,md in zip(j.f_arq,j.mandante)]; e=j.m-j.u; a_=e.abs(); es=(t.p-t.xg_understat).abs()
    k=t[(t.big==1)&(t.xg_understat>=.18)&(t.la=='TakeOn')]
    print(f'{nome:46s} finalização {es.mean():.4f} || time-jogo: médio {a_.mean():.3f} | mediano {a_.median():.3f} | 90% até {a_.quantile(.9):.2f} | acima de 0,30: {(a_>.3).mean():.1%} | acima de 0,50: {(a_>.5).mean():.1%} | desvio {e.mean():+.3f} || grande chance após drible: modelo {k.p.mean():.3f} x Understat {k.xg_understat.mean():.3f}')
