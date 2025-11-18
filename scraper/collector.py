import sys
import os

# --- CORREÇÃO DE CAMINHO (PATH HACK) ---
# Adiciona o diretório pai (PoliNoticiasPy) ao sistema de busca do Python.
# Isso permite que o script encontre o módulo 'scraper' e 'recipes' sem erros.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Importe TODAS as suas receitas aqui usando o caminho absoluto (scraper.recipes...)
# Isso evita confusão de pastas.
from scraper.recipes.cnn_brasil import coletar_cnn_brasil
from scraper.recipes.folha_sp import coletar_folha_sp
from scraper.recipes.estadao import coletar_estadao
from scraper.recipes.bbc_brasil import coletar_bbc_brasil
#from scraper.recipes.reuters import coletar_reuters
from scraper.recipes.o_globo import coletar_o_globo
from scraper.recipes.gazeta_do_povo import coletar_gazeta_do_povo
from scraper.recipes.metropoles import coletar_metropoles
from scraper.recipes.correio_braziliense import coletar_correio_braziliense
from scraper.recipes.piaui import coletar_piaui
from scraper.recipes.carta_capital import coletar_carta_capital
from scraper.recipes.veja import coletar_veja

load_dotenv() 
MONGO_URI = os.getenv("MONGO_URI")

def get_db_collection():
    if not MONGO_URI: return None
    try:
        client = MongoClient(MONGO_URI)
        db = client.polinoticias_db 
        return db.noticias_raw
    except Exception as e:
        print(f"Erro DB: {e}")
        return None

def rodar_coleta_completa():
    collection = get_db_collection()
    if collection is None: return

    # Lista completa de funções
    funcoes_coleta = [
        coletar_cnn_brasil, 
        coletar_folha_sp, 
        coletar_estadao,
        coletar_bbc_brasil,
        #coletar_reuters,
        coletar_o_globo,
        coletar_gazeta_do_povo,
        coletar_metropoles,
        coletar_correio_braziliense,
        coletar_piaui,
        coletar_carta_capital,
        coletar_veja
    ]

    todas_as_noticias = []
    
    for funcao_coleta in funcoes_coleta:
        print(f"\nIniciando coleta em: {funcao_coleta.__name__}")
        try:
            novas_noticias = funcao_coleta()
            todas_as_noticias.extend(novas_noticias)
        except Exception as e:
            print(f"❌ Erro fatal na função {funcao_coleta.__name__}: {e}")

    if todas_as_noticias:
        try:
            collection.insert_many(todas_as_noticias)
            print(f"\nSUCESSO: {len(todas_as_noticias)} documentos inseridos.")
        except Exception as e:
            print(f"❌ Erro ao salvar no MongoDB: {e}")
    else:
        print("AVISO: Nenhuma notícia nova coletada.")

if __name__ == '__main__':
    rodar_coleta_completa()