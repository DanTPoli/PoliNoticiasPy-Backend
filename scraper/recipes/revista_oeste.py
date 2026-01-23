from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
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
            # MUDANÇA 1: Adicionado argumento para ocultar que o navegador é um bot (evita o bloqueio do Cloudflare)
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            print(f"   [Revista Oeste] Acessando Home via Playwright...")
            page.goto(BASE_URL, timeout=60000)
            
            links_para_visitar = []
            
            try:
                page.wait_for_selector('article.card-post', timeout=15000)
                # MUDANÇA 2: Uso do BeautifulSoup (que estava faltando o import) para ler a home
                soup = BeautifulSoup(page.content(), 'html.parser')
                blocos = soup.find_all('article', class_='card-post')
                
                for bloco in blocos[:8]: 
                    link_el = bloco.find('a', class_='card-post__title')
                    if link_el:
                        url = link_el.get('href')
                        titulo = link_el.get_text().strip()
                        
                        # Filtro para ignorar títulos muito curtos (como charges)
                        if url and len(titulo) > 30:
                            links_para_visitar.append({'url': url, 'titulo': titulo})
            except Exception as e:
                print(f"   [Revista Oeste] Erro ao listar: {e}")

            for item in links_para_visitar:
                print(f"   [Revista Oeste] Navegando: {item['titulo'][:30]}...")
                try:
                    page.goto(item['url'], timeout=30000)
                    
                    # MUDANÇA 3: Espera 5 segundos para o desafio do Cloudflare "passar" sozinho
                    time.sleep(5) 
                    
                    # Chamamos o extrator central enviando o HTML da página carregada
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