import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_forbes_brasil():
    """
    Coleta notícias da Forbes Brasil (Últimas Notícias) com Deep Scraping.
    Baseado na estrutura <a><article class="row">...</a>.
    """
    # URL Ajustada conforme sua solicitação
    BASE_URL = "https://forbes.com.br/ultimas-noticias/" 
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        blocos_noticia = soup.find_all('article')

        count = 0

        for bloco in blocos_noticia:
            if count >= 8: break

            # 2. EXTRAINDO LINK E TÍTULO
            # Na Forbes, muitas vezes a tag <a> envolve o <article> inteiro
            link_tag = bloco.find_parent('a')
            
            # Se não achar no pai, procura dentro (caso o layout varie)
            if not link_tag:
                link_tag = bloco.find('a', href=True)
            
            titulo_tag = bloco.find('h3')

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                if not link or len(titulo) < 5:
                    continue

                # Extrai o resumo visual do card (classe meta-info) para fallback
                resumo_tag = bloco.find('div', class_='meta-info')
                resumo_capa = resumo_tag.get_text(strip=True) if resumo_tag else ""

                # --- DEEP SCRAPING ---
                print(f"   [Forbes] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    # Fallback com o resumo da capa
                    texto_analise_ia = f"{titulo}. {resumo_capa}"
                
                noticias_coletadas.append({
                    "nome_fonte": "Forbes Brasil",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"Forbes Brasil: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Forbes Brasil: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping da Forbes Brasil: {e}")
        return []