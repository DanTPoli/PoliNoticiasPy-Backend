# scraper/recipes/veja.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime

def coletar_veja():
    """
    Coleta notícias da Revista Veja (Seção Política).
    Ajustado para os seletores exatos fornecidos (card not-loaded list-item).
    """
    # URL da seção Política
    BASE_URL = "https://veja.abril.com.br/politica/" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE: O container principal
        blocos_noticia = soup.find_all('div', class_='list-item') 

        for bloco in blocos_noticia:
            # 2. EXTRAINDO LINK E TÍTULO
            # O link é a tag <a> que está logo antes do <h2>
            link_tag = bloco.find('a', title=True) 
            titulo_tag = bloco.find('h2', class_='title')
            
            # Não há resumo claro no bloco, então usamos o título
            resumo = ""
            
            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                texto_analise_ia = titulo
                
                noticias_coletadas.append({
                    "nome_fonte": "Veja",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
        
        print(f"Revista Veja: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Revista Veja: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping da Revista Veja: {e}")
        return []