import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def extrair_primeiro_paragrafo(url):
    try:
        # Aumentado para 10s para garantir carga em sites mais pesados
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. REFINAMENTO: Busca containers específicos para evitar lixo institucional
        # Se você notar que outros portais estão vindo com lixo, basta adicionar o elif aqui.
        target = None
        if "brasildefato.com.br" in url:
            target = soup.find('div', class_='elementor-widget-theme-post-content')
        
        # Se não for um site mapeado ou não achou o container, usa o seu padrão original
        if not target:
            target = soup.find('article') or soup.find('main') or soup.find('div', class_='content') or soup.body

        if target:
            paragrafos_validos = []
            paragrafos = target.find_all('p')
            
            for p in paragrafos:
                texto = p.get_text().strip()
                
                # FILTRO DE RUÍDO: Ignora parágrafos institucionais conhecidos
                if "Todos os conteúdos" in texto or "direitos reservados" in texto.lower():
                    continue
                
                if len(texto) > 50:
                    paragrafos_validos.append(texto)
                    
                    # REFINAMENTO "TEXTO COMPLETO": 
                    # Acumula até ter pelo menos 180 caracteres para a IA ter contexto real.
                    texto_acumulado = " ".join(paragrafos_validos)
                    if len(texto_acumulado) > 180:
                        return texto_acumulado
            
            # Caso tenha encontrado texto mas não atingiu 180 chars, retorna o que tiver
            if paragrafos_validos:
                return " ".join(paragrafos_validos)

        return None

    except Exception as e:
        print(f"⚠️ Falha ao extrair conteúdo de {url}: {e}")
        return None