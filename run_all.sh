#!/bin/bash

# Script OTIMIZADO para PythonAnywhere (Cota de Disco)
# Executa apenas a coleta de dados leve.
# A IA (Clusterização e Viés) deve ser executada localmente no seu PC.

echo "Iniciando Coleta (Modo Leve)..."

# Executa o coletor. 
# As fontes que exigem Playwright serão puladas automaticamente.
python3 scraper/collector.py

echo "Coleta finalizada. Dados salvos no MongoDB."