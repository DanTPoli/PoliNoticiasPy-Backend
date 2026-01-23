import sys
import os

# --- CORREÇÃO DE CAMINHO (PATH HACK) ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Importe TODAS as suas receitas aqui...
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
from scraper.recipes.infomoney import coletar_infomoney
from scraper.recipes.uol import coletar_uol
from scraper.recipes.revista_oeste import coletar_revista_oeste
from scraper.recipes.forbes_brasil import coletar_forbes_brasil
from scraper.recipes.brasil_paralelo import coletar_brasil_paralelo
from scraper.recipes.jovem_pan import coletar_jovem_pan
from scraper.recipes.agencia_brasil import coletar_agencia_brasil
from scraper.recipes.jornal_de_brasilia import coletar_jornal_de_brasilia
from scraper.recipes.the_intercept_brasil import coletar_the_intercept_brasil
from scraper.recipes.brasil_de_fato import coletar_brasil_de_fato
load_dotenv() 
MONGO_URI = os.getenv("MONGO_URI")

# --- MUDANÇA 1: Definição da Coleção Temporária ---
COLLECTION_TEMP = "noticias_temp"

def get_db_collection():
    if not MONGO_URI: return None
    try:
        client = MongoClient(MONGO_URI)
        db = client.polinoticias_db 
        # --- MUDANÇA 2: Aponta para a Temp ---
        return db[COLLECTION_TEMP]
    except Exception as e:
        print(f"Erro DB: {e}")
        return None

def rodar_coleta_completa():
    collection = get_db_collection()
    if collection is None: return

    # --- MUDANÇA 3: Limpeza da Área de Rascunho ---
    # Antes de coletar, garantimos que a tabela temporária esteja vazia
    print(f"🧹 Limpando coleção temporária ({COLLECTION_TEMP})...")
    collection.drop()

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
        coletar_veja,
        coletar_infomoney,
        coletar_uol,
        coletar_revista_oeste,
        coletar_forbes_brasil,
        coletar_brasil_paralelo,
        coletar_jovem_pan,
        coletar_agencia_brasil,
        coletar_jornal_de_brasilia,
        coletar_the_intercept_brasil,
        coletar_brasil_de_fato
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
            # Salva na coleção temporária
            collection.insert_many(todas_as_noticias)
            print(f"\nSUCESSO: {len(todas_as_noticias)} documentos inseridos em '{COLLECTION_TEMP}'.")
        except Exception as e:
            print(f"❌ Erro ao salvar no MongoDB: {e}")
    else:
        print("AVISO: Nenhuma notícia nova coletada.")

if __name__ == '__main__':
    rodar_coleta_completa()