from datetime import datetime
import time
from urllib.parse import urljoin
from scraper.content_extractor import extrair_primeiro_paragrafo

try:
    from playwright.sync_api import sync_playwright
    from bs4 import BeautifulSoup
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

def coletar_brasil_de_fato_home():
    if not PLAYWRIGHT_AVAILABLE:
        print("⚠️ [BdF] Playwright não disponível.")
        return []

    # AGORA NA HOME PRINCIPAL
    BASE_URL = "https://www.brasildefato.com.br/"
    noticias_coletadas = []
    urls_vistas = set() # Para evitar duplicados da home

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            print(f"🚀 [BdF Home] Acessando {BASE_URL}...")
            
            # Espera carregar os elementos do Elementor
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector(".e-loop-item", timeout=20000)
            
            # Scroll leve para carregar imagens e conteúdos dinâmicos
            page.evaluate("window.scrollBy(0, 800)")
            time.sleep(2)

            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            browser.close()

            # O Elementor usa 'e-loop-item' para quase todos os blocos de notícias na home
            itens = soup.find_all('div', class_='e-loop-item')
            
            count = 0
            for item in itens:
                if count >= 12: break # Pegamos um pouco mais na home para garantir variedade

                try:
                    # Captura o título dentro do padrão que você enviou
                    h2_tag = item.find(['h2', 'h3'], class_='elementor-heading-title')
                    if not h2_tag: continue
                    
                    link_tag = h2_tag.find('a')
                    if not link_tag: continue

                    titulo = link_tag.get_text().strip()
                    # Resolve URLs relativas para absolutas
                    link = urljoin(BASE_URL, link_tag.get('href'))

                    # --- REFINAMENTO DE FILTRAGEM ---
                    # 1. Evita duplicados (comum na home ter a mesma notícia em dois blocos)
                    # 2. Garante que o link é uma notícia (geralmente tem data no BDdeF)
                    if link in urls_vistas or "/202" not in link: 
                        continue

                    print(f"   [BdF Home] Lendo: {titulo[:45]}...")
                    
                    # Extração do Lead via Deep Scraping
                    conteudo_lead = extrair_primeiro_paragrafo(link)
                    
                    if conteudo_lead:
                        texto_analise_ia = f"{titulo}. {conteudo_lead}"
                    else:
                        texto_analise_ia = titulo

                    noticias_coletadas.append({
                        "nome_fonte": "Brasil de Fato",
                        "titulo": titulo,
                        "url": link,
                        "texto_analise_ia": texto_analise_ia,
                        "viés_classificado": None,
                        "id_cluster": None,
                        "data_coleta": datetime.now().isoformat()
                    })
                    
                    urls_vistas.add(link)
                    count += 1

                except Exception as e_item:
                    continue

            print(f"✅ BdF Home: {len(noticias_coletadas)} notícias coletadas.")
            return noticias_coletadas

    except Exception as e:
        print(f"❌ Erro fatal na Home do BdF: {e}")
        return []