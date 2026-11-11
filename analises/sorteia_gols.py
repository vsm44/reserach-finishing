import sys, json, glob, gzip, numpy as np, pandas as pd
S,OUT=sys.argv[1:3]
def marca(d):
    casa=d['general']['homeTeam']['id']; sh=[s for s in (d['content'].get('shotmap') or {}).get('shots') or [] if not s['isOwnGoal']]
    r=pd.DataFrame([dict(fid=s['id'],lado='h' if s['teamId']==casa else 'a',jog=s['playerId'],nome=s.get('fullName') or s.get('playerName'),minuto=s['min'],acr=s.get('minAdded') or 0,lance=s['situation'],gol=int(s['eventType']=='Goal'),xg_opta=s.get('expectedGoals') or 0.0) for s in sh]); r['big']=0
    perd={}
    for pl in (d['content'].get('playerStats') or {}).values():
        bc=pm=0
        for grp in pl.get('stats') or []:
            for v in (grp.get('stats') or {}).values():
                if v.get('key')=='big_chance_missed_title': bc=(v.get('stat') or {}).get('value') or 0
                elif v.get('key')=='missed_penalty': pm=(v.get('stat') or {}).get('value') or 0
        perd[pl['id']]=max(bc-pm,0)
    tot={s['key']:s['stats'] for grp in d['content']['stats']['Periods']['All']['stats'] for s in grp['stats'] if s.get('key') in ('big_chance','big_chance_missed_title') and len(s['stats'])==2 and s['stats'][0] is not None}
    np_=r[r.lance!='Penalty']
    for jog,kk in perd.items(): r.loc[np_[(np_.jog==jog)&(np_.gol==0)].sort_values('xg_opta',ascending=False).index[:int(kk)],'big']=1
    for i,lado in enumerate(('h','a')):
        conv=(tot.get('big_chance',[0,0])[i] or 0)-(tot.get('big_chance_missed_title',[0,0])[i] or 0)-int(((r.lado==lado)&(r.lance=='Penalty')&(r.gol==1)).sum())
        r.loc[np_[(np_.lado==lado)&(np_.gol==1)].sort_values('xg_opta',ascending=False).index[:max(int(conv),0)],'big']=1
    return r
L=[]
for f in glob.glob(S+'/fotmob/2025/[0-9]*.json.gz'):
    d=json.load(gzip.open(f)); dia=d['general']['matchTimeUTCDate'][:10]
    if dia<'2026-03-01': continue
    h=d['header']['teams']; r=marca(d); g=r[(r.gol==1)&(r.lance!='Penalty')&(r.big==1)]
    for x in g.itertuples(): L.append(dict(match_id=d['general']['matchId'],fid=x.fid,data=dia,jogo=f"{h[0]['name']} {h[0]['score']} x {h[1]['score']} {h[1]['name']}",minuto=f"{x.minuto}'" if not x.acr else f"{x.minuto}+{int(x.acr)}'",time=h[0]['name'] if x.lado=='h' else h[1]['name'],jogador=x.nome))
t=pd.DataFrame(L).sort_values(['data','match_id','fid']).reset_index(drop=True); print('gols de grande chance (sem pênalti) na La Liga, de 01/03 a 24/05/2026:',len(t),'| jogos',t.match_id.nunique())
a=t.sample(20,random_state=20261111).sort_values(['data','match_id','fid']).reset_index(drop=True); a.insert(0,'n',range(1,21))
a[['n','match_id','fid']].to_csv(OUT+'/teste_palpites_chave.csv',index=False)
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
wb=openpyxl.Workbook(); ws=wb.active; ws.title='Palpites'
cab=['Nº','Data','Jogo','Minuto','Time que marcou','Jogador','Sua avaliação (%)','Observações']; ws.append(cab)
for r in a.itertuples(): ws.append([r.n,pd.Timestamp(r.data).strftime('%d/%m/%Y'),r.jogo,r.minuto,r.time,r.jogador,None,None])
for c,w in zip('ABCDEFGH',(5,12,44,9,22,26,18,50)): ws.column_dimensions[c].width=w
fino=Side(style='thin',color='BBBBBB')
for i,row in enumerate(ws.iter_rows(min_row=1,max_row=21),1):
    for cell in row:
        cell.border=Border(top=fino,bottom=fino,left=fino,right=fino); cell.alignment=Alignment(vertical='center',wrap_text=True,horizontal='center' if cell.column in (1,2,4,7) else 'left')
        if i==1: cell.font=Font(bold=True); cell.fill=PatternFill('solid',fgColor='E8E8E8')
        elif cell.column==7: cell.fill=PatternFill('solid',fgColor='FFF7D6')
ws.freeze_panes='A2'
ws2=wb.create_sheet('Como preencher')
for l in ['Teste cego da sua avaliação — 20 gols da La Liga, de março a maio de 2026.','','São gols de grande chance, sorteados (não escolhidos). Nenhum número de xG aparece aqui de propósito.','','Para cada gol, assista ao lance e escreva na coluna amarela a chance de gol que você daria,','em porcentagem, de 0 a 100. Exemplo: 35.','','Avalie o lance no instante da finalização, como se não soubesse que entrou.','Use a coluna Observações para o que achar relevante (goleiro batido, ângulo, marcação, pé ruim).','','O minuto é o do relógio do jogo. Se não achar um lance, deixe em branco.','Não consulte o xG de nenhuma fonte antes de preencher.']: ws2.append([l])
ws2.column_dimensions['A'].width=100
wb.save(OUT+'/teste_palpites_20_gols.xlsx'); print(a[['n','data','jogo','minuto','time','jogador']].to_string(index=False))
