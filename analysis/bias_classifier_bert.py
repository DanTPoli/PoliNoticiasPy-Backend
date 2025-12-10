import sys
import os

# Garante que o Python encontre os módulos na pasta raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import torch 
from transformers import AutoModel, AutoTokenizer
from pymongo import MongoClient
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

# Carrega configurações
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI") 
DB_NAME = "polinoticias_db"
COLLECTION_RAW = "noticias_raw"

# Modelo base BERTimbau
MODEL_NAME = 'neuralmind/bert-base-portuguese-cased' 

print(f"Carregando modelo {MODEL_NAME}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

# --- 1. VIÉS DE REPUTAÇÃO (Ponto de Partida) ---
SOURCE_BIAS_MAP = {
    # ESQUERDA
    "Carta Capital": -2.5,
    "The Intercept Brasil": -2.0,
    "Revista Piauí": -1.5,
    "Folha de S.Paulo": -0.8,
    "UOL": -0.5,
    "Agência Brasil": -0.5,

    # CENTRO / NEUTRO
    "BBC Brasil": -0.2, 
    "Metrópoles": 0.0,
    "Correio Braziliense": 0.0,
    "Reuters": 0.0,
    
    # DIREITA
    "Jornal de Brasília": 0.5,
    "O Globo": 0.3, # Mantive o 0.3 original
    "CNN Brasil": 0.5,
    "Forbes Brasil": 0.7,
    "InfoMoney": 0.8,
    "Estadão": 1.0, 
    "Veja": 1.0,
    "Jovem Pan": 1.8,
    "Revista Oeste": 2.0,
    "Gazeta do Povo": 2.5,
    "Brasil Paralelo": 2.5
}

# --- 2. ÂNCORAS SEMÂNTICAS (Conceitos) ---
POLARITY_PHRASES = {
    "direita": [
        "defesa do livre mercado estado mínimo e privatizações",
        "redução de impostos e desburocratização para empresas",
        "responsabilidade fiscal teto de gastos e meritocracia",
        "crítica ao assistencialismo e defesa do empreendedorismo",
        "defesa da família tradicional e valores cristãos",
        "segurança pública rigorosa armamento e combate ao crime",
        "patriotismo e soberania nacional contra globalismo",
        "liberdade religiosa e oposição ao aborto"
    ],
    "esquerda": [
        "fortalecimento do estado e serviços públicos estatais",
        "distribuição de renda e taxação de grandes fortunas",
        "direitos trabalhistas e valorização do salário mínimo",
        "reforma agrária e função social da propriedade",
        "defesa dos direitos humanos e minorias sociais",
        "políticas de inclusão diversidade e cotas raciais",
        "proteção ambiental e demarcação de terras indígenas",
        "descriminalização das drogas e estado laico"
    ]
}

def get_text_embedding(text):
    """Gera o embedding para o texto completo (512 tokens)."""
    with torch.no_grad():
        encoded_input = tokenizer(text, padding=True, truncation=True, return_tensors='pt', max_length=512)
        model_output = model(**encoded_input)
        return torch.mean(model_output.last_hidden_state, dim=1).numpy()

# Pré-cálculo dos arquétipos
print("Gerando vetores de referência ideológica...")
POLARITY_EMBEDDINGS = {}
for key, phrases in POLARITY_PHRASES.items():
    embeddings = [get_text_embedding(p) for p in phrases]
    POLARITY_EMBEDDINGS[key] = np.mean(embeddings, axis=0) 

def classificar_vies_bert(text, nome_fonte):
    """
    Calcula o viés usando Média Ponderada: 60% Análise do Texto (IA) + 40% Histórico da Fonte.
    """
    if not text: return 0.0
    
    # A. Análise do Texto (Dinâmica)
    text_embedding = get_text_embedding(text)
    sim_dir = cosine_similarity(text_embedding, POLARITY_EMBEDDINGS["direita"])[0][0]
    sim_esq = cosine_similarity(text_embedding, POLARITY_EMBEDDINGS["esquerda"])[0][0]
    
    raw_diff = sim_dir - sim_esq
    
    # Amplificação e Clamping
    ai_score = raw_diff * 20 
    ai_score = max(-3.0, min(3.0, ai_score))

    # B. Viés da Fonte (Estático)
    source_score = SOURCE_BIAS_MAP.get(nome_fonte, 0.0)
    
    # C. Média Ponderada
    final_score = (ai_score * 0.6) + (source_score * 0.4)
    
    # CORREÇÃO DO ERRO: Converter numpy.float para float nativo do Python
    # O MongoDB não aceita tipos nativos do NumPy
    return float(round(final_score, 2))

def rodar_classificacao():
    if not MONGO_URI: 
        print("Erro: MONGO_URI não configurada.")
        return

    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        raw_collection = db[COLLECTION_RAW]
        
        noticias = list(raw_collection.find({}))
        
        if not noticias:
            print("Nenhuma notícia para classificar.")
            client.close()
            return

        print(f"Recalculando viés de {len(noticias)} notícias (Modelo Híbrido)...")
        
        updates = 0
        for n in noticias:
            texto_completo = n.get('texto_analise_ia', n.get('titulo', ''))
            nome_fonte = n.get('nome_fonte', '')
            
            if texto_completo:
                score = classificar_vies_bert(texto_completo, nome_fonte)
                
                raw_collection.update_one(
                    {"_id": n['_id']}, 
                    {"$set": {"viés_classificado": score}}
                )
                updates += 1
                
        print(f"Classificação concluída. {updates} notícias atualizadas.")
        client.close()

    except Exception as e:
        print(f"❌ Erro na classificação: {e}")

if __name__ == '__main__':
    rodar_classificacao()