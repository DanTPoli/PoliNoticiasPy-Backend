import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_gazeta_do_povo():
    """
    Coleta notícias da Gazeta do Povo com Deep Scraping (lê o conteúdo do link).
    """
    # Usando a URL da seção 'República' (Política)
    BASE_URL = "https://www.gazetadopovo.com.br/republica/" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        blocos_noticia = soup.find_all('article', class_='cardDefault_card-container___OSdW') 

        count = 0

        for bloco in blocos_noticia:
            if count >= 8: break

            # 2. EXTRAINDO LINK E TÍTULO
            link_tag = bloco.find('a', class_='cardDefault_title__ZpYJb')
            titulo_tag = bloco.find('h2')

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                if link.startswith('/'):
                    link = "https://www.gazetadopovo.com.br" + link

                # --- DEEP SCRAPING ---
                print(f"   [Gazeta] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    texto_analise_ia = titulo
                
                noticias_coletadas.append({
                    "nome_fonte": "Gazeta do Povo",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"Gazeta do Povo: {len(noticias_coletadas)} notícias coletadas com conteúdo profundo.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Gazeta do Povo: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping da Gazeta do Povo: {e}")
        return []