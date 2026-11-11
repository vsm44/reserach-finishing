import sys, warnings, json, glob, gzip, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
S,REPO=sys.argv[1:3]; sys.path.insert(0,S+'/work'); import le_ods
pd.set_option('display.width',250); PEN=0.7433
# ---- treino: legado inteiro (La Liga e Serie A, 2020-2024), marca escolhida pelo xG da Opta, posição da FotMob
v=pd.read_pickle(S+'/dados/dados/variaveis.pkl').dropna(subset=['xg_understat']); v=v[v.lance!='Penalty'].copy(); v['xg_opta']=v.xg_opta.fillna(0); v['big']=0
for gol,ch in ((0,['f_arq','jogador']),(1,['f_arq','time'])):
    m=v.gol==gol; k=v[m].groupby(ch).gc_marcada.transform('sum'); r=v[m].groupby(ch).xg_opta.rank(method='first',ascending=False); v.loc[m,'big']=(r<=k).astype(int)
v['X']=v.x/105; v['Y']=v.y/68; CAT={'parte':sorted(v.parte.unique()),'lance':sorted(v.lance.unique())}
def cod(d,cols):
    d=d[cols].copy()
    for c in CAT: d[c]=pd.Categorical(d[c].where(d[c].isin(CAT[c]),CAT[c][0]),categories=CAT[c])
    return d
F0=['X','Y','parte','lance','big']; F1=F0+['xg_opta']; SEM=['X','Y','parte','lance']
gbm=lambda: HistGradientBoostingRegressor(max_iter=600,learning_rate=0.06,max_leaf_nodes=47,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0)
M={n:gbm().fit(cod(v,c),v.xg_understat) for n,c in (('F0',F0),('F1',F1),('SEM',SEM))}
def fot_jogo(d):
    casa=d['general']['homeTeam']['id']; sh=[s for s in (d['content'].get('shotmap') or {}).get('shots') or [] if not s['isOwnGoal']]
    r=pd.DataFrame([dict(lado='h' if s['teamId']==casa else 'a',jog=s['playerId'],nome=s.get('playerName'),minute=s['min'],acr=s.get('minAdded') or 0,fid=s['id'],X=s['x']/105,Y=s['y']/68,parte=s['shotType'],lance=s['situation'],gol=int(s['eventType']=='Goal'),ev=s['eventType'],bloq=int(bool(s['isBlocked'])),alvo=int(bool(s['isOnTarget'])),xg_opta=s.get('expectedGoals') or 0.0) for s in sh]); r['big']=0
    perd={}
    for pl in (d['content'].get('playerStats') or {}).values():
        bc=pm=0
        for grp in pl.get('stats') or []:
            for x in (grp.get('stats') or {}).values():
                if x.get('key')=='big_chance_missed_title': bc=(x.get('stat') or {}).get('value') or 0
                elif x.get('key')=='missed_penalty': pm=(x.get('stat') or {}).get('value') or 0
        perd[pl['id']]=max(bc-pm,0)
    tot={s['key']:s['stats'] for grp in d['content']['stats']['Periods']['All']['stats'] for s in grp['stats'] if s.get('key') in ('big_chance','big_chance_missed_title','expected_goals') and len(s['stats'])==2 and s['stats'][0] is not None}
    np_=r[r.lance!='Penalty']
    for jog,kk in perd.items(): r.loc[np_[(np_.jog==jog)&(np_.gol==0)].sort_values('xg_opta',ascending=False).index[:int(kk)],'big']=1
    for i,lado in enumerate(('h','a')):
        conv=(tot.get('big_chance',[0,0])[i] or 0)-(tot.get('big_chance_missed_title',[0,0])[i] or 0)-int(((r.lado==lado)&(r.lance=='Penalty')&(r.gol==1)).sum())
        r.loc[np_[(np_.lado==lado)&(np_.gol==1)].sort_values('xg_opta',ascending=False).index[:max(int(conv),0)],'big']=1
    return r,[float(x) for x in tot['expected_goals']] if 'expected_goals' in tot else [np.nan,np.nan]
