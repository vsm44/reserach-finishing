import sys, warnings, json, glob, gzip, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy.optimize import linear_sum_assignment
S=sys.argv[1]; pd.set_option('display.width',250); PEN=0.7433
uj=pd.read_pickle(S+'/work/u_jogos.pkl'); uj=uj[uj.isResult&uj.gh.notna()].copy()
gbm=lambda: HistGradientBoostingRegressor(max_iter=600,learning_rate=0.06,max_leaf_nodes=47,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0)
# ===== treino nível FotMob: legado (variaveis.pkl), marca escolhida pelo xG da Opta, posição da FotMob
v=pd.read_pickle(S+'/dados/dados/variaveis.pkl').dropna(subset=['xg_understat']); v=v[v.lance!='Penalty'].copy(); v['xg_opta']=v.xg_opta.fillna(0)
v['big']=0
k=v[v.gol==0].groupby(['f_arq','jogador']).gc_marcada.transform('sum'); r=v[v.gol==0].groupby(['f_arq','jogador']).xg_opta.rank(method='first',ascending=False); v.loc[v.gol==0,'big']=(r<=k).astype(int)
k=v[v.gol==1].groupby(['f_arq','time']).gc_marcada.transform('sum'); r=v[v.gol==1].groupby(['f_arq','time']).xg_opta.rank(method='first',ascending=False); v.loc[v.gol==1,'big']=(r<=k).astype(int)
v['X']=v.x/105; v['Y']=v.y/68
CATF={'parte':sorted(v.parte.unique()),'lance':sorted(v.lance.unique())}
def codF(d,cols):
    d=d[cols].copy()
    for c in ('parte','lance'): d[c]=pd.Categorical(d[c].where(d[c].isin(CATF[c]),CATF[c][0]),categories=CATF[c])
    return d
F0=['X','Y','parte','lance','big']; F1=F0+['xg_opta']; F2=F1+['xgot']
mF={n:gbm().fit(codF(v,c),v.xg_understat) for n,c in (('F0',F0),('F1',F1),('F2',F2))}
# ===== treino nível WhoScored: legado pareado, campos da Understat + marca aprendida (xG>=0,18) + Opta
p=pd.read_pickle(S+'/dados/dados/chutes_pareados.pkl'); p=p[p.u_situation!='Penalty'].copy()
w=pd.DataFrame(dict(X=p.u_X.astype(float),Y=p.u_Y.astype(float),shotType=p.u_shotType,situation=p.u_situation,lastAction=p.u_lastAction.fillna('None').astype(str),xG=p.u_xG.astype(float),xg_opta=p.f_expectedGoals.fillna(0),xgot=p.f_expectedGoalsOnTarget)); w['big']=(w.xG>=.18).astype(int)
CATW={c:sorted(w[c].unique()) for c in ('shotType','situation','lastAction')}
def codW(d,cols):
    d=d[cols].copy()
    for c in CATW:
        if c in d: d[c]=pd.Categorical(d[c].where(d[c].isin(CATW[c]),'None' if c=='lastAction' else CATW[c][0]),categories=CATW[c])
    return d
