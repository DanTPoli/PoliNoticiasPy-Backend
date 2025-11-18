#!/bin/bash
# Script de execução da cadeia de processamento do PoliNotícias

# 1. Coletor (Scraper)
python3 scraper/collector.py

# 2. Agrupamento (Clusterização)
python3 analysis/cluster_manager.py

# 3. Classificação de Viés (IA)
python3 analysis/bias_classifier_bert.py

echo "Processamento de PoliNotícias concluído."