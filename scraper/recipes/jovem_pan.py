import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_jovem_pan():
    """
    Coleta notícias da Jovem Pan (Política) com Deep Scraping.
    Baseado na estrutura <a><div class="news-small">...</div></a>.
    """
    BASE_URL = "https://jovempan.com.br/noticias/politica" 
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        # O HTML mostra que o conteúdo principal fica em 'news-small'
        blocos_noticia = soup.find_all('div', class_='news-small')

        count = 0

        for bloco in blocos_noticia:
            if count >= 8: break

            # 2. EXTRAINDO LINK E TÍTULO
            # O link (<a>) é o PAI da div 'news-small' no seu exemplo
            link_tag = bloco.find_parent('a')
            
            # O título fica dentro de um <p class="title">
            titulo_tag = bloco.find('p', class_='title')

            if link_tag and titulo_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                if not link or len(titulo) < 5:
                    continue

                # Extrai a categoria se existir (ex: "Confusão na Câmara") para enriquecer o fallback
                cat_tag = bloco.find('h6', class_='category')
                categoria = cat_tag.text.strip() if cat_tag else ""

                # --- DEEP SCRAPING ---
                print(f"   [Jovem Pan] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    # Fallback com categoria + título
                    texto_analise_ia = f"{categoria}: {titulo}" if categoria else titulo
                
                noticias_coletadas.append({
                    "nome_fonte": "Jovem Pan",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"Jovem Pan: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Jovem Pan: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping da Jovem Pan: {e}")
        return []