import sys, warnings, json, glob, gzip, os, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy.optimize import linear_sum_assignment
S=sys.argv[1]; pd.set_option('display.width',250)
uj=pd.read_pickle(S+'/work/u_jogos.pkl'); uj=uj[uj.isResult&uj.gh.notna()].copy(); us=pd.read_pickle(S+'/work/u_shots.pkl')
PEN=0.7433
# ---------- WhoScored: finalizações com campos convertidos para o vocabulário da Understat
def ws_jogo(a):
    t=open(a,encoding='utf-8',errors='replace').read(); d,_=json.JSONDecoder().raw_decode(t[t.find('{',t.find('matchCentreData')):]); ev=d['events']
    gh,ga=[int(v) for v in d['score'].split(':')]; dia=d['startDate'][:10]; byid={(e['teamId'],e.get('eventId')):e for e in ev}; r=[]
    for k,e in enumerate(ev):
        if not e.get('isShot'): continue
        q={x['type']['displayName'] for x in e['qualifiers']}
        if 'OwnGoal' in q: continue
        rel=byid.get((e['teamId'],e.get('relatedEventId'))); prev=ev[k-1]; pq={x['type']['displayName'] for x in prev['qualifiers']}
        sit='Penalty' if 'Penalty' in q else 'DirectFreekick' if 'DirectFreekick' in q else 'FromCorner' if 'FromCorner' in q else 'SetPiece' if ('SetPiece' in q or 'ThrowinSetPiece' in q) else 'OpenPlay'
        corpo='Head' if 'Head' in q else 'LeftFoot' if 'LeftFoot' in q else 'RightFoot' if 'RightFoot' in q else 'OtherBodyPart'
        mesmo=prev['teamId']==e['teamId']; pt=prev['type']['displayName']
        if sit in ('Penalty','DirectFreekick'): la='Standard'
        elif rel is not None and rel.get('isShot'): la='Rebound'
        elif pt=='Pass' and mesmo: la='Cross' if 'Cross' in pq else 'Throughball' if 'Throughball' in pq else 'HeadPass' if 'HeadPass' in pq else 'LayOff' if 'LayOff' in pq else 'Chipped' if 'Chipped' in pq else 'Pass'
        elif (not mesmo) and pt not in ('Aerial','Foul','Challenge','Tackle'): la='None'
        else: la=pt
        r.append(dict(lado='h' if e['teamId']==d['home']['teamId'] else 'a',minute=e['minute'],seg=e.get('second') or 0,X=e['x']/100,Y=e['y']/100,shotType=corpo,situation=sit,lastAction=la,big=int('BigChance' in q),gol=int(e['type']['displayName']=='Goal')))
    return dia,gh,ga,d['home']['name'],pd.DataFrame(r)
# ---------- FotMob 2025
fot={}
for f in glob.glob(S+'/fotmob/2025/*.json.gz'):
    if f.endswith('liga.json.gz'): continue
    d=json.load(gzip.open(f)); g=d['general']; h=d['header']['teams']; fot[(g['matchTimeUTCDate'][:10],h[0].get('score'),h[1].get('score'),g['homeTeam']['name'][:4].lower())]=d
