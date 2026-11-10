import sys, pandas as pd, numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
W=sys.argv[1]; pd.set_option('display.width',250); pd.set_option('display.max_rows',100)
s=pd.read_pickle(W+'/u_shots.pkl'); s=s[(s.result!='OwnGoal')&(s.situation!='Penalty')].copy()
s['lastAction']=s.lastAction.fillna('None'); print('finalizações (sem pênalti e gol contra):',len(s))
# 1) finalizações com campos idênticos: o xG é sempre o mesmo?
for nome,ch in (('X,Y,parte,situação',['X','Y','shotType','situation']),('+ última ação',['X','Y','shotType','situation','lastAction']),('+ liga',['X','Y','shotType','situation','lastAction','liga']),('+ liga e temporada',['X','Y','shotType','situation','lastAction','liga','ano'])):
    g=s.groupby(ch).xG.agg(['size','min','max']); g=g[g['size']>=2]; r=g['max']-g['min']
    print(f'idênticas em [{nome}]: grupos {len(g)} ({int(g["size"].sum())} finalizações) | xG igual (dif<=0,001) em {(r<=0.001).mean():.1%} dos grupos | dif mediana {r.median():.4f} | p90 {r.quantile(.9):.4f}')
# 2) quanto os campos explicam (treino em 80% dos jogos, teste nos outros 20%)
rng=np.random.default_rng(0); jogos=s.arq.unique(); te_j=set(rng.choice(jogos,len(jogos)//5,replace=False)); te=s.arq.isin(te_j)
for c in ('shotType','situation','lastAction','liga','h_a'): s[c]=s[c].astype('category')
conj={'A posição':['X','Y'],'B + parte e situação':['X','Y','shotType','situation'],'C + última ação':['X','Y','shotType','situation','lastAction'],
      'D + liga e temporada':['X','Y','shotType','situation','lastAction','liga','ano'],'E + mando e minuto':['X','Y','shotType','situation','lastAction','liga','ano','h_a','minute']}
res={}
for nome,cols in conj.items():
    m=HistGradientBoostingRegressor(max_iter=500,learning_rate=0.08,max_leaf_nodes=63,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0).fit(s.loc[~te,cols],s.loc[~te,'xG'])
    p=np.clip(m.predict(s.loc[te,cols]),0,1); e=(p-s.loc[te,'xG']).abs(); res[nome]=p
    print(f'{nome:24s} erro abs médio {e.mean():.4f} | mediano {e.median():.4f} | até 0,01: {(e<=.01).mean():.1%} | até 0,02: {(e<=.02).mean():.1%} | até 0,05: {(e<=.05).mean():.1%} | acima de 0,10: {(e>.1).mean():.1%}')
t=s[te].copy(); t['p']=res['D + liga e temporada']; t['e']=(t.p-t.xG); t['ea']=t.e.abs()
print('xG médio no teste:',round(t.xG.mean(),4),'| n teste',len(t))
def tab(col,minn=300):
    g=t.groupby(col,observed=True).agg(n=('xG','size'),xG_medio=('xG','mean'),erro_abs=('ea','mean'),vies=('e','mean'),acima_010=('ea',lambda v:(v>.1).mean())); return g[g.n>=minn].round(4)
print('--- por última ação (conjunto D)'); print(tab('lastAction').sort_values('erro_abs',ascending=False).to_string())
print('--- por parte do corpo'); print(tab('shotType').to_string())
print('--- por situação'); print(tab('situation').to_string())
print('--- por resultado'); print(tab('result').to_string())
print('--- por temporada'); print(tab('ano').to_string())
print('--- por liga'); print(tab('liga').to_string())
t['faixa']=pd.cut(t.xG,[0,.05,.1,.2,.4,1]); print('--- por faixa de xG'); print(tab('faixa').to_string())
t[['id','p']].to_pickle(W+'/h1_pred.pkl')
