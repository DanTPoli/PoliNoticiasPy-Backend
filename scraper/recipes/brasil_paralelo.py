import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_brasil_paralelo():
    """
    Coleta notícias da Brasil Paralelo (Seção Notícias) com Deep Scraping.
    Baseado na estrutura <div class="_00-news-latest-item">.
    """
    BASE_URL = "https://www.brasilparalelo.com.br/noticias" 
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        # Baseado na classe do container fornecido
        blocos_noticia = soup.find_all('div', class_='_00-news-latest-item')

        count = 0

        for bloco in blocos_noticia:
            if count >= 8: break

            # 2. EXTRAINDO LINK E TÍTULO
            # O link tem a classe '_00-hobbit'
            link_tag = bloco.find('a', class_='_00-hobbit', href=True)
            
            if link_tag:
                link = link_tag.get('href')
                
                # O título está numa tag h3 com a classe '_00-hobbit-title'
                titulo_tag = link_tag.find('h3', class_='_00-hobbit-title')
                titulo = titulo_tag.text.strip() if titulo_tag else ""
                
                # Validações
                if not link or len(titulo) < 5:
                    continue

                # --- DEEP SCRAPING ---
                # O card não tem resumo, então a leitura é obrigatória para contexto
                print(f"   [Brasil Paralelo] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    # Fallback: Apenas o título (card não tem lead/resumo)
                    texto_analise_ia = titulo
                
                noticias_coletadas.append({
                    "nome_fonte": "Brasil Paralelo",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"Brasil Paralelo: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Brasil Paralelo: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping do Brasil Paralelo: {e}")
        return []