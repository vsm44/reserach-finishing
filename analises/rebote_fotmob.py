import sys, numpy as np, pandas as pd
S=sys.argv[1]; PENL={'La_liga':0.7433,'Serie_A':0.7613}
x=pd.read_pickle(S+'/work/disseca.pkl').sort_values(['f_arq','mandante','minuto','f_id']).reset_index(drop=True)
x['real']=(x.u_lastAction=='Rebound').astype(int); g=x.groupby(['f_arq','mandante'])
dm=x.minuto-g.minuto.shift(); ant_def=((g.no_alvo.shift()==1)|(g.bloqueado.shift()==1)|(g.trave.shift()==1))&(g.gol.shift()==0); ant_qualquer=g.gol.shift()==0
regras={'mesmo minuto, anterior defendida/bloqueada/trave':(dm==0)&ant_def,'até 1 minuto, anterior defendida/bloqueada/trave':(dm<=1)&ant_def,'mesmo minuto, anterior qualquer (sem gol)':(dm==0)&ant_qualquer,
        'mesmo minuto + mais perto do gol que a anterior':(dm==0)&ant_def&(x.x>=g.x.shift()-2)}
c0=pd.read_pickle(S+'/dados/dados/variaveis.pkl'); pen=c0[c0.lance=='Penalty'].assign(p=lambda d:d.liga.map(PENL)).groupby(['f_arq','mandante']).p.sum()
uj=pd.read_pickle(S+'/work/u_jogos.pkl').set_index('match_id'); jm=x.groupby('f_arq').u_match.first()
def mede(nome,reb):
    t=x.assign(r=reb.astype(int)); t['g']=(t.r==0).groupby([t.f_arq,t.mandante]).cumsum()
    s=t.groupby(['f_arq','mandante','g']).p.apply(lambda v:1-np.prod(1-v.values)).groupby(level=[0,1]).sum(); s=s.add(pen.reindex(s.index).fillna(0))
    j=s.rename('m').reset_index(); j['u']=[float(uj.loc[jm[a]].xg_h if md==1 else uj.loc[jm[a]].xg_a) for a,md in zip(j.f_arq,j.mandante)]; e=j.m-j.u; a_=e.abs()
    print(f'{nome:52s} erro médio {a_.mean():.4f} | mediano {a_.median():.3f} | acima de 0,30: {(a_>.3).mean():.1%} | acima de 0,50: {(a_>.5).mean():.1%} | desvio {e.mean():+.4f}')
print('rebotes segundo a Understat:',int(x.real.sum()),'de',len(x))
mede('sem unir (soma simples)',pd.Series(False,index=x.index))
for nome,r in regras.items():
    r=r.fillna(False); tp=int((r&(x.real==1)).sum()); print(f'  regra [{nome}]: aponta {int(r.sum())} | acerta {tp} ({tp/max(r.sum(),1):.0%} dos apontados) | cobre {tp/x.real.sum():.0%} dos rebotes da Understat')
    mede('  unindo por essa regra',r)
mede('unindo pelos rebotes da Understat (referência)',x.real==1)
