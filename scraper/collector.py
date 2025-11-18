# scraper/collector.py

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from recipes.cnn_brasil import coletar_cnn_brasil
from recipes.folha_sp import coletar_folha_sp
from recipes.estadao import coletar_estadao
from recipes.bbc_brasil import coletar_bbc_brasil
#from recipes.reuters import coletar_reuters
from recipes.o_globo import coletar_o_globo
from recipes.gazeta_do_povo import coletar_gazeta_do_povo
from recipes.metropoles import coletar_metropoles
from recipes.correio_braziliense import coletar_correio_braziliense
from recipes.piaui import coletar_piaui
from recipes.carta_capital import coletar_carta_capital
from recipes.veja import coletar_veja



# --- 1. CONFIGURAÇÃO E CONEXÃO ---
# Carrega a MONGO_URI do arquivo .env
load_dotenv() 
MONGO_URI = os.getenv("MONGO_URI")

def get_db_collection():
    """Conecta ao ClusterPoliNoticias e retorna a coleção 'noticias_raw'."""
    if not MONGO_URI:
        print("Erro: MONGO_URI não encontrada no arquivo .env!")
        return None
    try:
        # Conecta ao seu ClusterPoliNoticias
        client = MongoClient(MONGO_URI)
        # O nome do banco de dados (ajuste se preferir outro nome)
        db = client.polinoticias_db 
        
        # Cria ou seleciona a coleção que armazenará os dados brutos (antes da IA/Agrupamento)
        collection = db.noticias_raw
        print("Conexão com MongoDB Atlas bem-sucedida. Coleção 'noticias_raw' pronta.")
        return collection
    except Exception as e:
        print(f"Erro ao conectar ao MongoDB Atlas: {e}")
        return None

# --- 2. O ORQUESTRADOR ---
def rodar_coleta_completa():
    """Chama todas as funções de coleta e insere os dados no DB."""
    collection = get_db_collection()
    if collection is None:
        return

    # Lista de todas as funções de coleta (por enquanto, só a CNN)
    funcoes_coleta = [coletar_cnn_brasil, coletar_folha_sp, coletar_estadao, coletar_bbc_brasil, coletar_o_globo, coletar_gazeta_do_povo, coletar_metropoles, coletar_correio_braziliense, coletar_piaui, coletar_carta_capital, coletar_veja] # Adicione 'coletar_folha', 'coletar_estadao', etc., aqui

    todas_as_noticias = []
    
    for funcao_coleta in funcoes_coleta:
        print(f"\nIniciando coleta em: {funcao_coleta.__name__}")
        noticias_da_fonte = funcao_coleta()
        todas_as_noticias.extend(noticias_da_fonte)

    if todas_as_noticias:
        # Insere todos os documentos (notícias) coletados no banco de dados
        collection.insert_many(todas_as_noticias)
        print(f"\nSUCESSO: {len(todas_as_noticias)} documentos inseridos no ClusterPoliNoticias.")
    else:
        print("AVISO: Nenhuma notícia nova foi coletada.")

if __name__ == '__main__':
    rodar_coleta_completa()