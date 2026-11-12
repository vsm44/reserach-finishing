# pareia temporadas novas (FotMob x Understat), retreina com conjuntos diferentes e mede em 2026/27
import sys, warnings, glob, pickle, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from scipy.optimize import linear_sum_assignment
S,REPO=sys.argv[1:3]; sys.path.insert(0,REPO+'/scripts'); import modelo_fotmob as M
pd.set_option('display.width',240)
UJ=pd.read_pickle(S+'/work/u_jogos.pkl'); US=pd.read_pickle(S+'/work/u_shots.pkl'); US=US[US.result!='OwnGoal']
def pareia(liga,ano,pasta):
    uj=UJ[(UJ.liga==liga)&(UJ.ano==ano)&UJ.isResult].copy(); uj['d']=uj.data.str[:10]; uj['gh']=uj.gh.astype(int); uj['ga']=uj.ga.astype(int); us=US[(US.liga==liga)&(US.ano==ano)]
    fl=[]
    for f in glob.glob(f'{pasta}/[0-9]*.json.gz'):
        d=M.le(f); h=d['header']['teams']; fl.append((d['general']['matchTimeUTCDate'][:10],h[0].get('score'),h[1].get('score'),d['general']['homeTeam']['id'],d['general']['awayTeam']['id'],d))
    votos={}
    for j in uj.itertuples():
        c=[x for x in fl if x[0]==j.d and x[1]==j.gh and x[2]==j.ga]
        if len(c)==1:
            for a,b in ((j.h,c[0][3]),(j.a,c[0][4])): votos.setdefault(a,{}).setdefault(b,0); votos[a][b]+=1
    mapa={k:max(v,key=v.get) for k,v in votos.items()}; L=[]; nj=nu=0
    for j in uj.itertuples():
        c=[x for x in fl if x[3]==mapa.get(j.h) and x[4]==mapa.get(j.a) and abs((pd.Timestamp(x[0])-pd.Timestamp(j.d)).days)<=1 and x[1]==j.gh and x[2]==j.ga]
        if len(c)!=1: continue
        nj+=1; f=M.finalizacoes(c[0][5]); u=us[us.arq==j.match_id]
        for lado in ('h','a'):
            a=u[u.lado==lado].reset_index(drop=True); b=f[f.lado==lado].reset_index(drop=True); nu+=len(a)
            if not len(a) or not len(b): continue
            dm=np.abs((a.minute.values+1)[:,None]-(b.minute+b.acr).values[None,:]); di=np.hypot(a.X.values[:,None]*105-b.X.values[None,:]*105,a.Y.values[:,None]*68-b.Y.values[None,:]*68); cst=dm+di/4; cst[(dm>3)|(di>8)]=1e6
            li,co=linear_sum_assignment(cst)
            for i,k in zip(li,co):
                if cst[i,k]<1e6 and b.lance[k]!='Penalty' and a.situation[i]!='Penalty': L.append({**{c_:b.at[k,c_] for c_ in M.COLS},'xg_understat':a.xG[i],'liga':liga,'season':ano})
    t=pd.DataFrame(L); print(f'{liga} {ano}: jogos casados {nj} de {len(uj)} | finalizações Understat {nu} | pareadas para treino {len(t)} ({len(t)/max(nu,1):.1%}) | grande chance {t.big.mean():.3f} | xG Understat médio {t.xg_understat.mean():.4f}')
    return t
novas=[pareia(l,a,p) for l,a,p in (('Serie_A',2025,S+'/hist/seriea_2025'),('Ligue_1',2025,S+'/hist/ligue1_2025'),('Ligue_1',2024,S+'/hist/ligue1_2024')) if glob.glob(p+'/[0-9]*.json.gz')]
N=pd.concat(novas,ignore_index=True); N.to_pickle(S+'/work/treino_novas.pkl')
B=pd.read_csv(REPO+'/data/treino/treino_fotmob_2020-2025.csv.gz',float_precision='round_trip')
# gabarito de 2026/27: lista (liga, pasta, id, u_m, u_v)
G=[]
def gab(cmp,prev,pasta,liga):
    c=pd.read_pickle(cmp); p=pd.read_csv(prev)
    if 'id_fotmob' in c: c=c.rename(columns={'id_fotmob':'id'})
    else: p['jogo']=p.mandante+' x '+p.visitante; c=c.merge(p[['data','jogo','id']],on=['data','jogo'],how='left')
    for r in c.itertuples(): G.append((liga,pasta,int(r.id),r.u_m,(r.u_v/1000 if r.u_v>8 else r.u_v)))
gab(S+'/work/cmp_serie_a.pkl',S+'/prev/prev_serie_a_2026.csv',S+'/fot_seriea_2026','Serie_A'); gab(S+'/work/cmp_ligue1.pkl',S+'/prev/prev_ligue_1_2026.csv',S+'/fot_ligue1_2026','Ligue_1'); gab(S+'/work/cmp_la_liga.pkl',S+'/prev/prev_la_liga_2026.csv',S+'/fot2026','La_liga')
FIN={(l,i):(M.finalizacoes(M.le(f'{p}/{i}.json.gz'))) for l,p,i,_,_ in G}
def mede(nome,tr):
    mod=M.treina(tr); L=[]
    for l,p,i,um,uv in G:
        s=M.preve(mod,FIN[(l,i)],l); L+= [(l,M.total(s[s.lado=='h'])-um),(l,M.total(s[s.lado=='a'])-uv)]
    e=pd.DataFrame(L,columns=['liga','e']); e['a']=e.e.abs(); txt=f'{nome:44s} treino {len(tr):6d} || '
    for l,g in list(e.groupby('liga'))+[('TODAS',e)]: txt+=f'{l}: {g.a.mean():.3f} (med {g.a.median():.3f}, >0,50 {(g.a>.5).mean():.1%}, desvio {g.e.mean():+.3f}) | '
    print(txt)
mede('A base atual (La Liga + Serie A até 2024/25)',B)
if (N.liga=='Serie_A').any(): mede('B base + Serie A 2025/26',pd.concat([B,N[N.liga=='Serie_A']]))
if (N.liga=='Ligue_1').any(): mede('C base + Ligue 1 (2024/25 e 2025/26)',pd.concat([B,N[N.liga=='Ligue_1']]))
mede('D base + tudo que foi baixado',pd.concat([B,N]))
T=pd.concat([B,N]); mede('E só temporadas 2024 e 2025, todas as ligas',T[T.season>=2024]); mede('F só 2025/26, todas as ligas',T[T.season==2025])
