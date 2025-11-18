import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_carta_capital():
    """
    Coleta notícias da Carta Capital com Deep Scraping (lê o conteúdo do link).
    """
    BASE_URL = "https://www.cartacapital.com.br/politica/" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # O seletor que identificamos anteriormente (pode ser 'article' ou 'a')
        # Usamos 'a' com a classe 'nc-opening__item' para os destaques ou
        # procuramos pela lista padrão se o layout mudou.
        # Vamos manter o seletor robusto que funcionou antes:
        blocos_noticia = soup.find_all('a', class_='nc-opening__item') 
        
        # Se não achar nada com o seletor de destaque, tenta o de lista comum
        if not blocos_noticia:
             blocos_noticia = soup.find_all('article', class_='loop-item')

        count = 0

        for bloco in blocos_noticia:
            if count >= 8: break 

            # Lógica híbrida dependendo do tipo de bloco encontrado
            if bloco.name == 'a':
                link = bloco.get('href')
                titulo_tag = bloco.find('h2')
            else:
                # É um article
                link_tag = bloco.find('a', href=True)
                link = link_tag.get('href') if link_tag else None
                titulo_tag = bloco.find('h2', class_='loop-item__title')

            if link and titulo_tag:
                titulo = titulo_tag.text.strip()
                
                # --- DEEP SCRAPING ---
                print(f"   [Carta] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    texto_analise_ia = titulo
                
                noticias_coletadas.append({
                    "nome_fonte": "Carta Capital",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"Carta Capital: {len(noticias_coletadas)} notícias coletadas com conteúdo profundo.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Carta Capital: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping da Carta Capital: {e}")
        return []