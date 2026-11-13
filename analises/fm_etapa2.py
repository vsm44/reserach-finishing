# quanto do desvio nos times de elite sobra depois da segunda etapa (validação cruzada por jogo)
import sys, warnings, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
S,REPO=sys.argv[1:3]; sys.path.insert(0,REPO+'/scripts'); sys.dont_write_bytecode=True; import modelo_fotmob as M
T=pd.read_pickle(S+'/work/etapa2_treino.pkl').reset_index(drop=True); J=pd.read_pickle(S+'/work/fm_jogos.pkl')
T=T.merge(J[['mid','lado','time','adv']],on=['mid','lado'],how='left')
T['att_elite']=np.where(T.time.isna(),np.nan,(T.time.fillna('')!='').astype(float)); T['def_elite']=np.where(T.adv.isna(),np.nan,(T.adv.fillna('')!='').astype(float))
h2=lambda: HistGradientBoostingRegressor(max_iter=250,learning_rate=0.04,max_leaf_nodes=6,min_samples_leaf=40,l2_regularization=2.0,early_stopping=False,random_state=0)
def cv(cols):
    p=np.zeros(len(T))
    for a,b in GroupKFold(5).split(T,groups=T.mid): p[b]=h2().fit(T.iloc[a][cols],(T.u-T.m).iloc[a]).predict(T.iloc[b][cols])
    return np.clip(T.m+p,0,None)
V={'primeira etapa':T.m.values,'com a segunda etapa (modelo de uso)':cv(M.COLS2),'segunda etapa + marca de time de elite':cv(M.COLS2+['att_elite','def_elite'])}
k=T.time.notna(); print('time-jogos nas 3 temporadas do teste:',int(k.sum()))
G={'elite atacando':k&(T.time!=''),'elite defendendo':k&(T.adv!=''),'sem elite':k&(T.time=='')&(T.adv=='')}
for nome,v in V.items():
    e=pd.Series(v-T.u.values); txt=f'{nome:40s}'
    for g,f in G.items(): a=e[f].abs(); txt+=f' | {g} (n={int(f.sum())}): desvio {e[f].mean():+.3f}, >0,50 {int((a>.5).sum())} ({(a>.5).mean():.1%}), médio {a.mean():.3f}'
    print(txt)
e=pd.Series(V['com a segunda etapa (modelo de uso)']-T.u.values); f=G['elite atacando']
print('elite atacando, com a segunda etapa, por time:',{t:f'{e[f&(T.time==t)].mean():+.3f} (n={int((f&(T.time==t)).sum())}, graves {int((e[f&(T.time==t)].abs()>.5).sum())})' for t in sorted(T.time[f].unique())})
print('direção dos erros graves (elite atacando, segunda etapa): modelo abaixo',int((e[f]<-.5).sum()),'| modelo acima',int((e[f]>.5).sum()))
