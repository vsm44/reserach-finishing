import sys, warnings, json, glob, gzip, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy.optimize import linear_sum_assignment
S,REPO=sys.argv[1:3]; sys.path.insert(0,S+'/work'); import le_ods
pd.set_option('display.width',250); PEN=0.7433
def fot_jogo(d):
    casa=d['general']['homeTeam']['id']; sh=[s for s in (d['content'].get('shotmap') or {}).get('shots') or [] if not s['isOwnGoal']]
    r=pd.DataFrame([dict(lado='h' if s['teamId']==casa else 'a',jog=s['playerId'],minute=s['min'],acr=s.get('minAdded') or 0,fid=s['id'],fx=s['x'],fy=s['y'],X=s['x']/105,Y=s['y']/68,parte=s['shotType'],lance=s['situation'],gol=int(s['eventType']=='Goal'),ev=s['eventType'],bloq=int(bool(s['isBlocked'])),alvo=int(bool(s['isOnTarget'])),xg_opta=s.get('expectedGoals') or 0.0) for s in sh]); r['big']=0
    perd={}
    for pl in (d['content'].get('playerStats') or {}).values():
        bc=pm=0
        for grp in pl.get('stats') or []:
            for x in (grp.get('stats') or {}).values():
                if x.get('key')=='big_chance_missed_title': bc=(x.get('stat') or {}).get('value') or 0
                elif x.get('key')=='missed_penalty': pm=(x.get('stat') or {}).get('value') or 0
        perd[pl['id']]=max(bc-pm,0)
    tot={s['key']:s['stats'] for grp in (((d['content'].get('stats') or {}).get('Periods') or {}).get('All') or {}).get('stats',[]) for s in grp['stats'] if s.get('key') in ('big_chance','big_chance_missed_title','expected_goals') and len(s['stats'])==2 and s['stats'][0] is not None}
    np_=r[r.lance!='Penalty']
    for jog,kk in perd.items(): r.loc[np_[(np_.jog==jog)&(np_.gol==0)].sort_values('xg_opta',ascending=False).index[:int(kk)],'big']=1
    for i,lado in enumerate(('h','a')):
        conv=(tot.get('big_chance',[0,0])[i] or 0)-(tot.get('big_chance_missed_title',[0,0])[i] or 0)-int(((r.lado==lado)&(r.lance=='Penalty')&(r.gol==1)).sum())
        r.loc[np_[(np_.lado==lado)&(np_.gol==1)].sort_values('xg_opta',ascending=False).index[:max(int(conv),0)],'big']=1
    return r,[float(x) for x in tot['expected_goals']] if 'expected_goals' in tot else [np.nan,np.nan]
# ---- 2025/26: pareia FotMob x Understat (La Liga)
uj=pd.read_pickle(S+'/work/u_jogos.pkl'); uj=uj[(uj.liga=='La_liga')&(uj.ano==2025)&uj.isResult].copy(); uj['d']=uj.data.str[:10]; uj['gh']=uj.gh.astype(int); uj['ga']=uj.ga.astype(int)
us=pd.read_pickle(S+'/work/u_shots.pkl'); us=us[(us.liga=='La_liga')&(us.ano==2025)&(us.result!='OwnGoal')]
fl=[]
for f in glob.glob(S+'/fotmob/2025/[0-9]*.json.gz'):
    d=json.load(gzip.open(f)); h=d['header']['teams']; fl.append((d['general']['matchTimeUTCDate'][:10],h[0].get('score'),h[1].get('score'),d['general']['homeTeam']['id'],d['general']['awayTeam']['id'],d))
votos={}
for j in uj.itertuples():
    c=[x for x in fl if x[0]==j.d and x[1]==j.gh and x[2]==j.ga]
    if len(c)==1:
        for a,b in ((j.h,c[0][3]),(j.a,c[0][4])): votos.setdefault(a,{}).setdefault(b,0); votos[a][b]+=1
