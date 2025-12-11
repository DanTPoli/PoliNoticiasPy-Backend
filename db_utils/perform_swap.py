import sys
import os
# Hack para importar módulos da raiz se necessário
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI") 
DB_NAME = "polinoticias_db"

# Nomes das coleções (Devem bater com os scripts)
COLLECTION_TEMP = "noticias_temp"
COLLECTION_OFICIAL = "noticias_raw"

def realizar_troca():
    if not MONGO_URI:
        print("Erro: MONGO_URI não configurada.")
        return

    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        # Verifica se tem dados antes de trocar (Segurança)
        count = db[COLLECTION_TEMP].count_documents({})
        
        if count > 0:
            print(f"🔄 Trocando tabelas... ({count} novas notícias)")
            # O comando mágico: Temp vira Oficial, Oficial antiga é deletada
            db[COLLECTION_TEMP].rename(COLLECTION_OFICIAL, dropTarget=True)
            print("✅ SUCESSO! Feed Oficial atualizado.")
        else:
            print("⚠️ AVISO: A tabela temporária está vazia. Swap cancelado.")
            
        client.close()

    except Exception as e:
        print(f"❌ Erro ao realizar o swap: {e}")

if __name__ == '__main__':
    realizar_troca()