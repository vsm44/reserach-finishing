# casa as linhas de um arquivo de jogos (sem usar xG) com as previsões gravadas: casa_prev.py prev.csv jogos.csv liga
import sys, unicodedata, difflib, pandas as pd
P,U,LIGA=sys.argv[1:4]
def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
    for w in ('calcio 1913','deportivo ','racing ','rayo ','real ','athletic ','atletico ','ac ','as ','fc ','olympique ','stade ',' fc'): s=s.replace(w,' ')
    return ' '.join(s.split())
def sim(a,b):
    a,b=norm(a),norm(b); return 1.0 if (a in b or b in a) and min(len(a),len(b))>=3 else difflib.SequenceMatcher(None,a,b).ratio()
p=pd.read_csv(P); p['d']=pd.to_datetime(p.data); g=pd.read_csv(U,usecols=['date','home_team','away_team']); g['d']=pd.to_datetime(g.date.astype(str).str[:10]); L=[]
for r in g.itertuples():
    c=p[(p.d-r.d).abs()<=pd.Timedelta(days=1)].copy()
    if not len(c): L.append(dict(liga=LIGA,data=r.date,mandante=r.home_team,visitante=r.away_team)); continue
    c['s']=[sim(m,r.home_team)+sim(v,r.away_team) for m,v in zip(c.mandante,c.visitante)]; k=c.sort_values('s').iloc[-1]
    if k.s<1.3: L.append(dict(liga=LIGA,data=r.date,mandante=r.home_team,visitante=r.away_team)); continue
    L.append(dict(liga=LIGA,data=r.date,mandante=r.home_team,visitante=r.away_team,jogo_fotmob=f'{k.mandante} {k.gols_m}-{k.gols_v} {k.visitante}',id_fotmob=k.id,xg_modelo_mandante=round(k.xg_m,2),xg_modelo_visitante=round(k.xg_v,2),xg_opta_mandante=k.opta_m,xg_opta_visitante=k.opta_v,sim=round(k.s,2)))
o=pd.DataFrame(L); print(LIGA,'| linhas',len(o),'| com previsão',int(o.xg_modelo_mandante.notna().sum()),'| ids repetidos',int(o.id_fotmob.dropna().duplicated().sum()),'| menor semelhança de nomes',o.sim.min())
print(o[o.sim<1.9][['data','mandante','visitante','jogo_fotmob','sim']].to_string(index=False)); o.drop(columns='sim').to_pickle(f'{P}.casado.pkl')
