import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson.json_util import dumps
from operator import itemgetter 
import certifi
import re

from datetime import datetime, timezone

# --- 1. CONFIGURAÇÃO ---
load_dotenv() 
MONGO_URI = os.getenv("MONGO_URI") 

app = Flask(__name__)
CORS(app)

try:
    # Conexão segura com certificado SSL
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.polinoticias_db 
    noticias_collection = db.noticias_raw
    usuarios_collection = db.usuarios_perfil
    feedbacks_collection = db.feedbacks
    notificacoes_collection = db.notificacoes
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

            # --- Adiciona o texto descritivo em cada link ---
            for link in sorted_links:
                # Cria o campo 'vies_texto' baseado no número 'vies'
                link['vies_texto'] = mapear_viés(link.get('vies'))
            
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
    
# --- ROTA DE ESCRITA USERS ---

@app.route('/api/user/clique', methods=['POST'])
def registrar_clique():
    data = request.json
    uid = data.get('uid')
    vies_novo = data.get('vies')
    fonte = data.get('fonte')

    if not uid or vies_novo is None or not fonte:
        return jsonify({"error": "Dados incompletos"}), 400

    fonte_limpa = fonte.replace(".", "_")

    try:
        # 1. Buscamos o estado atual do usuário para o cálculo
        usuario = usuarios_collection.find_one({"uid": uid})
        
        if usuario:
            n = usuario.get("total_cliques", 0)
            media_antiga = usuario.get("vies_medio", 0)
            # Cálculo da média móvel
            nova_media = ((media_antiga * n) + vies_novo) / (n + 1)
        else:
            # Primeiro acesso do usuário
            nova_media = vies_novo

        # 2. Update atômico no MongoDB
        usuarios_collection.update_one(
            {"uid": uid},
            {
                "$set": {
                    "vies_medio": round(nova_media, 4), # Salva a média móvel
                    "ultima_atividade": datetime.now(timezone.utc)
                },
                "$inc": {
                    "total_cliques": 1,
                    f"frequencia_fontes.{fonte_limpa}": 1 # Frequência de acessos
                }
            },
            upsert=True
        )
        return jsonify({"status": "sucesso", "nova_media": nova_media}), 200
    except Exception as e:
        print(f"Erro no Mongo: {e}")
        return jsonify({"error": str(e)}), 500

# --- ROTA DE LEITURA USERS ---   

@app.route('/api/user/stats/<uid>', methods=['GET'])
def get_user_stats(uid):
    if usuarios_collection is None:
        return jsonify({"error": "Banco de dados offline"}), 500

    try:
        # Busca o perfil do usuário pelo UID único
        usuario = usuarios_collection.find_one({"uid": uid}, {"_id": 0})
        
        if not usuario:
            return jsonify({
                "vies_medio": 0,
                "total_cliques": 0,
                "frequencia_fontes": {},
                "mensagem": "Nenhum dado encontrado ainda."
            }), 200

        return jsonify(usuario), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# --- ROTA DE FEEDBACK (ANÔNIMO) ---

@app.route('/api/feedback', methods=['POST'])
def enviar_feedback():
    data = request.json
    conteudo = data.get('conteudo')

    if not conteudo:
        return jsonify({"error": "A mensagem não pode estar vazia"}), 400

    try:
        feedbacks_collection.insert_one({
            "conteudo": conteudo,
            "data_criacao": datetime.now(timezone.utc)
        })
        return jsonify({"status": "sucesso", "message": "Feedback registrado"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/feedback', methods=['GET'])
def listar_feedbacks():
    try:
        # Busca os 10 mais recentes, excluindo o _id para facilitar o JSON
        feedbacks = list(feedbacks_collection.find({}, {"_id": 0})
                         .sort("data_criacao", -1)
                         .limit(10))
        
        # Como o campo data_criacao é um objeto datetime, o jsonify do Flask 
        # pode ter problemas. Podemos converter para string ou usar o dumps do BSON.
        return app.response_class(
            response=dumps(feedbacks),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/notificacao-admin', methods=['GET'])
def get_notificacao_admin():
    try:
        # Busca a mais recente (data desc) que esteja ativa
        notificacao = notificacoes_collection.find_one(
            {"ativa": True}, 
            {"_id": 0}, 
            sort=[("data_criacao", -1)]
        )
        
        if not notificacao:
            return jsonify(None), 200
            
        return app.response_class(
            response=dumps(notificacao),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)