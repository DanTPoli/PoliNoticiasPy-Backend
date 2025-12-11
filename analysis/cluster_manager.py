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

# --- MUDANÇA PARA ATOMIC SWAP ---
# Lê a coleção alvo definida pelo orquestrador. Padrão: "noticias_raw"
COLLECTION_TARGET = "noticias_temp"

# --- CONFIGURAÇÃO E5 (Alta Precisão) ---
MODEL_NAME = 'intfloat/multilingual-e5-large'
PREFIXO_MODELO = "passage: "

# Threshold calibrado (0.945 é bem rigoroso, ideal para linkage='complete')
SIMILARITY_THRESHOLD = 0.90

print(f"Carregando modelo de clusterização: {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)

def get_clean_text_for_embedding(doc):
    """
    Prepara o texto para o modelo E5.
    Estratégia: Título + Lead (Início do texto).
    Isso ajuda a conectar notícias com títulos diferentes, mas corta o ruído do texto longo.
    """
    titulo = doc.get('titulo', '').strip()
    
    # Pega o texto extraído pela IA
    corpo = doc.get('texto_analise_ia', '').strip()
    
    # Remove o título do corpo se ele já estiver repetido lá
    if corpo.startswith(titulo):
        corpo = corpo[len(titulo):].strip()
        
    # TRUQUE DO LEAD: Pegamos apenas os primeiros 300 caracteres.
    lead = corpo[:300]
    
    # O E5 exige o prefixo
    return f"{PREFIXO_MODELO}{titulo}. {lead}"

def rodar_agrupamento():
    if not MONGO_URI:
        print("Erro: MONGO_URI não configurada.")
        return

    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        # --- USA A COLEÇÃO DINÂMICA ---
        raw_collection = db[COLLECTION_TARGET]
        
        # Busca notícias
        noticias = list(raw_collection.find({}))
        
        if not noticias:
            print(f"Nenhuma notícia encontrada em '{COLLECTION_TARGET}'.")
            return

        print(f"Processando {len(noticias)} notícias em '{COLLECTION_TARGET}' com E5-Large...")
        
        # Prepara lista de textos e IDs
        textos = [get_clean_text_for_embedding(n) for n in noticias]
        ids_map = [n['_id'] for n in noticias]
        
        # 1. Gera embeddings 
        print("Gerando vetores semânticos...")
        embeddings = model.encode(
            textos, 
            batch_size=16, 
            show_progress_bar=True, 
            normalize_embeddings=True 
        )

        # 2. Agrupa (Hierarchical Clustering)
        # Linkage 'complete' é essencial para evitar o "super-cluster"
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