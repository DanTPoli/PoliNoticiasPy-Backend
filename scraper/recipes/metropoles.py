# scraper/recipes/metropoles.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime

def coletar_metropoles():
    """
    Coleta notícias do Metrópoles (Seção Brasil).
    Ajustado para os seletores exatos fornecidos (NoticiaWrapper).
    """
    # URL da seção Brasil
    BASE_URL = "https://www.metropoles.com/brasil" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE: O container <article> principal
        # Usamos uma classe parcial para maior estabilidade, se necessário, ou a classe mais específica.
        blocos_noticia = soup.find_all('article', class_=lambda c: c and 'NoticiaWrapper__Article' in c) 

        for bloco in blocos_noticia:
            # 2. EXTRAINDO LINK, TÍTULO E RESUMO
            # O link está no <a> dentro do <h4>
            titulo_tag = bloco.find('h4', class_=lambda c: c and 'noticia__titulo' in c)
            link_tag = titulo_tag.find('a', href=True) if titulo_tag else None
            
            # O resumo está na tag <p> com a classe 'noticia__descricao'
            descricao_div = bloco.find('div', class_=lambda c: c and 'noticia__descricao' in c)
            resumo_tag = descricao_div.find('p') if descricao_div else None

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                # Resumo para a IA e Agrupamento
                resumo = resumo_tag.text.strip() if resumo_tag else ""
                texto_analise_ia = f"{titulo}. {resumo}"
                
                noticias_coletadas.append({
                    "nome_fonte": "Metrópoles",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
        
        print(f"Metrópoles: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Metrópoles: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping do Metrópoles: {e}")
        return []