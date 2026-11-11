import zipfile, xml.etree.ElementTree as ET
N={'t':'urn:oasis:names:tc:opendocument:xmlns:table:1.0','o':'urn:oasis:names:tc:opendocument:xmlns:office:1.0','x':'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}
def le(caminho):
    r=ET.fromstring(zipfile.ZipFile(caminho).read('content.xml')); out={}
    for tab in r.iter('{%s}table'%N['t']):
        linhas=[]
        for row in tab.iter('{%s}table-row'%N['t']):
            rep_l=int(row.get('{%s}number-rows-repeated'%N['t'],1)); cel=[]
            for c in row:
                if not c.tag.endswith('table-cell') and not c.tag.endswith('covered-table-cell'): continue
                rep=int(c.get('{%s}number-columns-repeated'%N['t'],1)); tp=c.get('{%s}value-type'%N['o'])
                if tp in ('float','percentage','currency'): v=float(c.get('{%s}value'%N['o']))
                elif tp=='date': v=c.get('{%s}date-value'%N['o'])
                else: v=' '.join(''.join(p.itertext()) for p in c.iter('{%s}p'%N['x'])) or None
                cel+= [v]*min(rep,60)
            while cel and cel[-1] is None: cel.pop()
            if cel: linhas+=[cel]*min(rep_l,3)
        out[tab.get('{%s}name'%N['t'])]=linhas
    return out
