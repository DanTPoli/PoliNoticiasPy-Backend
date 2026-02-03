import os
import sys
import csv
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Ajuste do path para alcançar a pasta 'analysis'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from analysis.bias_classifier_e5 import classificar_vies_e5
except ImportError as e:
    print(f"❌ Erro ao importar o classificador: {e}")
    sys.exit(1)

load_dotenv()

def run_recalculation():
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = "polinoticias_db"
    COLLECTION_NAME = "noticias_raw"

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    cluster_id = sys.argv[1] if len(sys.argv) > 1 else None
    query = {"cluster_id": cluster_id} if cluster_id else {}

    noticias = list(collection.find(query))
    total = len(noticias)

    if total == 0:
        print("📭 Nenhuma notícia encontrada.")
        return

    # Lista para armazenar os dados do CSV
    log_comparativo = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"comparativo_vies_{timestamp}.csv"

    print(f"🚀 Processando {total} notícias. Log será salvo em: {csv_filename}")

    updated_count = 0
    for n in noticias:
        texto = n.get('texto_analise_ia', n.get('titulo', ''))
        fonte = n.get('nome_fonte', 'Desconhecida')
        score_antigo = n.get('viés_classificado', 0.0)

        if texto:
            # Novo cálculo com as alterações que você fez no analysis/bias_classifier_e5.py
            novo_score = classificar_vies_e5(texto, fonte)
            
            # Atualiza o banco
            collection.update_one({"_id": n['_id']}, {"$set": {"viés_classificado": novo_score}})
            
            # Adiciona ao log
            log_comparativo.append({
                "ID": str(n['_id']),
                "Fonte": fonte,
                "Titulo": n.get('titulo', 'Sem título')[:100], # Limitado para não quebrar o CSV
                "Score_Antigo": score_antigo,
                "Score_Novo": novo_score,
                "Diferenca": round(novo_score - score_antigo, 2)
            })
            
            updated_count += 1
            if updated_count % 10 == 0:
                print(f"⏳ {updated_count}/{total} concluídas...")

    # Salva o arquivo CSV
    keys = log_comparativo[0].keys() if log_comparativo else []
    if keys:
        with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(log_comparativo)

    print(f"\n✨ Sucesso! {updated_count} notícias atualizadas.")
    print(f"📊 Arquivo de log gerado: {os.path.abspath(csv_filename)}")
    client.close()

if __name__ == "__main__":
    run_recalculation()