import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_veja():
    """
    Coleta notícias da Revista Veja com Deep Scraping (lê o conteúdo do link).
    Ajustado para os seletores exatos fornecidos (card not-loaded list-item).
    """
    # URL da seção Política
    BASE_URL = "https://veja.abril.com.br/politica/" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        blocos_noticia = soup.find_all('div', class_='list-item') 

        count = 0

        for bloco in blocos_noticia:
            if count >= 10: break

            # 2. EXTRAINDO LINK E TÍTULO
            # O link é a tag <a> que está logo antes do <h2> ou tem o title
            link_tag = bloco.find('a', title=True) 
            titulo_tag = bloco.find('h2', class_='title')
            
            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                # --- DEEP SCRAPING ---
                print(f"   [Veja] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    # Fallback: usa apenas o título se não conseguir ler
                    texto_analise_ia = titulo
                
                noticias_coletadas.append({
                    "nome_fonte": "Veja",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"Revista Veja: {len(noticias_coletadas)} notícias coletadas com conteúdo profundo.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Revista Veja: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping da Revista Veja: {e}")
        return []