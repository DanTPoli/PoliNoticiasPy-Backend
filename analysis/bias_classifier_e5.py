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
COLLECTION_RAW = "noticias_raw"

# --- MUDANÇA PARA E5-LARGE ---
MODEL_NAME = 'intfloat/multilingual-e5-large'
# Para análise de viés, tratamos tanto as âncoras quanto as notícias como "passage"
# para comparação simétrica de documentos.
PREFIXO_MODELO = "passage: "

print(f"Carregando modelo de viés: {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)

# --- 1. VIÉS DE REPUTAÇÃO (Mantido igual) ---
SOURCE_BIAS_MAP = {
    "Carta Capital": -2.5, "The Intercept Brasil": -2.0, "Revista Piauí": -1.5,
    "Folha de S.Paulo": -0.8, "UOL": -0.5, "Agência Brasil": -0.5,
    "BBC Brasil": -0.2, "Metrópoles": 0.0, "Correio Braziliense": 0.0, "Reuters": 0.0,
    "Jornal de Brasília": 0.5, "O Globo": 0.3, "CNN Brasil": 0.5, "Forbes Brasil": 0.7,
    "InfoMoney": 0.8, "Estadão": 1.0, "Veja": 1.0, "Jovem Pan": 1.8,
    "Revista Oeste": 2.0, "Gazeta do Povo": 2.5, "Brasil Paralelo": 2.5
}

# --- 2. ÂNCORAS SEMÂNTICAS ---
# Adicionamos o prefixo em cada frase para o E5
POLARITY_PHRASES = {
    "direita": [
        f"{PREFIXO_MODELO}defesa do livre mercado estado mínimo e privatizações",
        f"{PREFIXO_MODELO}redução de impostos e desburocratização para empresas",
        f"{PREFIXO_MODELO}responsabilidade fiscal teto de gastos e meritocracia",
        f"{PREFIXO_MODELO}crítica ao assistencialismo e defesa do empreendedorismo",
        f"{PREFIXO_MODELO}defesa da família tradicional e valores cristãos",
        f"{PREFIXO_MODELO}segurança pública rigorosa armamento e combate ao crime",
        f"{PREFIXO_MODELO}patriotismo e soberania nacional contra globalismo",
        f"{PREFIXO_MODELO}liberdade religiosa e oposição ao aborto"
    ],
    "esquerda": [
        f"{PREFIXO_MODELO}fortalecimento do estado e serviços públicos estatais",
        f"{PREFIXO_MODELO}distribuição de renda e taxação de grandes fortunas",
        f"{PREFIXO_MODELO}direitos trabalhistas e valorização do salário mínimo",
        f"{PREFIXO_MODELO}reforma agrária e função social da propriedade",
        f"{PREFIXO_MODELO}defesa dos direitos humanos e minorias sociais",
        f"{PREFIXO_MODELO}políticas de inclusão diversidade e cotas raciais",
        f"{PREFIXO_MODELO}proteção ambiental e demarcação de terras indígenas",
        f"{PREFIXO_MODELO}descriminalização das drogas e estado laico"
    ]
}

# Pré-cálculo dos arquétipos
print("Gerando vetores de referência ideológica...")
# O encode já retorna numpy arrays normalizados
emb_direita = model.encode(POLARITY_PHRASES["direita"], normalize_embeddings=True)
emb_esquerda = model.encode(POLARITY_PHRASES["esquerda"], normalize_embeddings=True)

# Vetor médio (Centróide)
CENTROIDE_DIREITA = np.mean(emb_direita, axis=0).reshape(1, -1)
CENTROIDE_ESQUERDA = np.mean(emb_esquerda, axis=0).reshape(1, -1)

def classificar_vies_e5(text, nome_fonte):
    if not text: return 0.0
    
    # Prepara o texto com o prefixo
    input_text = f"{PREFIXO_MODELO}{text}"
    
    # Gera embedding
    text_embedding = model.encode(input_text, normalize_embeddings=True).reshape(1, -1)
    
    # Calcula similaridade
    sim_dir = cosine_similarity(text_embedding, CENTROIDE_DIREITA)[0][0]
    sim_esq = cosine_similarity(text_embedding, CENTROIDE_ESQUERDA)[0][0]
    
    raw_diff = sim_dir - sim_esq
    
    # Fator de amplificação (E5 tem vetores mais distintos, talvez precise ajustar esse 20 futuramente)
    ai_score = raw_diff * 20 
    ai_score = max(-3.0, min(3.0, ai_score))

    # Viés da Fonte
    source_score = SOURCE_BIAS_MAP.get(nome_fonte, 0.0)
    
    # Média Ponderada (60% IA, 40% Fonte)
    final_score = (ai_score * 0.6) + (source_score * 0.4)
    
    return float(round(final_score, 2))

def rodar_classificacao():
    if not MONGO_URI: return

    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        raw_collection = db[COLLECTION_RAW]
        
        noticias = list(raw_collection.find({}))
        if not noticias: return

        print(f"Recalculando viés de {len(noticias)} notícias (E5-Large)...")
        
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