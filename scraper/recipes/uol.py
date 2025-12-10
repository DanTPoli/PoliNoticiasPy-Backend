import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_uol():
    """
    Coleta notícias da capa do UOL com Deep Scraping.
    Baseado na estrutura de 'thumbnails-item'.
    """
    BASE_URL = "https://www.uol.com.br/" 
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        # O UOL usa 'thumbnails-item' para os cards da home
        blocos_noticia = soup.find_all('div', class_='thumbnails-item')

        count = 0

        for bloco in blocos_noticia:
            if count >= 8: break

            # 2. EXTRAINDO LINK E TÍTULO
            link_tag = bloco.find('a', href=True)
            # O título fica dentro de um h3 com a classe 'thumb-title'
            titulo_tag = bloco.find('h3', class_='thumb-title')

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                # Filtros básicos de qualidade
                if not link or len(titulo) < 5:
                    continue
                
                # Ignora links de publicidade ou especiais que não são notícias reais
                if "uol.com.br/especiais" in link or "publicidade" in link:
                    continue

                # --- DEEP SCRAPING ---
                print(f"   [UOL] Lendo conteúdo: {titulo[:30]}...")
                
                # O UOL agrega Folha, Estadão, etc. O extrator genérico tentará lidar com isso.
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    # Fallback: UOL geralmente não tem resumo no card, usa só o título
                    texto_analise_ia = titulo
                
                noticias_coletadas.append({
                    "nome_fonte": "UOL",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"UOL: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar UOL: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping do UOL: {e}")
        return []