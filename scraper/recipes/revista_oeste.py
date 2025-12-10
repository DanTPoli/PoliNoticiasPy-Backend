import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_revista_oeste():
    """
    Coleta notícias da Revista Oeste (Política) com Deep Scraping.
    Baseado na estrutura <article class="card-post">.
    """
    BASE_URL = "https://revistaoeste.com/politica/" 
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://revistaoeste.com/'
    }
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        # A Revista Oeste usa tags <article> com a classe 'card-post'
        blocos_noticia = soup.find_all('article', class_='card-post')

        count = 0

        for bloco in blocos_noticia:
            if count >= 8: break

            # 2. EXTRAINDO LINK E TÍTULO
            # O link principal tem a classe 'card-post__title' e o título está num h3 dentro dele
            link_tag = bloco.find('a', class_='card-post__title', href=True)
            
            if link_tag:
                link = link_tag.get('href')
                
                titulo_tag = link_tag.find('h3')
                titulo = titulo_tag.text.strip() if titulo_tag else link_tag.text.strip()
                
                if not link or len(titulo) < 5:
                    continue

                # --- DEEP SCRAPING ---
                # Como o card não tem resumo, precisamos entrar no link
                print(f"   [Revista Oeste] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    # Fallback: Se não conseguir ler, usa só o título (não há resumo no card)
                    texto_analise_ia = titulo
                
                noticias_coletadas.append({
                    "nome_fonte": "Revista Oeste",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"Revista Oeste: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Revista Oeste: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping da Revista Oeste: {e}")
        return []