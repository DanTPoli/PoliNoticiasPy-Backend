from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime
import time

from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_revista_oeste():
    """
    Coleta notícias da Revista Oeste. Se o corpo for bloqueado pelo Cloudflare,
    garante que ao menos o título seja enviado para análise.
    """
    BASE_URL = "https://revistaoeste.com/politica/"
    noticias_coletadas = []

    try:
        with sync_playwright() as p:
            # Mantemos o disfarce para tentar passar pelo bloqueio
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            print(f"   [Revista Oeste] Acessando Home...")
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
            
            links_para_visitar = []
            try:
                page.wait_for_selector('article.card-post', timeout=20000)
                soup_home = BeautifulSoup(page.content(), 'html.parser')
                blocos = soup_home.find_all('article', class_='card-post')
                
                for bloco in blocos[:10]:
                    link_el = bloco.find('a', class_='card-post__title')
                    if link_el:
                        url = link_el.get('href')
                        titulo = link_el.get_text().strip()
                        if url and len(titulo) > 30:
                            links_para_visitar.append({'url': url, 'titulo': titulo})
            except Exception as e:
                print(f"   [Revista Oeste] Erro na home: {e}")

            for item in links_para_visitar:
                if len(noticias_coletadas) >= 8: break
                
                print(f"   [Revista Oeste] Processando: {item['titulo'][:35]}...")
                conteudo = ""
                
                try:
                    # Tenta carregar a página da notícia
                    page.goto(item['url'], wait_until="domcontentloaded", timeout=30000)
                    time.sleep(5) # Espera o desafio automático
                    
                    # Tenta extrair o conteúdo real
                    if page.query_selector('.artigo--texto'):
                        conteudo = extrair_primeiro_paragrafo(item['url'], html_content=page.content())
                    else:
                        print(f"      ⚠️ Bloqueio no corpo. Usando apenas título.")
                except Exception:
                    print(f"      ⚠️ Timeout na página. Usando apenas título.")

                # INDEPENDENTE DE SUCESSO NO CONTEÚDO, SALVAMOS O ITEM
                # Se 'conteudo' for vazio, o texto_analise_ia será apenas o título.
                texto_ia = f"{item['titulo']}. {conteudo}".strip(". ")
                
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

            browser.close()
            
        print(f"✅ Revista Oeste: {len(noticias_coletadas)} notícias processadas.")
        return noticias_coletadas

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
        return []