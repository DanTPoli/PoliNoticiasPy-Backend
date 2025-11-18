# scraper/recipes/o_globo.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime

def coletar_o_globo():
    """
    Coleta notícias de O Globo (Seção COP 30 Amazônia).
    Ajustado para os seletores exatos fornecidos.
    """
    # URL da seção COP 30 Amazônia (como no seu HTML)
    BASE_URL = "https://oglobo.globo.com/brasil/cop-30-amazonia/" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE: O container de cada matéria
        blocos_noticia = soup.find_all('div', class_='feed-post bstn-item-shape type-materia') 

        for bloco in blocos_noticia:
            # O link e o título estão na tag <h2>
            link_tag = bloco.find('a', class_='feed-post-link')
            titulo_tag = bloco.find('h2', class_='feed-post-link')
            
            # O resumo para o texto de análise (muito importante para a IA)
            resumo_tag = bloco.find('p', class_='feed-post-body-resumo')

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                # Resumo para a IA e Agrupamento
                resumo = resumo_tag.text.strip() if resumo_tag else ""
                # O texto para análise de viés será a junção de Título e Resumo
                texto_analise_ia = f"{titulo}. {resumo}"
                
                noticias_coletadas.append({
                    "nome_fonte": "O Globo",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
        
        print(f"O Globo: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar O Globo: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping de O Globo: {e}")
        return []