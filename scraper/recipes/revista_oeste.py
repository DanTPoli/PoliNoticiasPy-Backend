from playwright.sync_api import sync_playwright
from datetime import datetime
import time

from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_revista_oeste():
    """
    Coleta notícias da Revista Oeste usando Playwright TOTAL (Listagem + Conteúdo)
    para evitar o erro 403 Forbidden.
    """
    BASE_URL = "https://revistaoeste.com/politica/"
    noticias_coletadas = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            print(f"   [Revista Oeste] Acessando Home via Playwright...")
            page.goto(BASE_URL, timeout=60000)
            
            # Lista temporária para guardar links e não perder a referência da home
            links_para_visitar = []
            
            try:
                page.wait_for_selector('article.card-post', timeout=15000)
                blocos = page.query_selector_all('article.card-post')
                
                for bloco in blocos[:8]: # Limita a 8
                    link_el = bloco.query_selector('a.card-post__title')
                    if link_el:
                        url = link_el.get_attribute('href')
                        h3_el = link_el.query_selector('h3')
                        titulo = h3_el.inner_text().strip() if h3_el else link_el.inner_text().strip()
                        
                        if url and len(titulo) > 5:
                            links_para_visitar.append({'url': url, 'titulo': titulo})
            except Exception as e:
                print(f"   [Revista Oeste] Erro ao listar: {e}")

            # Agora visitamos cada link USANDO O MESMO BROWSER (fura o bloqueio)
            for item in links_para_visitar:
                print(f"   [Revista Oeste] Processando lead: {item['titulo'][:30]}...")
                try:
                    page.goto(item['url'], timeout=30000)
                    
                    # --- MUDANÇA CIRÚRGICA AQUI ---
                    # Chamamos o extrator central enviando o HTML da página atual
                    conteudo = extrair_primeiro_paragrafo(item['url'], html_content=page.content())
                    
                    texto_ia = f"{item['titulo']}. {conteudo}" if conteudo else item['titulo']
                    
                    noticias_coletadas.append({
                        "nome_fonte": "Revista Oeste",
                        "titulo": item['titulo'],
                        "url": item['url'],
                        "texto_analise_ia": texto_ia,
                        "viés_classificado": None,
                        "id_cluster": None,
                        "data_coleta": datetime.now().isoformat()
                    })
                    
                    time.sleep(1) 
                    
                except Exception as e:
                    print(f"   ⚠️ Falha ao ler artigo: {e}")

            browser.close()
            
        print(f"Revista Oeste: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except Exception as e:
        print(f"Erro Crítico no Playwright da Revista Oeste: {e}")
        return []