def fot_jogo(d):
    casa=d['general']['homeTeam']['id']; sh=[s for s in (d['content'].get('shotmap') or {}).get('shots') or [] if not s['isOwnGoal']]
    SIT={'RegularPlay':'OpenPlay','FastBreak':'OpenPlay','IndividualPlay':'OpenPlay','FromCorner':'FromCorner','SetPiece':'SetPiece','ThrowInSetPiece':'SetPiece','FreeKick':'DirectFreekick','Penalty':'Penalty'}
    COR={'Header':'Head','LeftFoot':'LeftFoot','RightFoot':'RightFoot','OtherBodyParts':'OtherBodyPart'}
    r=pd.DataFrame([dict(lado='h' if s['teamId']==casa else 'a',time=s['teamId'],jog=s['playerId'],minute=s['min']-1,X=s['x']/105,Y=s['y']/68,shotType=COR.get(s['shotType'],'RightFoot'),situation=SIT.get(s['situation'],'OpenPlay'),
        gol=int(s['eventType']=='Goal'),opta=s.get('expectedGoals') or 0.0,fx=s['x'],fy=s['y']) for s in sh]); r['big']=0
    # grandes chances: perdidas por jogador; convertidas por time; pênaltis fora; escolha pela MAIOR xG da Opta
    perd={}; 
    for p in (d['content'].get('playerStats') or {}).values():
        bc=pm=0
        for grp in p.get('stats') or []:
            for v in (grp.get('stats') or {}).values():
                if v.get('key')=='big_chance_missed_title': bc=(v.get('stat') or {}).get('value') or 0
                elif v.get('key')=='missed_penalty': pm=(v.get('stat') or {}).get('value') or 0
        perd[p['id']]=max(bc-pm,0)
    tot={}
    for grp in d['content']['stats']['Periods']['All']['stats']:
        for s in grp['stats']:
            if s.get('key') in ('big_chance','big_chance_missed_title') and len(s['stats'])==2: tot[s['key']]=s['stats']
    np_=r[r.situation!='Penalty']
    for jog,k in perd.items():
        idx=np_[(np_.jog==jog)&(np_.gol==0)].sort_values('opta',ascending=False).index[:int(k)]; r.loc[idx,'big']=1
    for i,lado in enumerate(('h','a')):
        conv=(tot.get('big_chance',[0,0])[i] or 0)-(tot.get('big_chance_missed_title',[0,0])[i] or 0)-int(((r.lado==lado)&(r.situation=='Penalty')&(r.gol==1)).sum())
        idx=np_[(np_.lado==lado)&(np_.gol==1)].sort_values('opta',ascending=False).index[:max(int(conv),0)]; r.loc[idx,'big']=1
    pub={k:[float(x) for x in s['stats']] for grp in d['content']['stats']['Periods']['All']['stats'] for s in grp['stats'] for k in [s.get('key')] if k=='expected_goals' and s['stats'][0] is not None}
    return r,pub.get('expected_goals')
# ---------- modelos treinados no bruto da Understat (sem os jogos de teste)
arqs=sorted(glob.glob(S+'/ws14/**/*.html',recursive=True)); jogos=[]
for a in arqs:
    dia,gh,ga,casa,w=ws_jogo(a); c=uj[(uj.liga=='La_liga')&(uj.ano==2025)&(uj.gh.astype(int)==gh)&(uj.ga.astype(int)==ga)&(uj.data.str[:10]==dia)]
    c=c[[casa.split()[-1][:4].lower() in h.lower() or h.split()[-1][:4].lower() in casa.lower() for h in c.h]] if len(c)>1 else c
    f=[v for k,v in fot.items() if k[0]==dia and k[1]==gh and k[2]==ga]; f=[v for v in f if v['general']['homeTeam']['name'][:4].lower()==casa[:4].lower()] if len(f)>1 else f
    assert len(c)==1 and len(f)==1,(a,len(c),len(f)); jogos.append((c.iloc[0],w,f[0]))
teste={j.match_id for j,_,_ in jogos}
s=us[(us.result!='OwnGoal')&(us.situation!='Penalty')&~us.arq.isin(teste)].copy(); s['lastAction']=s.lastAction.fillna('None').astype(str); s['big']=(s.xG>=.18).astype(int)
CAT={c:sorted(s[c].unique()) for c in ('shotType','situation','lastAction')}
def cod(d,cols):
    d=d[cols].copy()
    for c in cols:
        if c in CAT: d[c]=pd.Categorical(d[c].where(d[c].isin(CAT[c]),'None' if c=='lastAction' else CAT[c][0]),categories=CAT[c])
    return d
