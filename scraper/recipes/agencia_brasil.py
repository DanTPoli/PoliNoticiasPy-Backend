import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_agencia_brasil():
    """
    Coleta notícias da Agência Brasil (Política) com Deep Scraping.
    Baseado na estrutura <div class="noticia">.
    """
    BASE_URL = "https://agenciabrasil.ebc.com.br/politica" 
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        # O bloco principal de cada notícia tem a classe 'noticia'
        blocos_noticia = soup.find_all('div', class_='noticia')

        count = 0

        for bloco in blocos_noticia:
            if count >= 8: break

            # 2. EXTRAINDO LINK E TÍTULO
            # O link do título possui a classe 'titulo-noticia'
            link_tag = bloco.find('a', class_='titulo-noticia')

            if link_tag:
                # O HTML fornecido mostra espaços no href: "  https://..."
                # Usamos .strip() para limpar esses espaços
                link = link_tag.get('href', '').strip()
                
                # O título está dentro de um <h2> dentro do link
                titulo_tag = link_tag.find('h2')
                titulo = titulo_tag.text.strip() if titulo_tag else link_tag.text.strip()
                
                if not link or len(titulo) < 5:
                    continue
                
                # Extrai a categoria (ex: "Política") para fallback
                chapeu_tag = bloco.find('div', class_='chapeu')
                categoria = chapeu_tag.text.strip() if chapeu_tag else ""

                # --- DEEP SCRAPING ---
                print(f"   [Agência Brasil] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    # Fallback: Título + Categoria (card não tem resumo)
                    texto_analise_ia = f"{categoria}: {titulo}" if categoria else titulo
                
                noticias_coletadas.append({
                    "nome_fonte": "Agência Brasil",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"Agência Brasil: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Agência Brasil: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping da Agência Brasil: {e}")
        return []