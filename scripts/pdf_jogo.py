"""Gera o PDF de análise de um jogo a partir do bruto da Understat.

Lê direto de data/understat/<liga>.tar.xz. Uso, da raiz do repositório:
  python scripts/pdf_jogo.py <liga> <ano> <match_id> <saida.pdf> [v7.pkl]
Exemplo:
  python scripts/pdf_jogo.py Serie_A 2021 16977 empoli_roma.pdf

O último argumento é opcional: uma tabela (pickle do pandas) com as colunas u_id e v7,
para mostrar ao lado o valor por finalização do modelo antigo (legado).
Precisa de pandas, numpy e matplotlib.
"""
import sys, os, io, gzip, json, tarfile, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Arc
LIGA,ANO,MID,OUT=sys.argv[1:5]
FONTE='/usr/share/fonts/opentype/inter/Inter-%s.otf'
if os.path.exists(FONTE%'Regular'):
    for w in ('Regular','Medium','SemiBold','Bold'): fm.fontManager.addfont(FONTE%w)
    plt.rcParams['font.family']='Inter'
plt.rcParams['font.size']=8
BG='#fcfcfb'; TX='#0b0b0b'; T2='#52514e'; T3='#8a8983'; GR='#e4e3de'; CH='#2a78d6'; CA='#eb6834'; HL='#fdf1d6'
RES={'Goal':'gol','SavedShot':'defendida','MissedShots':'para fora','BlockedShot':'bloqueada','ShotOnPost':'trave','OwnGoal':'gol contra'}
SIT={'OpenPlay':'jogada','FromCorner':'escanteio','SetPiece':'bola parada','DirectFreekick':'falta direta','Penalty':'pênalti'}
COR={'RightFoot':'pé direito','LeftFoot':'pé esquerdo','Head':'cabeça','OtherBodyPart':'outra parte'}
def le_bruto(nomes):
    # devolve o conteúdo dos arquivos pedidos de dentro do .tar.xz da liga
    achados={}
    with tarfile.open(f'data/understat/{LIGA}.tar.xz') as tar:
        for mb in tar:
            for nome in nomes:
                if mb.name.endswith(f'{LIGA}/{ANO}/{nome}.json.gz'):
                    achados[nome]=json.load(gzip.open(io.BytesIO(tar.extractfile(mb).read())))
            if len(achados)==len(nomes): break
    faltam=[x for x in nomes if x not in achados]
    if faltam: sys.exit(f'não encontrado em data/understat/{LIGA}.tar.xz: {faltam}')
    return achados
bruto=le_bruto([MID,'liga']); m,lg=bruto[MID],bruto['liga']
d=[x for x in lg['dates'] if x['id']==MID][0]
H,A=d['h']['title'],d['a']['title']; data=d['datetime']
hist={}
for lado,tid in (('h',d['h']['id']),('a',d['a']['id'])):
    hist[lado]=[x for x in lg['teams'][tid]['history'] if x['date']==data][0]
sh=pd.DataFrame(m['shots']['h']+m['shots']['a'])
for c in ('xG','X','Y'): sh[c]=sh[c].astype(float)
sh['minute']=sh.minute.astype(int); sh['idn']=sh.id.astype(int); sh=sh.sort_values('idn').reset_index(drop=True)
v7=pd.read_pickle(sys.argv[5]) if len(sys.argv)>5 else None
if v7 is not None: sh=sh.merge(v7[['u_id','v7','xg_opta']].rename(columns={'u_id':'id'}),on='id',how='left')
else: sh['v7']=np.nan
# grupos de rebote
sh['grp']=0
for lado in ('h','a'):
    k=sh.h_a==lado; sh.loc[k,'grp']=(sh[k].lastAction!='Rebound').cumsum()
