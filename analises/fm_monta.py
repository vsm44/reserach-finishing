# monta a tabela do teste FM: todas as finalizações de 3 temporadas-liga, com alvo da Understat (quando pareada) e notas do FM
import sys, warnings, glob, pickle, unicodedata, re, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
from scipy.optimize import linear_sum_assignment
S,REPO=sys.argv[1:3]; sys.path.insert(0,REPO+'/scripts'); sys.dont_write_bytecode=True; import modelo_fotmob as M
TR=str.maketrans({"ı":"i","İ":"I","ø":"o","Ø":"O","đ":"d","Đ":"D","ł":"l","Ł":"L","ß":"ss","æ":"ae"})
def norm(s):
    s=unicodedata.normalize("NFKD",str(s).translate(TR)).encode("ascii","ignore").decode().lower(); return " ".join(re.sub(r"[^a-z ]"," ",s).split())
FM=pickle.load(open(S+'/work/fm_tabela2.pkl','rb'))
SEIS={'milan':'Milan','inter':'Inter','juventus':'Juventus','atletico madrid':'Atletico Madrid','barcelona':'Barcelona','real madrid':'Real Madrid'}
ALIAS={'daniel ceballos':'dani ceballos','daniel carvajal':'dani carvajal','alex balde':'alejandro balde','francisco garcia':'fran garcia'}
ATT=['Finishing','First Touch','Heading','Technique','Composure','Agility','Balance','Jumping Reach','Pace']
DEF=['Heading','Marking','Tackling','Anticipation','Positioning','Jumping Reach','Strength']
GK=['GK Aerial Reach','GK Command of Area','GK Communication','GK Handling','GK Reflexes','Concentration','Positioning','Agility']
def ficha(ed,nome,time):
    n=ALIAS.get(norm(nome),norm(nome)); c=[x for x in FM if x['edicao']==ed]
    m={x['ID FMInside']:x for x in c if norm(x['Nome'])==n}
    if n=='koke': m={k:v for k,v in m.items() if k=='67047092'}
    if len(m)==1: return list(m.values())[0]
    if len(m)>1:
        m={k:v for k,v in m.items() if v['time']==time}
        return list(m.values())[0] if len(m)==1 else None
    tk=set(n.split()); m={x['ID FMInside']:x for x in c if x['time']==time and (tk<=set(norm(x['Nome']).split()) or set(norm(x['Nome']).split())<=tk)}
    return list(m.values())[0] if len(m)==1 else None