W0=['X','Y','shotType','situation','lastAction','big']; W1=W0+['xg_opta']; W2=W1+['xgot']
mW={n:gbm().fit(codW(w,c),w.xG) for n,c in (('W0',W0),('W1',W1),('W2',W2))}
print('treino: nível FotMob',len(v),'finalizações | nível WhoScored',len(w))
# ===== teste: 15 jogos da La Liga 2025/26
def ws_jogo(a):
    t=open(a,encoding='utf-8',errors='replace').read(); d,_=json.JSONDecoder().raw_decode(t[t.find('{',t.find('matchCentreData')):]); ev=d['events']
    gh,ga=[int(x) for x in d['score'].split(':')]; byid={(e['teamId'],e.get('eventId')):e for e in ev}; r=[]
    for i,e in enumerate(ev):
        if not e.get('isShot'): continue
        q={x['type']['displayName'] for x in e['qualifiers']}
        if 'OwnGoal' in q: continue
        rel=byid.get((e['teamId'],e.get('relatedEventId'))); prev=ev[i-1]; pq={x['type']['displayName'] for x in prev['qualifiers']}
        sit='Penalty' if 'Penalty' in q else 'DirectFreekick' if 'DirectFreekick' in q else 'FromCorner' if 'FromCorner' in q else 'SetPiece' if ('SetPiece' in q or 'ThrowinSetPiece' in q) else 'OpenPlay'
        corpo='Head' if 'Head' in q else 'LeftFoot' if 'LeftFoot' in q else 'RightFoot' if 'RightFoot' in q else 'OtherBodyPart'
        mesmo=prev['teamId']==e['teamId']; pt=prev['type']['displayName']
        if sit in ('Penalty','DirectFreekick'): la='Standard'
        elif rel is not None and rel.get('isShot'): la='Rebound'
        elif pt=='Pass' and mesmo: la='Cross' if 'Cross' in pq else 'Throughball' if 'Throughball' in pq else 'HeadPass' if 'HeadPass' in pq else 'LayOff' if 'LayOff' in pq else 'Chipped' if 'Chipped' in pq else 'Pass'
        elif (not mesmo) and pt not in ('Aerial','Foul','Challenge','Tackle'): la='None'
        else: la=pt
        r.append(dict(lado='h' if e['teamId']==d['home']['teamId'] else 'a',minute=e['minute'],seg=e.get('second') or 0,X=e['x']/100,Y=e['y']/100,shotType=corpo,situation=sit,lastAction=la,big=int('BigChance' in q)))
    return d['startDate'][:10],gh,ga,d['home']['name'],pd.DataFrame(r)
def fot_jogo(d):
    casa=d['general']['homeTeam']['id']; sh=[s for s in (d['content'].get('shotmap') or {}).get('shots') or [] if not s['isOwnGoal']]
    r=pd.DataFrame([dict(lado='h' if s['teamId']==casa else 'a',jog=s['playerId'],minute=s['min']-1,X=s['x']/105,Y=s['y']/68,parte=s['shotType'],lance=s['situation'],gol=int(s['eventType']=='Goal'),xg_opta=s.get('expectedGoals') or 0.0,xgot=s.get('expectedGoalsOnTarget') if s.get('isOnTarget') else np.nan,fx=s['x'],fy=s['y']) for s in sh]); r['big']=0
    perd={}
    for pl in (d['content'].get('playerStats') or {}).values():
        bc=pm=0
        for grp in pl.get('stats') or []:
            for x in (grp.get('stats') or {}).values():
                if x.get('key')=='big_chance_missed_title': bc=(x.get('stat') or {}).get('value') or 0
                elif x.get('key')=='missed_penalty': pm=(x.get('stat') or {}).get('value') or 0
        perd[pl['id']]=max(bc-pm,0)
    tot={s['key']:s['stats'] for grp in d['content']['stats']['Periods']['All']['stats'] for s in grp['stats'] if s.get('key') in ('big_chance','big_chance_missed_title') and len(s['stats'])==2}
    np_=r[r.lance!='Penalty']
    for jog,kk in perd.items(): r.loc[np_[(np_.jog==jog)&(np_.gol==0)].sort_values('xg_opta',ascending=False).index[:int(kk)],'big']=1
    for i,lado in enumerate(('h','a')):
        conv=(tot.get('big_chance',[0,0])[i] or 0)-(tot.get('big_chance_missed_title',[0,0])[i] or 0)-int(((r.lado==lado)&(r.lance=='Penalty')&(r.gol==1)).sum())
        r.loc[np_[(np_.lado==lado)&(np_.gol==1)].sort_values('xg_opta',ascending=False).index[:max(int(conv),0)],'big']=1
    return r
fot={}
for f in glob.glob(S+'/fotmob/2025/*.json.gz'):
    if f.endswith('liga.json.gz'): continue
    d=json.load(gzip.open(f)); g=d['general']; h=d['header']['teams']; fot.setdefault((g['matchTimeUTCDate'][:10],h[0].get('score'),h[1].get('score')),[]).append(d)
