import sys
import os

# --- CORREÇÃO DE CAMINHO ---
# Adiciona o diretório pai ao path para garantir que imports funcionem
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
import numpy as np
import torch
from sklearn.cluster import AgglomerativeClustering
from transformers import AutoModel, AutoTokenizer
from pymongo import MongoClient
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv() 
MONGO_URI = os.getenv("MONGO_URI") 
DB_NAME = "polinoticias_db"
COLLECTION_RAW = "noticias_raw"

# Modelo BERTimbau (Base)
MODEL_NAME = 'neuralmind/bert-base-portuguese-cased' 

# --- AJUSTE DE SENSIBILIDADE (CORREÇÃO) ---
# Isso torna o algoritmo mais exigente. Notícias precisam ser muito parecidas para agrupar.
SIMILARITY_THRESHOLD = 0.90

# Inicializa o modelo
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

def get_sentence_embeddings(texts):
    """Gera embeddings (vetores numéricos) para uma lista de textos."""
    with torch.no_grad(): 
        # max_length=512 é crucial para ler o parágrafo inteiro coletado
        encoded_input = tokenizer(texts, padding=True, truncation=True, return_tensors='pt', max_length=512)
        
        model_output = model(**encoded_input)
        
        # Pega o vetor que representa a frase inteira (token CLS)
        return model_output.last_hidden_state[:, 0, :].numpy()

def rodar_agrupamento():
    if not MONGO_URI:
        print("Erro: MONGO_URI não configurada no arquivo .env")
        return

    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        raw_collection = db[COLLECTION_RAW]
        
        # --- RE-AGRUPAMENTO TOTAL ---
        # Buscamos TODAS as notícias ({}) para desfazer os grupos errados anteriores.
        noticias = list(raw_collection.find({}))
        
        if not noticias:
            print("Nenhuma notícia encontrada no banco de dados.")
            client.close()
            return

        print(f"Iniciando re-agrupamento de {len(noticias)} notícias...")
        print(f"Nível de similaridade exigido: {SIMILARITY_THRESHOLD}")
        
        # Prioriza o texto rico (parágrafo), usa o título se não houver parágrafo
        textos = [n.get('texto_analise_ia', n.get('titulo', '')) for n in noticias]
        ids_map = [n['_id'] for n in noticias]
        
        # 1. Gera os vetores matemáticos
        print("Gerando embeddings (isso pode levar alguns segundos)...")
        embeddings = get_sentence_embeddings(textos)

        # 2. Agrupa baseado na distância de cosseno
        clustering = AgglomerativeClustering(
            n_clusters=None, 
            # A distância máxima permitida é (1 - Similaridade). 
            # Com 0.85, a distância deve ser <= 0.15 para agrupar.
            distance_threshold=1 - SIMILARITY_THRESHOLD, 
            metric='cosine', 
            linkage='average' 
        ).fit(embeddings)
        
        cluster_labels = clustering.labels_
        
        # 3. Gera novos IDs para os clusters
        timestamp_prefix = datetime.now().strftime("%Y%m%d%H%M") 
        label_to_id = {}
        
        # Mapeia cada número de grupo (0, 1, 2...) para um ID string único
        for label in set(cluster_labels):
            label_to_id[label] = f"c_{timestamp_prefix}_{label}"
            
        print(f"Agrupamento concluído. {len(label_to_id)} clusters distintos encontrados.")

        # 4. Salva no MongoDB
        updates = 0
        for i, label in enumerate(cluster_labels):
            if label in label_to_id:
                id_cluster_final = label_to_id[label]
                
                # Atualiza o documento
                raw_collection.update_one(
                    {"_id": ids_map[i]},
                    {"$set": {"id_cluster": id_cluster_final}}
                )
                updates += 1
                
        print(f"Sucesso! {updates} notícias foram atualizadas no banco.")
        client.close()

    except Exception as e:
        print(f"❌ Erro fatal durante o agrupamento: {e}")

if __name__ == '__main__':
    rodar_agrupamento()