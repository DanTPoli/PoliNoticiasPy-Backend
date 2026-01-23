from datetime import datetime
import time
from scraper.content_extractor import extrair_primeiro_paragrafo

# Blindagem para ambientes sem Playwright
try:
    from playwright.sync_api import sync_playwright
    from bs4 import BeautifulSoup
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

def coletar_brasil_de_fato():
    if not PLAYWRIGHT_AVAILABLE:
        print("⚠️ [BdF] Playwright não instalado. Pulando fonte.")
        return []

    BASE_URL = "https://www.brasildefato.com.br/politica"
    noticias_coletadas = []

    try:
        with sync_playwright() as p:
            # Lançando o browser
            browser = p.chromium.launch(headless=True)
            # Definindo um User-Agent de navegador real para evitar bloqueios
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            print(f"🚀 [BdF] Navegando para {BASE_URL}...")
            
            # Navegação com espera inteligente
            page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
            
            # Espera específica pelo seletor do Elementor que você enviou
            page.wait_for_selector(".e-loop-item", timeout=15000)
            
            # Pequeno scroll para garantir que o lazy load (se houver) dispare
            page.mouse.wheel(0, 500)
            time.sleep(2)

            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            browser.close()

            # Localizando os itens de loop baseados no seu HTML
            itens = soup.find_all('div', class_='e-loop-item')
            
            count = 0
            for item in itens:
                if count >= 10: break

                try:
                    # O título está dentro de um h2 com a classe elementor-heading-title
                    h2_tag = item.find('h2', class_='elementor-heading-title')
                    if not h2_tag: continue
                    
                    link_tag = h2_tag.find('a')
                    if not link_tag: continue

                    titulo = link_tag.get_text().strip()
                    link = link_tag.get('href')

                    # Filtragem de links institucionais ou repetidos
                    if not titulo or "brasildefato.com.br" not in link: continue

                    print(f"   [BdF] Lendo conteúdo: {titulo[:40]}...")
                    
                    # Chamada para sua função de Deep Scraping (o primeiro parágrafo do link)
                    conteudo_real = extrair_primeiro_paragrafo(link)
                    
                    # Refinamento do Texto para IA (Título + Lead)
                    texto_analise_ia = f"{titulo}. {conteudo_real}" if conteudo_real else titulo

                    noticias_coletadas.append({
                        "nome_fonte": "Brasil de Fato",
                        "titulo": titulo,
                        "url": link,
                        "texto_analise_ia": texto_analise_ia,
                        "viés_classificado": None,
                        "id_cluster": None,
                        "data_coleta": datetime.now().isoformat()
                    })
                    count += 1

                except Exception as e_item:
                    print(f"⚠️ Erro no item individual BdF: {e_item}")
                    continue

            print(f"✅ Brasil de Fato: {len(noticias_coletadas)} notícias coletadas com Playwright.")
            return noticias_coletadas

    except Exception as e:
        print(f"❌ Erro fatal Playwright BdF: {e}")
        return []