"""Baixa os jogos encerrados de uma liga na FotMob, pelas páginas públicas do site.

Cada jogo vira um arquivo <id>.json.gz, no mesmo formato dos que estão em data/fotmob.
Jogos já baixados são pulados, então pode ser rodado de novo a cada rodada.

Uso:
  python scripts/baixa_fotmob.py <pasta_de_saida> [--liga 87] [--nome laliga] [--temporada 2026/2027] [--pausa 2]

Exemplos:
  python scripts/baixa_fotmob.py fotmob/la_liga/2026
  python scripts/baixa_fotmob.py fotmob/serie_a/2026 --liga 55 --nome serie

Só usa a biblioteca padrão do Python.
"""
import argparse, gzip, json, os, re, sys, time, urllib.parse, urllib.request

BASE = "https://www.fotmob.com"
CHAVES = ("general", "header", "nav", "ongoing", "hasPendingVAR", "content", "seo")


def pagina(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (uso pessoal; pesquisa)", "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=60) as r:
        html = r.read().decode("utf-8", "replace")
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise RuntimeError("a página não trouxe os dados esperados")
    return json.loads(m.group(1))["props"]["pageProps"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("saida")
    ap.add_argument("--liga", default="87")
    ap.add_argument("--nome", default="laliga")
    ap.add_argument("--temporada", default=None, help="ex.: 2025/2026; sem isso, a temporada atual")
    ap.add_argument("--pausa", type=float, default=2.0)
    a = ap.parse_args()
    os.makedirs(a.saida, exist_ok=True)
    url = f"{BASE}/leagues/{a.liga}/matches/{a.nome}"
    if a.temporada:
        url += "?season=" + urllib.parse.quote(a.temporada, safe="")
    liga = pagina(url)
    sel = (liga.get("details") or {}).get("selectedSeason")
    if a.temporada and sel != a.temporada:
        sys.exit(f"pedi a temporada {a.temporada}, mas o site devolveu {sel}; nada foi baixado")
    with gzip.open(os.path.join(a.saida, "liga.json.gz"), "wt", encoding="utf-8") as f:
        json.dump(liga, f)
    jogos = [j for j in liga["fixtures"]["allMatches"] if j["status"].get("finished") and not j["status"].get("cancelled")]
    faltam = [j for j in jogos if not os.path.exists(os.path.join(a.saida, f"{j['id']}.json.gz"))]
    print(f"temporada {sel}: {len(jogos)} jogos encerrados, {len(faltam)} a baixar")
    ok = erro = 0
    for n, j in enumerate(faltam, 1):
        try:
            p = pagina(f"{BASE}/match/{j['id']}")
            if str((p.get("general") or {}).get("matchId")) != str(j["id"]):
                raise RuntimeError("a página devolveu outro jogo")
            with gzip.open(os.path.join(a.saida, f"{j['id']}.json.gz"), "wt", encoding="utf-8") as f:
                json.dump({k: p.get(k) for k in CHAVES}, f)
            ok += 1
        except Exception as e:
            erro += 1
            print(f"  falhou {j['id']} ({j['home']['name']} x {j['away']['name']}): {e}")
        if n % 20 == 0:
            print(f"  {n} de {len(faltam)}")
        time.sleep(a.pausa)
    print(f"baixados {ok}, com erro {erro}")


if __name__ == "__main__":
    main()