def xg_time(x): return x.groupby('grp').xG.apply(lambda v:1-np.prod(1-v.values)).sum()
NOME={'h':H,'a':A}; COL={'h':CH,'a':CA}
dt=pd.Timestamp(data); DATA=dt.strftime('%d/%m/%Y')+f' · {dt.strftime("%H:%M")} UTC'
TIT=f'{H} {d["goals"]["h"]} × {d["goals"]["a"]} {A}'
pdf=PdfPages(OUT); npg=[0]
def pagina(sub):
    f=plt.figure(figsize=(11.69,8.27),facecolor=BG); npg[0]+=1
    f.text(0.04,0.945,TIT,fontsize=17,fontweight='bold',color=TX); f.text(0.04,0.915,sub,fontsize=10,color=T2)
    f.text(0.96,0.95,f'{LIGA.replace("_"," ")} {ANO}/{int(ANO)%100+1} · {DATA}',fontsize=8.5,color=T2,ha='right')
    f.text(0.96,0.928,f'Understat match {MID}',fontsize=8,color=T3,ha='right')
    f.add_artist(plt.Line2D([0.04,0.96],[0.9,0.9],color=GR,lw=0.8))
    f.text(0.04,0.025,'Fonte: bruto da Understat (data/understat). Rótulos de situação, resultado e parte do corpo traduzidos; "última ação" mantida como no original.',fontsize=6.5,color=T3)
    f.text(0.96,0.025,str(npg[0]),fontsize=7,color=T3,ha='right'); return f
def fim(f): pdf.savefig(f,facecolor=BG); plt.close(f)
def tabela(f,x0,y0,cols,rows,lh=0.0235,fs=8,hl=None,cores=None):
    # cols: (titulo, largura, alinhamento)
    xs=[x0]; 
    for c in cols: xs.append(xs[-1]+c[1])
    for i,c in enumerate(cols):
        xx=xs[i]+0.004 if c[2]=='l' else xs[i+1]-0.004
        f.text(xx,y0,c[0],fontsize=fs-0.8,color=T3,ha='left' if c[2]=='l' else 'right',fontweight='medium')
    f.add_artist(plt.Line2D([x0,xs[-1]],[y0-0.007,y0-0.007],color=GR,lw=0.8))
    for r,row in enumerate(rows):
        y=y0-(r+1)*lh
        if hl and hl[r]: f.add_artist(Rectangle((x0,y-0.006),xs[-1]-x0,lh,color=HL,lw=0,transform=f.transFigure,zorder=0))
        if cores and cores[r]: f.add_artist(Rectangle((x0-0.006,y-0.006),0.003,lh,color=cores[r],lw=0,transform=f.transFigure))
        for i,c in enumerate(cols):
            xx=xs[i]+0.004 if c[2]=='l' else xs[i+1]-0.004
            v=row[i]; bold=isinstance(v,tuple); v=v[0] if bold else v
            f.text(xx,y,v,fontsize=fs,color=TX,ha='left' if c[2]=='l' else 'right',fontweight='bold' if bold else 'normal')
    return y0-(len(rows)+1)*lh
n=lambda v,k=2: ('{:.%df}'%k).format(v).replace('.',',')
# ---------- página 1: resumo
f=pagina('Resumo do jogo · indicadores da Understat por time')
def conta(lado,cond): return int(cond(sh[sh.h_a==lado]).sum())
linhas=[]
def L(nome,fh,fa): linhas.append((nome,fh,fa))
hh,ha=hist['h'],hist['a']
L('Gols',(str(d['goals']['h']),),(str(d['goals']['a']),))
L('xG (publicado)',(n(float(d['xG']['h'])),),(n(float(d['xG']['a'])),))
L('xGA',n(hh['xGA']),n(ha['xGA'])); L('npxG (sem pênaltis)',n(hh['npxG']),n(ha['npxG'])); L('npxGA',n(hh['npxGA']),n(ha['npxGA']))
L('xPTS (pontos esperados)',n(hh['xpts']),n(ha['xpts']))
fc=d['forecast']; L('Previsão Understat: vitória',n(float(fc['w'])*100,1)+'%',n(float(fc['l'])*100,1)+'%'); L('Previsão Understat: empate',n(float(fc['d'])*100,1)+'%',n(float(fc['d'])*100,1)+'%')
L('PPDA',n(hh['ppda']['att']/max(hh['ppda']['def'],1)),n(ha['ppda']['att']/max(ha['ppda']['def'],1)))
L('   passes do adversário / ações defensivas',f"{hh['ppda']['att']} / {hh['ppda']['def']}",f"{ha['ppda']['att']} / {ha['ppda']['def']}")
L('PPDA sofrido',n(hh['ppda_allowed']['att']/max(hh['ppda_allowed']['def'],1)),n(ha['ppda_allowed']['att']/max(ha['ppda_allowed']['def'],1)))
L('Deep',str(hh['deep']),str(ha['deep'])); L('Deep sofrido',str(hh['deep_allowed']),str(ha['deep_allowed']))
L('Finalizações',str(conta('h',lambda x:x.result!='OwnGoal')),str(conta('a',lambda x:x.result!='OwnGoal')))
L('   no alvo (gol + defendida)',str(conta('h',lambda x:x.result.isin(['Goal','SavedShot']))),str(conta('a',lambda x:x.result.isin(['Goal','SavedShot']))))
for k,v in (('SavedShot','defendidas'),('MissedShots','para fora'),('BlockedShot','bloqueadas'),('ShotOnPost','na trave')):
    L('   '+v,str(conta('h',lambda x:x.result==k)),str(conta('a',lambda x:x.result==k)))
