# scraper/recipes/reuters.py (VERSÃO FINAL COM WAIT_FOR_SELECTOR)

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime
import time 

def coletar_reuters():
    """
    Coleta notícias da Reuters (Seção World/Américas) usando PLAYWRIGHT.
    Utiliza page.wait_for_selector para garantir que o feed foi renderizado.
    """
    BASE_URL = "https://www.reuters.com/world/americas/" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        # --- EXECUÇÃO DO PLAYWRIGHT ---
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print(f"Playwright: Navegando em {BASE_URL}...")
            page.goto(BASE_URL, timeout=60000)
            
            # A CORREÇÃO: Espera ATÉ que o primeiro item da lista apareça.
            try:
                # Esperamos pela tag <a> com o data-testid='TitleLink'
                page.wait_for_selector('a[data-testid="TitleLink"]', timeout=30000) 
                print("Elemento do feed Reuters encontrado. Capturando HTML.")
            except Exception:
                print("❌ Tempo esgotado esperando o feed da Reuters carregar. Seletor não encontrado.")
                browser.close()
                return []
                
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            browser.close()
            # -----------------------------

            # 1. IDENTIFICANDO OS BLOCOS CHAVE (Seletor data-testid)
            blocos_noticia = soup.find_all('li', {'data-testid': 'FeedListItem'}) 

            for bloco in blocos_noticia:
                # 2. EXTRAÇÃO DE DADOS (usando data-testid)
                link_tag = bloco.find('a', {'data-testid': 'TitleLink'})
                titulo_tag = bloco.find('span', {'data-testid': 'TitleHeading'}) 
                resumo_tag = bloco.find('p', {'data-testid': 'Description'})

                if link_tag and titulo_tag:
                    link = link_tag.get('href')
                    titulo = titulo_tag.text.strip()
                    
                    resumo = resumo_tag.text.strip() if resumo_tag else ""
                    texto_analise_ia = f"{titulo}. {resumo}"
                    
                    if link.startswith('/'):
                        link = "https://www.reuters.com" + link
                    
                    noticias_coletadas.append({
                        "nome_fonte": "Reuters",
                        "titulo": titulo,
                        "url": link,
                        "texto_analise_ia": texto_analise_ia,
                        "viés_classificado": None,
                        "id_cluster": None,
                        "data_coleta": datetime.now().isoformat()
                    })
            
            print(f"Reuters (Playwright): {len(noticias_coletadas)} notícias coletadas.")
            return noticias_coletadas

    except Exception as e:
        print(f"❌ Erro ao coletar Reuters: {e}")
        return []