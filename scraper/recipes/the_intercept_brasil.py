import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_the_intercept_brasil():
    """
    Coleta notícias do The Intercept Brasil com Deep Scraping.
    Baseado na estrutura <article class="feed ...">.
    """
    BASE_URL = "https://www.intercept.com.br/" 
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        # O Intercept usa article com classe feed (ex: feed-xl-v2, feed-lg, etc)
        blocos_noticia = soup.find_all('article', class_=lambda c: c and 'feed' in c)

        count = 0

        for bloco in blocos_noticia:
            if count >= 8: break

            # 2. EXTRAINDO LINK E TÍTULO
            # O link envolve o conteúdo ou está dentro
            link_tag = bloco.find('a', href=True)
            
            # O título é um h2 com classe feed-title
            titulo_tag = bloco.find('h2', class_='feed-title')

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                if not link or len(titulo) < 5:
                    continue

                # Extrai o resumo do cartão (excelente no Intercept)
                resumo_tag = bloco.find('p', class_='feed-excert')
                resumo_capa = resumo_tag.text.strip() if resumo_tag else ""

                # --- DEEP SCRAPING ---
                print(f"   [The Intercept] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    # Fallback robusto: O resumo do Intercept é muito bom
                    texto_analise_ia = f"{titulo}. {resumo_capa}" if resumo_capa else titulo
                
                noticias_coletadas.append({
                    "nome_fonte": "The Intercept Brasil",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"The Intercept: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar The Intercept: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping do The Intercept: {e}")
        return []