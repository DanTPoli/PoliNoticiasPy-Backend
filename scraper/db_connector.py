# scraper/db_connector.py

import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Carrega as variáveis do .env (incluindo a MONGO_URI)
load_dotenv() 
MONGO_URI = os.getenv("MONGO_URI")

def get_db_connection():
    """
    Retorna o cliente e o objeto do banco de dados PoliNoticias.
    """
    try:
        # Tenta conectar ao ClusterPoliNoticias
        client = MongoClient(MONGO_URI)
        # O nome do seu banco de dados (pode ser 'polinoticias_db')
        db = client.polinoticias_db 
        print("Conexão com o ClusterPoliNoticias bem-sucedida!")
        return db
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Teste (opcional)
if __name__ == '__main__':
    db = get_db_connection()