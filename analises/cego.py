import sys, warnings, json, glob, gzip, os, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
S=sys.argv[1]; pd.set_option('display.width',250); pd.set_option('display.max_rows',100); PEN=0.7613   # pênalti da Serie A no bruto
gbm=lambda: HistGradientBoostingRegressor(max_iter=600,learning_rate=0.06,max_leaf_nodes=47,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0)
# ===== nível WhoScored: treino no bruto inteiro da Understat (5 ligas), marca aprendida com xG >= 0,18
u=pd.read_pickle(S+'/work/u_shots.pkl'); u=u[(u.result!='OwnGoal')&(u.situation!='Penalty')].copy(); u['lastAction']=u.lastAction.fillna('None').astype(str); u['big']=(u.xG>=.18).astype(int); u['gol']=(u.result=='Goal').astype(int)
CW=['X','Y','shotType','situation','lastAction','big','gol']; CATW={c:sorted(u[c].unique()) for c in ('shotType','situation','lastAction')}
def codW(d):
    d=d[CW].copy()
    for c in CATW: d[c]=pd.Categorical(d[c].where(d[c].isin(CATW[c]),'None' if c=='lastAction' else CATW[c][0]),categories=CATW[c])
    return d
mW=gbm().fit(codW(u),u.xG)
# ===== nível FotMob: treino no legado (2020-24, duas ligas) + La Liga 2025/26
x=pd.read_pickle(S+'/work/disseca.pkl'); n25=pd.read_pickle(S+'/work/treino_2025.pkl'); CF=['X','Y','parte','lance','big','gol']
tr=pd.concat([x[CF+['xg_understat']],n25[CF+['xg_understat']]],ignore_index=True); CATF={c:sorted(tr[c].unique()) for c in ('parte','lance')}
def codF(d):
    d=d[CF].copy()
    for c in CATF: d[c]=pd.Categorical(d[c].where(d[c].isin(CATF[c]),CATF[c][0]),categories=CATF[c])
    return d
mF=gbm().fit(codF(tr),tr.xg_understat); print('treino: WhoScored',len(u),'| FotMob',len(tr))
def ws_jogo(a):
    t=open(a,encoding='utf-8',errors='replace').read(); d,_=json.JSONDecoder().raw_decode(t[t.find('{',t.find('matchCentreData')):]); ev=d['events']
    gh,ga=[int(v) for v in d['score'].split(':')]; byid={(e['teamId'],e.get('eventId')):e for e in ev}; r=[]
    for i,e in enumerate(ev):
        if not e.get('isShot'): continue
        q={v['type']['displayName'] for v in e['qualifiers']}
        if 'OwnGoal' in q: continue
        rel=byid.get((e['teamId'],e.get('relatedEventId'))); prev=ev[i-1]; pq={v['type']['displayName'] for v in prev['qualifiers']}
        sit='Penalty' if 'Penalty' in q else 'DirectFreekick' if 'DirectFreekick' in q else 'FromCorner' if 'FromCorner' in q else 'SetPiece' if ('SetPiece' in q or 'ThrowinSetPiece' in q) else 'OpenPlay'
        corpo='Head' if 'Head' in q else 'LeftFoot' if 'LeftFoot' in q else 'RightFoot' if 'RightFoot' in q else 'OtherBodyPart'
        mesmo=prev['teamId']==e['teamId']; pt=prev['type']['displayName']
        if sit in ('Penalty','DirectFreekick'): la='Standard'
        elif rel is not None and rel.get('isShot'): la='Rebound'
        elif pt=='Pass' and mesmo: la='Cross' if 'Cross' in pq else 'Throughball' if 'Throughball' in pq else 'HeadPass' if 'HeadPass' in pq else 'LayOff' if 'LayOff' in pq else 'Chipped' if 'Chipped' in pq else 'Pass'
        elif (not mesmo) and pt not in ('Aerial','Foul','Challenge','Tackle'): la='None'
        else: la=pt
        r.append(dict(lado='h' if e['teamId']==d['home']['teamId'] else 'a',minute=e['minute'],seg=e.get('second') or 0,X=e['x']/100,Y=e['y']/100,shotType=corpo,situation=sit,lastAction=la,big=int('BigChance' in q),gol=int(e['type']['displayName']=='Goal')))
    return d['startDate'][:10],d['home']['name'],d['away']['name'],gh,ga,pd.DataFrame(r)