gbm=lambda: HistGradientBoostingRegressor(max_iter=500,learning_rate=0.08,max_leaf_nodes=63,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0)
CA=['X','Y','shotType','situation','lastAction','big']; CB=['X','Y','shotType','situation','big']; CC=['X','Y','shotType','situation']
mA=gbm().fit(cod(s,CA),s.xG); mB=gbm().fit(cod(s,CB),s.xG); mC=gbm().fit(cod(s,CC),s.xG)
def prev(m,d,cols): return np.where(d.situation=='Penalty',PEN,np.clip(m.predict(cod(d,cols)),0,1))
def total(d,col,une):
    out={}
    for lado,g in d.groupby('lado'):
        g=g.sort_values(['minute','seg'] if 'seg' in g else ['minute']); 
        if une and 'lastAction' in g:
            grp=(g.lastAction!='Rebound').cumsum(); out[lado]=g.groupby(grp)[col].apply(lambda v:1-np.prod(1-v.values)).sum()
        else: out[lado]=g[col].sum()
    return out
lin=[]; acerto=[0,0]
for j,w,fd in jogos:
    f,opta_pub=fot_jogo(fd); u=us[(us.arq==j.match_id)&(us.result!='OwnGoal')]
    w['p1']=prev(mA,w,CA); f['p2']=prev(mB,f,CB); f['p2s']=prev(mC,f,CC)
    # versão 3: marcas do WhoScored com a posição da FotMob (casa as finalizações por lado, minuto e posição)
    w3=w.copy()
    for lado in ('h','a'):
        a=w[w.lado==lado]; b=f[f.lado==lado]
        if not len(a) or not len(b): continue
        dm=np.abs(a.minute.values[:,None]-b.minute.values[None,:]); di=np.hypot(a.X.values[:,None]*105-b.fx.values[None,:],a.Y.values[:,None]*68-b.fy.values[None,:]); c=dm+di/4; c[(dm>3)|(di>10)]=1e6
        li,co=linear_sum_assignment(c)
        for i,k in zip(li,co):
            if c[i,k]<1e6: w3.loc[a.index[i],['X','Y']]=[b.X.values[k],b.Y.values[k]]
    w3['p3']=prev(mA,w3,CA)
    # conferência da última ação derivada
    uu=u.sort_values('ordem'); 
    for lado in ('h','a'):
        a=uu[uu.lado==lado]; b=w[w.lado==lado]
        if len(a)==len(b): acerto[0]+=(a.lastAction.fillna('None').astype(str).values==b.lastAction.values).sum(); acerto[1]+=len(a)
    t1=total(w,'p1',True); t2=total(f,'p2',False); t2s=total(f,'p2s',False); t3=total(w3,'p3',True)
    for i,lado in enumerate(('h','a')):
        lin.append(dict(jogo=f'{j.h} x {j.a}',lado=lado,understat=float(j.xg_h if lado=='h' else j.xg_a),v1=t1.get(lado,0),v2=t2.get(lado,0),v2_sem_gc=t2s.get(lado,0),v3=t3.get(lado,0),opta=opta_pub[i] if opta_pub else np.nan))
r=pd.DataFrame(lin); print(f'última ação derivada do WhoScored igual à da Understat: {acerto[0]} de {acerto[1]}')
print('time-jogos:',len(r),'| xG Understat médio',round(r.understat.mean(),3))
for nome,col in (('1 só WhoScored','v1'),('2 só FotMob (grande chance escolhida pela Opta)','v2'),('  só FotMob, sem grande chance','v2_sem_gc'),('3 posição FotMob + marcas WhoScored','v3'),('(ref.) xG da Opta publicado, direto','opta')):
    e=r[col]-r.understat; a=e.abs()
    print(f'{nome:50s} erro médio {a.mean():.3f} | mediano {a.median():.3f} | maior {a.max():.2f} | acima de 0,30: {(a>.3).sum()} | acima de 0,50: {(a>.5).sum()} | para mais {(e>0.05).sum()} / para menos {(e<-0.05).sum()} | média do desvio {e.mean():+.3f}')
r['e1']=r.v1-r.understat; r['e2']=r.v2-r.understat
print(r.reindex(r.e1.abs().sort_values(ascending=False).index)[['jogo','lado','understat','v1','v2','v3','opta']].head(8).round(2).to_string(index=False))
r.to_pickle(S+'/work/tres.pkl')
