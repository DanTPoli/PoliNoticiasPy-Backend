from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime
import time

from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_revista_oeste():
    """
    Coleta notícias da Revista Oeste usando Playwright com técnicas de evasão
    de bot para contornar o bloqueio do Cloudflare e o erro 403.
    """
    BASE_URL = "https://revistaoeste.com/politica/"
    noticias_coletadas = []

    try:
        with sync_playwright() as p:
            # 1. DISFARCE: Oculta a flag de automação que o Cloudflare usa para barrar bots
            browser = p.chromium.launch(
                headless=True, 
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 800}
            )
            page = context.new_page()
            
            print(f"   [Revista Oeste] Acessando Home via Playwright...")
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
            
            links_para_visitar = []
            try:
                # Espera os blocos de notícias aparecerem
                page.wait_for_selector('article.card-post', timeout=20000)
                soup_home = BeautifulSoup(page.content(), 'html.parser')
                blocos = soup_home.find_all('article', class_='card-post')
                
                for bloco in blocos[:10]:
                    link_el = bloco.find('a', class_='card-post__title')
                    if link_el:
                        url = link_el.get('href')
                        titulo = link_el.get_text().strip()
                        # FILTRO: Ignora links curtos como "Charge da semana" (economiza tempo)
                        if url and len(titulo) > 30:
                            links_para_visitar.append({'url': url, 'titulo': titulo})
            except Exception as e:
                print(f"   [Revista Oeste] Erro ao listar links: {e}")

            # Processamento individual das notícias
            for item in links_para_visitar:
                if len(noticias_coletadas) >= 8: break
                
                print(f"   [Revista Oeste] Lendo: {item['titulo'][:35]}...")
                try:
                    page.goto(item['url'], wait_until="domcontentloaded", timeout=45000)
                    
                    # 2. PACIÊNCIA: O Cloudflare geralmente leva 5-7 segundos para validar o acesso
                    time.sleep(7) 
                    
                    # 3. VERIFICAÇÃO: Se '.artigo--texto' não aparecer, fomos barrados (desafio manual)
                    try:
                        page.wait_for_selector('.artigo--texto', timeout=10000)
                        
                        # Chamamos o extrator central enviando o HTML que já foi validado pelo Cloudflare
                        conteudo = extrair_primeiro_paragrafo(item['url'], html_content=page.content())
                        
                        if conteudo:
                            noticias_coletadas.append({
                                "nome_fonte": "Revista Oeste",
                                "titulo": item['titulo'],
                                "url": item['url'],
                                "texto_analise_ia": f"{item['titulo']}. {conteudo}",
                                "viés_classificado": None,
                                "id_cluster": None,
                                "data_coleta": datetime.now().isoformat()
                            })
                    except:
                        # Se der erro aqui, apenas ignora essa matéria e vai para a próxima
                        print(f"      ⚠️ Bloqueio persistente em: {item['url'][:30]}...")
                        continue
                    
                    time.sleep(2) # Pausa entre requisições
                    
                except Exception:
                    continue

            browser.close()
            
        print(f"✅ Revista Oeste finalizada: {len(noticias_coletadas)} coletadas.")
        return noticias_coletadas

    except Exception as e:
        print(f"❌ Erro Crítico Playwright Oeste: {e}")
        return []