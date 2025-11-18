# scraper/recipes/bbc_brasil.py (VERSÃO CORRIGIDA)

import requests
from bs4 import BeautifulSoup
from datetime import datetime

def coletar_bbc_brasil():
    """
    Coleta notícias da BBC News Brasil (Seção Brasil) usando requests/BeautifulSoup.
    Ajustado para as classes específicas da lista.
    """
    BASE_URL = "https://www.bbc.com/portuguese/brasil" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE: O contêiner <li> principal
        # Usamos a classe mais específica da lista de notícias:
        blocos_noticia = soup.find_all('li', class_='bbc-t44f9r') 

        for bloco in blocos_noticia:
            # O link e o título estão dentro de div class="promo-text"
            titulo_tag = bloco.find('h2', class_='bbc-1slyjq2')
            link_tag = bloco.find('a', class_='bbc-1i4ie53') # O link dentro do <h2>

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                # A BBC usa links relativos, precisamos torná-los absolutos
                if link.startswith('/'):
                    link = "https://www.bbc.com" + link
                
                # O texto para IA/Agrupamento será o título
                texto_analise_ia = titulo 
                
                noticias_coletadas.append({
                    "nome_fonte": "BBC Brasil",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
        
        print(f"BBC Brasil: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar BBC Brasil: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping da BBC Brasil: {e}")
        return []