def total(g,col,une):
    g=g.sort_values(['minute','acr','fid'])
    if not une: return g[col].sum()
    ant_ok=((g.alvo.shift()==1)|(g.bloq.shift()==1)|(g.ev.shift()=='Post'))&(g.gol.shift()==0); reb=((g.minute+g.acr)==(g.minute+g.acr).shift())&ant_ok
    return g.groupby((~reb).cumsum())[col].apply(lambda x:1-np.prod(1-x.values)).sum()
# ---- gabarito: planilha da Understat
L=le_ods.le(REPO+'/data/understat/La_Liga_atual.ods')['Planilha1']; g=pd.DataFrame(L[1:],columns=L[0])
for c in ('home_xg','away_xg'): g[c]=g[c].astype(float)
g['hg']=g.home_goals.astype(int); g['ag']=g.away_goals.astype(int)
jogos=[]
for f in glob.glob(S+'/fot2026/[0-9]*.json.gz'):
    d=json.load(gzip.open(f)); h=d['header']['teams']; jogos.append((d['general']['matchTimeUTCDate'][:10],h[0]['name'],h[1]['name'],h[0].get('score'),h[1].get('score'),d))
lin=[]; sem=[]; fin=[]
for r in g.itertuples():
    c=[j for j in jogos if abs((pd.Timestamp(j[0])-pd.Timestamp(r.date)).days)<=1 and j[3]==r.hg and j[4]==r.ag]
    if len(c)>1:
        k=lambda a,b: len(set(a.lower().replace('real ','').split())&set(b.lower().replace('real ','').split()))>0 or a[:4].lower()==b[:4].lower()
        c2=[j for j in c if k(j[1],r.home_team) or k(j[2],r.away_team)]; c=c2 if len(c2)==1 else c
    if len(c)!=1: sem.append((r.date,r.home_team,r.away_team,len(c))); continue
    j=c[0]; s,opta=fot_jogo(j[5])
    for n,cols in (('F0',F0),('F1',F1),('SEM',SEM)): s[n]=np.where(s.lance=='Penalty',PEN,np.clip(M[n].predict(cod(s,cols)),0,1))
    for i,lado in enumerate(('h','a')):
        t=s[s.lado==lado]; lin.append(dict(data=r.date,jogo=f'{j[1]} x {j[2]}',time=j[1] if lado=='h' else j[2],understat=r.home_xg if lado=='h' else r.away_xg,soma=total(t,'F0',False),unido=total(t,'F0',True),com_opta=total(t,'F1',True),sem_gc=total(t,'SEM',False),opta=opta[i],n_big=int(t.big.sum()),n=len(t)))
    s['jogo']=f'{j[1]} x {j[2]}'; fin.append(s)
r=pd.DataFrame(lin); print('jogos na planilha',len(g),'| casados',len(r)//2,'| não casados',sem)
print('time-jogos',len(r),'| xG Understat médio',round(r.understat.mean(),3),'| período',r.data.min(),'a',r.data.max())
for nome,col in (('modelo, soma simples','soma'),('modelo, unindo rebotes do mesmo minuto','unido'),('modelo + xG da Opta, unindo rebotes','com_opta'),('(ref.) sem grande chance','sem_gc'),('(ref.) xG da Opta publicado, direto','opta')):
    e=r[col]-r.understat; a=e.abs(); print(f'{nome:40s} erro médio {a.mean():.3f} | mediano {a.median():.3f} | 90% até {a.quantile(.9):.2f} | maior {a.max():.2f} | acima de 0,30: {(a>.3).mean():.1%} | acima de 0,50: {(a>.5).mean():.1%} | desvio médio {e.mean():+.3f}')
r['erro']=r.unido-r.understat
print(r.reindex(r.erro.abs().sort_values(ascending=False).index)[['data','jogo','time','understat','unido','opta','erro','n','n_big']].head(12).round(2).to_string(index=False))
r.to_pickle(S+'/work/teste2026.pkl'); pd.concat(fin).to_pickle(S+'/work/teste2026_fin.pkl')
