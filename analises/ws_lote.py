import sys, re, json, glob, os, collections, pandas as pd, numpy as np
S=sys.argv[1]; pd.set_option('display.width',250)
uj=pd.read_pickle(S+'/work/u_jogos.pkl'); uj=uj[uj.isResult&uj.gh.notna()].copy(); us=pd.read_pickle(S+'/work/u_shots.pkl'); us=us[us.result!='OwnGoal']
arqs=sorted(glob.glob(S+'/ws14/**/*.html',recursive=True))+sorted(glob.glob(S+'/whoscored/[A-Z]*.html'))
tudo=[]; res=[]
for a in arqs:
    t=open(a,encoding='utf-8',errors='replace').read(); i=t.find('matchCentreData')
    if i<0: print('SEM DADOS:',os.path.basename(a)); continue
    d,_=json.JSONDecoder().raw_decode(t[t.find('{',i):]); ev=d['events']; nomes=d['playerIdNameDictionary']
    gh,ga=[int(v) for v in d['score'].split(':')]; dia=d['startDate'][:10]
    c=uj[(uj.data.str[:10].isin([dia,str((pd.Timestamp(dia)+pd.Timedelta(days=1)).date()),str((pd.Timestamp(dia)-pd.Timedelta(days=1)).date())]))&(uj.gh.astype(int)==gh)&(uj.ga.astype(int)==ga)]
    c=c[[ (d['home']['name'].split()[-1][:5].lower() in h.lower()) or (h.split()[-1][:5].lower() in d['home']['name'].lower()) for h in c.h]] if len(c)>1 else c
    if len(c)!=1: print('JOGO NÃO CASADO:',os.path.basename(a),dia,gh,ga,len(c)); continue
    mid=c.match_id.iloc[0]; byid={(e['teamId'],e.get('eventId')):e for e in ev}; w=[]
    for k,e in enumerate(ev):
        if not e.get('isShot'): continue
        q={x['type']['displayName'] for x in e['qualifiers']}
        if 'OwnGoal' in q: continue
        rel=byid.get((e['teamId'],e.get('relatedEventId'))); rq={x['type']['displayName'] for x in rel['qualifiers']} if rel else set()
        w.append(dict(lado='h' if e['teamId']==d['home']['teamId'] else 'a',wmin=e['minute'],wx=e['x'],wy=e['y'],big='BigChance' in q,fast='FastBreak' in q,one='OneOnOne' in q,first='FirstTouch' in q,volley='Volley' in q,indiv='IndividualPlay' in q,
            wpen='Penalty' in q,rel=rel['type']['displayName'] if rel else 'nenhum',rel_bcc='BigChanceCreated' in rq,rel_inten='IntentionalAssist' in rq,marcas=' '.join(sorted(q))))
    w=pd.DataFrame(w); u=us[us.arq==mid].sort_values('ordem'); n=0
    for lado in ('h','a'):
        a_=u[u.lado==lado].reset_index(drop=True); b=w[w.lado==lado].reset_index(drop=True); usado=set()
        for r in a_.itertuples():
            cand=[(abs(r.minute-k.wmin)*3+abs(r.X*100-k.wx)+abs(r.Y*100-k.wy),k.Index) for k in b.itertuples() if k.Index not in usado]
            if not cand: continue
            cu,ix=min(cand)
            if cu>15: continue
            usado.add(ix); n+=1; tudo.append({**{c:getattr(r,c) for c in ('id','arq','liga','ano','lado','minute','player','result','situation','shotType','lastAction','X','Y','xG')},**b.loc[ix].drop('lado').to_dict()})
    res.append((f"{d['home']['name']} {gh}-{ga} {d['away']['name']}",dia,c.liga.iloc[0],mid,len(u),len(w),n))
t=pd.DataFrame(tudo); t.to_pickle(S+'/work/ws_lote.pkl')
r=pd.DataFrame(res,columns=['jogo','data','liga','understat_id','fin_U','fin_W','pareadas']); print(r.to_string(index=False))
print('total: jogos',len(r),'| Understat',r.fin_U.sum(),'| WhoScored',r.fin_W.sum(),'| pareadas',len(t))
t['dx']=(t.X*100-t.wx).abs(); t['dy']=(t.Y*100-t.wy).abs()
print(f"posição idêntica (até 0,1): {((t.dx<=.11)&(t.dy<=.11)).mean():.1%} | até 1,0: {((t.dx<=1)&(t.dy<=1)).mean():.1%} | mesmo minuto: {(t.wmin==t.minute).mean():.1%}")
s=t[t.situation!='Penalty']
print('sem pênalti:',len(s),'| com marca de grande chance:',int(s.big.sum()))
print('xG Understat por marca:'); print(s.groupby('big').xG.describe(percentiles=[.1,.5,.9]).round(3).to_string())
for lim in (.15,.2,.3):
    print(f'  xG >= {lim}: {int((s.xG>=lim).sum())} finalizações, das quais {int(((s.xG>=lim)&s.big).sum())} com a marca | com a marca e xG < {lim}: {int((s.big&(s.xG<lim)).sum())}')
print('marcadas com xG < 0,20:'); print(s[s.big&(s.xG<.2)][['arq','minute','player','result','situation','shotType','lastAction','fast','first','xG']].round(3).to_string(index=False))
print('sem a marca com xG >= 0,20:'); print(s[~s.big&(s.xG>=.2)][['arq','minute','player','result','situation','shotType','lastAction','fast','first','one','xG','marcas']].round(3).to_string(index=False))
print('outras marcas: n e xG médio | fast',int(s.fast.sum()),round(s[s.fast].xG.mean(),3),'| one',int(s.one.sum()),'| first',int(s['first'].sum()),round(s[s['first']].xG.mean(),3),'| volley',int(s.volley.sum()),'| rel_bcc (passe marcado como grande chance criada)',int(s.rel_bcc.sum()))
