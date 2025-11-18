# db_utils/reset_db.py

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Carrega variáveis de ambiente (MONGO_URI)
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI") 
DB_NAME = "polinoticias_db"
COLLECTIONS_TO_RESET = ["noticias_raw"] # Lista de coleções a serem limpas

def reset_collections():
    """Conecta ao MongoDB Atlas e apaga todos os documentos das coleções listadas."""
    if not MONGO_URI:
        print("Erro: MONGO_URI não encontrada. Verifique o arquivo .env.")
        return

    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        print(f"Conectado ao Database: {DB_NAME}")
        
        for col_name in COLLECTIONS_TO_RESET:
            collection = db[col_name]
            
            # Executa a operação de exclusão
            result = collection.delete_many({})
            
            # Reporta o resultado
            print(f"✅ Coleção '{col_name}' resetada. {result.deleted_count} documentos removidos.")

        client.close()
        print("Conexão fechada.")

    except Exception as e:
        print(f"❌ Erro fatal durante o reset do DB: {e}")

if __name__ == '__main__':
    # Executa a função principal
    reset_collections()