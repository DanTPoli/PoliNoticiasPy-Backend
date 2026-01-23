import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import re
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_brasil_de_fato():
    BASE_URL = "https://www.brasildefato.com.br/politica"
    # User-Agent mais completo para evitar bloqueios de segurança
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    }
    noticias_coletadas = []

    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # ESTRATÉGIA REFINADA: 
        # Em vez de buscar o div 'e-loop-item', vamos buscar todos os H2 
        # que contenham a classe 'elementor-heading-title', que vimos no seu HTML.
        manchetes = soup.find_all('h2', class_=re.compile("elementor-heading-title"))

        if not manchetes:
            # Fallback: Busca qualquer link que tenha o padrão de data do BdF (/2026/01/...)
            manchetes = [a.parent for a in soup.find_all('a', href=re.compile(r'/\d{4}/\d{2}/\d{2}/'))]

        urls_vistas = set()
        count = 0
        
        for tag in manchetes:
            if count >= 10: break

            # Busca o <a> dentro ou próximo à tag encontrada
            link_tag = tag.find('a') if tag.name != 'a' else tag
            
            if link_tag and link_tag.get('href'):
                href = link_tag.get('href')
                link_completo = urljoin(BASE_URL, href)
                
                # Limpeza: evita links repetidos, de categorias ou institucionais
                if link_completo in urls_vistas or "/editoria/" in link_completo or "doar" in link_completo:
                    continue
                
                titulo = link_tag.get_text().strip()
                if len(titulo) < 10: continue # Pula títulos muito curtos/ruídos

                print(f"   [BdF] Processando: {titulo[:50]}...")
                
                # DEEP SCRAPING
                conteudo_lead = extrair_primeiro_paragrafo(link_completo)
                
                if conteudo_lead:
                    texto_analise_ia = f"{titulo}. {conteudo_lead}"
                else:
                    # Se não conseguir ler o conteúdo, tenta pegar o texto ao redor do link na home
                    texto_analise_ia = titulo

                noticias_coletadas.append({
                    "nome_fonte": "Brasil de Fato",
                    "titulo": titulo,
                    "url": link_completo,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                
                urls_vistas.add(link_completo)
                count += 1

        print(f"✅ Brasil de Fato: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except Exception as e:
        print(f"❌ Erro fatal no Brasil de Fato: {e}")
        return []