L('   de cabeça',str(conta('h',lambda x:x.shotType=='Head')),str(conta('a',lambda x:x.shotType=='Head')))
L('   de escanteio / bola parada',str(conta('h',lambda x:x.situation.isin(['FromCorner','SetPiece','DirectFreekick']))),str(conta('a',lambda x:x.situation.isin(['FromCorner','SetPiece','DirectFreekick']))))
L('   marcadas como rebote',str(conta('h',lambda x:x.lastAction=='Rebound')),str(conta('a',lambda x:x.lastAction=='Rebound')))
tabela(f,0.04,0.86,[('Indicador',0.27,'l'),(H,0.09,'r'),(A,0.09,'r')],linhas,lh=0.0335,fs=9)
f.add_artist(Rectangle((0.326,0.872),0.012,0.012,color=CH,lw=0,transform=f.transFigure)); f.add_artist(Rectangle((0.416,0.872),0.012,0.012,color=CA,lw=0,transform=f.transFigure))
# bloco direito: soma x publicado x V7
f.text(0.56,0.86,'xG do time: três contas',fontsize=11,fontweight='bold',color=TX)
rows=[]
for lado in ('h','a'):
    x=sh[(sh.h_a==lado)&(sh.result!='OwnGoal')]
    rows.append((NOME[lado],n(x.xG.sum(),3),n(xg_time(x),3),n(float(d['xG'][lado]),3),n(x.v7.sum(),3) if x.v7.notna().all() else '—',('{:+.3f}'.format(x.v7.sum()-float(d['xG'][lado])).replace('.',','),) if x.v7.notna().all() else '—'))
tabela(f,0.56,0.82,[('Time',0.08,'l'),('Soma das\nfinalizações',0.07,'r'),('Com rebotes\nunidos',0.07,'r'),('Publicado\nUnderstat',0.07,'r'),('Modelo\nantigo (V7)',0.07,'r'),('V7 −\npublicado',0.06,'r')],rows,lh=0.034,fs=9,cores=[CH,CA])
f.text(0.56,0.69,'Soma das finalizações: soma simples do xG de cada finalização.\nCom rebotes unidos: finalização com última ação "Rebound" unida à anterior\ndo mesmo time por 1 − (1−a)×(1−b), depois soma.\nModelo antigo (V7): valores reproduzidos nesta sessão com o script e os dados\ndo legado (treino só na La Liga); servem de registro do que tínhamos.',fontsize=7.6,color=T2,va='top',linespacing=1.5)
f.text(0.56,0.52,'O que cada indicador é (definições divulgadas pela Understat)',fontsize=11,fontweight='bold',color=TX)
f.text(0.56,0.495,'xG · gols esperados; xGA · xG sofrido (o xG do adversário neste jogo).\nnpxG · xG sem os pênaltis.\nxPTS · pontos esperados a partir do xG das finalizações do jogo.\nPPDA · passes permitidos ao adversário por ação defensiva, no campo de ataque.\n   Quanto menor, mais intensa a pressão. "Sofrido" é o mesmo índice visto pelo adversário.\nDeep · passes completados perto do gol adversário (cerca de 20 jardas), sem cruzamentos.\nxGChain · xG de todas as posses em que o jogador participou.\nxGBuildup · o mesmo, sem contar finalizações e passes para finalização.',fontsize=7.6,color=T2,va='top',linespacing=1.55)
fim(f)
# ---------- página 2: mapas
f=pagina('Mapa das finalizações · posição registrada pela Understat · cada time atacando para a direita')
def campo(ax):
    ax.set_xlim(50,106.5); ax.set_ylim(-1,69); ax.set_aspect('equal'); ax.axis('off')
    k=dict(color='#b9b8b2',lw=0.9,fill=False)
    ax.add_patch(Rectangle((52.5,0),52.5,68,**k)); ax.add_patch(Rectangle((88.5,13.84),16.5,40.32,**k)); ax.add_patch(Rectangle((99.5,24.84),5.5,18.32,**k))
    ax.add_patch(Rectangle((105,30.34),1.2,7.32,**k)); ax.add_patch(Arc((94,34),18.3,18.3,theta1=127,theta2=233,color='#b9b8b2',lw=0.9)); ax.add_patch(Arc((52.5,34),18.3,18.3,theta1=-90,theta2=90,color='#b9b8b2',lw=0.9))
    ax.plot([94],[34],'o',ms=1.5,color='#b9b8b2')
