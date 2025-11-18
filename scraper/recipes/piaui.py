# scraper/recipes/piaui.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime

def coletar_piaui():
    """
    Coleta notícias da Revista Piauí (Homepage/Artigos mais recentes).
    Ajustado para os seletores exatos fornecidos (main__noticia).
    """
    BASE_URL = "https://piaui.folha.uol.com.br/" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE: O container <div class="main__noticia">
        # Buscamos por todas as tags que tenham a classe 'main__noticia'
        blocos_noticia = soup.find_all('div', class_=lambda c: c and 'main__noticia' in c) 

        for bloco in blocos_noticia:
            # O link, título e resumo estão no bloco de info
            info_div = bloco.find('div', class_='main__noticia--destaque--info')
            
            # 2. EXTRAINDO LINK, TÍTULO E RESUMO
            # O link é o 'href' da tag <a> que encapsula o título
            titulo_tag = info_div.find('h2', class_='main__noticia--destaque--title') if info_div else None
            link_tag = titulo_tag.find_parent('a', href=True) if titulo_tag else None
            
            resumo_tag = info_div.find('p', class_='main__noticia--desc') if info_div else None

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                # Resumo para a IA e Agrupamento
                resumo = resumo_tag.text.strip() if resumo_tag else ""
                texto_analise_ia = f"{titulo}. {resumo}"
                
                noticias_coletadas.append({
                    "nome_fonte": "Revista Piauí",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
        
        print(f"Revista Piauí: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Revista Piauí: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping da Revista Piauí: {e}")
        return []