import sys
import os

# --- CORREÇÃO DE CAMINHO ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from sklearn.cluster import AgglomerativeClustering
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv() 
MONGO_URI = os.getenv("MONGO_URI") 
DB_NAME = "polinoticias_db"
COLLECTION_RAW = "noticias_raw"

# --- CONFIGURAÇÃO E5 (Alta Precisão) ---
MODEL_NAME = 'intfloat/multilingual-e5-large'
# O E5 exige que digamos o que é o texto. "passage: " é para documentos.
PREFIXO_MODELO = "passage: "

# Com o E5, a precisão é maior, então 0.85 é um corte muito seguro (equivalente a 0.95 do BERT)
SIMILARITY_THRESHOLD = 0.94

print(f"Carregando modelo de clusterização: {MODEL_NAME}...")
# A biblioteca gerencia o download e cache automaticamente
model = SentenceTransformer(MODEL_NAME)

def get_clean_text_for_embedding(doc):
    """
    Prepara o texto para o modelo E5.
    O E5 funciona melhor com Título + Lead curto, sem sujeira.
    """
    titulo = doc.get('titulo', '').strip()
    # Adicionamos o prefixo obrigatório
    return f"{PREFIXO_MODELO}{titulo}"

def rodar_agrupamento():
    if not MONGO_URI:
        print("Erro: MONGO_URI não configurada.")
        return

    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        raw_collection = db[COLLECTION_RAW]
        
        # Filtro opcional: em produção, filtrar por data (ex: últimas 48h) economiza RAM
        noticias = list(raw_collection.find({}))
        
        if not noticias:
            print("Nenhuma notícia encontrada.")
            return

        print(f"Processando {len(noticias)} notícias com E5-Large...")
        
        # Prepara lista de textos e IDs
        textos = [get_clean_text_for_embedding(n) for n in noticias]
        ids_map = [n['_id'] for n in noticias]
        
        # 1. Gera embeddings (A mágica acontece aqui, muito mais limpo)
        # batch_size=16 é um bom equilíbrio para o Pi 5
        print("Gerando vetores semânticos...")
        embeddings = model.encode(
            textos, 
            batch_size=16, 
            show_progress_bar=True, 
            normalize_embeddings=True # Crucial para distância cosseno
        )

        # 2. Agrupa (Hierarchical Clustering)
        # Linkage 'average' funciona melhor com embeddings de alta qualidade como E5
        clustering = AgglomerativeClustering(
            n_clusters=None, 
            distance_threshold=1 - SIMILARITY_THRESHOLD, 
            metric='cosine', 
            linkage='complete' 
        ).fit(embeddings)
        
        cluster_labels = clustering.labels_
        
        # 3. Gera IDs de Cluster
        timestamp_prefix = datetime.now().strftime("%Y%m%d%H") 
        unique_labels = set(cluster_labels)
        label_to_id = {lbl: f"c_{timestamp_prefix}_{lbl}" for lbl in unique_labels}
            
        print(f"Agrupamento concluído. {len(unique_labels)} clusters formados.")

        # 4. Salva no MongoDB
        updates = 0
        for i, label in enumerate(cluster_labels):
            raw_collection.update_one(
                {"_id": ids_map[i]},
                {"$set": {"id_cluster": label_to_id[label]}}
            )
            updates += 1
                
        print(f"Sucesso! {updates} notícias atualizadas.")
        client.close()

    except Exception as e:
        print(f"❌ Erro fatal durante o agrupamento: {e}")

if __name__ == '__main__':
    rodar_agrupamento()