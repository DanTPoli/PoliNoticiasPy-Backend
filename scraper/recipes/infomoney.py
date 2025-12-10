import requests
from bs4 import BeautifulSoup
from datetime import datetime
# Importa a função que lê o conteúdo real da página
from scraper.content_extractor import extrair_primeiro_paragrafo

def coletar_infomoney():
    """
    Coleta notícias do InfoMoney (Política) com Deep Scraping.
    Baseado nos componentes data-ds-component="card-..."
    """
    BASE_URL = "https://www.infomoney.com.br/politica/" 
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    noticias_coletadas = []
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICANDO OS BLOCOS CHAVE
        # O InfoMoney usa atributos data-ds-component="card-xs", "card-sm", etc.
        # Usamos uma função lambda para pegar qualquer div que tenha 'card' no nome do componente
        blocos_noticia = soup.find_all('div', attrs={'data-ds-component': lambda x: x and 'card' in x})

        count = 0

        for bloco in blocos_noticia:
            if count >= 8: break

            # 2. EXTRAINDO LINK E TÍTULO
            # O título está sempre numa tag h2 com a classe font-im-sans
            titulo_tag = bloco.find('h2', class_='font-im-sans')
            
            if titulo_tag:
                link_tag = titulo_tag.find('a', href=True)

                if link_tag:
                    link = link_tag.get('href')
                    titulo = link_tag.text.strip()
                    
                    # Evita pegar links vazios ou javascript
                    if not link or len(titulo) < 5:
                        continue

                    # --- DEEP SCRAPING ---
                    print(f"   [InfoMoney] Lendo conteúdo: {titulo[:30]}...")
                    conteudo_real = extrair_primeiro_paragrafo(link)

                    if conteudo_real:
                        texto_analise_ia = f"{titulo}. {conteudo_real}"
                    else:
                        # Fallback: InfoMoney cards as vezes não tem resumo visual, usa só o título
                        texto_analise_ia = titulo
                    
                    noticias_coletadas.append({
                        "nome_fonte": "InfoMoney",
                        "titulo": titulo,
                        "url": link,
                        "texto_analise_ia": texto_analise_ia,
                        "viés_classificado": None,
                        "id_cluster": None,
                        "data_coleta": datetime.now().isoformat()
                    })
                    count += 1
        
        print(f"InfoMoney: {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

    except requests.RequestException as e:
        print(f"Erro ao coletar InfoMoney: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado no scraping do InfoMoney: {e}")
        return []