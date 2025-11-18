# analysis/bias_classifier_bert.py

import os
import torch
import numpy as np
from transformers import AutoModel, AutoTokenizer
from pymongo import MongoClient
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI") 
DB_NAME = "polinoticias_db"
COLLECTION_RAW = "noticias_raw"

# Modelo base BERTimbau (O mesmo que funcionou no Agrupamento)
MODEL_NAME = 'neuralmind/bert-base-portuguese-cased' 
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

# VETORES DE VIÉS: Frases polares para classificação por similaridade de cosseno
POLARITY_PHRASES = {
    # Usado para classificar a tendência do texto
    "direita": ["Bolsonaro livre mercado capitalista individualismo", "redução de impostos iniciativa privada segurança", "Ordem e progresso privatização"],
    "esquerda": ["Lula reforma agrária direitos sociais estado forte", "aumento de impostos investimento público igualdade", "justiça social contra o fascismo"]
}

def get_text_embedding(text):
    """Gera o embedding (vetor) para um único texto usando BERTimbau."""
    with torch.no_grad():
        encoded_input = tokenizer(text, padding=True, truncation=True, return_tensors='pt', max_length=128)
        model_output = model(**encoded_input)
        return model_output.last_hidden_state[0, 0, :].numpy().reshape(1, -1)

# Pré-calcula os embeddings das frases polares
POLARITY_EMBEDDINGS = {}
for key, phrases in POLARITY_PHRASES.items():
    embeddings = [get_text_embedding(p) for p in phrases]
    # Média dos vetores para ter um único ponto polar de referência
    POLARITY_EMBEDDINGS[key] = np.mean(embeddings, axis=0) 


def classificar_vies_bert(text):
    """Classifica o viés comparando o texto com os vetores de Esquerda e Direita."""
    text_embedding = get_text_embedding(text)
    
    # Calcula a similaridade do texto com os vetores polares
    similarity_direita = cosine_similarity(text_embedding, POLARITY_EMBEDDINGS["direita"])[0][0]
    similarity_esquerda = cosine_similarity(text_embedding, POLARITY_EMBEDDINGS["esquerda"])[0][0]
    
    # A diferença de similaridade. Positivo = Mais à Direita. Negativo = Mais à Esquerda.
    bias_diff = similarity_direita - similarity_esquerda
    
    # Mapeamento para a escala -3 a +3
    if bias_diff > 0.10: # Forte inclinação à direita
        return 3
    if bias_diff > 0.04: # Leve inclinação à direita
        return 1
    if bias_diff < -0.10: # Forte inclinação à esquerda
        return -3
    if bias_diff < -0.04: # Leve inclinação à esquerda
        return -1
    return 0 # Centro/Neutro (diferença baixa)


def rodar_classificacao():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    raw_collection = db[COLLECTION_RAW]
    
    noticias_para_classificar = list(raw_collection.find({
        "id_cluster": {"$ne": None}, 
        "viés_classificado": None      
    }))
    
    if not noticias_para_classificar:
        print("Nenhuma notícia agrupada para classificar. Saindo.")
        client.close()
        return

    print(f"Iniciando classificação de viés por Similaridade BERT em {len(noticias_para_classificar)} notícias...")
    
    for noticia in noticias_para_classificar:
        bias_score = classificar_vies_bert(noticia['texto_analise_ia'])
        
        # Atualização no MongoDB
        raw_collection.update_one(
            {"_id": noticia['_id']},
            {"$set": {"viés_classificado": bias_score}}
        )
        
    print("Classificação de viés por Similaridade concluída!")
    client.close()

if __name__ == '__main__':
    rodar_classificacao()