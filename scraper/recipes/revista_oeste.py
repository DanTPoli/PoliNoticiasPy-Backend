from playwright.sync_api import sync_playwright
from datetime import datetime
import time

from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_revista_oeste():
    """
    Coleta notícias da Revista Oeste usando Playwright TOTAL (Listagem + Conteúdo)
    para evitar o erro 403 Forbidden e contornar desafios de bot.
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
            page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
            
            links_para_visitar = []
            
            try:
                page.wait_for_selector('article.card-post', timeout=15000)
                blocos = page.query_selector_all('article.card-post')
                
                for bloco in blocos[:10]: 
                    link_el = bloco.query_selector('a.card-post__title')
                    if link_el:
                        url = link_el.get_attribute('href')
                        h3_el = link_el.query_selector('h3')
                        titulo = h3_el.inner_text().strip() if h3_el else link_el.inner_text().strip()
                        
                        # FILTRO 1: Ignora títulos muito curtos (como 'Charge da semana')
                        if url and len(titulo) > 30:
                            links_para_visitar.append({'url': url, 'titulo': titulo})
            except Exception as e:
                print(f"   [Revista Oeste] Erro ao listar: {e}")

            for item in links_para_visitar:
                if len(noticias_coletadas) >= 8: break
                
                print(f"   [Revista Oeste] Navegando: {item['titulo'][:30]}...")
                try:
                    # Mudança: wait_until="networkidle" ajuda a esperar o desafio de bot sumir
                    page.goto(item['url'], wait_until="networkidle", timeout=40000)
                    
                    # Mudança: Espera forçada por um seletor de conteúdo real da notícia
                    # Isso garante que o Playwright só capture o HTML APÓS o "Verifying you are human"
                    page.wait_for_selector('.artigo--texto, article, .entry-content', timeout=15000)
                    
                    # Chamamos o extrator central enviando o HTML da página já carregada
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
                    
                    time.sleep(2) # Pausa levemente maior para evitar bloqueios sequenciais
                    
                except Exception as e:
                    print(f"   ⚠️ Falha ao ler artigo (pode ser bloqueio): {item['url']}")

            browser.close()
            
        print(f"Revista Oeste: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except Exception as e:
        print(f"Erro Crítico no Playwright da Revista Oeste: {e}")
        return []