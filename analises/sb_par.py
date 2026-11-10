import sys, json, glob, numpy as np, pandas as pd
from scipy.optimize import linear_sum_assignment
S,COMP,LIGA,ANO=sys.argv[1:5]; ANO=int(ANO)
sb=pd.DataFrame([r for f in glob.glob(f'{S}/statsbomb/sh_{COMP}/*.json') for r in json.load(open(f))]); sb['match_id']=sb.match_id.astype(int)
mm=pd.DataFrame([dict(match_id=x['match_id'],data=x['match_date'],sh=x['home_team']['home_team_name'],sa=x['away_team']['away_team_name'],hg=x['home_score'],ag=x['away_score']) for x in json.load(open(f'{S}/statsbomb/matches/{COMP}.json'))])
uj=pd.read_pickle(S+'/work/u_jogos.pkl'); uj=uj[(uj.liga==LIGA)&(uj.ano==ANO)].copy(); uj['d']=uj.data.str[:10]; uj['gh']=uj.gh.astype(int); uj['ga']=uj.ga.astype(int)
us=pd.read_pickle(S+'/work/u_shots.pkl'); us=us[(us.liga==LIGA)&(us.ano==ANO)&(us.result!='OwnGoal')].copy()
# jogos: data e placar com candidato único ensinam o mapa de nomes; depois times + data (±1 dia)
votos={}
for j in uj.itertuples():
    c=mm[(mm.data==j.d)&(mm.hg==j.gh)&(mm.ag==j.ga)]
    if len(c)==1:
        for a,b in ((j.h,c.sh.iloc[0]),(j.a,c.sa.iloc[0])): votos.setdefault(a,{}).setdefault(b,0); votos[a][b]+=1
mapa={k:max(v,key=v.get) for k,v in votos.items()}; pares=[]
mm['dt']=pd.to_datetime(mm.data); uj['dt']=pd.to_datetime(uj.d)
for j in uj.itertuples():
    c=mm[(mm.sh==mapa.get(j.h))&(mm.sa==mapa.get(j.a))&((mm.dt-j.dt).abs()<=pd.Timedelta(days=1))]
    if len(c)==1 and c.hg.iloc[0]==j.gh and c.ag.iloc[0]==j.ga: pares.append((j.match_id,c.match_id.iloc[0],c.sh.iloc[0]))
print('jogos Understat',len(uj),'| StatsBomb',len(mm),'| casados',len(pares))
def casa(u,f,flip):
    ux=np.c_[u.X*105,(1-u.Y if flip else u.Y)*68,u.minute]; fx=np.c_[f.x*105/120,f.y*68/80,f.minute]
    dm=np.abs(ux[:,2][:,None]-fx[:,2][None,:]); di=np.hypot(ux[:,0][:,None]-fx[:,0][None,:],ux[:,1][:,None]-fx[:,1][None,:])
    c=dm+di/4; c[(dm>4)|(di>10)]=1e6; li,co=linear_sum_assignment(c); return [(i,k,di[i,k],dm[i,k]) for i,k in zip(li,co) if c[i,k]<1e6]
for flip in (False,True):
    linhas=[]; nu=nf=0
    for um,sm,shome in pares:
        for lado in ('h','a'):
            u=us[(us.arq==um)&(us.lado==lado)].reset_index(drop=True); f=sb[(sb.match_id==sm)&((sb.team==shome)==(lado=='h'))].reset_index(drop=True)
            nu+=len(u); nf+=len(f)
            if not len(u) or not len(f): continue
            for i,k,di,dm in casa(u,f,flip): linhas.append({**{'u_'+c:u.at[i,c] for c in ('id','xG','X','Y','minute','result','situation','shotType','lastAction','player','arq','lado')},**f.loc[k].to_dict(),'dist':di,'dmin':dm})
    p=pd.DataFrame(linhas)
    print(f'Y invertido={flip}: finalizações Understat {nu} | StatsBomb {nf} | pareadas {len(p)} ({len(p)/nu:.1%} da Understat) | distância mediana {p.dist.median():.2f} m | p90 {p.dist.quantile(.9):.2f} | mesmo minuto {(p.dmin==0).mean():.1%}')
    if flip==False: p0=p
best=p if len(p)>len(p0) else p0
best.to_pickle(f'{S}/work/sb_par_{COMP}.pkl')
print('dmin:',best.dmin.value_counts().sort_index().to_dict())
print('resultado Understat x StatsBomb:'); print(pd.crosstab(best.u_result,best.outcome).to_string())
print('parte do corpo:'); print(pd.crosstab(best.u_shotType,best.body).to_string())
