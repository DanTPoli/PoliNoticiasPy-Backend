from playwright.sync_api import sync_playwright
from datetime import datetime
import time

def coletar_brasil_paralelo():
    """
    Coleta notícias do Brasil Paralelo usando Playwright.
    Resolve o problema de 'Lorem Ipsum' esperando o conteúdo carregar dinamicamente.
    """
    BASE_URL = "https://www.brasilparalelo.com.br/noticias"
    BASE_DOMAIN = "https://www.brasilparalelo.com.br"
    noticias_coletadas = []

    try:
        with sync_playwright() as p:
            # Lança o navegador
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            print(f"   [Brasil Paralelo] Acessando Home via Playwright...")
            page.goto(BASE_URL, timeout=60000)
            
            links_para_visitar = []
            
            try:
                # Espera os cards carregarem
                page.wait_for_selector('div._00-news-latest-item', timeout=15000)
                
                # Coleta os links da listagem
                blocos = page.query_selector_all('div._00-news-latest-item')
                
                for bloco in blocos[:8]: # Limite de 8 notícias
                    link_el = bloco.query_selector('a._00-hobbit')
                    
                    if link_el:
                        url = link_el.get_attribute('href')
                        if url and url.startswith('/'):
                            url = BASE_DOMAIN + url
                            
                        # Título
                        h3_el = link_el.query_selector('h3')
                        titulo = h3_el.inner_text().strip() if h3_el else ""
                        
                        if url and len(titulo) > 5:
                            links_para_visitar.append({'url': url, 'titulo': titulo})
                            
            except Exception as e:
                print(f"   [Brasil Paralelo] Erro ao listar: {e}")

            # Visita cada notícia individualmente
            for item in links_para_visitar:
                print(f"   [Brasil Paralelo] Navegando: {item['titulo'][:30]}...")
                try:
                    page.goto(item['url'], timeout=30000)
                    
                    # Espera o texto principal carregar. 
                    # No Brasil Paralelo, o texto geralmente está em classes 'rich-text' ou 'w-richtext'
                    try:
                        page.wait_for_selector('div.w-richtext p', timeout=10000)
                        paragrafos = page.query_selector_all('div.w-richtext p')
                    except:
                        # Fallback se não achar a classe específica
                        paragrafos = page.query_selector_all('article p')

                    conteudo = ""
                    # Pega o primeiro parágrafo que tenha um tamanho decente (evita legendas curtas)
                    for p in paragrafos:
                        texto_p = p.inner_text().strip()
                        if len(texto_p) > 50 and "lorem ipsum" not in texto_p.lower():
                            conteudo = texto_p
                            break
                    
                    # Se falhar totalmente, usa o título como fallback para não salvar "lorem ipsum"
                    texto_ia = f"{item['titulo']}. {conteudo}" if conteudo else item['titulo']
                    
                    noticias_coletadas.append({
                        "nome_fonte": "Brasil Paralelo",
                        "titulo": item['titulo'],
                        "url": item['url'],
                        "texto_analise_ia": texto_ia,
                        "viés_classificado": None,
                        "id_cluster": None,
                        "data_coleta": datetime.now().isoformat()
                    })
                    
                    time.sleep(1) # Respeita o servidor
                    
                except Exception as e:
                    print(f"   ⚠️ Falha ao ler artigo BP: {e}")

            browser.close()
            
        print(f"Brasil Paralelo: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except Exception as e:
        print(f"Erro Crítico no Playwright do Brasil Paralelo: {e}")
        return []