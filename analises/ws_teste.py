import sys, numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
S=sys.argv[1]; t=pd.read_pickle(S+'/work/ws_lote.pkl'); t['lastAction']=t.lastAction.fillna('None').astype(str)
s=pd.read_pickle(S+'/work/u_shots.pkl'); s=s[(s.result!='OwnGoal')&(s.situation!='Penalty')].copy(); s['lastAction']=s.lastAction.fillna('None').astype(str)
C=['X','Y','shotType','situation','lastAction']; cats={c:sorted(s[c].unique()) for c in C[2:]}
def cod(d):
    d=d[C].copy()
    for c in C[2:]: d[c]=pd.Categorical(d[c],categories=cats[c])
    return d
tr=s[~s.arq.isin(t.arq.unique())]
mb=HistGradientBoostingRegressor(max_iter=500,learning_rate=0.08,max_leaf_nodes=63,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0).fit(cod(tr),tr.xG)
pen=t.situation=='Penalty'; t['base']=np.where(pen,t.xG,np.clip(mb.predict(cod(t)),0,1))
p=t[~pen].reset_index(drop=True)
for c in ('big','fast','one','first','volley','indiv','rel_bcc','rel_inten'): p[c]=p[c].astype(int)
p['dist']=np.hypot((1-p.X)*105,(p.Y-.5)*68); p['cab']=(p.shotType=='Head').astype(int)
def cv(cols,leaf=8):
    out=np.zeros(len(p))
    for a,b in GroupKFold(6).split(p,groups=p.arq):
        m=HistGradientBoostingRegressor(max_iter=200,learning_rate=0.05,max_leaf_nodes=6,min_samples_leaf=leaf,early_stopping=False,random_state=0).fit(p.loc[a,cols],p.loc[a,'xG']-p.loc[a,'base']); out[b]=m.predict(p.loc[b,cols])
    return np.clip(p.base+out,0,1)
def med(nome,pr):
    e=(pr-p.xG).abs(); x=pd.concat([p.assign(pr=pr)[['arq','lado','xG','pr']],t[pen].assign(pr=t[pen].xG)[['arq','lado','xG','pr']]]); j=x.groupby(['arq','lado']).agg(u=('xG','sum'),m=('pr','sum')); ej=(j.m-j.u).abs()
    print(f'{nome:52s} finalização: erro médio {e.mean():.4f} | acima de 0,10: {(e>.1).mean():.1%} || time-jogo ({len(j)}): médio {ej.mean():.3f} | mediano {ej.median():.3f} | maior {ej.max():.2f} | acima de 0,30: {(ej>.3).sum()} | acima de 0,50: {(ej>.5).sum()}')
print('finalizações sem pênalti:',len(p),'| jogos',p.arq.nunique())
med('0 base: campos da Understat',p.base.values)
med('1 base + grande chance',cv(['base','big']))
med('2 base + grande chance + posição e cabeça',cv(['base','big','dist','X','Y','cab']))
med('3 = 2 + contra-ataque, de primeira, voleio, 1x1',cv(['base','big','dist','X','Y','cab','fast','first','volley','one','indiv','rel_bcc','rel_inten']))
med('4 base + demais marcas, SEM grande chance',cv(['base','dist','X','Y','cab','fast','first','volley','one','indiv','rel_inten']))
