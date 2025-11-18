from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime
import time 
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_cnn_brasil():
    BASE_URL = "https://www.cnnbrasil.com.br/politica/"
    noticias_coletadas = []

    # 1. INICIALIZAR O PLAYWRIGHT (Só para pegar a lista dinâmica)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print(f"Playwright: Navegando em {BASE_URL}...")
            page.goto(BASE_URL)
            time.sleep(5) 
            
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            browser.close()
            
            # 4. APLICAÇÃO DO SELETOR H3
            todos_h3 = soup.find_all('h3') 
            
            count = 0
            for titulo_tag in todos_h3:
                if count >= 8: break

                link_tag = titulo_tag.find_parent('a')
                figcaption_tag = titulo_tag.find_parent('figcaption')

                if link_tag and figcaption_tag:
                    link = link_tag.get('href')
                    titulo = titulo_tag.text.strip()
                    
                    categoria_tag = figcaption_tag.find('span', class_='text-base font-medium text-gray-400')
                    categoria = categoria_tag.text.strip() if categoria_tag else "Sem Categoria"
                    
                    # --- DEEP SCRAPING ---
                    print(f"   [CNN] Lendo conteúdo: {titulo[:30]}...")
                    conteudo_real = extrair_primeiro_paragrafo(link)

                    if conteudo_real:
                        texto_analise_ia = f"{titulo}. {conteudo_real}"
                    else:
                        texto_analise_ia = titulo

                    noticias_coletadas.append({
                        "nome_fonte": "CNN Brasil",
                        "titulo": titulo,
                        "url": link,
                        "categoria": categoria,
                        "texto_analise_ia": texto_analise_ia, 
                        "viés_classificado": None,
                        "id_cluster": None,
                        "data_coleta": datetime.now().isoformat()
                    })
                    count += 1
            
            print(f"CNN Brasil (Playwright): {len(noticias_coletadas)} notícias coletadas com conteúdo profundo.")
            return noticias_coletadas

    except Exception as e:
        print(f"Erro Playwright CNN: {e}")
        return []