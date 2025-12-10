import requests
from bs4 import BeautifulSoup
from datetime import datetime
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_jornal_de_brasilia():
    BASE_URL = "https://jornaldebrasilia.com.br/noticias/politica-e-poder/" 
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Busca H2 com classe 'title' (padrão deles) ou genéricos
        titulos = soup.select('h2.title, article h2')

        count = 0
        for h2 in titulos:
            if count >= 8: break
            
            link_tag = h2.find('a') if h2.find('a') else h2.find_parent('a')
            if link_tag:
                link = link_tag.get('href')
                titulo = h2.text.strip()
                
                if not link or len(titulo) < 5: continue

                print(f"   [JdB] Lendo: {titulo[:30]}...")
                conteudo = extrair_primeiro_paragrafo(link)
                texto_ia = f"{titulo}. {conteudo}" if conteudo else titulo

                noticias_coletadas.append({
                    "nome_fonte": "Jornal de Brasília",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"Jornal de Brasília: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except Exception as e:
        print(f"Erro JdB: {e}")
        return []