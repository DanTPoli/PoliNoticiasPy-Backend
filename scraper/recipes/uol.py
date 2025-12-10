from playwright.sync_api import sync_playwright
from datetime import datetime
import time

def coletar_uol():
    """
    Coleta notícias do UOL usando Playwright para evitar erro 403
    tanto na listagem quanto na leitura do conteúdo.
    """
    BASE_URL = "https://www.uol.com.br/"
    noticias_coletadas = []

    try:
        with sync_playwright() as p:
            # Lança navegador headless (sem interface gráfica)
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            print(f"   [UOL] Acessando Home via Playwright...")
            page.goto(BASE_URL, timeout=60000)
            
            links_para_visitar = []
            
            try:
                # Estratégia Genérica: Pega elementos que parecem manchetes (h2, h3 com links)
                # O UOL usa muito h3.thumb-title ou apenas h3 dentro de links
                elementos = page.query_selector_all('a h3, h3 a') 
                
                seen_urls = set()
                
                for el in elementos:
                    if len(links_para_visitar) >= 8: break
                    
                    # Tenta achar o elemento 'a' pai ou filho
                    link_el = el.query_selector('xpath=ancestor-or-self::a')
                    if not link_el:
                        # Se o h3 está dentro do a, o xpath acima resolve. 
                        # Se o a está dentro do h3, precisamos buscar o a
                        link_el = el.query_selector('a')
                    
                    if link_el:
                        url = link_el.get_attribute('href')
                        titulo = el.inner_text().strip()
                        
                        # Filtros
                        if not url or len(titulo) < 10: continue
                        if "uol.com.br" not in url: continue
                        if "publicidade" in url or "especiais" in url: continue
                        if url in seen_urls: continue
                        
                        seen_urls.add(url)
                        links_para_visitar.append({'url': url, 'titulo': titulo})
                        
            except Exception as e:
                print(f"   [UOL] Erro ao listar: {e}")

            # Visita cada notícia para pegar o conteúdo (Bypassing 403)
            for item in links_para_visitar:
                print(f"   [UOL] Navegando: {item['titulo'][:30]}...")
                try:
                    page.goto(item['url'], timeout=30000)
                    
                    # Seletores comuns de texto no UOL
                    # .text-content, .c-news__body, article
                    conteudo = ""
                    paragrafo = page.query_selector('.text-content p, .c-news__body p, article p')
                    
                    if paragrafo:
                        conteudo = paragrafo.inner_text().strip()
                    
                    texto_ia = f"{item['titulo']}. {conteudo}" if conteudo else item['titulo']
                    
                    noticias_coletadas.append({
                        "nome_fonte": "UOL",
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
                    print(f"   ⚠️ Falha ao ler artigo UOL: {e}")

            browser.close()
            
        print(f"UOL: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except Exception as e:
        print(f"Erro Crítico no Playwright do UOL: {e}")
        return []