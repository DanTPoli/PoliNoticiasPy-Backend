from datetime import datetime
import time 

# --- BLINDAGEM CONTRA FALTA DE PLAYWRIGHT ---
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

def coletar_metropoles():
    """
    Coleta notícias do Metrópoles usando Playwright, adaptado para o novo layout com Tailwind.
    """
    if not PLAYWRIGHT_AVAILABLE:
        print("⚠️ [Metrópoles] Playwright não detectado. Pulando fonte.")
        return []

    BASE_URL = "https://www.metropoles.com/brasil" 
    noticias_coletadas = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Para o Metrópoles não precisamos necessariamente desligar o JS, 
            # mas vamos manter o padrão otimizado de carregamento
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            print(f"   [Metrópoles] Acessando Home via Playwright...")
            page.goto(BASE_URL, timeout=60000, wait_until="domcontentloaded")
            
            links_para_visitar = []
            seen_urls = set()
            seen_titles = set()
            
            try:
                # O Metrópoles coloca os links (<a>) sempre dentro de <h2> (Manchete principal) ou <h3> (Demais notícias)
                # Restringimos a busca dentro do 'main' e 'aside' para não pegar lixo do cabeçalho
                elementos = page.query_selector_all('main h2 a, main h3 a, aside h3 a') 
                
                for el in elementos:
                    if len(links_para_visitar) >= 8: break
                    
                    titulo = el.inner_text().strip()
                    url = el.get_attribute('href')
                            
                    if not url or len(titulo) < 10: continue
                    
                    # Limpeza pesada na URL (Corta rastreadores ? e âncoras #)
                    url_limpa = url.split('?')[0].split('#')[0].rstrip('/')
                    
                    # Trata links relativos (ex: /brasil/noticia)
                    if url_limpa.startswith('/'):
                        url_limpa = f"https://www.metropoles.com{url_limpa}"
                        
                    # Filtros de exclusão para evitar lixo
                    if "busca" in url_limpa or "autor" in url_limpa or "newsletter" in url_limpa: continue
                    
                    # Bloqueio de duplicadas (mesma matéria mostrada em duas seções da home)
                    if url_limpa in seen_urls or titulo in seen_titles: 
                        continue
                    
                    seen_urls.add(url_limpa)
                    seen_titles.add(titulo)
                    links_para_visitar.append({'url': url_limpa, 'titulo': titulo})
                        
            except Exception as e:
                print(f"   [Metrópoles] Erro ao listar: {e}")

            # Visita cada notícia para pegar o conteúdo real
            for item in links_para_visitar:
                print(f"   [Metrópoles] Lendo conteúdo: {item['titulo'][:30]}...")
                try:
                    page.goto(item['url'], timeout=30000, wait_until="domcontentloaded")
                    
                    conteudo = ""
                    # Seletores genéricos e específicos do Metrópoles para o corpo da matéria
                    paragrafo = page.query_selector('article p, .conteudo-materia p, .m-content p')
                    
                    if paragrafo:
                        conteudo = paragrafo.inner_text().strip()
                    
                    texto_ia = f"{item['titulo']}. {conteudo}" if conteudo else item['titulo']
                    
                    noticias_coletadas.append({
                        "nome_fonte": "Metrópoles",
                        "titulo": item['titulo'],
                        "url": item['url'],
                        "texto_analise_ia": texto_ia,
                        "viés_classificado": None,
                        "id_cluster": None,
                        "data_coleta": datetime.now().isoformat()
                    })
                    time.sleep(1) # Pausa para evitar sobrecarga no servidor do portal
                    
                except Exception as e:
                    print(f"   ⚠️ Falha ao ler artigo Metrópoles: {e}")

            browser.close()
            
        print(f"Metrópoles: {len(noticias_coletadas)} notícias coletadas com sucesso.")
        return noticias_coletadas

    except Exception as e:
        print(f"Erro Crítico no Playwright do Metrópoles: {e}")
        return []