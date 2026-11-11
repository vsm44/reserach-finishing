import sys, warnings, json, glob, gzip, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
S,REPO=sys.argv[1:3]; sys.path.insert(0,S+'/work'); pd.set_option('display.width',250); PEN=0.7613
x=pd.read_pickle(S+'/work/disseca.pkl'); n25=pd.read_pickle(S+'/work/treino_2025.pkl'); CF=['X','Y','parte','lance','big','gol']
tr=pd.concat([x[CF+['xg_understat']],n25[CF+['xg_understat']]],ignore_index=True); CATF={c:sorted(tr[c].unique()) for c in ('parte','lance')}
def codF(d):
    d=d[CF].copy()
    for c in CATF: d[c]=pd.Categorical(d[c].where(d[c].isin(CATF[c]),CATF[c][0]),categories=CATF[c])
    return d
mF=HistGradientBoostingRegressor(max_iter=600,learning_rate=0.06,max_leaf_nodes=47,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0).fit(codF(tr),tr.xg_understat)
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
def totF(g):
    if not len(g): return 0.0
    g=g.sort_values(['minute','acr','fid']); ok=((g.alvo.shift()==1)|(g.bloq.shift()==1)|(g.ev.shift()=='Post'))&(g.gol.shift()==0); reb=((g.minute+g.acr)==(g.minute+g.acr).shift())&ok
    return g.groupby((~reb).cumsum()).p.apply(lambda v:1-np.prod(1-v.values)).sum()
# 1) previsões da rodada 1 (22 a 24/08), feitas antes de abrir os valores da planilha
prev=[]
for f in glob.glob(S+'/fot_seriea_2026/[0-9]*.json.gz'):
    d=json.load(gzip.open(f)); dia=d['general']['matchTimeUTCDate'][:10]
    if not ('2026-08-22'<=dia<='2026-08-25'): continue
    h=d['header']['teams']; s,opta=fot_jogo(d); s['p']=np.where(s.lance=='Penalty',PEN,np.clip(mF.predict(codF(s)),0,1))
    prev.append(dict(data=dia,mandante=h[0]['name'],visitante=h[1]['name'],placar=f"{h[0]['score']}-{h[1]['score']}",fot_h=totF(s[s.lado=='h']),fot_a=totF(s[s.lado=='a']),opta_h=opta[0],opta_a=opta[1]))
p=pd.DataFrame(prev).sort_values(['data','mandante']).reset_index(drop=True); p.round(3).to_csv(S+'/work/cego_seriea_r1.csv',index=False)
print('PREVISÕES DA RODADA 1 (gravadas antes da comparação):'); print(p.round(2).to_string(index=False))
# 2) só agora os valores da planilha
import le_ods
L=list(le_ods.le(REPO+'/Serie_A_atual.ods').values())[0]; g=pd.DataFrame(L,columns=['season','date','kickoff','home_team','away_team','home_xg','away_xg','home_goals','away_goals'])
g['pl']=g.home_goals.astype(int).astype(str)+'-'+g.away_goals.astype(int).astype(str); o=[]
for r in p.itertuples():
    c=g[(g.date.astype(str).str[:10]==r.data)&(g.pl==r.placar)]
    if len(c)>1: c=c[[str(h)[:4].lower() in r.mandante.lower() or r.mandante[:4].lower() in str(h).lower() for h in c.home_team]]
    if len(c)!=1: print('não casou',r.mandante,r.visitante); continue
    o.append(dict(jogo=f'{r.mandante} x {r.visitante}',u_h=float(c.home_xg.iloc[0]),u_a=float(c.away_xg.iloc[0]),fot_h=r.fot_h,fot_a=r.fot_a,opta_h=r.opta_h,opta_a=r.opta_a))
o=pd.DataFrame(o); print('RODADA 1, comparação:'); print(o.round(2).to_string(index=False))
t=pd.DataFrame(dict(u=np.r_[o.u_h,o.u_a],fot=np.r_[o.fot_h,o.fot_a],opta=np.r_[o.opta_h,o.opta_a]))
a=pd.read_pickle(S+'/work/cego_resultado.pkl'); t2=pd.concat([t,pd.DataFrame(dict(u=np.r_[a.u_h,a.u_a],fot=np.r_[a.fot_h,a.fot_a],opta=np.r_[a.opta_h,a.opta_a]))])
for nome,d in (('rodada 1 (20 time-jogos)',t),('rodadas 1 a 3 (60 time-jogos)',t2)):
    for n,c in (('só FotMob','fot'),('Opta direto','opta')):
        e=d[c]-d.u; ab=e.abs(); print(f'{nome:30s} {n:12s} erro médio {ab.mean():.3f} | mediano {ab.median():.3f} | maior {ab.max():.2f} | até 0,10: {(ab<=.1).sum()} | acima de 0,30: {(ab>.3).sum()} | acima de 0,50: {(ab>.5).sum()} | desvio {e.mean():+.3f}')
