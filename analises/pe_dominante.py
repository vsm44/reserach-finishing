import sys, warnings, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
S=sys.argv[1]; pd.set_option('display.width',220)
s=pd.read_pickle(S+'/work/u_shots.pkl'); s=s[(s.result!='OwnGoal')&(s.situation!='Penalty')].copy(); s['lastAction']=s.lastAction.fillna('None').astype(str)
pe=s[s.shotType.isin(['LeftFoot','RightFoot'])]; c=pe.groupby('player_id').shotType.agg(n='size',esq=lambda v:(v=='LeftFoot').mean())
c['dom']=np.where(c.esq>=.7,'LeftFoot',np.where(c.esq<=.3,'RightFoot','ambos')); ok=c[c.n>=30]
print('jogadores com 30+ finalizações com os pés:',len(ok),'| canhotos',int((ok.dom=='LeftFoot').sum()),'| destros',int((ok.dom=='RightFoot').sum()),'| usam os dois',int((ok.dom=='ambos').sum()))
s=s.merge(ok[['dom']],left_on='player_id',right_index=True,how='left')
s['pe']=np.where(~s.shotType.isin(['LeftFoot','RightFoot']),'não é pé',np.where(s.dom.isna(),'jogador sem histórico',np.where(s.dom=='ambos','usa os dois',np.where(s.shotType==s.dom,'pé bom','pé ruim'))))
s['parte']=np.where(s.shotType.isin(['LeftFoot','RightFoot']),'Pe',s.shotType); s['Yc']=(s.Y-.5).abs()
# lado do campo em relação ao pé: chute de pé direito vindo da esquerda do ataque (pé "aberto") etc.
C=['X','Y','parte','situation','lastAction']
for k in ('parte','situation','lastAction'): s[k]=s[k].astype('category')
s['res']=np.nan
for a,b in GroupKFold(4).split(s,groups=s.arq):
    m=HistGradientBoostingRegressor(max_iter=400,learning_rate=0.08,max_leaf_nodes=63,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0).fit(s.iloc[a][C],s.iloc[a].xG)
    s.iloc[b,s.columns.get_loc('res')]=s.iloc[b].xG.values-m.predict(s.iloc[b][C])
g=s.groupby('pe').agg(n=('xG','size'),xG_medio=('xG','mean'),dist_media=('X',lambda v:((1-v)*105).mean()),sobra_media=('res','mean'),gols=('result',lambda v:(v=='Goal').mean())); print(g.round(4).to_string())
f=s[s.pe.isin(['pé bom','pé ruim'])].copy(); f['alto']=f.xG>=.18
print('parcela com xG >= 0,18:',f.groupby('pe').alto.mean().round(4).to_dict())
f['faixa']=pd.cut((1-f.X)*105,[0,6,11,16.5,25,60]); print('sobra média (xG Understat menos o que posição, situação e jogada anterior explicam), por distância:'); print(f.groupby(['faixa','pe'],observed=True).agg(n=('res','size'),xG=('xG','mean'),sobra=('res','mean')).unstack().round(4).to_string())
