# segunda etapa: corrige o total do time com dados do jogo inteiro. Treina no histórico (primeira etapa fora da amostra) e mede em 2026/27.
import sys, warnings, glob, gzip, json, pickle, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
S,REPO=sys.argv[1:3]; sys.path.insert(0,REPO+'/scripts'); sys.dont_write_bytecode=True; import modelo_fotmob as M
pd.set_option('display.width',250)
UJ=pd.read_pickle(S+'/work/u_jogos.pkl'); B=pd.read_csv(REPO+'/data/treino/treino_fotmob_2020-2025.csv.gz',float_precision='round_trip'); PROD=pickle.load(open(REPO+'/scripts/modelo_fotmob.pkl','rb'))
def hist_understat(liga,ano):
    lg=json.load(gzip.open(f'{S}/understat/{liga}/{ano}/liga.json.gz')); return {(t['title'],h['date'][:10]):h for t in lg['teams'].values() for h in t['history']}
def linhas(d,mod,liga,ano):
    h=d['header']['teams']; s=M.preve(mod,M.finalizacoes(d),liga); st=M.estatisticas(d); out=[]
    for i,lado in enumerate(('h','a')):
        t=s[s.lado==lado]; o=s[s.lado!=lado]
        r=dict(liga=liga,ano=ano,mid=d['general']['matchId'],data=d['general']['matchTimeUTCDate'][:10],lado=lado,m=M.total(t),m_adv=M.total(o),soma=float(t.p.sum()),n_fin=len(t),n_big=int(t.big.sum()),p_big=float(t[t.big==1].p.sum()),p_max=float(t.p.max()) if len(t) else 0.0,
               n_cab=int((t.parte=='Header').sum()),n_alvo=int(t.alvo.sum()),n_bloq=int(t.bloq.sum()),n_pen=int((t.lance=='Penalty').sum()),opta_fin=float(t.xg_opta.sum()),xgot_fin=float(t.xgot.fillna(0).sum()),gols=float(h[i].get('score') or 0),gols_adv=float(h[1-i].get('score') or 0),mandante=int(i==0))
        for k,v in st[i].items(): r['f_'+k]=v
        for k,v in st[1-i].items(): r['a_'+k]=v
        out.append(r)
    return out
def temporada(liga,ano,pasta,mod):
    uj=UJ[(UJ.liga==liga)&(UJ.ano==ano)&UJ.isResult].copy(); uj['d']=uj.data.str[:10]; uj['gh']=uj.gh.astype(int); uj['ga']=uj.ga.astype(int); hu=hist_understat(liga,ano)
    fl=[]
    for f in glob.glob(f'{pasta}/[0-9]*.json.gz'):
        d=M.le(f); h=d['header']['teams']; fl.append((d['general']['matchTimeUTCDate'][:10],h[0].get('score'),h[1].get('score'),d['general']['homeTeam']['id'],d['general']['awayTeam']['id'],d))
    votos={}
    for j in uj.itertuples():
        c=[x for x in fl if x[0]==j.d and x[1]==j.gh and x[2]==j.ga]
        if len(c)==1:
            for a,b in ((j.h,c[0][3]),(j.a,c[0][4])): votos.setdefault(a,{}).setdefault(b,0); votos[a][b]+=1
    mapa={k:max(v,key=v.get) for k,v in votos.items()}; L=[]
    for j in uj.itertuples():
        c=[x for x in fl if x[3]==mapa.get(j.h) and x[4]==mapa.get(j.a) and abs((pd.Timestamp(x[0])-pd.Timestamp(j.d)).days)<=1 and x[1]==j.gh and x[2]==j.ga]
        if len(c)!=1: continue
        for r,(u,tit) in zip(linhas(c[0][5],mod,liga,ano),((float(j.xg_h),j.h),(float(j.xg_a),j.a))):
            r['u']=u; hh=hu.get((tit,j.d)) or {}; r['us_deep']=hh.get('deep',np.nan); r['us_deep_adv']=hh.get('deep_allowed',np.nan); r['us_ppda']=(hh['ppda']['att']/max(hh['ppda']['def'],1)) if hh else np.nan; r['us_ppda_adv']=(hh['ppda_allowed']['att']/max(hh['ppda_allowed']['def'],1)) if hh else np.nan; L.append(r)
    print(f'  {liga} {ano}: {len(L)//2} jogos'); return L
T=[]
for ano in range(2021,2026):
    mod=M.treina(B[~((B.liga=='La_liga')&(B.season==ano))]); T+=temporada('La_liga',ano,f'{S}/fotmob/{ano}',mod)
