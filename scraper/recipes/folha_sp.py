# scraper/recipes/folha_sp.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime

def coletar_folha_sp():
    """
    Coleta notícias da Folha de S.Paulo usando o método requests/BeautifulSoup,
    o que é possível pois o conteúdo é carregado estaticamente.
    """
    BASE_URL = "https://www1.folha.uol.com.br/poder/" # Seção de Política/Poder
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        # O bloco que contém o título, o resumo e o link.
        blocos_noticia = soup.find_all('div', class_='c-headline__content') 

        for bloco in blocos_noticia:
            link_tag = bloco.find('a', class_='c-headline__url')
            titulo_tag = bloco.find('h2', class_='c-headline__title')
            resumo_tag = bloco.find('p', class_='c-headline__standfirst') 

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                # Resumo para a IA e Agrupamento
                resumo = resumo_tag.text.strip() if resumo_tag else ""
                
                # Juntamos título e resumo. Isso é o 'Texto para Análise de Viés'.
                texto_analise_ia = f"{titulo}. {resumo}"
                
                noticias_coletadas.append({
                    "nome_fonte": "Folha de S.Paulo",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
        
        print(f"Folha de S.Paulo: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro de requisição ao coletar Folha: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping da Folha: {e}")
        return []

if __name__ == '__main__':
    dados_folha = coletar_folha_sp()
    for item in dados_folha:
        print(f"Título: {item['titulo']} | Resumo: {item['texto_analise_ia']}")