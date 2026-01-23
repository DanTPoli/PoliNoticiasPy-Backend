import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def extrair_primeiro_paragrafo(url, html_content=None):
    """
    Tenta extrair um lead completo. Se html_content for passado, pula o requests (útil para Playwright).
    """
    try:
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
        else:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

        # 1. IDENTIFICAÇÃO DO CONTAINER DE CONTEÚDO REAL
        target = None
        if "brasildefato.com.br" in url:
            target = soup.find('div', class_='elementor-widget-theme-post-content')
        elif "revistaoeste.com" in url:
            # Revista Oeste usa majoritariamente 'artigo--texto' ou 'entry-content'
            target = soup.find('div', class_='artigo--texto') or soup.find('div', class_='entry-content')
        
        # Fallback genérico se não achou container específico
        if not target:
            target = soup.find('article') or soup.find('main') or soup.find('div', class_='content') or soup.body

        if target:
            paragrafos_validos = []
            # Buscamos apenas parágrafos diretos para evitar legendas e lixo
            for p in target.find_all('p', recursive=True):
                texto = p.get_text().strip()
                
                # FILTRO DE RUÍDO: Ignora parágrafos institucionais
                blacklist = ["Todos os conteúdos", "direitos reservados", "assinante", 
    "Leia também", "Clique aqui", "Verifying you are human", "Cloudflare"]
                if any(termo in texto for termo in blacklist) or len(texto) < 45:
                    continue
                
                paragrafos_validos.append(texto)
                
                # REFINAMENTO ACÚMULO: Garante lead de ~180 caracteres para a IA
                texto_acumulado = " ".join(paragrafos_validos)
                if len(texto_acumulado) > 180:
                    return texto_acumulado
            
            if paragrafos_validos:
                return " ".join(paragrafos_validos)

        return None
    except Exception as e:
        print(f"⚠️ Erro no extractor para {url}: {e}")
        return None