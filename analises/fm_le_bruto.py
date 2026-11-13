# lê o bruto do FMInside (HTML por ficha) e monta a tabela única; confere com a planilha FM23/FM26
import sys, gzip, json, glob, os, re, html, pickle, collections
S = sys.argv[1]
CLUBE = {"1099":("Milan","Serie_A"),"1135":("Inter","Serie_A"),"1139":("Juventus","Serie_A"),"1687":("Atletico Madrid","La_liga"),"1708":("Barcelona","La_liga"),"1736":("Real Madrid","La_liga")}
tx = lambda h: html.unescape(re.sub(r"<[^>]+>", "", h)).strip()
def ficha(r, cid, ed):
    b = r["blocos"]; cab, inf, atr = (b.get("cabecalho") or ""), (b.get("player_info") or ""), (b.get("atributos_papeis") or "")
    d = {"edicao": ed, "time": CLUBE[cid][0], "liga": CLUBE[cid][1], "ID FMInside": str(r["fminside_uid"]), "Nome": r.get("nome_h1")}
    m = re.search(r'player-hero-eyebrow-link"[^>]*>.*?<span>(.*?)</span>', cab, re.S); d["Clube"] = tx(m.group(1)) if m else None
    m = re.search(r"Current ability (\d+)", cab); d["CA"] = int(m.group(1)) if m else None
    for k, v in re.findall(r'<span class="key">(.*?)</span>\s*<span class="value">(.*?)</span>\s*</li>', inf, re.S):
        k = tx(k).rstrip(": ").strip()
        if k == "Positions": d["Posições"] = ", ".join(tx(x) for x in re.findall(r'<span position="[^"]*"[^>]*>(.*?)</span>', v, re.S))
        elif k == "Height": m = re.search(r"(\d+)", tx(v)); d["Altura"] = int(m.group(1)) if m else None
        elif k == "Weak foot": m = re.search(r"(\d) out of 5", v); d["Pé fraco (1–5)"] = int(m.group(1)) if m else None
        elif k == "Footedness": d["Pé"] = tx(v)
        elif k == "Age": d["Idade"] = tx(v)
    gk = (d.get("Posições") or "").strip() == "GK"; vistos = set()
    for row in atr.split("<tr data-profile-stat")[1:]:
        n = re.search(r'data-player-stat-name="([^"]+)"', row); v = re.search(r'data-profile-value="[^"]*"[^>]*>\s*(\d+)\s*<', row)
        if not n or not v: continue
        nome = html.unescape(n.group(1))
        if nome in vistos: continue
        vistos.add(nome); d[nome] = int(v.group(1))
        if gk: d["GK " + nome] = int(v.group(1))
    return d
T = []; vis = set()
for f in sorted(glob.glob(S + "/fm_bruto/*.jsonl.gz")):
    m = re.search(r"clube(\d+)_(FM\d+)", os.path.basename(f)); cid, ed = m.group(1), m.group(2)
    for x in gzip.open(f, "rt", encoding="utf-8"):
        if not x.strip(): continue
        r = json.loads(x)
        if (ed, cid, r["fminside_uid"]) in vis: continue
        vis.add((ed, cid, r["fminside_uid"])); T.append(ficha(r, cid, ed))
pickle.dump(T, open(S + "/work/fm_tabela2.pkl", "wb"))
c = collections.Counter((x["edicao"], x["time"]) for x in T); eds = sorted({k[0] for k in c})
print("fichas:", len(T)); print("time".ljust(18) + "".join(e.rjust(6) for e in eds))
for t in sorted({k[1] for k in c}): print(t.ljust(18) + "".join(str(c.get((e, t), 0)).rjust(6) for e in eds))
CH = ["Finishing","First Touch","Heading","Technique","Composure","Agility","Balance","Jumping Reach","Pace","Marking","Tackling","Anticipation","Positioning","Strength","Concentration"]
print("fichas sem CA:", sum(x.get("CA") is None for x in T), "| sem posição:", sum(not x.get("Posições") for x in T), "| de linha sem Finishing:", sum(x.get("Posições") != "GK" and x.get("Finishing") is None for x in T), "| goleiros sem Reflexes:", sum(x.get("Posições") == "GK" and x.get("GK Reflexes") is None for x in T), "| sem altura:", sum(x.get("Altura") is None for x in T))
# confere com a planilha
P = {(x["edicao"], x["time"], x["ID FMInside"]): x for x in pickle.load(open(S + "/work/fm_tabela.pkl", "rb"))}
n = dif = 0; ex = []
for x in T:
    p = P.get((x["edicao"], x["time"], x["ID FMInside"]))
    if not p: continue
    for k in ["CA", "Posições", "Clube"] + CH + ["GK Reflexes", "GK Handling", "GK Aerial Reach"]:
        a, b = x.get(k), p.get(k)
        if a is None and b is None: continue
        n += 1
        if str(a) != str(b): dif += 1; ex.append((x["Nome"], k, a, b))
print("conferência com a planilha: campos comparados", n, "| diferentes", dif, ex[:8])
