from playwright.sync_api import sync_playwright
from datetime import datetime
import time

def coletar_bbc_brasil():
    """
    Coleta notícias da BBC News Brasil usando Playwright.
    """
    BASE_URL = "https://www.bbc.com/portuguese"
    noticias_coletadas = []

    try:
        with sync_playwright() as p:
            # Lança navegador headless
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            print(f"   [BBC] Acessando Home via Playwright...")
            page.goto(BASE_URL, timeout=60000)
            
            links_para_visitar = []
            
            try:
                # Estratégia BBC: Títulos ficam dentro de um <h3> com um <a> logo dentro
                elementos = page.query_selector_all('h3 a') 
                
                seen_urls = set()
                
                for el in elementos:
                    if len(links_para_visitar) >= 8: break
                    
                    url = el.get_attribute('href')
                    titulo = el.inner_text().strip()
                    
                    # Tratamento de URL (caso a BBC retorne links relativos como /portuguese/...)
                    if url and url.startswith('/'):
                        url = f"https://www.bbc.com{url}"
                        
                    # Filtros
                    if not url or len(titulo) < 10: continue
                    if "bbc.com/portuguese" not in url: continue
                    # Ignora páginas de seções/tópicos (ex: /topics/c8epw74n6k0t)
                    if "/topics/" in url: continue 
                    if url in seen_urls: continue
                    
                    seen_urls.add(url)
                    links_para_visitar.append({'url': url, 'titulo': titulo})
                    
            except Exception as e:
                print(f"   [BBC] Erro ao listar: {e}")

            # Visita cada notícia para pegar o conteúdo
            for item in links_para_visitar:
                print(f"   [BBC] Navegando: {item['titulo'][:30]}...")
                try:
                    page.goto(item['url'], timeout=30000)
                    
                    # Seletores comuns de texto interno na BBC
                    conteudo = ""
                    paragrafo = page.query_selector('main p, article p, [data-component="text-block"]')
                    
                    if paragrafo:
                        conteudo = paragrafo.inner_text().strip()
                    
                    texto_ia = f"{item['titulo']}. {conteudo}" if conteudo else item['titulo']
                    
                    noticias_coletadas.append({
                        "nome_fonte": "BBC News Brasil",
                        "titulo": item['titulo'],
                        "url": item['url'],
                        "texto_analise_ia": texto_ia,
                        "viés_classificado": None,
                        "id_cluster": None,
                        "data_coleta": datetime.now().isoformat()
                    })
                    # Pausa leve
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"   ⚠️ Falha ao ler artigo BBC: {e}")

            browser.close()
            
        print(f"BBC: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except Exception as e:
        print(f"Erro Crítico no Playwright da BBC: {e}")
        return []