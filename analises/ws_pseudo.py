import sys, warnings, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
S=sys.argv[1]; t=pd.read_pickle(S+'/work/ws_lote.pkl'); t['lastAction']=t.lastAction.fillna('None').astype(str)
s=pd.read_pickle(S+'/work/u_shots.pkl'); s=s[(s.result!='OwnGoal')&(s.situation!='Penalty')].copy(); s['lastAction']=s.lastAction.fillna('None').astype(str)
C=['X','Y','shotType','situation','lastAction']; cats={c:sorted(s[c].unique()) for c in C[2:]}
def cod(d,extra=()):
    d=d[C+list(extra)].copy()
    for c in C[2:]: d[c]=pd.Categorical(d[c].where(d[c].isin(cats[c]),'None'),categories=cats[c])
    return d
tr=s[~s.arq.isin(t.arq.unique())].copy(); pen=t.situation=='Penalty'; p=t[~pen].reset_index(drop=True); p['big']=p.big.astype(int)
gbm=lambda: HistGradientBoostingRegressor(max_iter=500,learning_rate=0.08,max_leaf_nodes=63,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0)
def med(nome,pr):
    e=(pr-p.xG).abs(); x=pd.concat([p.assign(pr=pr)[['arq','lado','xG','pr']],t[pen].assign(pr=t[pen].xG)[['arq','lado','xG','pr']]]); j=x.groupby(['arq','lado']).agg(u=('xG','sum'),m=('pr','sum')); ej=(j.m-j.u).abs()
    print(f'{nome:46s} finalização: erro médio {e.mean():.4f} | acima de 0,10: {(e>.1).mean():.1%} || time-jogo (36): médio {ej.mean():.3f} | mediano {ej.median():.3f} | maior {ej.max():.2f} | acima de 0,30: {(ej>.3).sum()} | acima de 0,50: {(ej>.5).sum()}')
    return pr,ej
b,_=med('base: campos da Understat',np.clip(gbm().fit(cod(tr),tr.xG).predict(cod(p)),0,1))
print('parcela do bruto com xG >=: 0,15',f'{(tr.xG>=.15).mean():.1%}','| 0,20',f'{(tr.xG>=.2).mean():.1%}','| 0,25',f'{(tr.xG>=.25).mean():.1%}','| parcela com a marca nos 18 jogos',f'{p.big.mean():.1%}')
for lim in (.15,.18,.2,.25):
    tr['big']=(tr.xG>=lim).astype(int); m=gbm().fit(cod(tr,['big']),tr.xG); pr,ej=med(f'marca aprendida no bruto com corte em {lim}',np.clip(m.predict(cod(p,['big'])),0,1))
    if lim==.18: p['pr']=pr
p['e']=p.pr-p.xG
print('maiores erros (corte 0,18):'); print(p.reindex(p.e.abs().sort_values(ascending=False).index)[['arq','minute','player','result','situation','shotType','lastAction','big','xG','pr','e']].head(12).round(3).to_string(index=False))
print('erro abs médio: com a marca',round(p[p.big==1].e.abs().mean(),3),'| sem a marca',round(p[p.big==0].e.abs().mean(),4))
