import sys, warnings, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
S=sys.argv[1]; sys.path.insert(0,S+'/novos'); import treina_avalia as t
T=pd.read_pickle(S+'/work/etapa2_treino.pkl'); T['sobra']=T.u-T.m
OPTA=[c for c in ('f_expected_goals','f_expected_goals_open_play','f_expected_goals_set_play','f_expected_goals_non_penalty','f_expected_goals_on_target','a_expected_goals') if c in T]
cols=['m','m_adv','soma','n_fin','n_big','p_big','p_max','n_cab','n_alvo','n_bloq','n_pen','opta_fin','xgot_fin','mandante','gols','gols_adv']+OPTA
cv=np.zeros(len(T))
for a,b in GroupKFold(5).split(T,groups=T.mid): cv[b]=HistGradientBoostingRegressor(max_iter=250,learning_rate=0.04,max_leaf_nodes=6,min_samples_leaf=40,l2_regularization=2.0,early_stopping=False,random_state=0).fit(T.iloc[a][cols],T.iloc[a].sobra).predict(T.iloc[b][cols])
T['novo2']=T.m+cv; N=T[(T.liga=='La_liga')&(T.ano<=2024)][['mid','lado','u','m','novo2','ano']].copy(); N['mid']=N.mid.astype(int)
c=pd.read_pickle(S+'/dados/dados/variaveis.pkl'); tr=c[(c.liga=='Serie_A')&(c.lance!='Penalty')].dropna(subset=['xg_understat']); mod=t.treina(tr,t.V7)
te=c[(c.liga=='La_liga')&(c.season>=2021)].copy(); te['p']=np.where(te.lance=='Penalty',0.7433,np.clip(mod.predict(t.codifica(te,t.V7)),0.001,0.99))
v=te.groupby(['f_arq','mandante']).p.sum().reset_index(); v['mid']=v.f_arq.str.replace('.json.gz','').astype(int); v['lado']=np.where(v.mandante==1,'h','a')
x=N.merge(v[['mid','lado','p']],on=['mid','lado']); print('La Liga 2021/22 a 2024/25, os mesmos time-jogos nos três modelos:',len(x))
for nome,col in (('V7 antigo (treinado na Serie A)','p'),('novo, só a primeira etapa','m'),('novo, com a segunda etapa','novo2')):
    e=x[col]-x.u; a=e.abs(); print(f'{nome:34s} >0,50: {(a>.5).mean():.2%} ({int((a>.5).sum())}) | >0,30: {(a>.3).mean():.1%} | >0,70: {(a>.7).mean():.2%} | médio {a.mean():.3f} | mediano {a.median():.3f} | desvio {e.mean():+.3f}')
print('por temporada, erros > 0,50 (V7 / primeira etapa / segunda etapa):',{int(k):(f'{((g.p-g.u).abs()>.5).mean():.1%}',f'{((g.m-g.u).abs()>.5).mean():.1%}',f'{((g.novo2-g.u).abs()>.5).mean():.1%}') for k,g in x.groupby('ano')})
