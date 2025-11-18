# scraper/recipes/gazeta_do_povo.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime

def coletar_gazeta_do_povo():
    """
    Coleta notícias da Gazeta do Povo (Seção República).
    Ajustado para os seletores exatos fornecidos (cardDefault).
    """
    # Usando a URL da seção 'República' (Política)
    BASE_URL = "https://www.gazetadopovo.com.br/republica/" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE: O container <article>
        blocos_noticia = soup.find_all('article', class_='cardDefault_card-container___OSdW') 

        for bloco in blocos_noticia:
            # 2. EXTRAINDO LINK E TÍTULO
            # O link principal e o título estão na tag <a> com classe cardDefault_title
            link_tag = bloco.find('a', class_='cardDefault_title__ZpYJb')
            titulo_tag = bloco.find('h2')

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                # O texto para análise de viés será o título (lead)
                texto_analise_ia = titulo
                
                noticias_coletadas.append({
                    "nome_fonte": "Gazeta do Povo",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
        
        print(f"Gazeta do Povo: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Gazeta do Povo: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping da Gazeta do Povo: {e}")
        return []