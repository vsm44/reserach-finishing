# reproduz a V7 antiga (treino na OUTRA liga) para um jogo: v7_jogo.py S liga match_id saida.pkl
import sys, pandas as pd, numpy as np
S,LIGA,MID,OUT=sys.argv[1:5]; sys.path.insert(0,S+'/novos')
import treina_avalia as t
OUTRA={'La_liga':'Serie_A','Serie_A':'La_liga'}[LIGA]
c=pd.read_pickle(S+'/dados/dados/variaveis.pkl')
base=c[(c.liga==OUTRA)&(c.lance!='Penalty')].dropna(subset=['xg_understat'])
pen=c[(c.liga==OUTRA)&(c.lance=='Penalty')].xg_understat.median()
m=t.treina(base,t.V7); g=c[c.u_match==MID].copy(); g['v7']=t.preve(m,g,t.V7,pen)
p=pd.read_pickle(S+'/dados/dados/chutes_pareados.pkl')[['f_arq','f_id','u_id']]
g=g.merge(p,on=['f_arq','f_id'],how='left')
print('finalizações no legado:',len(g),'| sem par na Understat:',g.u_id.isna().sum())
print(g.groupby('h_a').agg(n=('v7','size'),v7=('v7','sum'),understat=('xg_understat','sum'),opta=('xg_opta','sum')).round(3).to_string())
g[['u_id','f_id','h_a','v7','xg_understat','xg_opta','xgot','grande_chance','gc_marcada','minuto','lance','parte','gol']].to_pickle(OUT)