num=lambda v: float(v) if isinstance(v,(int,float)) else np.nan
UJ=pd.read_pickle(S+'/work/u_jogos.pkl'); US=pd.read_pickle(S+'/work/u_shots.pkl'); US=US[US.result!='OwnGoal']
def temporada(liga,ano,pasta,ed):
    uj=UJ[(UJ.liga==liga)&(UJ.ano==ano)&UJ.isResult].copy(); uj['d']=uj.data.str[:10]; uj['gh']=uj.gh.astype(int); uj['ga']=uj.ga.astype(int); us=US[(US.liga==liga)&(US.ano==ano)]
    fl=[]
    for f in glob.glob(f'{pasta}/[0-9]*.json.gz'):
        d=M.le(f); h=d['header']['teams']; fl.append((d['general']['matchTimeUTCDate'][:10],h[0].get('score'),h[1].get('score'),d['general']['homeTeam']['id'],d['general']['awayTeam']['id'],d))
    votos={}
    for j in uj.itertuples():
        c=[x for x in fl if x[0]==j.d and x[1]==j.gh and x[2]==j.ga]
        if len(c)==1:
            for a,b in ((j.h,c[0][3]),(j.a,c[0][4])): votos.setdefault(a,{}).setdefault(b,0); votos[a][b]+=1
    mapa={k:max(v,key=v.get) for k,v in votos.items()}; L=[]; J=[]; cache={}
    for j in uj.itertuples():
        c=[x for x in fl if x[3]==mapa.get(j.h) and x[4]==mapa.get(j.a) and abs((pd.Timestamp(x[0])-pd.Timestamp(j.d)).days)<=1 and x[1]==j.gh and x[2]==j.ga]
        if len(c)!=1: continue
        d=c[0][5]; mid=d['general']['matchId']; f=M.finalizacoes(d); u=us[us.arq==j.match_id]; lu=d['content'].get('lineup') or {}
        if not len(f): continue
        f['xg_understat']=np.nan
        for lado in ('h','a'):
            a=u[u.lado==lado].reset_index(drop=True); b=f[f.lado==lado]
            if len(a) and len(b):
                dm=np.abs((a.minute.values+1)[:,None]-(b.minute+b.acr).values[None,:]); di=np.hypot(a.X.values[:,None]*105-b.X.values[None,:]*105,a.Y.values[:,None]*68-b.Y.values[None,:]*68); cst=dm+di/4; cst[(dm>3)|(di>8)]=1e6
                li,co=linear_sum_assignment(cst)
                for i,k in zip(li,co):
                    if cst[i,k]<1e6 and b.lance.iloc[k]!='Penalty' and a.situation[i]!='Penalty': f.loc[b.index[k],'xg_understat']=a.xG[i]
        # notas: time de cada lado, goleiro e zagueiros titulares
        info={}
        for lado,chave in (('h','homeTeam'),('a','awayTeam')):
            t=lu.get(chave) or {}; tn=SEIS.get(norm(t.get('name'))); r={'time':tn,'elite':int(tn is not None)}
            if tn:
                fs=[]
                for p in t.get('starters') or []:
                    k=(ed,p['id'],tn)
                    if k not in cache: cache[k]=ficha(ed,p['name'],tn)
                    if cache[k]: fs.append(cache[k])
                g=[x for x in fs if str(x['Posições']).strip()=='GK']; z=[x for x in fs if 'DC' in [y.strip() for y in str(x['Posições']).split(',')]]
                if g:
                    r['gk_CA']=num(g[0]['CA'])
                    for a_ in GK: r['gk_'+a_]=num(g[0][a_])
                if z:
                    r['def_CA']=np.nanmean([num(x['CA']) for x in z]); r['def_n']=len(z)
                    for a_ in DEF: r['def_'+a_]=np.nanmean([num(x[a_]) for x in z])
            info[lado]=r
        for i in f.index:
            lado=f.at[i,'lado']; eu,adv=info[lado],info['a' if lado=='h' else 'h']
            f.at[i,'time']=eu['time'] or ''; f.at[i,'att_elite']=eu['elite']; f.at[i,'def_elite']=adv['elite']
            for k,v in adv.items():
                if k.startswith('gk_') or k.startswith('def_') and k!='def_elite': f.at[i,k]=v
            if eu['time']:
                k=(ed,f.at[i,'jog'],eu['time'])
                if k not in cache: cache[k]=ficha(ed,f.at[i,'jogador'],eu['time'])
                x=cache[k]
                if x and str(x['Posições']).strip()!='GK':
                    f.at[i,'att_CA']=num(x['CA']); f.at[i,'att_pos']=str(x['Posições'])
                    for a_ in ATT: f.at[i,'att_'+a_]=num(x[a_])
        f['mid']=mid; f['liga']=liga; f['season']=ano; L.append(f)
        for lado,uu,i in (('h',j.xg_h,0),('a',j.xg_a,1)): J.append(dict(liga=liga,season=ano,mid=mid,lado=lado,u=float(uu),time=info[lado]['time'] or '',adv=info['a' if lado=='h' else 'h']['time'] or ''))
    t=pd.concat(L,ignore_index=True); print(f'{liga} {ano} ({ed}): jogos {t.mid.nunique()} | finalizações {len(t)} | pareadas {t.xg_understat.notna().sum()} | com nota do finalizador {t.att_CA.notna().sum()} | com nota do goleiro {t.gk_CA.notna().sum()} | com nota dos zagueiros {t.def_CA.notna().sum()} | as três {(t.att_CA.notna()&t.gk_CA.notna()&t.def_CA.notna()).sum()}')
    return t,pd.DataFrame(J)
R=[temporada('La_liga',2021,S+'/fotmob/2021','FM22'),temporada('La_liga',2022,S+'/fotmob/2022','FM23'),temporada('La_liga',2023,S+'/fotmob/2023','FM24'),temporada('La_liga',2025,S+'/fotmob/2025','FM26'),temporada('Serie_A',2025,S+'/hist/seriea_2025','FM26')]
T=pd.concat([r[0] for r in R],ignore_index=True); J=pd.concat([r[1] for r in R],ignore_index=True); J['u']=np.where(J.u>8,J.u/1000,J.u)
T.to_pickle(S+'/work/fm_fin.pkl'); J.to_pickle(S+'/work/fm_jogos.pkl')
print('total',len(T),'| time-jogos',len(J),'| de elite atacando',(J.time!='').sum(),'| defendendo',(J.adv!='').sum())
print('zagueiros titulares com ficha por jogo:',dict(T.drop_duplicates(['mid','lado']).def_n.value_counts(dropna=False)))
print('posições dos finalizadores com nota (finalizações):',dict(T.att_pos.str.contains('ST').value_counts()))
