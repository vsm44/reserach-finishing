# compara as previsões gravadas com um CSV da Understat: compara.py prev.csv understat.csv saida.pkl
import sys, numpy as np, pandas as pd
P,U,OUT=sys.argv[1:4]; pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
p=pd.read_csv(P); g=pd.read_csv(U); g['d']=pd.to_datetime(g.date.astype(str).str[:10]); p['d']=pd.to_datetime(p.data)
def par(a,b):
    a,b=a.lower(),b.lower(); t=lambda s:{w for w in s.replace('.',' ').split() if w not in ('fc','ac','cf','real','de','calcio','1913','as','ss','us','rc','ud','cd','sc','olympique','stade','saint','st','paris','le')}
    return bool(t(a)&t(b)) or a[:4]==b[:4]
L=[]; sem=[]
for r in g.itertuples():
    c=p[((p.d-r.d).abs()<=pd.Timedelta(days=1))&(p.gols_m==int(r.home_goals))&(p.gols_v==int(r.away_goals))]
    if len(c)>1:
        c2=c[[par(m,r.home_team) or par(v,r.away_team) for m,v in zip(c.mandante,c.visitante)]]; c=c2 if len(c2)>=1 else c
    if len(c)>1:
        c2=c[[par(m,r.home_team) and par(v,r.away_team) for m,v in zip(c.mandante,c.visitante)]]; c=c2 if len(c2)==1 else c
    if len(c)!=1: sem.append((r.date,r.home_team,r.away_team,len(c))); continue
    k=c.iloc[0]; L.append(dict(data=k.data,jogo=f'{k.mandante} x {k.visitante}',placar=f'{k.gols_m}-{k.gols_v}',u_m=float(r.home_xg),u_v=float(r.away_xg),xg_m=k.xg_m,xg_v=k.xg_v,opta_m=k.opta_m,opta_v=k.opta_v))
o=pd.DataFrame(L); o.to_pickle(OUT); print('linhas no CSV',len(g),'| casadas',len(o),'| não casadas',sem)
t=pd.DataFrame(dict(data=np.r_[o.data,o.data],time=np.r_[o.jogo+' (casa)',o.jogo+' (fora)'],u=np.r_[o.u_m,o.u_v],m=np.r_[o.xg_m,o.xg_v],opta=np.r_[o.opta_m,o.opta_v]))
def mede(nome,d):
    for n,c in (('modelo','m'),('Opta direto','opta')):
        e=d[c]-d.u; a=e.abs(); print(f'{nome:34s} {n:12s} n={len(d):3d} | erro médio {a.mean():.3f} | mediano {a.median():.3f} | 90% até {a.quantile(.9):.2f} | maior {a.max():.2f} | até 0,10: {(a<=.1).mean():.0%} | acima de 0,30: {(a>.3).mean():.1%} | acima de 0,50: {(a>.5).mean():.1%} | desvio {e.mean():+.3f}')
print('xG médio por time: Understat',round(t.u.mean(),3),'| modelo',round(t.m.mean(),3),'| Opta',round(t.opta.mean(),3),'| período',o.data.min(),'a',o.data.max())
mede('todos',t)
if len(sys.argv)>4:
    corte=sys.argv[4]; mede(f'até {corte} (já vistos antes)',t[t.data<=corte]); mede(f'depois de {corte} (inéditos)',t[t.data>corte])
t['e']=t.m-t.u; print(t.reindex(t.e.abs().sort_values(ascending=False).index)[['data','time','u','m','opta','e']].head(10).round(2).to_string(index=False))
