import requests
from bs4 import BeautifulSoup

# Headers padrão para evitar bloqueios simples
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def extrair_primeiro_paragrafo(url):
    """
    Visita a URL da notícia e tenta extrair o primeiro parágrafo significativo.
    Retorna uma string limpa ou None se falhar.
    """
    try:
        # Timeout curto para não travar o scraper se o site for lento
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Tenta encontrar o corpo do texto. 
        # A maioria dos sites usa <article>, <main> ou classes específicas.
        # Esta é uma heurística genérica que funciona em muitos portais.
        
        # 1. Procura por tags <p> dentro de um <article> (Padrão moderno HTML5)
        article = soup.find('article')
        if article:
            paragrafos = article.find_all('p')
            for p in paragrafos:
                texto = p.text.strip()
                # Ignora parágrafos muito curtos (legendas, autores, datas)
                if len(texto) > 50: 
                    return texto

        # 2. Fallback: Procura por tags <p> no corpo principal se não achar <article>
        # Exclui headers e footers da busca
        main_content = soup.find('main') or soup.find('div', class_='content') or soup.body
        
        if main_content:
            paragrafos = main_content.find_all('p')
            for p in paragrafos:
                texto = p.text.strip()
                if len(texto) > 50:
                    return texto
        
        return None

    except Exception as e:
        print(f"⚠️ Falha ao extrair conteúdo de {url}: {e}")
        return None