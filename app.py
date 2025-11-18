import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from pymongo import MongoClient
from bson.json_util import dumps
from operator import itemgetter 

# --- 1. CONFIGURAÇÃO DE AMBIENTE E DB ---
load_dotenv() 
MONGO_URI = os.getenv("MONGO_URI") 

app = Flask(__name__)

try:
    client = MongoClient(MONGO_URI)
    db = client.polinoticias_db 
    noticias_collection = db.noticias_raw
    print("API: Conectada ao ClusterPoliNoticias com sucesso.")
except Exception as e:
    print(f"API: Falha na conexão com o DB! Erro: {e}")
    client = None
    noticias_collection = None


# --- FUNÇÃO DE MÁPEAMENTO DE VIÉS (NOVO) ---
def mapear_viés(viés_num):
    """Mapeia a classificação numérica média de viés para uma string descritiva (UX)."""
    if viés_num is None: return "Dados Ausentes"
    if viés_num <= -2.0:
        return "Extrema-Esquerda"
    if viés_num <= -1.0:
        return "Esquerda"
    if viés_num <= -0.5:
        return "Centro-Esquerda"
    if viés_num <= 0.5:
        return "Centro"
    if viés_num <= 1.0:
        return "Centro-Direita"
    if viés_num <= 2.0:
        return "Direita"
    return "Extrema-Direita" # Viés > 2.0

# --- FUNÇÃO DE CÁLCULO DE POSIÇÃO PARA O GRADIENTE (FALTANDO) ---
def calcular_posicao_gradiente(viés_num):
    """Converte a escala de -3 a +3 para a escala de 0 a 100% para o gradiente."""
    if viés_num is None: return 50.0 # Se não houver dados, centraliza (50%)
    min_vies = -3.0
    max_vies = 3.0
    
    # Mapeamento linear: (-3) -> 0%; (0) -> 50%; (+3) -> 100%
    viés_clamped = max(min_vies, min(max_vies, viés_num))
    posicao_percentual = ((viés_clamped - min_vies) / (max_vies - min_vies)) * 100
    
    return round(posicao_percentual, 1)


# --- 2. ROTA DA API PARA O FEED AGRUPADO ---
@app.route('/api/feed', methods=['GET'])
def get_feed_agrupado():
    if noticias_collection is None:
        return jsonify({"error": "Banco de dados indisponível."}), 500

    try:
        # Pipeline de Agregação do MongoDB
        pipeline = [
            {"$match": {"id_cluster": {"$ne": None}}},
            {"$group": {
                "_id": "$id_cluster",
                "links": {
                    "$push": {
                        "titulo": "$titulo",
                        "url": "$url",
                        "fonte": "$nome_fonte",
                        "vies": "$viés_classificado",
                        "data": "$data_coleta"
                    }
                },
                "total_links": {"$sum": 1},
                "media_vies": {"$avg": "$viés_classificado"}
            }},
            {"$match": {"total_links": {"$gt": 1}}},
        ]
        
        feed_agregado = list(noticias_collection.aggregate(pipeline))
        
        # 5. Lógica de Seleção do LEAD, Ordenação e Mapeamento de Viés
        final_feed = []
        for cluster in feed_agregado:
            sorted_links = sorted(cluster['links'], key=itemgetter('vies')) 
            lead_link = min(cluster['links'], key=lambda x: abs(x['vies'] if x['vies'] is not None else 3.0))

            cluster_data = {
                "cluster_id": cluster['_id'],
                "total_fontes": cluster['total_links'],
                "media_vies_num": cluster['media_vies'],
                "viés_descritivo": mapear_viés(cluster['media_vies']), 
                "gradiente_posicao": calcular_posicao_gradiente(cluster['media_vies']), # <-- ADICIONADO
                "lead_titulo": lead_link['titulo'],
                "lead_fonte": lead_link['fonte'],
                "lead_vies_num": lead_link['vies'],
                "links_ordenados": sorted_links 
            }
            final_feed.append(cluster_data)
        
        # 6. ORDENAÇÃO POR RELEVÂNCIA (total_fontes)
        final_feed_ordenado = sorted(final_feed, key=itemgetter('total_fontes'), reverse=True)

        # Converte a lista final para JSON
        feed_json = dumps(final_feed_ordenado)
        
        return app.response_class(
            response=feed_json,
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        print(f"Erro na rota /api/feed: {e}")
        return jsonify({"error": "Erro interno ao buscar dados agrupados."}), 500


# --- 3. INICIALIZAÇÃO ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)