mapa={k:max(v,key=v.get) for k,v in votos.items()}; novo=[]; nj=nu=npar=0
for j in uj.itertuples():
    c=[x for x in fl if x[3]==mapa.get(j.h) and x[4]==mapa.get(j.a) and abs((pd.Timestamp(x[0])-pd.Timestamp(j.d)).days)<=1 and x[1]==j.gh and x[2]==j.ga]
    if len(c)!=1: continue
    nj+=1; f,_=fot_jogo(c[0][5]); u=us[us.arq==j.match_id]
    for lado in ('h','a'):
        a=u[u.lado==lado].reset_index(drop=True); b=f[f.lado==lado].reset_index(drop=True); nu+=len(a)
        if not len(a) or not len(b): continue
        dm=np.abs((a.minute.values+1)[:,None]-(b.minute+b.acr).values[None,:]); di=np.hypot(a.X.values[:,None]*105-b.fx.values[None,:],a.Y.values[:,None]*68-b.fy.values[None,:]); cst=dm+di/4; cst[(dm>3)|(di>8)]=1e6
        li,co=linear_sum_assignment(cst)
        for i,k in zip(li,co):
            if cst[i,k]<1e6: npar+=1; novo.append({**b.loc[k].to_dict(),'xg_understat':a.xG[i],'u_sit':a.situation[i],'season':2025,'liga':'La_liga'})
n25=pd.DataFrame(novo); n25=n25[(n25.lance!='Penalty')&(n25.u_sit!='Penalty')]
print(f'2025/26: jogos casados {nj} de {len(uj)} | finalizações Understat {nu} | pareadas {npar} ({npar/nu:.1%}) | para treino {len(n25)}')
# ---- legado
v=pd.read_pickle(S+'/dados/dados/variaveis.pkl').dropna(subset=['xg_understat']); v=v[v.lance!='Penalty'].copy(); v['xg_opta']=v.xg_opta.fillna(0); v['big']=0
for gol,ch in ((0,['f_arq','jogador']),(1,['f_arq','time'])):
    m=v.gol==gol; k=v[m].groupby(ch).gc_marcada.transform('sum'); r=v[m].groupby(ch).xg_opta.rank(method='first',ascending=False); v.loc[m,'big']=(r<=k).astype(int)
v['X']=v.x/105; v['Y']=v.y/68
COLS=['X','Y','parte','lance','big']; base=v[COLS+['xg_understat','season','liga']]; tudo=pd.concat([base,n25[COLS+['xg_understat','season','liga']]],ignore_index=True)
CAT={'parte':sorted(tudo.parte.unique()),'lance':sorted(tudo.lance.unique())}
def cod(d):
    d=d[COLS].copy()
    for c in CAT: d[c]=pd.Categorical(d[c].where(d[c].isin(CAT[c]),CAT[c][0]),categories=CAT[c])
    return d
gbm=lambda: HistGradientBoostingRegressor(max_iter=600,learning_rate=0.06,max_leaf_nodes=47,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0)
print('xG Understat médio por finalização no treino, por temporada:',tudo.groupby('season').xg_understat.mean().round(4).to_dict(),'| parcela com grande chance:',tudo.groupby('season').big.mean().round(3).to_dict())
treinos={'A legado 2020-2024 (como antes)':tudo[tudo.season<=2024],'B legado + 2025/26':tudo,'C só 2023 a 2025':tudo[tudo.season>=2023],'D só La Liga, 2020 a 2025':tudo[tudo.liga=='La_liga'],'E só 2025/26':tudo[tudo.season==2025]}
# ---- teste 2026/27
L=le_ods.le(REPO+'/data/understat/La_Liga_atual.ods')['Planilha1']; g=pd.DataFrame(L[1:],columns=L[0])
for c in ('home_xg','away_xg'): g[c]=g[c].astype(float)
jg=[]
for f in glob.glob(S+'/fot2026/[0-9]*.json.gz'):
    d=json.load(gzip.open(f)); h=d['header']['teams']; jg.append((d['general']['matchTimeUTCDate'][:10],h[0]['name'],h[1]['name'],h[0].get('score'),h[1].get('score'),d))