def soma(d,col,une):
    o={}
    for lado,g in d.groupby('lado'):
        if une: g=g.sort_values(['minute','seg']); o[lado]=g.groupby((g.lastAction!='Rebound').cumsum())[col].apply(lambda x:1-np.prod(1-x.values)).sum()
        else: o[lado]=g[col].sum()
    return o
lin=[]; bigs=[0,0,0]
for a in sorted(glob.glob(S+'/ws14/**/*.html',recursive=True)):
    dia,gh,ga,casa,ws=ws_jogo(a); c=uj[(uj.liga=='La_liga')&(uj.ano==2025)&(uj.gh.astype(int)==gh)&(uj.ga.astype(int)==ga)&(uj.data.str[:10]==dia)]
    c=c[[casa.split()[-1][:4].lower() in h.lower() or h.split()[-1][:4].lower() in casa.lower() for h in c.h]] if len(c)>1 else c
    fl=fot[(dia,gh,ga)]; fl=[x for x in fl if x['general']['homeTeam']['name'][:4].lower()==casa[:4].lower()] if len(fl)>1 else fl; assert len(c)==1 and len(fl)==1
    j=c.iloc[0]; f=fot_jogo(fl[0])
    for n,cols in (('F0',F0),('F1',F1),('F2',F2)): f[n]=np.where(f.lance=='Penalty',PEN,np.clip(mF[n].predict(codF(f,cols)),0,1))
    ws['xg_opta']=0.0; ws['xgot']=np.nan; ws['fbig']=0
    for lado in ('h','a'):
        x=ws[ws.lado==lado]; y=f[f.lado==lado]
        if not len(x) or not len(y): continue
        dm=np.abs(x.minute.values[:,None]-y.minute.values[None,:]); di=np.hypot(x.X.values[:,None]*105-y.fx.values[None,:],x.Y.values[:,None]*68-y.fy.values[None,:]); cst=dm+di/4; cst[(dm>3)|(di>10)]=1e6
        li,co=linear_sum_assignment(cst)
        for i,kk in zip(li,co):
            if cst[i,kk]<1e6: ws.loc[x.index[i],['xg_opta','xgot','fbig']]=[y.xg_opta.values[kk],y.xgot.values[kk],y.big.values[kk]]
    bigs[0]+=int(ws.big.sum()); bigs[1]+=int(f.big.sum()); bigs[2]+=int((ws.big*ws.fbig).sum())
    for n,cols in (('W0',W0),('W1',W1),('W2',W2)): ws[n]=np.where(ws.situation=='Penalty',PEN,np.clip(mW[n].predict(codW(ws,cols)),0,1))
    t={n:soma(f,n,False) for n in ('F0','F1','F2')}; t.update({n:soma(ws,n,True) for n in ('W0','W1','W2')})
    for lado in ('h','a'): lin.append(dict(jogo=f'{j.h} x {j.a}',lado=lado,understat=float(j.xg_h if lado=='h' else j.xg_a),**{n:t[n].get(lado,0) for n in t}))
r=pd.DataFrame(lin); print(f'grandes chances nos 15 jogos: WhoScored {bigs[0]} | FotMob (escolhidas pela Opta) {bigs[1]} | as mesmas finalizações: {bigs[2]}')
for nome,col in (('só FotMob: posição, parte, lance, grande chance','F0'),('só FotMob + xG da Opta','F1'),('só FotMob + xG da Opta + xGOT','F2'),('WhoScored: campos + grande chance','W0'),('WhoScored + xG da Opta','W1'),('WhoScored + xG da Opta + xGOT','W2')):
    e=r[col]-r.understat; a=e.abs(); print(f'{nome:48s} erro médio {a.mean():.3f} | mediano {a.median():.3f} | maior {a.max():.2f} | acima de 0,20: {(a>.2).sum()} | acima de 0,30: {(a>.3).sum()} | desvio médio {e.mean():+.3f}')
r['eF1']=(r.F1-r.understat); r['eW1']=(r.W1-r.understat)
print(r.reindex(r.eW1.abs().sort_values(ascending=False).index)[['jogo','lado','understat','F0','F1','F2','W0','W1','W2']].head(8).round(2).to_string(index=False)); r.to_pickle(S+'/work/quatro.pkl')
