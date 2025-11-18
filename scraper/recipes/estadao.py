# scraper/recipes/estadao.py (VERSÃO CORRIGIDA)

import requests
from bs4 import BeautifulSoup
from datetime import datetime

def coletar_estadao():
    """
    Coleta notícias do Estadão (Seção Política).
    Ajustado para os seletores exatos fornecidos.
    """
    BASE_URL = "https://www.estadao.com.br/politica/" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE: O container principal da notícia
        # Buscamos por uma classe que contenha 'noticia-single-block' para cobrir a maioria dos formatos.
        blocos_noticia = soup.find_all('div', class_=lambda c: c and 'noticia-single-block' in c) 

        for bloco in blocos_noticia:
            # 2. EXTRAINDO LINK, TÍTULO E RESUMO
            link_tag = bloco.find('a', href=True)
            titulo_tag = bloco.find('h2', class_='headline')
            resumo_tag = bloco.find('div', class_='subheadline')

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                
                # O título está dentro de <b>, extraímos o texto limpo
                titulo = titulo_tag.text.strip()
                
                # Resumo para a IA e Agrupamento
                resumo = resumo_tag.text.strip() if resumo_tag else ""
                texto_analise_ia = f"{titulo}. {resumo}"
                
                noticias_coletadas.append({
                    "nome_fonte": "Estadão",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
        
        print(f"Estadão: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Estadão: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping do Estadão: {e}")
        return []