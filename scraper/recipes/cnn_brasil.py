from datetime import datetime
import time 

# --- BLINDAGEM CONTRA FALTA DE PLAYWRIGHT ---
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

def coletar_cnn_brasil():
    if not PLAYWRIGHT_AVAILABLE:
        print("⚠️ [CNN] Playwright não detectado. Pulando fonte para economizar memória.")
        return []

    BASE_URL = "https://www.cnnbrasil.com.br/politica/"
    noticias_coletadas = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            print(f"   [CNN Brasil] Acessando Home via Playwright...")
            page.goto(BASE_URL, timeout=60000)
            time.sleep(3) # Aguarda carregamento inicial
            
            links_para_visitar = []
            
            try:
                # Na CNN, os títulos variam entre h2 (Destaques) e h3 (Últimas Notícias e Relacionadas)
                elementos = page.query_selector_all('h2, h3') 
                
                seen_urls = set()
                
                for el in elementos:
                    if len(links_para_visitar) >= 8: break
                    
                    # Tenta achar o elemento 'a' pai ou filho (cobre os dois cenários do HTML da CNN)
                    link_el = el.query_selector('xpath=ancestor-or-self::a')
                    if not link_el:
                        link_el = el.query_selector('a')
                    
                    if link_el:
                        url = link_el.get_attribute('href')
                        titulo = el.inner_text().strip()
                        
                        # Filtros
                        if not url or len(titulo) < 10: continue
                        if "cnnbrasil.com.br" not in url: continue
                        if url in seen_urls: continue
                        
                        seen_urls.add(url)
                        links_para_visitar.append({'url': url, 'titulo': titulo})
                        
            except Exception as e:
                print(f"   [CNN Brasil] Erro ao listar: {e}")

            # Visita cada notícia para pegar o conteúdo (Bypassing 403)
            for item in links_para_visitar:
                print(f"   [CNN Brasil] Lendo conteúdo: {item['titulo'][:30]}...")
                try:
                    page.goto(item['url'], timeout=30000)
                    
                    # Seletores comuns de texto no artigo da CNN
                    conteudo = ""
                    paragrafo = page.query_selector('.single-content p, .post__content p, article p')
                    
                    if paragrafo:
                        conteudo = paragrafo.inner_text().strip()
                    
                    texto_ia = f"{item['titulo']}. {conteudo}" if conteudo else item['titulo']
                    
                    noticias_coletadas.append({
                        "nome_fonte": "CNN Brasil",
                        "titulo": item['titulo'],
                        "url": item['url'],
                        "categoria": "Política", # Adicionado conforme seu script original
                        "texto_analise_ia": texto_ia,
                        "viés_classificado": None,
                        "id_cluster": None,
                        "data_coleta": datetime.now().isoformat()
                    })
                    # Pausa leve
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"   ⚠️ Falha ao ler artigo CNN: {e}")

            browser.close()
            
        print(f"CNN Brasil: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except Exception as e:
        print(f"Erro Crítico no Playwright da CNN: {e}")
        return []