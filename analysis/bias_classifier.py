# analysis/bias_classifier.py

import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI") 
DB_NAME = "polinoticias_db"
COLLECTION_RAW = "noticias_raw"

# Modelo de análise de SENTIMENTO em português (proxy para viés)
MODEL_NAME = "adalberto/bert-base-portuguese-cased-prosa" 
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

def sentiment_to_bias(score):
    """
    Mapeia a pontuação de sentimento (Neg/Pos) para a escala de viés (-3 a +3).
    A lógica é um PROXY inicial: Sentimento Negativo = Viés Esquerda; Positivo = Viés Direita.
    """
    # Escala simples de -3 a +3
    if score >= 0.7:  # Forte Positivo (Tendência Direita Forte)
        return 3
    if score >= 0.3:  # Positivo Leve (Tendência Direita Leve)
        return 1
    if score <= -0.7: # Forte Negativo (Tendência Esquerda Forte)
        return -3
    if score <= -0.3: # Negativo Leve (Tendência Esquerda Leve)
        return -1
    return 0 # Neutro/Centro

def classificar_vies():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    raw_collection = db[COLLECTION_RAW]
    
    # Busca notícias que foram agrupadas, mas ainda não classificadas
    noticias_para_classificar = list(raw_collection.find({
        "id_cluster": {"$ne": None}, # Deve ter sido agrupada
        "viés_classificado": None      # Ainda não classificada
    }))
    
    if not noticias_para_classificar:
        print("Nenhuma notícia agrupada para classificar. Saindo.")
        client.close()
        return

    print(f"Iniciando classificação de viés em {len(noticias_para_classificar)} notícias...")
    
    for noticia in noticias_para_classificar:
        text = noticia['texto_analise_ia']
        
        # 1. Análise de Sentimento com PyTorch
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        outputs = model(**inputs)
        
        # Saída do modelo: 0=Negativo, 1=Neutro, 2=Positivo
        probabilities = torch.softmax(outputs.logits, dim=1)[0]
        
        # Calculamos um score simples (Positivo - Negativo)
        sentiment_score = probabilities[2].item() - probabilities[0].item() 
        
        # 2. Mapeamento para a Escala de Viés
        bias_score = sentiment_to_bias(sentiment_score)
        
        # 3. Atualização no MongoDB
        raw_collection.update_one(
            {"_id": noticia['_id']},
            {"$set": {"viés_classificado": bias_score}}
        )
        
    print("Classificação de viés concluída!")
    client.close()

if __name__ == '__main__':
    classificar_vies()