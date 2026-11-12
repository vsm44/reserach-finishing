"""Treina o modelo só FotMob a partir da tabela de treino e grava scripts/modelo_fotmob.pkl.

Uso, da raiz do repositório:
  python3 scripts/treina_modelo.py
Precisa de pandas, numpy e scikit-learn. O arquivo .pkl gravado só abre com a mesma versão
do scikit-learn que o treinou; ao trocar de máquina, rode este script de novo.
"""
import os, pickle, sys
import pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import modelo_fotmob as M

tabela = pd.read_csv(os.path.join(AQUI, "..", "data", "treino", "treino_fotmob_2020-2025.csv.gz"), float_precision="round_trip")
mod = M.treina(tabela)
# segunda etapa: tabela por time-jogo, com o total da primeira etapa calculado fora da amostra
tabela2 = pd.read_csv(os.path.join(AQUI, "..", "data", "treino", "treino_etapa2.csv.gz"), float_precision="round_trip")
mod["etapa2"] = M.treina2(tabela2)
saida = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "modelo_fotmob.pkl")
with open(saida, "wb") as f:
    pickle.dump(mod, f)
print(f"primeira etapa: {len(tabela)} finalizações; segunda etapa: {len(tabela2)} time-jogos; gravado em {saida}")
