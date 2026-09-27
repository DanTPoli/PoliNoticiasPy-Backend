from datetime import datetime
import time 

# --- BLINDAGEM CONTRA FALTA DE PLAYWRIGHT ---
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

def coletar_estadao():
    """
    Coleta notícias do Estadão com Playwright, blindado contra links duplicados.
    """
    if not PLAYWRIGHT_AVAILABLE:
        print("⚠️ [Estadão] Playwright não detectado. Pulando fonte.")
        return []

    BASE_URL = "https://www.estadao.com.br/politica/" 
    noticias_coletadas = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                java_script_enabled=False 
            )
            page = context.new_page()
            
            print(f"   [Estadão] Acessando Home via Playwright...")
            page.goto(BASE_URL, timeout=60000, wait_until="domcontentloaded")
            
            links_para_visitar = []
            seen_urls = set()
            seen_titles = set() # <-- NOVO: Verifica também o título
            
            try:
                elementos = page.query_selector_all('.headline') 
                
                for el in elementos:
                    if len(links_para_visitar) >= 8: break
                    
                    titulo = el.inner_text().strip()
                    
                    url = el.get_attribute('href')
                    if not url:
                        link_el = el.query_selector('xpath=ancestor::a')
                        if link_el:
                            url = link_el.get_attribute('href')
                            
                    if not url or len(titulo) < 10: continue
                    
                    # --- NOVO: Limpeza pesada na URL ---
                    # Corta parâmetros de rastreio (?) e âncoras da página (#)
                    url_limpa = url.split('?')[0].split('#')[0]
                    # Remove barra no final para padronizar
                    url_limpa = url_limpa.rstrip('/')
                    
                    if url_limpa.startswith('/'):
                        url_limpa = f"https://www.estadao.com.br{url_limpa}"
                        
                    if "busca" in url_limpa or "autor" in url_limpa or "em-alta" in url_limpa: continue
                    
                    # Se a URL ou o Título já estiverem na lista, pula para o próximo!
                    if url_limpa in seen_urls or titulo in seen_titles: 
                        continue
                    
                    seen_urls.add(url_limpa)
                    seen_titles.add(titulo)
                    links_para_visitar.append({'url': url_limpa, 'titulo': titulo})
                        
            except Exception as e:
                print(f"   [Estadão] Erro ao listar: {e}")

            # Visita cada notícia
            for item in links_para_visitar:
                print(f"   [Estadão] Lendo conteúdo: {item['titulo'][:30]}...")
                try:
                    page.goto(item['url'], timeout=30000, wait_until="domcontentloaded")
                    
                    conteudo = ""
                    paragrafo = page.query_selector('.news-body p, article p, .story-content p')
                    
                    if paragrafo:
                        conteudo = paragrafo.inner_text().strip()
                    
                    texto_ia = f"{item['titulo']}. {conteudo}" if conteudo else item['titulo']
                    
                    noticias_coletadas.append({
                        "nome_fonte": "Estadão",
                        "titulo": item['titulo'],
                        "url": item['url'],
                        "texto_analise_ia": texto_ia,
                        "viés_classificado": None,
                        "id_cluster": None,
                        "data_coleta": datetime.now().isoformat()
                    })
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"   ⚠️ Falha ao ler artigo Estadão: {e}")

            browser.close()
            
        print(f"Estadão: {len(noticias_coletadas)} notícias coletadas com sucesso.")
        return noticias_coletadas

    except Exception as e:
        print(f"Erro Crítico no Playwright do Estadão: {e}")
        return []