def fot_jogo(d):
    casa=d['general']['homeTeam']['id']; sh=[s for s in (d['content'].get('shotmap') or {}).get('shots') or [] if not s['isOwnGoal']]
    r=pd.DataFrame([dict(lado='h' if s['teamId']==casa else 'a',jog=s['playerId'],minute=s['min'],acr=s.get('minAdded') or 0,fid=s['id'],X=s['x']/105,Y=s['y']/68,parte=s['shotType'],lance=s['situation'],gol=int(s['eventType']=='Goal'),ev=s['eventType'],bloq=int(bool(s['isBlocked'])),alvo=int(bool(s['isOnTarget'])),xg_opta=s.get('expectedGoals') or 0.0) for s in sh]); r['big']=0
    perd={}
    for pl in (d['content'].get('playerStats') or {}).values():
        bc=pm=0
        for grp in pl.get('stats') or []:
            for v in (grp.get('stats') or {}).values():
                if v.get('key')=='big_chance_missed_title': bc=(v.get('stat') or {}).get('value') or 0
                elif v.get('key')=='missed_penalty': pm=(v.get('stat') or {}).get('value') or 0
        perd[pl['id']]=max(bc-pm,0)
    tot={s['key']:s['stats'] for grp in d['content']['stats']['Periods']['All']['stats'] for s in grp['stats'] if s.get('key') in ('big_chance','big_chance_missed_title','expected_goals') and len(s['stats'])==2 and s['stats'][0] is not None}
    np_=r[r.lance!='Penalty']
    for jog,kk in perd.items(): r.loc[np_[(np_.jog==jog)&(np_.gol==0)].sort_values('xg_opta',ascending=False).index[:int(kk)],'big']=1
    for i,lado in enumerate(('h','a')):
        conv=(tot.get('big_chance',[0,0])[i] or 0)-(tot.get('big_chance_missed_title',[0,0])[i] or 0)-int(((r.lado==lado)&(r.lance=='Penalty')&(r.gol==1)).sum())
        r.loc[np_[(np_.lado==lado)&(np_.gol==1)].sort_values('xg_opta',ascending=False).index[:max(int(conv),0)],'big']=1
    return r,[float(v) for v in tot['expected_goals']] if 'expected_goals' in tot else [np.nan,np.nan]
def totW(g):
    g=g.sort_values(['minute','seg']); return g.groupby((g.lastAction!='Rebound').cumsum()).p.apply(lambda v:1-np.prod(1-v.values)).sum() if len(g) else 0.0
def totF(g):
    if not len(g): return 0.0
    g=g.sort_values(['minute','acr','fid']); ok=((g.alvo.shift()==1)|(g.bloq.shift()==1)|(g.ev.shift()=='Post'))&(g.gol.shift()==0); reb=((g.minute+g.acr)==(g.minute+g.acr).shift())&ok
    return g.groupby((~reb).cumsum()).p.apply(lambda v:1-np.prod(1-v.values)).sum()
fot=[]
for f in glob.glob(S+'/fot_seriea_2026/[0-9]*.json.gz'):
    d=json.load(gzip.open(f)); h=d['header']['teams']; fot.append((d['general']['matchTimeUTCDate'][:10],h[0]['name'],h[1]['name'],h[0].get('score'),h[1].get('score'),d))
lin=[]
for a in sorted(glob.glob(S+'/ws_seriea/**/*.html',recursive=True)):
    dia,casa,fora,gh,ga,w=ws_jogo(a); w['p']=np.where(w.situation=='Penalty',PEN,np.clip(mW.predict(codW(w)),0,1))
    c=[j for j in fot if abs((pd.Timestamp(j[0])-pd.Timestamp(dia)).days)<=1 and j[3]==gh and j[4]==ga]
    if len(c)>1: c=[j for j in c if j[1][:4].lower()==casa[:4].lower() or j[2][:4].lower()==fora[:4].lower()] or c
    l=dict(data=dia,mandante=casa,visitante=fora,placar=f'{gh}-{ga}',ws_h=totW(w[w.lado=='h']),ws_a=totW(w[w.lado=='a']),n_h=int((w.lado=='h').sum()),n_a=int((w.lado=='a').sum()),gc_h=int(w[w.lado=='h'].big.sum()),gc_a=int(w[w.lado=='a'].big.sum()))
    if len(c)==1:
        s,opta=fot_jogo(c[0][5]); s['p']=np.where(s.lance=='Penalty',PEN,np.clip(mF.predict(codF(s)),0,1)); l.update(fot_h=totF(s[s.lado=='h']),fot_a=totF(s[s.lado=='a']),opta_h=opta[0],opta_a=opta[1])
    else: l.update(fot_h=np.nan,fot_a=np.nan,opta_h=np.nan,opta_a=np.nan); print('sem par na FotMob:',dia,casa,fora,len(c))
    lin.append(l)
r=pd.DataFrame(lin).sort_values(['data','mandante']).reset_index(drop=True); r.to_pickle(S+'/work/cego_seriea.pkl'); r.round(3).to_csv(S+'/work/cego_seriea.csv',index=False)
print('jogos',len(r),'| de',r.data.min(),'a',r.data.max(),'| com par na FotMob',int(r.fot_h.notna().sum()))
print(r[['data','mandante','visitante','placar','ws_h','ws_a','fot_h','fot_a','opta_h','opta_a']].round(2).to_string(index=False))
