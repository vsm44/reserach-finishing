import gzip,json,glob,os,sys
import pandas as pd
R=sys.argv[1]; out=sys.argv[2]
sh=[];jg=[];bad=[]
for l in sorted(os.listdir(R)):
    for a in sorted(os.listdir(f'{R}/{l}')):
        fl=f'{R}/{l}/{a}/liga.json.gz'
        if os.path.exists(fl):
            d=json.load(gzip.open(fl))
            for j in d['dates']:
                jg.append(dict(liga=l,ano=int(a),match_id=j['id'],isResult=j['isResult'],h=j['h']['title'],a=j['a']['title'],
                    gh=j['goals']['h'],ga=j['goals']['a'],xg_h=j['xG']['h'],xg_a=j['xG']['a'],data=j['datetime']))
        for f in glob.glob(f'{R}/{l}/{a}/*.json.gz'):
            if f.endswith('liga.json.gz'): continue
            try: d=json.load(gzip.open(f))
            except Exception as e: bad.append((f,str(e)[:60])); continue
            for lado in ('h','a'):
                for i,s in enumerate(d['shots'][lado]):
                    s=dict(s); s['liga']=l; s['ano']=int(a); s['lado']=lado; s['ordem']=i; s['arq']=os.path.basename(f).split('.')[0]; sh.append(s)
s=pd.DataFrame(sh); j=pd.DataFrame(jg)
for c in ('xG','X','Y','minute'): s[c]=s[c].astype(float)
for c in ('xg_h','xg_a'): j[c]=pd.to_numeric(j[c],errors='coerce')
s.to_pickle(out+'/u_shots.pkl'); j.to_pickle(out+'/u_jogos.pkl')
print('chutes',len(s),'jogos em liga.json',len(j),'arquivos ruins',len(bad),bad[:5])
print(j.groupby(['liga','ano']).agg(jogos=('match_id','size'),com_resultado=('isResult','sum')).unstack(0).to_string())
print(s.groupby(['liga','ano']).agg(jogos=('arq','nunique')).unstack(0).to_string())
print(s.columns.tolist())
