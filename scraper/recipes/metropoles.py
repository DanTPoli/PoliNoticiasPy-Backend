import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_metropoles():
    """
    Coleta notícias do Metrópoles (Seção Brasil) com Deep Scraping.
    Ajustado para os seletores exatos fornecidos (NoticiaWrapper).
    """
    # URL da seção Brasil
    BASE_URL = "https://www.metropoles.com/brasil" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE: O container <article> principal
        # Usamos uma classe parcial para maior estabilidade
        blocos_noticia = soup.find_all('article', class_=lambda c: c and 'NoticiaWrapper__Article' in c) 

        count = 0

        for bloco in blocos_noticia:
            if count >= 8: break

            # 2. EXTRAINDO LINK, TÍTULO E RESUMO
            # O link está no <a> dentro do <h4>
            titulo_tag = bloco.find('h4', class_=lambda c: c and 'noticia__titulo' in c)
            link_tag = titulo_tag.find('a', href=True) if titulo_tag else None
            
            # O resumo está na tag <p> com a classe 'noticia__descricao'
            descricao_div = bloco.find('div', class_=lambda c: c and 'noticia__descricao' in c)
            resumo_tag = descricao_div.find('p') if descricao_div else None

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                # --- DEEP SCRAPING ---
                print(f"   [Metrópoles] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    # Fallback: usa o resumo da capa
                    resumo = resumo_tag.text.strip() if resumo_tag else ""
                    texto_analise_ia = f"{titulo}. {resumo}"
                
                noticias_coletadas.append({
                    "nome_fonte": "Metrópoles",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"Metrópoles: {len(noticias_coletadas)} notícias coletadas com conteúdo profundo.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Metrópoles: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping do Metrópoles: {e}")
        return []