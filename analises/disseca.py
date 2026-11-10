import sys, warnings, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
S=sys.argv[1]; pd.set_option('display.width',250)
c=pd.read_pickle(S+'/dados/dados/variaveis.pkl').dropna(subset=['xg_understat']); c=c[c.lance!='Penalty'].copy(); c['xg_opta']=c.xg_opta.fillna(0); c['X']=c.x/105; c['Y']=c.y/68; c['big']=0
for gol,ch in ((0,['f_arq','jogador']),(1,['f_arq','time'])):
    m=c.gol==gol; k=c[m].groupby(ch).gc_marcada.transform('sum'); r=c[m].groupby(ch).xg_opta.rank(method='first',ascending=False); c.loc[m,'big']=(r<=k).astype(int)
CAT={'parte':sorted(c.parte.unique()),'lance':sorted(c.lance.unique())}; cols=['X','Y','parte','lance','big']
def cod(d):
    d=d[cols].copy()
    for k in CAT: d[k]=pd.Categorical(d[k],categories=CAT[k])
    return d
ps=[]
for a,b in (('La_liga','Serie_A'),('Serie_A','La_liga')):
    m=HistGradientBoostingRegressor(max_iter=600,learning_rate=0.06,max_leaf_nodes=47,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0).fit(cod(c[c.liga==a]),c[c.liga==a].xg_understat)
    te=c[c.liga==b].copy(); te['p']=np.clip(m.predict(cod(te)),0.001,0.99); ps.append(te)
x=pd.concat(ps); p=pd.read_pickle(S+'/dados/dados/chutes_pareados.pkl')[['f_arq','f_id','u_id','u_lastAction','u_result','u_situation','u_player','u_minute','u_h_team','u_a_team','u_date']]
x=x.merge(p,on=['f_arq','f_id'],how='left'); x['e']=x.p-x.xg_understat; x['ea']=x.e.abs(); x['alto']=(x.xg_understat>=.18).astype(int)
x.to_pickle(S+'/work/disseca.pkl'); T=x.ea.sum()
print('finalizações',len(x),'| erro absoluto total',round(T,1))
x['grupo']=np.select([(x.big==1)&(x.alto==1),(x.big==1)&(x.alto==0),(x.big==0)&(x.alto==1)],['marcada e Understat alta (concordam)','marcada, Understat baixa','não marcada, Understat alta'],'nenhuma das duas (concordam)')
g=x.groupby('grupo').agg(n=('ea','size'),xG_U=('xg_understat','mean'),modelo=('p','mean'),erro_medio=('ea','mean'),erro_total=('ea','sum')); g['parcela_n']=(g.n/len(x)).map('{:.1%}'.format); g['parcela_do_erro']=(g.erro_total/T).map('{:.1%}'.format)
print(g.round(3).to_string())
d=x[x.grupo.str.contains('baixa|não marcada')]
print('\n== NÃO MARCADA com Understat alta: por última ação / parte / resultado')
n=x[x.grupo=='não marcada, Understat alta']; base=x[x.big==0]
for col in ('u_lastAction','parte','u_result','lance'):
    t=pd.DataFrame({'n':n[col].value_counts(),'taxa_entre_nao_marcadas':(n[col].value_counts()/base[col].value_counts())}).dropna().sort_values('n',ascending=False).head(8); t['taxa_entre_nao_marcadas']=t.taxa_entre_nao_marcadas.map('{:.1%}'.format); print(col,'|',t.to_dict('index'))
print('\n== MARCADA com Understat baixa: por última ação / parte / resultado')
n=x[x.grupo=='marcada, Understat baixa']; base=x[x.big==1]
for col in ('u_lastAction','parte','u_result','lance'):
    t=pd.DataFrame({'n':n[col].value_counts(),'taxa_entre_marcadas':(n[col].value_counts()/base[col].value_counts())}).dropna().sort_values('n',ascending=False).head(8); t['taxa_entre_marcadas']=t.taxa_entre_marcadas.map('{:.1%}'.format); print(col,'|',t.to_dict('index'))
print('\n== dentro das que concordam como grande chance: erro por última ação (valor da chance)')
k=x[x.grupo.str.startswith('marcada e')]; print(k.groupby('u_lastAction').agg(n=('ea','size'),xG_U=('xg_understat','mean'),modelo=('p','mean'),erro=('ea','mean'),vies=('e','mean')).query('n>=150').sort_values('erro',ascending=False).round(3).to_string())
print('xG Opta médio | não marcada com U alta:',round(x[x.grupo=='não marcada, Understat alta'].xg_opta.mean(),3),'| marcada com U baixa:',round(x[x.grupo=='marcada, Understat baixa'].xg_opta.mean(),3),'| concordam alta:',round(k.xg_opta.mean(),3))
