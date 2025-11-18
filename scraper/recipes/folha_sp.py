import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_folha_sp():
    """
    Coleta notícias da Folha de S.Paulo com Deep Scraping (lê o conteúdo do link).
    """
    BASE_URL = "https://www1.folha.uol.com.br/poder/" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        blocos_noticia = soup.find_all('div', class_='c-headline__content') 

        count = 0
        
        for bloco in blocos_noticia:
            if count >= 10: break # Limite de segurança

            link_tag = bloco.find('a', class_='c-headline__url')
            titulo_tag = bloco.find('h2', class_='c-headline__title')
            resumo_tag = bloco.find('p', class_='c-headline__standfirst') 

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                # --- DEEP SCRAPING ---
                print(f"   [Folha] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    # Fallback: Usa o resumo da capa se não conseguir ler o artigo
                    resumo = resumo_tag.text.strip() if resumo_tag else ""
                    texto_analise_ia = f"{titulo}. {resumo}"
                
                noticias_coletadas.append({
                    "nome_fonte": "Folha de S.Paulo",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"Folha de S.Paulo: {len(noticias_coletadas)} notícias coletadas com conteúdo profundo.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro de requisição ao coletar Folha: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping da Folha: {e}")
        return []