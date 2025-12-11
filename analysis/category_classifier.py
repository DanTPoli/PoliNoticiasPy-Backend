import sys
import os
import re

# Garante que o Python encontre os módulos na pasta raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pymongo import MongoClient
from dotenv import load_dotenv

# Carrega configurações
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI") 
DB_NAME = "polinoticias_db"

# --- MUDANÇA PARA ATOMIC SWAP ---
# Tenta pegar a variável de ambiente definida pelo orquestrador.
# Se não existir, usa o padrão "noticias_raw".
COLLECTION_TARGET = "noticias_temp"

# --- DEFINIÇÃO DE CATEGORIAS E PALAVRAS-CHAVE ---
KEYWORDS = {
    "Economia": [
        "dólar", "euro", "bolsa", "ibovespa", "selic", "inflação", "ipca", "pib", 
        "mercado financeiro", "banco central", "campos neto", "haddad", "arcabouço fiscal",
        "imposto", "tributária", "investimento", "receita federal", "petrobras", "vale",
        "agronegócio", "exportação", "importação", "superávit", "déficit", "meta fiscal"
    ],
    "Justiça": [
        "stf", "supremo", "pgr", "procuradoria", "polícia federal", "pf", "operação",
        "moraes", "zanin", "barroso", "gilmar", "fux", "mandado", "prisão", "condenação",
        "réu", "processo", "julgamento", "tse", "eleitoral", "constituição", "crime",
        "investigação", "denúncia", "delação", "lava jato", "oab", "jurídico"
    ],
    "Mundo": [
        "eua", "estados unidos", "biden", "trump", "china", "xi jinping", "rússia", "putin",
        "ucrânia", "zelensky", "israel", "gaza", "palestina", "hamas", "netanyahu",
        "argentina", "milei", "europa", "união europeia", "onu", "g20", "brics",
        "venezuela", "maduro", "frança", "macron", "reino unido", "guerra", "internacional"
    ],
    "Política": [
        "lula", "bolsonaro", "planalto", "governo", "presidente", "ministro", "ministério",
        "câmara", "senado", "congresso", "deputado", "senador", "arthur lira", "pacheco",
        "pt", "pl", "psol", "união brasil", "centrão", "oposição", "situação", "leis",
        "decreto", "medida provisória", "votação", "pec", "comissão", "cpi", "cpmi", "eleições"
    ],
    "Brasil": [
        "brasil", "lula", "bolsonaro","arthur lira", "pacheco", "pt", "pl", "psol", "união brasil",
        "stf", "pgr", "moraes", "zanin", "barroso", "gilmar", "fux", "tse", "lava jato", "oab"
    ]
}

def classificar_categoria(texto):
    """
    Analisa o texto e retorna uma LISTA de categorias relevantes.
    """
    if not texto: return ["Brasil"] 
    
    texto_lower = texto.lower()
    scores = {cat: 0 for cat in KEYWORDS}
    
    for categoria, termos in KEYWORDS.items():
        for termo in termos:
            if re.search(rf"\b{termo}\b", texto_lower):
                scores[categoria] += 1
    
    categorias_detectadas = [cat for cat, score in scores.items() if score > 0]
    categorias_detectadas.sort(key=lambda x: scores[x], reverse=True)
    
    if not categorias_detectadas:
        return ["Brasil"]
        
    return categorias_detectadas

def rodar_classificacao_categorias():
    if not MONGO_URI: 
        print("Erro: MONGO_URI não configurada.")
        return

    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        # --- MUDANÇA: Usa a coleção dinâmica ---
        raw_collection = db[COLLECTION_TARGET]
        
        noticias = list(raw_collection.find({}))
        
        print(f"Classificando categorias em '{COLLECTION_TARGET}' ({len(noticias)} notícias)...")
        
        updates = 0
        for n in noticias:
            texto_completo = n.get('texto_analise_ia', n.get('titulo', ''))
            
            novas_categorias = classificar_categoria(texto_completo)
            
            raw_collection.update_one(
                {"_id": n['_id']},
                {"$set": {"categoria": novas_categorias}} 
            )
            updates += 1
            
        print(f"Categorização concluída. {updates} notícias atualizadas.")
        client.close()

    except Exception as e:
        print(f"Erro na categorização: {e}")

if __name__ == '__main__':
    rodar_classificacao_categorias()