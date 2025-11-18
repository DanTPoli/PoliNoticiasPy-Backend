# NOVO scraper/recipes/cnn_brasil.py (Com Playwright)

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime
import time # Usado para dar um tempo para o JS carregar

def coletar_cnn_brasil():
    BASE_URL = "https://www.cnnbrasil.com.br/politica/"
    noticias_coletadas = []

    # 1. INICIALIZAR O PLAYWRIGHT
    with sync_playwright() as p:
        # Usamos o Chromium, mas sem interface gráfica (headless=True)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 2. NAVEGAR E ESPERAR
        print(f"Playwright: Navegando em {BASE_URL}...")
        page.goto(BASE_URL)
        
        # Damos um pequeno tempo para o JavaScript carregar tudo
        time.sleep(5) 
        
        # 3. OBTER O CONTEÚDO RENDERIZADO
        # Agora o Beautiful Soup vai ver o HTML COMPLETO
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        browser.close() # Fechamos o navegador simulado
        
        # 4. APLICAÇÃO DO SELETOR ROBUSTO H3
        
        todos_h3 = soup.find_all('h3') 
        
        for titulo_tag in todos_h3:
            link_tag = titulo_tag.find_parent('a')
            figcaption_tag = titulo_tag.find_parent('figcaption')

            if link_tag and figcaption_tag:
                link = link_tag.get('href')
                titulo = titulo_tag.text.strip()
                
                categoria_tag = figcaption_tag.find('span', class_='text-base font-medium text-gray-400')
                categoria = categoria_tag.text.strip() if categoria_tag else "Sem Categoria"
                
                noticias_coletadas.append({
                    "nome_fonte": "CNN Brasil",
                    "titulo": titulo,
                    "url": link,
                    "categoria": categoria,
                    "texto_analise_ia": titulo, 
                    "viés_classificado": None,
                    "id_cluster": None,
                    "data_coleta": datetime.now().isoformat()
                })
        
        print(f"CNN Brasil (Playwright): {len(noticias_coletadas)} notícias coletadas.")
        return noticias_coletadas

if __name__ == '__main__':
    # Teste
    dados_cnn = coletar_cnn_brasil()
    for item in dados_cnn:
        print(f"Título: {item['titulo']} | URL: {item['url']}")