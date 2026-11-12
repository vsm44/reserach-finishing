import sys, pickle, pandas as pd
S=sys.argv[1]; sys.path.insert(0,S+'/ferramenta'); import modelo_fotmob as M
x=pd.read_pickle(S+'/work/disseca.pkl'); n25=pd.read_pickle(S+'/work/treino_2025.pkl')
tr=pd.concat([x[M.COLS+['xg_understat']],n25[M.COLS+['xg_understat']]],ignore_index=True)
mod=M.treina(tr); pickle.dump(mod,open(S+'/ferramenta/modelo_fotmob.pkl','wb')); print('treinado com',len(tr),'finalizações | categorias',mod['cats'])