teste=[]
for r in g.itertuples():
    c=[j for j in jg if abs((pd.Timestamp(j[0])-pd.Timestamp(r.date)).days)<=1 and j[3]==int(r.home_goals) and j[4]==int(r.away_goals)]
    if len(c)>1:
        k=lambda a,b: len(set(a.lower().replace('real ','').split())&set(b.lower().replace('real ','').split()))>0 or a[:4].lower()==b[:4].lower()
        c2=[j for j in c if k(j[1],r.home_team) or k(j[2],r.away_team)]; c=c2 if len(c2)==1 else c
    assert len(c)==1; s,_=fot_jogo(c[0][5]); teste.append((r,c[0],s))
for nome,tr in treinos.items():
    m=gbm().fit(cod(tr),tr.xg_understat); e=[]
    for r,j,s in teste:
        p=np.where(s.lance=='Penalty',PEN,np.clip(m.predict(cod(s)),0,1))
        for lado,u in (('h',r.home_xg),('a',r.away_xg)): e.append(p[(s.lado==lado).values].sum()-u)
    e=pd.Series(e); a=e.abs(); print(f'{nome:34s} treino {len(tr):6d} | erro médio {a.mean():.3f} | mediano {a.median():.3f} | 90% até {a.quantile(.9):.2f} | acima de 0,30: {(a>.3).mean():.1%} | acima de 0,50: {(a>.5).mean():.1%} | desvio médio {e.mean():+.3f}')
n25.to_pickle(S+'/work/treino_2025.pkl')
# ---- conferência: modelo A (treino até 2024) aplicado em 2025/26 inteira, contra o xG publicado no bruto
mA=gbm().fit(cod(treinos['A legado 2020-2024 (como antes)']),treinos['A legado 2020-2024 (como antes)'].xg_understat); e=[]; por_mes=[]
for j in uj.itertuples():
    c=[x for x in fl if x[3]==mapa.get(j.h) and x[4]==mapa.get(j.a) and abs((pd.Timestamp(x[0])-pd.Timestamp(j.d)).days)<=1 and x[1]==j.gh and x[2]==j.ga]
    if len(c)!=1: continue
    s,_=fot_jogo(c[0][5]); p=np.where(s.lance=='Penalty',PEN,np.clip(mA.predict(cod(s)),0,1))
    for lado,u in (('h',j.xg_h),('a',j.xg_a)): e.append(p[(s.lado==lado).values].sum()-float(u)); por_mes.append(j.d[:7])
e=pd.Series(e); a=e.abs(); print(f'CONFERÊNCIA modelo A em 2025/26 (760 time-jogos, bruto): erro médio {a.mean():.3f} | mediano {a.median():.3f} | acima de 0,30: {(a>.3).mean():.1%} | acima de 0,50: {(a>.5).mean():.1%} | desvio {e.mean():+.3f}')
print('por mês:',a.groupby(por_mes).mean().round(3).to_dict())
# ---- o jogo mais divergente de 2026/27, finalização a finalização
for r,j,s in teste:
    if 'Villarreal' in j[1] and 'Coru' in j[2]:
        s=s.copy(); s['modelo']=np.where(s.lance=='Penalty',PEN,np.clip(mA.predict(cod(s)),0,1)); print('planilha:',r.date,r.home_team,r.away_team,r.home_xg,r.away_xg,r.home_goals,r.away_goals,'| FotMob:',j[0],j[1],j[3],j[4],j[2])
        print(s.sort_values(['lado','minute'])[['lado','minute','parte','lance','ev','gol','big','xg_opta','modelo']].round(3).to_string(index=False)); print(s.groupby('lado').agg(n=('modelo','size'),opta=('xg_opta','sum'),modelo=('modelo','sum'),grandes=('big','sum'),gols=('gol','sum')).round(2).to_string())
