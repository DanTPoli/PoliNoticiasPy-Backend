import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_correio_braziliense():
    """
    Coleta notícias do Correio Braziliense com Deep Scraping (lê o conteúdo do link).
    """
    BASE_URL = "https://www.correiobraziliense.com.br/politica" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        blocos_li = soup.find_all('li') 
        
        count = 0

        for li_tag in blocos_li:
            if count >= 8: break

            # 2. EXTRAINDO O LINK (o <a> principal)
            link_tag = li_tag.find('a', href=True) 
            
            # 3. ENCONTRANDO TÍTULO dentro do ARTICLE
            box_text = li_tag.find('div', class_='box-text')
            titulo_tag = box_text.find('h2') if box_text else None

            # Só processamos se encontrarmos o link e o título
            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                if link.startswith('/'):
                    link = "https://www.correiobraziliense.com.br" + link
                
                # --- DEEP SCRAPING ---
                print(f"   [Correio] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    texto_analise_ia = titulo
                
                noticias_coletadas.append({
                    "nome_fonte": "Correio Braziliense",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"Correio Braziliense: {len(noticias_coletadas)} notícias coletadas com conteúdo profundo.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Correio Braziliense: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping do Correio Braziliense: {e}")
        return []