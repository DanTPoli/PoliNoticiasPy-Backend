import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_jornal_de_brasilia():
    """
    Coleta notícias do Jornal de Brasília (Política e Poder) com Deep Scraping.
    Baseado na estrutura <article><div class="block">.
    """
    # URL baseada no link do seu exemplo
    BASE_URL = "https://jornaldebrasilia.com.br/noticias/politica-e-poder/" 
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        # O HTML mostra tags <article> contendo div class="block"
        blocos_noticia = soup.find_all('article')

        count = 0

        for bloco in blocos_noticia:
            if count >= 8: break

            # Procura a div interna "block" para garantir que é o elemento certo
            div_block = bloco.find('div', class_='block')
            if not div_block:
                continue

            # 2. EXTRAINDO LINK E TÍTULO
            # O link mais seguro está dentro de .inner > a
            div_inner = div_block.find('div', class_='inner')
            if not div_inner:
                continue
                
            link_tag = div_inner.find('a', href=True)
            
            if link_tag:
                link = link_tag.get('href')
                
                # O título está no h2 class="title"
                titulo_tag = link_tag.find('h2', class_='title')
                titulo = titulo_tag.text.strip() if titulo_tag else ""
                
                if not link or len(titulo) < 5:
                    continue

                # --- DEEP SCRAPING ---
                print(f"   [Jornal de Brasília] Lendo conteúdo: {titulo[:30]}...")
                conteudo_real = extrair_primeiro_paragrafo(link)

                if conteudo_real:
                    texto_analise_ia = f"{titulo}. {conteudo_real}"
                else:
                    # Fallback: Apenas o título (card não tem resumo)
                    texto_analise_ia = titulo
                
                noticias_coletadas.append({
                    "nome_fonte": "Jornal de Brasília",
                    "titulo": titulo,
                    "url": link,
                    "texto_analise_ia": texto_analise_ia,
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
                count += 1
        
        print(f"Jornal de Brasília: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar Jornal de Brasília: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping do Jornal de Brasília: {e}")
        return []