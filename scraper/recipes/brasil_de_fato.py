import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_brasil_de_fato():
    """
    Scraper refinado para Brasil de Fato usando estrutura Elementor (2026).
    """
    BASE_URL = "https://www.brasildefato.com.br/politica"
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    noticias_coletadas = []

    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # O padrão do seu HTML mostra que cada notícia é um 'e-loop-item'
        itens_loop = soup.find_all('div', class_='e-loop-item')

        count = 0
        for item in itens_loop:
            if count >= 10: break

            try:
                # 1. Busca o título e link dentro da classe padrão do Elementor
                # O seu HTML mostra: <h2 class="elementor-heading-title"><a href="...">Título</a></h2>
                h2_titulo = item.find('h2', class_='elementor-heading-title')
                if not h2_titulo: continue
                
                link_tag = h2_titulo.find('a')
                if not link_tag: continue

                titulo = link_tag.text.strip()
                link_completo = urljoin(BASE_URL, link_tag.get('href'))

                # 2. Evita links repetidos ou institucionais
                if not titulo or "aniversario" in link_completo.lower():
                    continue

                # 3. DEEP SCRAPING: Busca o lead da notícia
                print(f"   [BdF] Lendo lead: {titulo[:40]}...")
                conteudo_lead = extrair_primeiro_paragrafo(link_completo)

                # 4. Construção do texto para a IA (Título + Contexto)
                if conteudo_lead:
                    texto_analise_ia = f"{titulo}. {conteudo_lead}"
                else:
                    # Se falhar o deep scraping, tentamos pegar qualquer texto curto no card
                    resumo_fallback = item.get_text(separator=" ", strip=True).replace(titulo, "")[:200]
                    texto_analise_ia = f"{titulo}. {resumo_fallback}"

                noticias_coletadas.append({
                    "nome_fonte": "Brasil de Fato",
                    "titulo": titulo,
                    "url": link_completo,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1

            except Exception as e_item:
                print(f"⚠️ Erro no item BdF: {e_item}")
                continue

        print(f"✅ Brasil de Fato: {len(noticias_coletadas)} notícias processadas.")
        return noticias_coletadas

    except Exception as e:
        print(f"❌ Erro fatal no scraper BdF: {e}")
        return []