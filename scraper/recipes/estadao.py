import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_estadao():
    """
    Coleta notícias do Estadão com Deep Scraping (lê o conteúdo do link).
    """
    BASE_URL = "https://www.estadao.com.br/politica/" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        blocos_noticia = soup.find_all('div', class_=lambda c: c and 'noticia-single-block' in c) 

        count = 0

        for bloco in blocos_noticia:
            if count >= 8: break

            # 2. EXTRAINDO LINK E TÍTULO
            link_tag = bloco.find('a', href=True)
            titulo_tag = bloco.find('h2', class_='headline')
            # O resumo da capa (subheadline) serve como fallback
            resumo_capa_tag = bloco.find('div', class_='subheadline')

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                # --- DEEP SCRAPING ---
                print(f"   [Estadão] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    # Fallback: Se não conseguir ler o artigo, usa o resumo da capa
                    resumo = resumo_capa_tag.text.strip() if resumo_capa_tag else ""
                    texto_analise_ia = f"{titulo}. {resumo}"
                
                noticias_coletadas.append({
                    "nome_fonte": "Estadão",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"Estadão: {len(noticias_coletadas)} notícias coletadas com conteúdo profundo.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Estadão: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping do Estadão: {e}")
        return []