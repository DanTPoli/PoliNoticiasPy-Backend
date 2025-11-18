import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_bbc_brasil():
    """
    Coleta notícias da BBC News Brasil com Deep Scraping (lê o conteúdo do link).
    """
    BASE_URL = "https://www.bbc.com/portuguese/brasil" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        blocos_noticia = soup.find_all('li', class_='bbc-t44f9r') 

        # Contador para evitar timeout durante testes (lê apenas as 8 primeiras)
        count = 0

        for bloco in blocos_noticia:
            if count >= 8: break 

            titulo_tag = bloco.find('h2', class_='bbc-1slyjq2')
            link_tag = bloco.find('a', class_='bbc-1i4ie53')

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                if link.startswith('/'):
                    link = "https://www.bbc.com" + link
                
                # --- DEEP SCRAPING: Extraindo conteúdo real ---
                print(f"   [BBC] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                # Se conseguiu extrair o parágrafo, usa ele. Senão, fica só com o título.
                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    texto_analise_ia = titulo
                
                noticias_coletadas.append({
                    "nome_fonte": "BBC Brasil",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"BBC Brasil: {len(noticias_coletadas)} notícias coletadas com conteúdo profundo.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar BBC Brasil: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping da BBC Brasil: {e}")
        return []