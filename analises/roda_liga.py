# roda o modelo em todos os jogos de uma pasta da FotMob e grava as previsões: roda_liga.py S pasta liga saida.csv
import sys, glob, pickle, pandas as pd
S,PASTA,LIGA,OUT=sys.argv[1:5]; sys.path.insert(0,S+'/ferramenta'); import modelo_fotmob as M
mod=pickle.load(open(S+'/ferramenta/modelo_fotmob.pkl','rb')); L=[]
for f in sorted(glob.glob(f'{S}/{PASTA}/[0-9]*.json.gz')):
    l,_=M.jogo(mod,M.le(f),LIGA); L.append(l)
r=pd.DataFrame(L).sort_values(['data','id']); r.round(3).to_csv(OUT,index=False); print(LIGA,'| jogos',len(r),'| de',r.data.min(),'a',r.data.max(),'| gravado em',OUT)
