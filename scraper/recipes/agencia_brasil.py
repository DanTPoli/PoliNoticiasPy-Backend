import requests
from bs4 import BeautifulSoup
from datetime import datetime
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_agencia_brasil():
    """
    Coleta notícias da Agência Brasil (Últimas) com Deep Scraping.
    Baseado na estrutura <div class="ultima-noticia">.
    """
    # Mudei para /ultimas conforme seu exemplo, pois a estrutura lá é garantida
    BASE_URL = "https://agenciabrasil.ebc.com.br/ultimas" 
    BASE_DOMAIN = "https://agenciabrasil.ebc.com.br"
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        # O bloco agora é "ultima-noticia"
        blocos = soup.find_all('div', class_='ultima-noticia')
        
        count = 0
        for bloco in blocos:
            if count >= 8: break
            
            # 2. EXTRAINDO LINK E TÍTULO
            # O link com a classe 'titulo-noticia' contém o texto direto
            link_tag = bloco.find('a', class_='titulo-noticia')
            
            if link_tag:
                link = link_tag.get('href', '').strip()
                # Correção de URL relativa
                if link.startswith('/'): link = BASE_DOMAIN + link
                
                # O título é o próprio texto do link neste formato
                titulo = link_tag.get_text(strip=True)
                
                if len(titulo) < 10: continue

                # Filtro opcional: Se quiser focar em política, podemos checar a editoria
                # editoria_tag = bloco.find('a', class_='editoria')
                # if editoria_tag and 'Política' not in editoria_tag.text: continue

                print(f"   [Agência Brasil] Lendo: {titulo[:30]}...")
                conteudo = extrair_primeiro_paragrafo(link)
                texto_ia = f"{titulo}. {conteudo}" if conteudo else titulo

                noticias_coletadas.append({
                    "nome_fonte": "Agência Brasil",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1

        print(f"Agência Brasil: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas
    except Exception as e:
        print(f"Erro Agência Brasil: {e}")
        return []