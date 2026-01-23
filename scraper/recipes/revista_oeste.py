from playwright.sync_api import sync_playwright
from datetime import datetime
import time

from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_revista_oeste():
    BASE_URL = "https://revistaoeste.com/politica/"
    noticias_coletadas = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Aumentamos um pouco o viewport para parecer mais um navegador real
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 800}
            )
            page = context.new_page()
            
            print(f"   [Revista Oeste] Acessando Home...")
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
            
            links_para_visitar = []
            try:
                page.wait_for_selector('article.card-post', timeout=20000)
                # Pequeno scroll para garantir que o JS da home carregue os links
                page.evaluate("window.scrollBy(0, 500)")
                
                soup_home = BeautifulSoup(page.content(), 'html.parser')
                blocos = soup_home.find_all('article', class_='card-post')
                
                for bloco in blocos[:8]:
                    link_el = bloco.find('a', class_='card-post__title')
                    if link_el:
                        url = link_el.get('href')
                        titulo = link_el.get_text().strip()
                        if url and len(titulo) > 30:
                            links_para_visitar.append({'url': url, 'titulo': titulo})
            except Exception as e:
                print(f"   [Revista Oeste] Erro na listagem: {e}")

            for item in links_para_visitar:
                if len(noticias_coletadas) >= 8: break
                
                print(f"   [Revista Oeste] Lendo: {item['titulo'][:30]}...")
                try:
                    # AJUSTE 1: Espera apenas o carregamento básico do HTML
                    page.goto(item['url'], wait_until="domcontentloaded", timeout=40000)
                    
                    # AJUSTE 2: Pausa tática para o Cloudflare processar o desafio automático
                    time.sleep(4) 
                    
                    # AJUSTE 3: Espera o seletor real. Se falhar aqui, o site nos bloqueou.
                    page.wait_for_selector('.artigo--texto, .entry-content', timeout=20000)
                    
                    conteudo = extrair_primeiro_paragrafo(item['url'], html_content=page.content())
                    
                    if conteudo and "Verifying you are human" not in conteudo:
                        noticias_coletadas.append({
                            "nome_fonte": "Revista Oeste",
                            "titulo": item['titulo'],
                            "url": item['url'],
                            "texto_analise_ia": f"{item['titulo']}. {conteudo}",
                            "viés_classificado": None,
                            "id_cluster": None,
                            "data_coleta": datetime.now().isoformat()
                        })
                    
                    time.sleep(2) 
                    
                except Exception as e:
                    # Imprime o erro para diagnóstico (ex: se foi Timeout)
                    print(f"   ⚠️ Falha em {item['url'][:40]}: {type(e).__name__}")

            browser.close()
            
        print(f"✅ Revista Oeste: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except Exception as e:
        print(f"❌ Erro Crítico Revista Oeste: {e}")
        return []