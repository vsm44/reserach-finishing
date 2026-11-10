import sys, numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
S,COMP,LIGA,ANO=sys.argv[1:5]; ANO=int(ANO); pd.set_option('display.width',250)
p=pd.read_pickle(f'{S}/work/sb_par_{COMP}.pkl'); p=p[p.u_situation!='Penalty'].reset_index(drop=True)
# base: modelo com os campos da Understat, treinado em todo o bruto MENOS esta liga/temporada
s=pd.read_pickle(S+'/work/u_shots.pkl'); s=s[(s.result!='OwnGoal')&(s.situation!='Penalty')].copy(); s['lastAction']=s.lastAction.fillna('None')
C=['X','Y','shotType','situation','lastAction']; cats={c:sorted(s[c].unique()) for c in C[2:]}
def cod(d):
    d=d[C].copy()
    for c in C[2:]: d[c]=pd.Categorical(d[c],categories=cats[c])
    return d
tr=s[~((s.liga==LIGA)&(s.ano==ANO))]
mb=HistGradientBoostingRegressor(max_iter=500,learning_rate=0.08,max_leaf_nodes=63,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0).fit(cod(tr),tr.xG)
q=p.rename(columns={'u_X':'X','u_Y':'Y','u_shotType':'shotType','u_situation':'situation','u_lastAction':'lastAction'}); q['lastAction']=q.lastAction.fillna('None')
p['base']=np.clip(mb.predict(cod(q)),0,1)
# geometria do freeze frame (coordenadas StatsBomb: gol em x=120, traves em y=36 e 44)
def geo(r):
    sx,sy=r.x,r.y; ff=r.ff; opp=[(a,b) for a,b,t,g in ff if not t and not g]; gk=[(a,b) for a,b,t,g in ff if not t and g]; mate=[(a,b) for a,b,t,g in ff if t]
    def cone(a,b):
        # dentro do triângulo finalizador–traves
        def sg(x1,y1,x2,y2,x3,y3): return (x1-x3)*(y2-y3)-(x2-x3)*(y1-y3)
        d1=sg(a,b,sx,sy,120,36); d2=sg(a,b,120,36,120,44); d3=sg(a,b,120,44,sx,sy); neg=(d1<0)or(d2<0)or(d3<0); pos=(d1>0)or(d2>0)or(d3>0); return not(neg and pos)
    dd=[np.hypot(a-sx,b-sy) for a,b in opp]
    o=dict(n_ff=len(ff),def_cone=sum(cone(a,b) for a,b in opp),comp_cone=sum(cone(a,b) for a,b in mate),def_perto2=sum(d<=2 for d in dd),def_perto5=sum(d<=5 for d in dd),
           def_mais_prox=min(dd) if dd else 30.0,def_atras_bola=sum(a>=sx for a,b in opp),tem_gk=len(gk)>0)
    if gk:
        gx,gy=gk[0]; o.update(gk_cone=cone(gx,gy),gk_dist_gol=np.hypot(120-gx,40-gy),gk_dist_fin=np.hypot(gx-sx,gy-sy))
        # afastamento lateral do goleiro em relação à linha finalizador–centro do gol
        vx,vy=120-sx,40-sy; n=np.hypot(vx,vy) or 1; o['gk_lateral']=abs((gx-sx)*vy-(gy-sy)*vx)/n
    else: o.update(gk_cone=False,gk_dist_gol=np.nan,gk_dist_fin=np.nan,gk_lateral=np.nan)
    return pd.Series(o)
G=p.apply(geo,axis=1); p=pd.concat([p,G],axis=1); GEO=list(G.columns)
FL=['play_pattern','under_pressure','first_time','one_on_one','open_goal','technique','follows_dribble','aerial_won','deflected','redirect','kp_tipo','kp_cross','kp_through','kp_cutback']
for c in ('play_pattern','technique','kp_tipo'): p[c]=p[c].fillna('nenhum').astype('category')
p['gol']=(p.u_result=='Goal').astype(int); p['no_alvo']=p.u_result.isin(['Goal','SavedShot']).astype(int); p['bloq']=(p.u_result=='BlockedShot').astype(int)
print('finalizações pareadas sem pênalti:',len(p),'| xG Understat médio',round(p.u_xG.mean(),4),'| com goleiro no quadro',f'{p.tem_gk.mean():.1%}')
def cv(cols):
    out=np.zeros(len(p))
    for a,b in GroupKFold(5).split(p,groups=p.u_arq):
        m=HistGradientBoostingRegressor(max_iter=300,learning_rate=0.05,max_leaf_nodes=15,min_samples_leaf=20,categorical_features='from_dtype',early_stopping=True,random_state=0).fit(p.loc[a,cols],p.loc[a,'u_xG']-p.loc[a,'base'])
        out[b]=m.predict(p.loc[b,cols])
    return np.clip(p.base+out,0,1)
def med(nome,pr):
    e=(pr-p.u_xG).abs(); j=p.assign(pr=pr).groupby(['u_arq','u_lado']).agg(u=('u_xG','sum'),m=('pr','sum')); ej=(j.m-j.u).abs()
    g=(pr-p.u_xG)[p.gol==1].mean(); bl=(pr-p.u_xG)[p.bloq==1].mean()
    print(f'{nome:46s} por finalização: erro médio {e.mean():.4f} | acima de 0,10: {(e>.1).mean():.1%} || por time-jogo: médio {ej.mean():.3f} | mediano {ej.median():.3f} | acima de 0,50: {(ej>.5).mean():.1%} || viés nos gols {g:+.3f} | nas bloqueadas {bl:+.3f}')
    return pr
med('0 base (campos da Understat)',p.base.values)
r1=med('1 base + posição da defesa e do goleiro',cv(['base']+GEO))
r2=med('2 base + marcas da StatsBomb',cv(['base']+FL))
r3=med('3 base + posição + marcas',cv(['base']+GEO+FL))
r4=med('4 base + resultado (gol, no alvo, bloqueada)',cv(['base','gol','no_alvo','bloq']))
r5=med('5 base + posição + marcas + resultado',cv(['base']+GEO+FL+['gol','no_alvo','bloq']))
med('(ref.) xG da própria StatsBomb, direto',p.xg_sb.values)
p['r3']=r3; p.to_pickle(f'{S}/work/sb_feat_{COMP}.pkl')
# importância simples: tirar um grupo de cada vez do modelo 3
for nome,tira in (('sem def_cone/comp_cone',['def_cone','comp_cone']),('sem goleiro (gk_*)',[c for c in GEO if c.startswith('gk')or c=='tem_gk']),('sem defensores próximos',['def_perto2','def_perto5','def_mais_prox','def_atras_bola'])):
    pr=cv(['base']+[c for c in GEO if c not in tira]+FL); print(f'   modelo 3 {nome}: erro médio {(pr-p.u_xG).abs().mean():.4f}')