T+=temporada('Serie_A',2025,S+'/hist/seriea_2025',PROD); T+=temporada('Ligue_1',2025,S+'/hist/ligue1_2025',PROD); T+=temporada('Ligue_1',2024,S+'/hist/ligue1_2024',PROD)
T=pd.DataFrame(T)
# teste: 2026/27 com gabarito
G=[]
def gab(cmp,prev,pasta,liga):
    c=pd.read_pickle(cmp); p=pd.read_csv(prev)
    if 'id_fotmob' in c: c=c.rename(columns={'id_fotmob':'id'})
    else: p['jogo']=p.mandante+' x '+p.visitante; c=c.merge(p[['data','jogo','id']],on=['data','jogo'],how='left')
    for r in c.itertuples():
        for x,u in zip(linhas(M.le(f'{pasta}/{int(r.id)}.json.gz'),PROD,liga,2026),(r.u_m,(r.u_v/1000 if r.u_v>8 else r.u_v))): x['u']=u; G.append(x)
gab(S+'/work/cmp_serie_a.pkl',S+'/prev/prev_serie_a_2026.csv',S+'/fot_seriea_2026','Serie_A'); gab(S+'/work/cmp_ligue1.pkl',S+'/prev/prev_ligue_1_2026.csv',S+'/fot_ligue1_2026','Ligue_1'); gab(S+'/work/cmp_la_liga.pkl',S+'/prev/prev_la_liga_2026.csv',S+'/fot2026','La_liga')
G=pd.DataFrame(G); T.to_pickle(S+'/work/etapa2_treino.pkl'); G.to_pickle(S+'/work/etapa2_teste.pkl')
print('histórico:',len(T),'time-jogos | teste 2026/27:',len(G))
def res(nome,e):
    a=e.abs(); return f'{nome}: >0,50 {(a>.5).mean():.1%} | >0,30 {(a>.3).mean():.1%} | médio {a.mean():.3f} | desvio {e.mean():+.3f}'
print('PRIMEIRA ETAPA |',res('histórico (fora da amostra)',T.m-T.u),'||',res('2026/27',G.m-G.u))
# diagnóstico: a sobra acompanha algum indicador da Understat?
T['sobra']=T.u-T.m
print('correlação da sobra (Understat − modelo) com:',{k:round(T.sobra.corr(T[k]),3) for k in ('us_deep','us_deep_adv','us_ppda','us_ppda_adv','gols','gols_adv','m','m_adv','n_fin','n_big','f_touches_opp_box','f_BallPossesion','f_expected_goals','f_expected_goals_on_target','f_corners','f_accurate_crosses','f_ShotsOnTarget','f_shots_inside_box','f_big_chance','f_big_chance_missed_title') if k in T})
FS=[c for c in T.columns if c.startswith('f_') or c.startswith('a_')]; OPTA=[c for c in ('f_expected_goals','f_expected_goals_open_play','f_expected_goals_set_play','f_expected_goals_non_penalty','f_expected_goals_on_target','a_expected_goals') if c in T]
PROPRIAS=['m','m_adv','soma','n_fin','n_big','p_big','p_max','n_cab','n_alvo','n_bloq','n_pen','opta_fin','xgot_fin','mandante']
conj={'1 gols e gap (m, m_adv, gols, gols_adv)':['m','m_adv','gols','gols_adv'],'2 = 1 + contagens das finalizações':PROPRIAS+['gols','gols_adv'],'3 = 2 + xG da Opta por time':PROPRIAS+['gols','gols_adv']+OPTA,'4 = 3 + todas as estatísticas do jogo':PROPRIAS+['gols','gols_adv']+FS}
h2=lambda: HistGradientBoostingRegressor(max_iter=250,learning_rate=0.04,max_leaf_nodes=6,min_samples_leaf=40,l2_regularization=2.0,early_stopping=False,random_state=0)
for nome,cols in conj.items():
    cols=[c for c in dict.fromkeys(cols) if c in T and c in G]
    cvp=np.zeros(len(T))
    for a,b in GroupKFold(5).split(T,groups=T.mid): cvp[b]=h2().fit(T.iloc[a][cols],T.iloc[a].sobra).predict(T.iloc[b][cols])
    mm=h2().fit(T[cols],T.sobra); gp=G.m+mm.predict(G[cols]); txt=f'{nome:42s} | '+res('histórico (validação cruzada)',T.m+cvp-T.u)+' || '+res('2026/27',gp-G.u)
    print(txt)
    if nome.startswith('4'):
        G['aj']=gp; print('   2026/27 por liga:',{l:f'{((g.aj-g.u).abs()>.5).mean():.1%} (antes {((g.m-g.u).abs()>.5).mean():.1%})' for l,g in G.groupby('liga')}); print('   por faixa do modelo:',{str(k):f'{((g.aj-g.u).abs()>.5).mean():.1%} (antes {((g.m-g.u).abs()>.5).mean():.1%}, n={len(g)})' for k,g in G.groupby(pd.cut(G.m,[0,1,2,10]),observed=True)})
        from sklearn.inspection import permutation_importance
        pi=permutation_importance(mm,T[cols],T.sobra,n_repeats=3,random_state=0); print('   variáveis que mais pesam:',[(cols[i],round(pi.importances_mean[i],4)) for i in np.argsort(-pi.importances_mean)[:12]])
