# scraper/recipes/correio_braziliense.py (VERSÃO CORRIGIDA)

import requests
from bs4 import BeautifulSoup
from datetime import datetime

def coletar_correio_braziliense():
    """
    Coleta notícias do Correio Braziliense (Seção Política).
    Ajustado para buscar todos os itens de lista que contêm o bloco de texto.
    """
    BASE_URL = "https://www.correiobraziliense.com.br/politica" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE: Buscamos pelo container de lista principal
        # Vamos buscar por todos os <li> tags.
        # Um seletor mais específico poderia ser necessário se o site tivesse múltiplas listas <ul>.
        blocos_li = soup.find_all('li') 
        
        for li_tag in blocos_li:
            # 2. EXTRAINDO O LINK (o <a> principal)
            link_tag = li_tag.find('a', href=True) # Busca o primeiro link dentro do <li>
            
            # 3. ENCONTRANDO TÍTULO E RESUMO dentro do ARTICLE
            box_text = li_tag.find('div', class_='box-text')
            titulo_tag = box_text.find('h2') if box_text else None
            resumo_tag = box_text.find('p') if box_text else None

            # Só processamos se encontrarmos o link e o título
            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                # O CB usa links relativos, precisamos torná-los absolutos
                if link.startswith('/'):
                    link = "https://www.correiobraziliense.com.br" + link
                
                # Resumo para a IA e Agrupamento
                # A tag <p> no HTML que você forneceu estava vazia, mas a mantemos
                # no caso de outros itens a preencherem.
                resumo = resumo_tag.text.strip() if resumo_tag else ""
                texto_analise_ia = f"{titulo}. {resumo}"
                
                noticias_coletadas.append({
                    "nome_fonte": "Correio Braziliense",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
        
        print(f"Correio Braziliense: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Correio Braziliense: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping do Correio Braziliense: {e}")
        return []