for i,lado in enumerate(('h','a')):
    ax=f.add_axes([0.03+0.48*i,0.13,0.46,0.72]); campo(ax); x=sh[(sh.h_a==lado)&(sh.result!='OwnGoal')]
    ax.set_title(f'{NOME[lado]} · {len(x)} finalizações · xG {n(float(d["xG"][lado]))}',fontsize=11,fontweight='bold',color=TX,loc='left',pad=4)
    for r in x.sort_values('xG',ascending=False).itertuples():
        gol=r.result=='Goal'; px,py=r.X*105,(1-r.Y)*68
        ax.scatter(px,py,s=40+r.xG*1500,facecolor=COL[lado] if gol else 'none',edgecolor=COL[lado],lw=1.6,alpha=0.95 if gol else 0.9,zorder=3)
        ax.text(px,py+1.2+np.sqrt(40+r.xG*1500)/9,f"{r.minute}'",fontsize=6.3,color=T2,ha='center',zorder=4)
f.text(0.04,0.085,'Círculo cheio: gol. Círculo vazado: não gol. Área do círculo proporcional ao xG da Understat. O número é o minuto.',fontsize=8,color=T2)
f.text(0.04,0.062,'Coordenada crua: X = 1 é a linha do gol adversário; Y vai de 0 a 1 na largura. O lado em que Y = 0 aparece no desenho é uma escolha deste relatório.',fontsize=7.2,color=T3)
fim(f)
# ---------- páginas 3-4: finalizações por time
for lado in ('h','a'):
    f=pagina(f'Finalizações de {NOME[lado]} · uma a uma, na ordem do jogo')
    x=sh[sh.h_a==lado]; rows=[];hl=[]
    tam=x.groupby('grp').size()
    for r in x.itertuples():
        dif=r.v7-r.xG if pd.notna(r.v7) else np.nan
        reb='↳ ' if r.lastAction=='Rebound' else ''
        rows.append((f"{r.minute}'",reb+r.player,SIT.get(r.situation,r.situation),COR.get(r.shotType,r.shotType),r.lastAction if r.lastAction not in (None,'None') else '—',(r.player_assisted if isinstance(r.player_assisted,str) else '—'),
            (RES.get(r.result,r.result),) if r.result=='Goal' else RES.get(r.result,r.result),n(r.X,3),n(r.Y,3),n(r.xG,3),n(r.v7,3) if pd.notna(r.v7) else '—','{:+.3f}'.format(dif).replace('.',',') if pd.notna(dif) else '—'))
        hl.append(pd.notna(dif) and abs(dif)>=0.05)
    y=tabela(f,0.04,0.86,[('Min',0.035,'r'),('Jogador',0.17,'l'),('Situação',0.085,'l'),('Parte do corpo',0.085,'l'),('Última ação',0.085,'l'),('Assistência',0.15,'l'),('Resultado',0.075,'l'),('X',0.045,'r'),('Y',0.045,'r'),('xG Understat',0.07,'r'),('V7 antigo',0.06,'r'),('V7 − U',0.055,'r')],rows,lh=0.031,fs=8.6,hl=hl)
    xx=x[x.result!='OwnGoal']
    f.text(0.04,y-0.012,f'Total · soma simples {n(xx.xG.sum(),3)} · com rebotes unidos {n(xg_time(xx),3)} · publicado {n(float(d["xG"][lado]),3)} · V7 antigo {n(xx.v7.sum(),3)}',fontsize=9,fontweight='bold',color=TX)
    f.text(0.04,y-0.04,'Fundo amarelo: diferença de 0,05 ou mais entre o V7 antigo e a Understat. "↳": finalização marcada como rebote (unida à anterior no xG do time).',fontsize=7.6,color=T2)
    fim(f)
