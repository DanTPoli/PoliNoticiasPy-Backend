import re
import time
from datetime import datetime
from urllib.parse import urljoin

try:
    from playwright.sync_api import sync_playwright
    from bs4 import BeautifulSoup
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from scraper.content_extractor import extrair_primeiro_paragrafo

# Padrão de URL de notícia: /2026/01/23/titulo-da-materia/
REGEX_DATA_NEWS = re.compile(r'/\d{4}/\d{2}/\d{2}/')

def coletar_brasil_de_fato():
    if not PLAYWRIGHT_AVAILABLE:
        print("⚠️ [BdF] Playwright não disponível.")
        return []

    BASE_URL = "https://www.brasildefato.com.br/"
    noticias_coletadas = []
    urls_vistas = set()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            print(f"[BdF] Acessando Home via Playwright...")
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
            
            # Espera o Elementor carregar os blocos de notícia
            page.wait_for_selector(".e-loop-item", timeout=20000)
            
            soup = BeautifulSoup(page.content(), 'html.parser')
            browser.close()

            # Estratégia: Buscamos as manchetes dentro dos Heading Titles do Elementor
            manchetes_tags = soup.find_all(['h2', 'h3'], class_='elementor-heading-title')

            for tag in manchetes_tags:
                link_tag = tag.find('a', href=REGEX_DATA_NEWS)
                if not link_tag:
                    continue

                url_completa = urljoin(BASE_URL, link_tag['href'])
                titulo_candidato = link_tag.get_text().strip()

                # --- FILTROS INTELIGENTES ---
                
                # 1. Ignora "Chapéus" (Tags curtas como 'TENSÃO', 'É GREVE', 'RUMO AO OSCAR')
                # Manchetes reais do BdF dificilmente têm menos de 35 caracteres.
                if len(titulo_candidato) < 35:
                    continue

                # 2. Evita duplicados (A home repete links em diferentes blocos)
                if url_completa in urls_vistas:
                    continue

                if len(noticias_coletadas) >= 10: 
                    break

                print(f"   [BdF] Lendo conteúdo: {titulo_candidato[:50]}...")
                
                # DEEP SCRAPING: Acessa a página da notícia para pegar o lead real
                conteudo_lead = extrair_primeiro_paragrafo(url_completa)

                # Limpeza de boilerplate que possa ter vindo no lead
                if conteudo_lead:
                    # Se o lead vier com o aviso de copyright, cortamos ele
                    if "Todos os conteúdos" in conteudo_lead:
                        conteudo_lead = conteudo_lead.split("Todos os conteúdos")[0].strip()
                    
                    texto_ia = f"{titulo_candidato}. {conteudo_lead}"
                else:
                    texto_ia = titulo_candidato

                noticias_coletadas.append({
                    "nome_fonte": "Brasil de Fato",
                    "titulo": titulo_candidato,
                    "url": url_completa,
                    "texto_analise_ia": texto_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                
                urls_vistas.add(url_completa)

            print(f"Brasil de Fato: {len(noticias_coletadas)} notícias filtradas com sucesso.")
            return noticias_coletadas

    except Exception as e:
        print(f"❌ Erro Crítico no Scraper BdF: {e}")
        return []