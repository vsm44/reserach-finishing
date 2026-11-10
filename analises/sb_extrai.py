# lê um arquivo de eventos da StatsBomb (stdin) e grava só as finalizações, com contexto mínimo
import sys, json
mid,out=sys.argv[1],sys.argv[2]
e=json.load(sys.stdin); r=[]
byid={x['id']:x for x in e}
for i,x in enumerate(e):
    if x['type']['name']!='Shot': continue
    s=x['shot']; kp=byid.get(s.get('key_pass_id'))
    # eventos anteriores da mesma posse (até 6), só tipo e time
    ant=[(y['type']['name'],y['team']['name']==x['team']['name'],y.get('dribble',{}).get('outcome',{}).get('name'),y.get('position',{}).get('name')) for y in e[max(0,i-8):i] if y['possession']==x['possession']][-6:]
    r.append(dict(match_id=mid,id=x['id'],period=x['period'],minute=x['minute'],second=x['second'],team=x['team']['name'],player=x['player']['name'],
        x=x['location'][0],y=x['location'][1],play_pattern=x['play_pattern']['name'],under_pressure=bool(x.get('under_pressure')),
        xg_sb=s['statsbomb_xg'],outcome=s['outcome']['name'],body=s['body_part']['name'],tipo=s['type']['name'],technique=s['technique']['name'],
        first_time=bool(s.get('first_time')),one_on_one=bool(s.get('one_on_one')),open_goal=bool(s.get('open_goal')),aerial_won=bool(s.get('aerial_won')),
        deflected=bool(s.get('deflected')),redirect=bool(s.get('redirect')),follows_dribble=bool(s.get('follows_dribble')),
        end=s.get('end_location'),kp_tipo=(kp or {}).get('pass',{}).get('height',{}).get('name'),kp_cross=bool((kp or {}).get('pass',{}).get('cross')),
        kp_through=bool((kp or {}).get('pass',{}).get('through_ball') or (kp or {}).get('pass',{}).get('technique',{}).get('name')=='Through Ball'),kp_cutback=bool((kp or {}).get('pass',{}).get('cut_back')),
        ant=ant,ff=[(p['location'][0],p['location'][1],p['teammate'],p['position']['name']=='Goalkeeper') for p in s.get('freeze_frame') or []]))
json.dump(r,open(out,'w'))