# ---------- página 5: xG acumulado
f=pagina('xG acumulado ao longo do jogo · Understat (linha cheia) e modelo antigo V7 (tracejada)')
ax=f.add_axes([0.07,0.14,0.86,0.7],facecolor=BG)
mx=max(95,sh.minute.max()+2)
for lado in ('h','a'):
    x=sh[(sh.h_a==lado)&(sh.result!='OwnGoal')]
    ax.step([0]+list(x.minute)+[mx],[0]+list(x.xG.cumsum())+[x.xG.sum()],where='post',color=COL[lado],lw=2,label=f'{NOME[lado]} · Understat')
    if x.v7.notna().all(): ax.step([0]+list(x.minute)+[mx],[0]+list(x.v7.cumsum())+[x.v7.sum()],where='post',color=COL[lado],lw=1.6,ls=(0,(4,2)),label=f'{NOME[lado]} · V7 antigo')
    g=x[x.result=='Goal']; ax.scatter(g.minute,x.xG.cumsum()[g.index],s=55,color=COL[lado],edgecolor=BG,lw=2,zorder=5)
    ax.text(mx+0.6,x.xG.sum(),n(x.xG.sum()),fontsize=8.5,color=TX,va='center')
    if x.v7.notna().all(): ax.text(mx+0.6,x.v7.sum(),n(x.v7.sum())+' (V7)',fontsize=8.5,color=T2,va='center')
ax.axvline(45,color=GR,lw=0.8); ax.set_xlim(0,mx); ax.set_ylim(0,None); ax.set_xlabel('minuto',color=T2); ax.set_ylabel('xG acumulado (soma simples das finalizações)',color=T2)
for s in ('top','right'): ax.spines[s].set_visible(False)
for s in ('left','bottom'): ax.spines[s].set_color(GR)
ax.tick_params(colors=T2,length=0); ax.grid(axis='y',color=GR,lw=0.6); ax.set_axisbelow(True)
ax.legend(frameon=False,fontsize=8.5,loc='upper left',labelcolor=TX)
f.text(0.07,0.075,'Ponto: gol. A linha usa a soma simples; o xG publicado do time une os rebotes e pode ficar um pouco abaixo do último ponto da linha cheia.',fontsize=7.6,color=T2)
fim(f)
# ---------- página 6: jogadores
f=pagina('Jogadores · dados da Understat por jogador neste jogo')
for i,lado in enumerate(('h','a')):
    r=pd.DataFrame(m['rosters'][lado].values()); r['o']=r.positionOrder.astype(int); r=r.sort_values('o')
    ent={x['id']:x for x in r.to_dict('records')}
    rows=[]
    for p in r.itertuples():
        ct=('A' if p.yellow_card!='0' else '')+('V' if p.red_card!='0' else '')
        rows.append((p.position,p.player,p.time,p.shots,(p.goals,) if p.goals!='0' else p.goals,n(float(p.xG)),p.key_passes,p.assists,n(float(p.xA)),n(float(p.xGChain)),n(float(p.xGBuildup)),ct or '—'))
    x0=0.04+0.48*i
    f.add_artist(Rectangle((x0,0.862),0.012,0.012,color=COL[lado],lw=0,transform=f.transFigure)); f.text(x0+0.018,0.862,NOME[lado],fontsize=11,fontweight='bold',color=TX)
    tabela(f,x0,0.83,[('Pos',0.03,'l'),('Jogador',0.105,'l'),('Min',0.027,'r'),('Fin',0.025,'r'),('Gols',0.028,'r'),('xG',0.033,'r'),('PF',0.025,'r'),('Ass',0.027,'r'),('xA',0.033,'r'),('xGChain',0.04,'r'),('xGBuild',0.04,'r'),('Cart',0.028,'r')],rows,lh=0.036,fs=8)
f.text(0.04,0.075,'Pos: posição registrada pela Understat (Sub = entrou do banco). Fin: finalizações. PF: passes para finalização. Ass: assistências. Cart: A amarelo, V vermelho.',fontsize=7.6,color=T2)
fim(f); pdf.close(); print('ok',OUT,npg[0],'páginas')
