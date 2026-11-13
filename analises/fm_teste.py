# teste FM: primeira etapa com e sem as notas, validação cruzada por jogo nas 3 temporadas-liga
import sys, warnings, pickle, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
S,REPO=sys.argv[1:3]; sys.path.insert(0,REPO+'/scripts'); sys.dont_write_bytecode=True; import modelo_fotmob as M
T=pd.read_pickle(S+'/work/fm_fin.pkl'); J=pd.read_pickle(S+'/work/fm_jogos.pkl')
B=pd.read_csv(REPO+'/data/treino/treino_fotmob_2020-2025.csv.gz',float_precision='round_trip'); B=B[~((B.liga=='La_liga')&B.season.isin([2021,2022,2023,2025]))]
ATT=['att_'+a for a in ['Finishing','First Touch','Heading','Technique','Composure','Agility','Balance','Jumping Reach','Pace']]
DEF=['def_'+a for a in ['Heading','Marking','Tackling','Anticipation','Positioning','Jumping Reach','Strength']]
GK=['gk_'+a for a in ['GK Aerial Reach','GK Command of Area','GK Communication','GK Handling','GK Reflexes','Concentration','Positioning','Agility']]
CONJ={'A base (modelo atual)':[], 'B base + marca de time de elite':['att_elite','def_elite'], 'C B + nota geral (finalizador, goleiro, zagueiros)':['att_elite','def_elite','att_CA','gk_CA','def_CA'],
      'D B + atributos-chave':['att_elite','def_elite']+ATT+GK+DEF}
EXTRA=sorted({c for v in CONJ.values() for c in v})
for c in EXTRA:
    if c not in B: B[c]=0.0 if c.endswith('elite') else np.nan
cats={c:sorted(set(B[c])|set(T[c][T.lance!='Penalty'])) for c in ('parte','lance')}
def cod(d,cols):
    d=d[M.COLS+cols].copy()
    for c,l in cats.items(): d[c]=pd.Categorical(d[c].where(d[c].isin(l),l[0]),categories=l)
    return d
hg=lambda: HistGradientBoostingRegressor(max_iter=600,learning_rate=0.06,max_leaf_nodes=47,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0)
folds=list(GroupKFold(5).split(T,groups=T.mid)); P={}
for nome,cols in CONJ.items():
    p=np.zeros(len(T))
    for a,b in folds:
        tr=T.iloc[a]; tr=tr[tr.xg_understat.notna()]
        m=hg().fit(cod(pd.concat([B,tr],ignore_index=True),cols),pd.concat([B.xg_understat,tr.xg_understat],ignore_index=True))
        p[b]=np.clip(m.predict(cod(T.iloc[b],cols)),0,1)
    P[nome]=np.where(T.lance=='Penalty',T.liga.map(M.PENALTI),p)
pickle.dump(P,open(S+'/work/fm_pred.pkl','wb'))
par=T.xg_understat.notna().values; na=T.att_CA.notna().values&par; nd=T.gk_CA.notna().values&par
print('POR FINALIZAÇÃO, erro médio contra a Understat (fora da amostra)')
print(f'{"":52s} todas ({par.sum()})  com nota finalizador ({na.sum()})  com nota goleiro/zaga ({nd.sum()})')
for nome,p in P.items():
    e=np.abs(p-T.xg_understat.values); print(f'{nome:52s} {e[par].mean():.4f}        {e[na].mean():.4f}                    {e[nd].mean():.4f}')
print('\nPOR TIME-JOGO, primeira etapa, contra o xG publicado pela Understat')
def tot(p):
    t=T.copy(); t['p']=p; s=t.groupby(['mid','lado']).apply(M.total); return J.merge(s.rename('m').reset_index(),on=['mid','lado'],how='left').fillna({'m':0.0})
grupos={'todos':lambda j: j.u>-1,'elite atacando':lambda j: j.time!='','elite defendendo':lambda j: j.adv!='','sem time de elite':lambda j:(j.time=='')&(j.adv=='')}
for nome,p in P.items():
    j=tot(p); e=j.m-j.u; txt=f'{nome:52s}'
    for g,f in grupos.items():
        k=f(j); a=e[k].abs(); txt+=f' | {g} (n={k.sum()}): >0,50 {(a>.5).mean():.1%} [{(a>.5).sum()}], médio {a.mean():.3f}, desvio {e[k].mean():+.3f}'
    print(txt)
j=tot(P['A base (modelo atual)']); e=(j.m-j.u).abs()>.5
print('\nerros graves do modelo atual (primeira etapa) nestas 3 temporadas:',int(e.sum()),'| com time de elite atacando',int((e&(j.time!="")).sum()),'| defendendo',int((e&(j.adv!="")).sum()),'| sem elite',int((e&(j.time=="")&(j.adv=="")).sum()))
