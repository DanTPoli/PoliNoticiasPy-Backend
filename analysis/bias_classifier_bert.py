import os
import numpy as np
import torch 
from transformers import AutoModel, AutoTokenizer
from pymongo import MongoClient
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI") 
DB_NAME = "polinoticias_db"
COLLECTION_RAW = "noticias_raw"

# Modelo base BERTimbau
MODEL_NAME = 'neuralmind/bert-base-portuguese-cased' 
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

# VETORES DE VIÉS (Polaridade)
# Com textos mais ricos, a comparação semântica fica mais precisa.
POLARITY_PHRASES = {
    "direita": ["Bolsonaro livre mercado capitalista individualismo conservadorismo família", "redução de impostos estado mínimo privatização segurança pública"],
    "esquerda": ["Lula reforma agrária direitos sociais estado forte progressismo igualdade", "taxação de grandes fortunas investimento público justiça social"]
}

def get_text_embedding(text):
    """Gera o embedding (vetor) para um texto usando BERTimbau."""
    with torch.no_grad():
        # --- ATUALIZAÇÃO CRÍTICA ---
        # Aumentamos max_length para 512 para ler o parágrafo inteiro coletado.
        encoded_input = tokenizer(text, padding=True, truncation=True, return_tensors='pt', max_length=512)
        model_output = model(**encoded_input)
        return model_output.last_hidden_state[0, 0, :].numpy().reshape(1, -1)

# Pré-calcula os embeddings das frases polares
POLARITY_EMBEDDINGS = {}
for key, phrases in POLARITY_PHRASES.items():
    embeddings = [get_text_embedding(p) for p in phrases]
    POLARITY_EMBEDDINGS[key] = np.mean(embeddings, axis=0) 

def classificar_vies_bert(text):
    """Classifica o viés comparando o texto completo com os vetores polares."""
    text_embedding = get_text_embedding(text)
    
    similarity_direita = cosine_similarity(text_embedding, POLARITY_EMBEDDINGS["direita"])[0][0]
    similarity_esquerda = cosine_similarity(text_embedding, POLARITY_EMBEDDINGS["esquerda"])[0][0]
    
    bias_diff = similarity_direita - similarity_esquerda
    
    # Limiares ajustados para sensibilidade
    if bias_diff > 0.08: return 3 
    if bias_diff > 0.03: return 1 
    if bias_diff < -0.08: return -3 
    if bias_diff < -0.03: return -1 
    return 0 

def rodar_classificacao():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    raw_collection = db[COLLECTION_RAW]
    
    # Busca notícias que têm cluster mas ainda não têm viés
    noticias_para_classificar = list(raw_collection.find({
        "id_cluster": {"$ne": None}, 
        "viés_classificado": None      
    }))
    
    if not noticias_para_classificar:
        print("Nenhuma notícia nova para classificar.")
        client.close()
        return

    print(f"Iniciando classificação profunda em {len(noticias_para_classificar)} notícias...")
    
    for noticia in noticias_para_classificar:
        # Garante que usa o texto rico (se disponível) ou o título como fallback
        texto_completo = noticia.get('texto_analise_ia', noticia.get('titulo', ''))
        
        if not texto_completo: continue

        bias_score = classificar_vies_bert(texto_completo)
        
        raw_collection.update_one(
            {"_id": noticia['_id']},
            {"$set": {"viés_classificado": bias_score}}
        )
        
    print("Classificação de viés concluída!")
    client.close()

if __name__ == '__main__':
    rodar_classificacao()