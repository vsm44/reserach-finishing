import sys, pandas as pd, numpy as np
S=sys.argv[1]; sys.path.insert(0,S+'/novos'); import treina_avalia as t
c=pd.read_pickle(S+'/dados/dados/variaveis.pkl').dropna(subset=['xg_understat']); c=c[c.lance!='Penalty']
vers={'V0 posição, parte, situação':t.V0,'V2 + placar, minuto, jogador, histórico dos times':t.V2,'V3 + resultado (no alvo, bloqueada, trave, gol)':t.V3,'V4 + ponto no gol e estatísticas do jogo':t.V4,'V5 + grande chance (por jogador)':t.V5,'V7 + grande chance marcada por finalização':t.V7,
      'V7 sem resultado nem ponto no gol':[v for v in t.V7 if v not in ('no_alvo','bloqueado','trave','gol','gol_y','gol_z')],
      'só V0 + grande chance marcada':t.V0+['gc_marcada','grande_chance'],'V0 + xG da Opta':t.V0+['xg_opta']}
print('finalizações:',len(c),'| xG Understat médio',round(c.xg_understat.mean(),4))
for nome,cols in vers.items():
    partes=[]
    for a,b in (('La_liga','Serie_A'),('Serie_A','La_liga')):
        m=t.treina(c[c.liga==a],cols); te=c[c.liga==b].copy(); te['p']=np.clip(m.predict(t.codifica(te,cols)),0.001,0.99); partes.append(te)
    x=pd.concat(partes); e=(x.p-x.xg_understat).abs(); j=x.groupby(['f_arq','time']).agg(u=('xg_understat','sum'),m=('p','sum')); ej=(j.m-j.u).abs()
    print(f'{nome:52s} finalização: erro médio {e.mean():.4f} | acima de 0,10: {(e>.1).mean():.1%} || time-jogo: médio {ej.mean():.3f} | mediano {ej.median():.3f} | acima de 0,50: {(ej>.5).mean():.1%} || viés nos gols {(x.p-x.xg_understat)[x.gol==1].mean():+.3f}')
