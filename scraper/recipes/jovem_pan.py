import requests
from bs4 import BeautifulSoup
from datetime import datetime
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_jovem_pan():
    BASE_URL = "https://jovempan.com.br/noticias/politica" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Busca H2 com classe 'post-title' OU qualquer H2 dentro de um <article>
        titulos = soup.select('h2.post-title, article h2, .title')

        count = 0
        for h2 in titulos:
            if count >= 8: break
            
            link_tag = h2.find('a') if h2.find('a') else h2.find_parent('a')
            
            if link_tag:
                link = link_tag.get('href')
                titulo = h2.text.strip()
                
                if not link or len(titulo) < 10: continue

                print(f"   [Jovem Pan] Lendo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)
                texto_ia = f"{titulo}. {conteudo_real}" if conteudo_real else titulo

                noticias_coletadas.append({
                    "nome_fonte": "Jovem Pan",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
                
        print(f"Jovem Pan: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas
    except Exception as e:
        print(f"Erro Jovem Pan: {e}")
        return []