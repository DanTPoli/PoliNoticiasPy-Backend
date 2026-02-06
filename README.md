# PoliNoticiasPy - Backend

Este repositório contém o backend do PoliNoticias, um agregador de notícias brasileiro inspirado no Ground News. O projeto utiliza técnicas de Processamento de Linguagem Natural (NLP) com o modelo Multilingual-E5 para agrupar matérias e oferecer uma visão crítica sobre o viés midiático.

## 🚀 Funcionalidades

### Scraping de Portais: 
Coleta automatizada de notícias de diversas fontes nacionais.

### Processamento Semântico:
Uso de NLP para gerar embeddings, permitindo o agrupamento de notícias por similaridade de contexto e busca semântica.

### Análise de Viés:
Algoritmo para classificação da inclinação política e ideológica das matérias.

### API para Mobile e Web:
Servidor Flask que alimenta a interface desenvolvida em React Native + Expo.

## 📂 Estrutura do Projeto

### /scraper:
Scripts de extração de dados e tratamento de anti-bot.

### /analysis:
Lógica de inteligência artificial, classificação e implementação dos embeddings E5.

### /db_utils:
Utilitários para persistência de documentos e vetores no MongoDB.

### app.py:
Ponto central da API REST.

## 🛠️ Tecnologias Utilizadas

### Linguagem:
Python 3.10+

### NLP & IA:
sentence-transformers (Multilingual-E5), torch.

### Backend:
Flask.

### Banco de Dados:
MongoDB (NoSQL).

### Web Scraping:
BeautifulSoup4, requests.

## ⚙️ Configuração Local

### Instalação

#### 1. Clone o repositório:

```python
git clone https://github.com/DanTPoli/PoliNoticiasPy-Backend.git
cd PoliNoticiasPy-Backend
```

#### 2. Ambiente Virtual & Dependências:

```python
python -m venv venv
source venv/bin/activate  # ou .\venv\Scripts\activate no Windows
pip install -r requirements.txt
```

#### 3. Configuração: 
Crie um arquivo .env na raiz do projeto com suas credenciais do MongoDB e outras chaves necessárias (veja .env.example).

### Execução

Para iniciar o servidor:

```python
python app.py
```

Nota: Na primeira execução, o modelo E5 será baixado automaticamente via Hugging Face.

## 🤝 Sobre o Projeto

O PoliNoticias é um projeto sem fins lucrativos que busca facilitar o acesso a diferentes perspectivas sobre os mesmos fatos, promovendo o pluralismo de ideias.

---

Desenvolvido por DanTPoli. README escrito pelo Gemini, IA do Google.
