import sys, warnings, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
S=sys.argv[1]; sys.path.insert(0,S+'/novos'); import treina_avalia as t
PENL={'La_liga':0.7433,'Serie_A':0.7613}
c=pd.read_pickle(S+'/dados/dados/variaveis.pkl'); c['xg_opta']=c.xg_opta.fillna(0); c['X']=c.x/105; c['Y']=c.y/68
np_=c.lance!='Penalty'; c['big']=0
for gol,chave in ((0,['f_arq','jogador']),(1,['f_arq','time'])):
    m=np_&(c.gol==gol); k=c[m].groupby(chave).gc_marcada.transform('sum'); r=c[m].groupby(chave).xg_opta.rank(method='first',ascending=False); c.loc[m,'big']=(r<=k).astype(int)
print('finalizações',len(c),'| marcadas por geometria',int(c.gc_marcada.sum()),'| pela Opta',int(c.big.sum()),'| iguais',int((c.big*c.gc_marcada).sum()))
uj=pd.read_pickle(S+'/work/u_jogos.pkl').set_index('match_id')
CAT={'parte':sorted(c.parte.unique()),'lance':sorted(c.lance.unique())}
def cod(d,cols):
    d=d[cols].copy()
    for k in ('parte','lance'):
        if k in d: d[k]=pd.Categorical(d[k],categories=CAT[k])
    return d
gbm=lambda: HistGradientBoostingRegressor(max_iter=600,learning_rate=0.06,max_leaf_nodes=47,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0)
B=['X','Y','parte','lance']
vers={'A sem grande chance':B,'B grande chance por geometria (como o legado)':B+['gc_marcada'],'C grande chance escolhida pela Opta':B+['big'],'D = C + xG da Opta':B+['big','xg_opta'],'E = D + xGOT':B+['big','xg_opta','xgot'],
      'F = C + no alvo, bloqueada':B+['big','no_alvo','bloqueado'],'G = D + estatísticas do jogo (legado)':B+['big','xg_opta','jg_grandes','jg_grandes_perdidas','jg_chutes_area','jga_grandes','jga_chutes_area'],'V7 antigo completo':t.V7}
jm=c.dropna(subset=['u_match']).groupby('f_arq').agg(u_match=('u_match','first')); 
def pub(row): 
    j=uj.loc[row.u_match]; return float(j.xg_h if row.mandante==1 else j.xg_a)
res={}
for nome,cols in vers.items():
    partes=[]
    for a,b in (('La_liga','Serie_A'),('Serie_A','La_liga')):
        tr=c[(c.liga==a)&np_].dropna(subset=['xg_understat']); te=c[c.liga==b].copy()
        m=gbm().fit(cod(tr,cols) if nome[0]!='V' else t.codifica(tr,cols),tr.xg_understat)
        te['p']=np.where(te.lance=='Penalty',PENL[b],np.clip(m.predict(cod(te,cols) if nome[0]!='V' else t.codifica(te,cols)),0.001,0.99)); partes.append(te)
    x=pd.concat(partes); j=x.groupby(['f_arq','mandante']).agg(m=('p','sum')).reset_index().merge(jm,on='f_arq'); j['u']=j.apply(pub,axis=1); e=j.m-j.u; a_=e.abs()
    sh=x[np_.reindex(x.index)].dropna(subset=['xg_understat']); es=(sh.p-sh.xg_understat).abs()
    print(f'{nome:46s} finalização {es.mean():.4f} || time-jogo ({len(j)}): médio {a_.mean():.3f} | mediano {a_.median():.3f} | 90% até {a_.quantile(.9):.2f} | acima de 0,30: {(a_>.3).mean():.1%} | acima de 0,50: {(a_>.5).mean():.1%} | desvio médio {e.mean():+.3f}')
    res[nome]=j.assign(e=e)
j=res['D = C + xG da Opta']; j.to_pickle(S+'/work/legado_D.pkl')
