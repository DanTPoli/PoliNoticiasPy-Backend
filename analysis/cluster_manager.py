# analysis/cluster_manager.py

import os
from datetime import datetime
import torch
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoModel, AutoTokenizer
from pymongo import MongoClient
from dotenv import load_dotenv

# Carrega as variáveis de ambiente IMEDIATAMENTE.
load_dotenv()

# --- CONFIGURAÇÃO ---
# Endereço de conexão com o MongoDB (deve ser o mesmo do seu app.py)
MONGO_URI = os.getenv("MONGO_URI") 
DB_NAME = "polinoticias_db"
COLLECTION_RAW = "noticias_raw"
# Modelo BERTimbau: excelente para tarefas em Português
MODEL_NAME = 'neuralmind/bert-base-portuguese-cased' 

# O quão semelhantes as notícias devem ser (0.0 a 1.0).
# Um valor de 0.8 a 0.85 é um bom ponto de partida para similaridade de cosseno.
SIMILARITY_THRESHOLD = 0.82 

# Inicializa o tokenizer e o modelo BERTimbau uma única vez
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

def get_sentence_embeddings(texts):
    """Gera embeddings (vetores) para uma lista de textos."""
    # O PyTorch é usado internamente pelo modelo transformers
    # O torch.no_grad() desativa o cálculo de gradientes para otimizar a memória
    with torch.no_grad(): 
        # Tokenização e preparação da entrada
        encoded_input = tokenizer(texts, padding=True, truncation=True, return_tensors='pt', max_length=128)
        
        # Passa pelo modelo
        model_output = model(**encoded_input)
        
        # Pega o embedding do [CLS] token (o primeiro token) como o embedding da frase
        embeddings = model_output.last_hidden_state[:, 0, :].numpy()
        return embeddings

def rodar_agrupamento():
    """
    Busca notícias não agrupadas, cria embeddings, faz o cluster e atualiza o MongoDB.
    """
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    raw_collection = db[COLLECTION_RAW]
    
    noticias_nao_agrupadas = list(raw_collection.find({"id_cluster": None}))
    
    if not noticias_nao_agrupadas:
        print("Nenhuma notícia nova para agrupar. Saindo.")
        client.close()
        return

    print(f"Iniciando agrupamento de {len(noticias_nao_agrupadas)} notícias...")
    
    # 1. Preparação e Geração de Embeddings
    textos = [n['texto_analise_ia'] for n in noticias_nao_agrupadas]
    ids_map = [n['_id'] for n in noticias_nao_agrupadas]
    
    embeddings = get_sentence_embeddings(textos)
    print("Embeddings gerados.")

    # 2. Agrupamento (Clusterização)
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=1 - SIMILARITY_THRESHOLD, 
        metric='cosine',
        linkage='average'
    ).fit(embeddings)
    
    cluster_labels = clustering.labels_
    
    # 3. Mapeamento e Atribuição de ID Único
    
    # Mapeia o rótulo numérico do algoritmo (0, 1, 2...) para um ID de string único
    # O set garante que só criamos IDs para os rótulos que existem
    unique_labels = set(cluster_labels) 
    
    # Mapeamento do rótulo temporário -> ID final de string
    label_to_id = {} 
    timestamp_prefix = datetime.now().strftime("%Y%m%d%H%M%S")
    
    for label in unique_labels:
        # Cria um ID de cluster permanente para este grupo
        if label != -1: # Ignoramos o rótulo -1, caso tenha sido gerado (Ruído)
            label_to_id[label] = f"cluster_{timestamp_prefix}_{label}"
        
    print(f"Agrupamento concluído. {len(label_to_id)} clusters encontrados.")

    # 4. Atualização no MongoDB
    for i, label in enumerate(cluster_labels):
        if label in label_to_id:
            id_cluster_final = label_to_id[label]
            
            # Atualiza o documento no MongoDB
            raw_collection.update_one(
                {"_id": ids_map[i]},
                {"$set": {"id_cluster": id_cluster_final}}
            )
            
    print(f"Banco de dados atualizado com {len(label_to_id)} novos clusters.")

    client.close()

if __name__ == '__main__':
    # Certifique-se de que o .env está carregado para a URI do Mongo
    from dotenv import load_dotenv
    load_dotenv()
    
    rodar_agrupamento()