import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI") 
DB_NAME = "polinoticias_db"

# --- MUDANÇA PARA ATOMIC SWAP ---
# Tenta pegar a variável de ambiente definida pelo orquestrador.
# Se não existir, usa o padrão "noticias_raw".
COLLECTION_TARGET = "noticias_temp"

# --- MUDANÇA PARA E5-LARGE ---
MODEL_NAME = 'intfloat/multilingual-e5-large'
PREFIXO_MODELO = "query: "

print(f"Carregando modelo de viés: {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)

# --- 1. VIÉS DE REPUTAÇÃO ---
SOURCE_BIAS_MAP = {
    "Carta Capital": -1.5, "The Intercept Brasil": -1.5, "Revista Piauí": -1.2, "Brasil de Fato": -1.0,
    "Folha de S.Paulo": -0.4, "UOL": -0.5, "Agência Brasil": -0.7,
    "BBC Brasil": -0.1, "Metrópoles": 0.0, "Correio Braziliense": 0.2, "Reuters": 0.0,
    "Jornal de Brasília": 0.5, "O Globo": 0.3, "CNN Brasil": 0.4, "Forbes Brasil": 1.0,
    "InfoMoney": 0.8, "Estadão": 1.0, "Veja": 0.8, "Jovem Pan": 1.5,
    "Revista Oeste": 1.7, "Gazeta do Povo": 1.8, "Brasil Paralelo": 1.9
}

# --- 2. ÂNCORAS SEMÂNTICAS ---
POLARITY_PHRASES = {
    "direita": [
        f"{PREFIXO_MODELO}artigo que defende o livre mercado, o estado mínimo e as privatizações",
        f"{PREFIXO_MODELO}texto focado na redução de impostos e na desburocratização para empresas",
        f"{PREFIXO_MODELO}conteúdo que exalta a responsabilidade fiscal, o teto de gastos e a meritocracia",
        f"{PREFIXO_MODELO}notícia com críticas ao assistencialismo estatal e defesa do empreendedorismo",
        f"{PREFIXO_MODELO}texto que valoriza a família tradicional e os valores cristãos",
        f"{PREFIXO_MODELO}artigo que apoia a segurança pública rigorosa, o armamento e o combate ao crime",
        f"{PREFIXO_MODELO}conteúdo que exalta o patriotismo e a soberania nacional contra o globalismo",
        f"{PREFIXO_MODELO}texto em defesa da liberdade religiosa e com posicionamento contrário ao aborto"
    ],
    "esquerda": [
        f"{PREFIXO_MODELO}artigo que defende o fortalecimento do estado e dos serviços públicos estatais",
        f"{PREFIXO_MODELO}texto focado na distribuição de renda e na taxação de grandes fortunas",
        f"{PREFIXO_MODELO}notícia que reivindica direitos trabalhistas e a valorização do salário mínimo",
        f"{PREFIXO_MODELO}conteúdo que apoia a reforma agrária e a função social da propriedade",
        f"{PREFIXO_MODELO}texto em defesa dos direitos humanos, das minorias e dos movimentos sociais",
        f"{PREFIXO_MODELO}artigo que promove políticas de inclusão, diversidade e cotas raciais",
        f"{PREFIXO_MODELO}notícia sobre a importância da proteção ambiental e demarcação de terras indígenas",
        f"{PREFIXO_MODELO}texto que defende a descriminalização das drogas e a manutenção do estado laico"
    ]
}

# Pré-cálculo dos arquétipos
print("Gerando vetores de referência ideológica...")
emb_direita = model.encode(POLARITY_PHRASES["direita"], normalize_embeddings=True)
emb_esquerda = model.encode(POLARITY_PHRASES["esquerda"], normalize_embeddings=True)

CENTROIDE_DIREITA = np.mean(emb_direita, axis=0).reshape(1, -1)
CENTROIDE_ESQUERDA = np.mean(emb_esquerda, axis=0).reshape(1, -1)

def classificar_vies_e5(text, nome_fonte):
    if not text: return 0.0
    
    input_text = f"{PREFIXO_MODELO}{text}"
    text_embedding = model.encode(input_text, normalize_embeddings=True).reshape(1, -1)
    
    sim_dir = cosine_similarity(text_embedding, CENTROIDE_DIREITA)[0][0]
    sim_esq = cosine_similarity(text_embedding, CENTROIDE_ESQUERDA)[0][0]
    
    raw_diff = sim_dir - sim_esq
    
    ai_score = raw_diff * 80 
    ai_score = max(-3.0, min(3.0, ai_score))

    source_score = SOURCE_BIAS_MAP.get(nome_fonte, 0.0)
    
    final_score = (ai_score * 0.7) + (source_score * 0.3)
    
    return float(round(final_score, 2))

def rodar_classificacao():
    if not MONGO_URI: return

    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        # --- USA A COLEÇÃO DINÂMICA ---
        raw_collection = db[COLLECTION_TARGET]
        
        # Busca apenas na coleção alvo
        noticias = list(raw_collection.find({}))
        if not noticias: return

        print(f"Recalculando viés de {len(noticias)} notícias em '{COLLECTION_TARGET}' (E5-Large)...")
        
        updates = 0
        for n in noticias:
            texto_completo = n.get('texto_analise_ia', n.get('titulo', ''))
            nome_fonte = n.get('nome_fonte', '')
            
            if texto_completo:
                score = classificar_vies_e5(texto_completo, nome_fonte)
                
                raw_collection.update_one(
                    {"_id": n['_id']}, 
                    {"$set": {"viés_classificado": score}}
                )
                updates += 1
                
        print(f"Classificação concluída. {updates} atualizados.")
        client.close()

    except Exception as e:
        print(f"❌ Erro na classificação: {e}")

if __name__ == '__main__':
    rodar_classificacao()