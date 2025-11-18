import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson.json_util import dumps
from operator import itemgetter 
import certifi
import re

# --- 1. CONFIGURAÇÃO ---
load_dotenv() 
MONGO_URI = os.getenv("MONGO_URI") 

app = Flask(__name__)

try:
    # Conexão segura com certificado SSL
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.polinoticias_db 
    noticias_collection = db.noticias_raw
    print("API: Conectada com sucesso.")
except Exception as e:
    print(f"API: Falha na conexão! {e}")
    client = None
    noticias_collection = None

# --- FUNÇÕES AUXILIARES ---
def mapear_viés(viés_num):
    if viés_num is None: return "Dados Ausentes"
    if viés_num <= -2.0: return "Extrema-Esquerda"
    if viés_num <= -1.0: return "Esquerda"
    if viés_num <= -0.5: return "Centro-Esquerda"
    if viés_num <= 0.5: return "Centro"
    if viés_num <= 1.0: return "Centro-Direita"
    if viés_num <= 2.0: return "Direita"
    return "Extrema-Direita"

def calcular_posicao_gradiente(viés_num):
    if viés_num is None: return 50.0 
    min_vies, max_vies = -3.0, 3.0
    viés_clamped = max(min_vies, min(max_vies, viés_num))
    return round(((viés_clamped - min_vies) / (max_vies - min_vies)) * 100, 1)

# --- ROTA DO FEED ---
@app.route('/api/feed', methods=['GET'])
def get_feed_agrupado():
    if noticias_collection is None:
        return jsonify({"error": "DB indisponível"}), 500

    try:
        # 1. Captura a categoria da URL (Ex: /api/feed?category=Politica)
        categoria_filtro = request.args.get('category')
        
        # Filtro base: Apenas notícias já processadas (com cluster)
        match_stage = {"id_cluster": {"$ne": None}}

        # Se houver categoria selecionada (e não for "Todos"), adiciona ao filtro
        if categoria_filtro and categoria_filtro != "Todos":
            # Cria uma expressão regular para buscar no título ou categoria (case insensitive)
            regex = re.compile(categoria_filtro, re.IGNORECASE)
            match_stage["$or"] = [
                {"categoria": regex},   # Se o scraper coletou a categoria
                {"titulo": regex},      # Fallback: procura no título
                {"texto_analise_ia": regex} # Procura no conteúdo
            ]

        pipeline = [
            {"$match": match_stage}, # Aplica o filtro ANTES de agrupar
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
            {"$match": {"total_links": {"$gt": 1}}}, # Garante relevância
        ]
        
        feed_agregado = list(noticias_collection.aggregate(pipeline))
        
        final_feed = []
        for cluster in feed_agregado:
            # Ordena links internos pelo viés (-3 a +3)
            sorted_links = sorted(cluster['links'], key=lambda x: x['vies'] if x['vies'] is not None else 0) 
            
            # Lead neutro (protegido contra None)
            lead_link = min(cluster['links'], key=lambda x: abs(x['vies'] if x['vies'] is not None else 0))

            # Proteção se media_vies for None
            media_vies = cluster.get('media_vies', 0) or 0

            cluster_data = {
                "cluster_id": cluster['_id'],
                "total_fontes": cluster['total_links'],
                "viés_descritivo": mapear_viés(media_vies), 
                "gradiente_posicao": calcular_posicao_gradiente(media_vies),
                "lead_titulo": lead_link['titulo'],
                "lead_fonte": lead_link['fonte'],
                "links_ordenados": sorted_links 
            }
            final_feed.append(cluster_data)
        
        # Ordena feed final por número de fontes (relevância)
        final_feed_ordenado = sorted(final_feed, key=itemgetter('total_fontes'), reverse=True)

        return app.response_class(response=dumps(final_feed_ordenado), status=200, mimetype='application/json')

    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)