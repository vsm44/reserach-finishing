"""Roda o modelo só FotMob em todos os jogos de uma pasta e grava o xG e o xGA por jogo.

Uso, da raiz do repositório:
  python3 scripts/roda_modelo.py <pasta_com_os_jogos> <liga> <saida.csv>
Ligas aceitas: La_liga, Serie_A, Ligue_1, EPL, Bundesliga (definem o valor do pênalti).

Exemplo, depois de baixar a rodada:
  python3 scripts/baixa_fotmob.py fotmob/la_liga/2026
  python3 scripts/roda_modelo.py fotmob/la_liga/2026 La_liga la_liga_2026.csv

No arquivo de saída, xg_m e xg_v são o xG do mandante e do visitante; o xGA de um é o xG do outro.
"""
import glob, os, pickle, sys
import pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import modelo_fotmob as M

pasta, liga, saida = sys.argv[1:4]
if liga not in M.PENALTI:
    sys.exit(f"liga desconhecida: {liga}. Use uma de {list(M.PENALTI)}")
with open(os.path.join(AQUI, "modelo_fotmob.pkl"), "rb") as f:
    mod = pickle.load(f)
linhas = [M.jogo(mod, M.le(f), liga)[0] for f in sorted(glob.glob(os.path.join(pasta, "[0-9]*.json.gz")))]
r = pd.DataFrame(linhas).sort_values(["data", "id"])
r.round(3).to_csv(saida, index=False)
print(f"{liga}: {len(r)} jogos, de {r.data.min()} a {r.data.max()}; gravado em {saida}")
