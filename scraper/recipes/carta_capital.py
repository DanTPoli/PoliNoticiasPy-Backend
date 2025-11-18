# scraper/recipes/carta_capital.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime

def coletar_carta_capital():
    """
    Coleta notícias da Carta Capital (Seção Política).
    Ajustado para os seletores exatos fornecidos (nc-opening__item).
    """
    BASE_URL = "https://www.cartacapital.com.br/politica/" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE: O link principal que envolve a notícia
        blocos_noticia = soup.find_all('a', class_='nc-opening__item') 

        for link_tag in blocos_noticia:
            # 2. EXTRAINDO DADOS DENTRO DO LINK
            link = link_tag.get('href')
            
            # O título está no <h2> dentro da div nc-opening__text
            titulo_tag = link_tag.find('h2')
            resumo_tag = link_tag.find('p')

            if link and titulo_tag:
                titulo = titulo_tag.text.strip()
                
                # Resumo para a IA e Agrupamento
                resumo = resumo_tag.text.strip() if resumo_tag else ""
                texto_analise_ia = f"{titulo}. {resumo}"
                
                noticias_coletadas.append({
                    "nome_fonte": "Carta Capital",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
        
        print(f"Carta Capital: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Carta Capital: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping da Carta Capital: {e}")
        return []