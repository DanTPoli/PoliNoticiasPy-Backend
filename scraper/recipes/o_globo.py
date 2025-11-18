import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_o_globo():
    """
    Coleta notícias de O Globo com Deep Scraping (lê o conteúdo do link).
    Ajustado para os seletores da seção fornecida.
    """
    # URL da seção (mantendo a que você estava usando)
    BASE_URL = "https://oglobo.globo.com/politica/" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        blocos_noticia = soup.find_all('div', class_='feed-post bstn-item-shape type-materia') 

        count = 0

        for bloco in blocos_noticia:
            if count >= 10: break

            # 2. EXTRAINDO LINK E TÍTULO
            link_tag = bloco.find('a', class_='feed-post-link')
            titulo_tag = bloco.find('h2', class_='feed-post-link')
            resumo_tag = bloco.find('p', class_='feed-post-body-resumo')

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                # --- DEEP SCRAPING ---
                print(f"   [O Globo] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    # Fallback: usa o resumo da capa
                    resumo = resumo_tag.text.strip() if resumo_tag else ""
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
                count += 1
        
        print(f"O Globo: {len(noticias_coletadas)} notícias coletadas com conteúdo profundo.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar O Globo: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping de O Globo: {e}")
        return []