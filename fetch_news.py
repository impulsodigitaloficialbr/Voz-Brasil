"""
============================================================
VOZ BRASIL - Gerador Automático de Notícias
Busca RSS de fontes brasileiras e gera index.html atualizado
============================================================
Fontes:
  - CNN Brasil    → Notícias Gerais
  - Exame         → Economia
  - Lance         → Esportes
  - Adrenaline    → Tecnologia
  - Revista Oeste → Política
============================================================
"""

import feedparser
import json
import os
import re
import html
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# ============================================================
# CONFIGURAÇÃO DAS FONTES RSS
# ============================================================
RSS_SOURCES = {
    "geral": {
        "nome": "CNN Brasil",
        "url": "https://www.cnnbrasil.com.br/feed/",
        "categoria": "Notícias",
        "cat_class": "world",
        "cor": "#e74c3c"
    },
    "economia": {
        "nome": "Exame",
        "url": "https://exame.com/feed/",
        "categoria": "Economia",
        "cat_class": "economy",
        "cor": "#f39c12"
    },
    "esportes": {
        "nome": "Lance",
        "url": "https://www.lance.com.br/feed/",
        "categoria": "Esportes",
        "cat_class": "sports",
        "cor": "#2ecc71"
    },
    "tecnologia": {
        "nome": "Adrenaline",
        "url": "https://adrenaline.com/feed/",
        "categoria": "Tecnologia",
        "cat_class": "tech",
        "cor": "#00d4ff"
    },
    "politica": {
        "nome": "Revista Oeste",
        "url": "https://revistaoeste.com/feed/",
        "categoria": "Política",
        "cat_class": "politics",
        "cor": "#e74c3c"
    }
}

# Imagens padrão por categoria — múltiplas opções para variar (caso o RSS não traga imagem)
FALLBACK_IMAGES = {
    "geral": [
        "https://images.unsplash.com/photo-1504711434969-e33886168d6c?w=600&q=80",  # jornalismo
        "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=600&q=80",  # notícias
        "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=600&q=80",  # jornal impresso
        "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=600&q=80",     # reunião/debate
        "https://images.unsplash.com/photo-1478737270239-2f02b77fc618?w=600&q=80",  # rádio/comunicação
    ],
    "economia": [
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=600&q=80",  # dinheiro
        "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=600&q=80",     # finanças
        "https://images.unsplash.com/photo-1579532537598-459ecdaf39cc?w=600&q=80",  # negócios
        "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=600&q=80",  # executivo
        "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=600&q=80",  # contrato/trabalho
    ],
    "esportes": [
        "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=600&q=80",  # atletismo
        "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=600&q=80",  # futebol
        "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=600&q=80",     # basquete
        "https://images.unsplash.com/photo-1538805060514-97d9cc17730c?w=600&q=80",  # corrida
        "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=600&q=80",  # fitness/treino
    ],
    "tecnologia": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&q=80",  # circuito
        "https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=600&q=80",  # laptop moderno
        "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=600&q=80",     # cibersegurança
        "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=600&q=80",  # robô/IA
        "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?w=600&q=80",  # análise dados
    ],
    "politica": [
        "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=600&q=80",  # votação/democracia
        "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=600&q=80",     # congresso
        "https://images.unsplash.com/photo-1555848962-6e79363ec58f?w=600&q=80",     # discurso
        "https://images.unsplash.com/photo-1568092795958-a3e4aadc5d0c?w=600&q=80",  # bandeira brasil
        "https://images.unsplash.com/photo-1570126618953-d437176e8c79?w=600&q=80",  # protesto/manifestação
    ],
}

import random
def get_fallback_image(chave):
    """Retorna uma imagem padrão aleatória da categoria para variar o visual."""
    opcoes = FALLBACK_IMAGES.get(chave, FALLBACK_IMAGES["geral"])
    return random.choice(opcoes)

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def limpar_html(texto):
    """Remove tags HTML e entidades do texto."""
    if not texto:
        return ""
    texto = re.sub(r'<[^>]+>', '', str(texto))
    texto = html.unescape(texto)
    texto = ' '.join(texto.split())
    return texto.strip()

def extrair_imagem(entry):
    """Tenta extrair a imagem de uma entrada RSS por diferentes métodos."""
    # 1. media_thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url', '')

    # 2. media_content
    if hasattr(entry, 'media_content') and entry.media_content:
        for m in entry.media_content:
            if m.get('url') and m.get('medium') == 'image':
                return m['url']
            if m.get('url') and 'image' in m.get('type', ''):
                return m['url']

    # 3. enclosures
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if 'image' in enc.get('type', ''):
                return enc.get('href', enc.get('url', ''))

    # 4. Busca img na descrição/summary
    for campo in ['summary', 'content', 'description']:
        texto = ''
        if campo == 'content' and hasattr(entry, 'content'):
            texto = entry.content[0].value if entry.content else ''
        else:
            texto = getattr(entry, campo, '')
        if texto:
            match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', str(texto))
            if match:
                url = match.group(1)
                if url.startswith('http') and any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    return url

    return ''

def formatar_data(entry):
    """Formata a data de publicação de forma legível."""
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            agora = datetime.now(timezone.utc)
            diff = agora - dt
            minutos = int(diff.total_seconds() / 60)
            if minutos < 60:
                return f"{minutos} min atrás" if minutos > 1 else "Agora"
            horas = int(minutos / 60)
            if horas < 24:
                return f"{horas}h atrás"
            dias = int(horas / 24)
            if dias == 1:
                return "Ontem"
            return f"{dias} dias atrás"
    except:
        pass
    return "Recentemente"

def extrair_resumo(entry):
    """Extrai e limpa o resumo da notícia."""
    for campo in ['summary', 'description']:
        texto = getattr(entry, campo, '')
        if texto:
            limpo = limpar_html(texto)
            if len(limpo) > 20:
                return limpo[:200] + '...' if len(limpo) > 200 else limpo
    return "Clique para ler a notícia completa."

def buscar_noticias(chave, config, limite=6):
    """Busca notícias de uma fonte RSS e retorna lista formatada."""
    print(f"  → Buscando {config['nome']}...")
    try:
        feed = feedparser.parse(config['url'])
        noticias = []

        for entry in feed.entries[:limite]:
            titulo = limpar_html(getattr(entry, 'title', 'Sem título'))
            if not titulo or len(titulo) < 10:
                continue

            imagem = extrair_imagem(entry)
            if not imagem:
                imagem = get_fallback_image(chave)

            noticia = {
                "title":        titulo,
                "summary":      extrair_resumo(entry),
                "category":     config['categoria'],
                "categoryClass": config['cat_class'],
                "img":          imagem,
                "link":         getattr(entry, 'link', '#'),
                "source":       config['nome'],
                "date":         formatar_data(entry)
            }
            noticias.append(noticia)

        print(f"     ✓ {len(noticias)} notícias encontradas")
        return noticias

    except Exception as e:
        print(f"     ✗ Erro ao buscar {config['nome']}: {e}")
        return []

# ============================================================
# GERADOR DO HTML
# ============================================================

def gerar_html(todas_noticias):
    """Gera o index.html completo com as notícias reais."""

    agora = datetime.now()
    data_atualizacao = agora.strftime("%d/%m/%Y às %H:%M")

    noticias_geral    = todas_noticias.get("geral", [])
    noticias_economia = todas_noticias.get("economia", [])
    noticias_esportes = todas_noticias.get("esportes", [])
    noticias_tech     = todas_noticias.get("tecnologia", [])
    noticias_politica = todas_noticias.get("politica", [])

    # Notícias em destaque: primeiras de cada categoria
    destaques = []
    for chave in ["geral", "politica", "economia", "esportes"]:
        if todas_noticias.get(chave):
            destaques.append(todas_noticias[chave][0])

    # Ticker: títulos das primeiras notícias de cada categoria
    ticker_items = []
    for chave in RSS_SOURCES.keys():
        if todas_noticias.get(chave):
            n = todas_noticias[chave][0]
            ticker_items.append(f"{n['source'].upper()}: {n['title']}")

    ticker_html = ""
    for item in ticker_items * 2:
        ticker_html += f'<span><a href="#">{item}</a></span><span style="color:rgba(255,255,255,0.4);padding:0 10px;">• • •</span>'

    # ---- Gerador de cards de notícia ----
    def card_html(n, extra_class=""):
        return f"""
                <article class="news-card {extra_class}" onclick="window.open('{n['link']}','_blank')" style="cursor:pointer;">
                    <div class="card-image">
                        <img src="{n['img']}" alt="{n['title']}" loading="lazy"
                             onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168d6c?w=600&q=80'">
                        <span class="card-category cat-{n['categoryClass']}">{n['category']}</span>
                    </div>
                    <div class="card-body">
                        <h3 class="card-title">{n['title']}</h3>
                        <p class="card-summary">{n['summary']}</p>
                        <span class="card-read-more">Ler mais <i class="fas fa-arrow-right"></i></span>
                        <div class="card-meta">
                            <div class="card-author">
                                <div class="avatar">{n['source'][0]}</div>
                                <span>{n['source']}</span>
                            </div>
                            <span class="card-date"><i class="far fa-clock"></i> {n['date']}</span>
                        </div>
                    </div>
                </article>"""

    # ---- Cards do hero ----
    hero_slides = ""
    hero_dots = ""
    hero_images = [
        "https://images.unsplash.com/photo-1504711434969-e33886168d6c?w=1920&q=80",
        "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=1920&q=80",
        "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=1920&q=80",
        "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=1920&q=80",
    ]
    for i, noticia in enumerate(destaques[:4]):
        active = "active" if i == 0 else ""
        img = hero_images[i] if i < len(hero_images) else hero_images[0]
        hero_slides += f"""
            <div class="hero-slide {active}" data-index="{i}">
                <img src="{img}" alt="{noticia['title']}" class="hero-bg">
                <div class="hero-overlay"></div>
                <div class="hero-content">
                    <span class="hero-category">{noticia['category']}</span>
                    <h2 class="hero-title">{noticia['title']}</h2>
                    <p class="hero-subtitle">{noticia['summary'][:150]}...</p>
                    <a href="{noticia['link']}" target="_blank" class="hero-btn">
                        Ler Notícia Completa <i class="fas fa-arrow-right"></i>
                    </a>
                </div>
            </div>"""
        hero_dots += f'<button class="hero-dot {"active" if i == 0 else ""}" data-slide="{i}"></button>'

    # ---- Cards das seções ----
    def secao_cards(lista, limite=4):
        return "".join(card_html(n) for n in lista[:limite])

    top_news_html    = secao_cards(noticias_geral, 4)
    more_news_html   = secao_cards(
        (noticias_economia[:2] + noticias_tech[:2]), 4
    )
    politics_html    = secao_cards(noticias_politica, 4)
    tech_html        = secao_cards(noticias_tech, 4)
    economy_html     = secao_cards(noticias_economia, 4)
    sports_html      = secao_cards(noticias_esportes, 4)

    # ---- Mais lidas (sidebar) ----
    mais_lidas = ""
    todas_flat = []
    for v in todas_noticias.values():
        todas_flat.extend(v[:2])
    tops = ["top-1", "top-2", "top-3", "", ""]
    for i, n in enumerate(todas_flat[:5]):
        mais_lidas += f"""
                        <div class="most-read-item" onclick="window.open('{n['link']}','_blank')" style="cursor:pointer;">
                            <span class="mr-number {tops[i] if i < len(tops) else ''}">{i+1}</span>
                            <div class="mr-content">
                                <h4>{n['title'][:80]}...</h4>
                                <span>{n['date']} • {n['source']}</span>
                            </div>
                        </div>"""

    # ============================================================
    # HTML COMPLETO
    # ============================================================
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Voz Brasil - As últimas notícias do Brasil e do mundo em tempo real.">
    <meta name="keywords" content="notícias, Brasil, mundo, política, tecnologia, economia, esportes">
    <meta name="author" content="Voz Brasil">
    <meta property="og:title" content="Voz Brasil - Portal de Notícias">
    <meta property="og:description" content="As últimas notícias do Brasil e do mundo em tempo real.">
    <meta property="og:type" content="website">
    <title>Voz Brasil - Notícias em Tempo Real</title>
    <!-- Atualizado automaticamente em: {data_atualizacao} -->

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800;900&family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

    <style>
        *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --bg-primary: #0b1020; --bg-secondary: #111827;
            --bg-card: rgba(255,255,255,0.05); --blue-neon: #1e90ff;
            --blue-dark: #0a6fd4; --blue-light: rgba(30,144,255,0.15);
            --white: #ffffff; --gray-light: #d1d5db; --gray-mid: #6b7280;
            --glass-bg: rgba(255,255,255,0.08); --glass-border: rgba(255,255,255,0.12);
            --shadow-neon: 0 0 20px rgba(30,144,255,0.3);
            --shadow-card: 0 4px 20px rgba(0,0,0,0.3);
            --shadow-hover: 0 8px 30px rgba(30,144,255,0.2);
            --cat-politics: #e74c3c; --cat-tech: #00d4ff;
            --cat-economy: #f39c12; --cat-sports: #2ecc71;
            --cat-world: #9b59b6; --cat-entertainment: #e91e90;
            --container-max: 1280px;
            --transition-fast: 0.2s ease; --transition-normal: 0.3s ease;
        }}
        body.light-mode {{
            --bg-primary: #f0f2f5; --bg-secondary: #e5e7eb;
            --bg-card: rgba(255,255,255,0.9); --white: #1a1a2e;
            --gray-light: #374151; --gray-mid: #6b7280;
            --glass-bg: rgba(255,255,255,0.6); --glass-border: rgba(0,0,0,0.1);
        }}
        html {{ scroll-behavior: smooth; overflow-x: hidden; }}
        body {{ font-family: 'Roboto', sans-serif; background: var(--bg-primary); color: var(--gray-light); line-height: 1.7; overflow-x: hidden; }}
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg-primary); }}
        ::-webkit-scrollbar-thumb {{ background: var(--blue-neon); border-radius: 10px; }}
        .container {{ max-width: var(--container-max); margin: 0 auto; padding: 0 20px; }}

        /* TOP BAR */
        .top-bar {{ background: var(--bg-secondary); border-bottom: 1px solid var(--glass-border); padding: 8px 0; font-size: 0.8rem; }}
        .top-bar .container {{ display: flex; justify-content: space-between; align-items: center; }}
        .top-bar-left {{ display: flex; gap: 20px; align-items: center; }}
        .top-bar-left a {{ color: var(--gray-light); text-decoration: none; transition: color var(--transition-fast); }}
        .top-bar-left a:hover {{ color: var(--blue-neon); }}
        .datetime-display {{ color: var(--gray-mid); font-size: 0.8rem; display: flex; align-items: center; gap: 8px; }}
        .datetime-display i {{ color: var(--blue-neon); }}
        .dark-mode-toggle {{ background: none; border: 1px solid var(--glass-border); color: var(--gray-light); padding: 6px 12px; border-radius: 20px; cursor: pointer; font-size: 0.85rem; transition: all var(--transition-fast); display: flex; align-items: center; gap: 6px; }}
        .dark-mode-toggle:hover {{ background: var(--blue-light); color: var(--blue-neon); border-color: var(--blue-neon); }}
        .update-badge {{ background: rgba(46,204,113,0.15); border: 1px solid rgba(46,204,113,0.3); color: #2ecc71; padding: 3px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; display: flex; align-items: center; gap: 5px; }}

        /* BREAKING BAR */
        .breaking-news-bar {{ background: linear-gradient(90deg,#e74c3c,#c0392b); padding: 10px 0; overflow: hidden; }}
        .breaking-label {{ background: var(--white); color: #e74c3c; padding: 4px 14px; font-weight: 800; font-size: 0.75rem; letter-spacing: 1px; text-transform: uppercase; display: inline-flex; align-items: center; gap: 6px; animation: pulse-label 2s infinite; }}
        @keyframes pulse-label {{ 0%,100%{{opacity:1}} 50%{{opacity:0.8}} }}
        .ticker-track {{ display: flex; animation: ticker-scroll 40s linear infinite; white-space: nowrap; }}
        .ticker-track span {{ flex-shrink: 0; padding: 0 30px; color: #fff; font-size: 0.82rem; }}
        .ticker-track span a {{ color: #fff; text-decoration: none; }}
        @keyframes ticker-scroll {{ 0%{{transform:translateX(0)}} 100%{{transform:translateX(-50%)}} }}

        /* HEADER */
        .header {{ background: rgba(11,16,32,0.95); backdrop-filter: blur(20px); position: fixed; top: 0; left: 0; right: 0; z-index: 1000; padding: 0 20px; border-bottom: 1px solid var(--glass-border); transition: transform var(--transition-normal); }}
        .header .container {{ display: flex; align-items: center; justify-content: space-between; height: 70px; }}
        .logo {{ display: flex; align-items: center; gap: 12px; text-decoration: none; flex-shrink: 0; }}
        .logo-icon {{ width: 42px; height: 42px; background: linear-gradient(135deg,var(--blue-neon),#0a6fd4); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; color: #fff; box-shadow: 0 2px 10px rgba(30,144,255,0.3); transition: transform var(--transition-normal); }}
        .logo:hover .logo-icon {{ transform: rotate(-5deg) scale(1.05); }}
        .logo-text {{ font-family: 'Montserrat', sans-serif; font-size: 1.6rem; font-weight: 800; color: var(--white); }}
        .logo-text span {{ color: var(--blue-neon); }}
        .logo-subtitle {{ font-size: 0.65rem; color: var(--gray-mid); text-transform: uppercase; letter-spacing: 2px; font-family: 'Montserrat', sans-serif; }}
        .nav-desktop {{ display: flex; align-items: center; gap: 5px; }}
        .nav-desktop a {{ color: var(--gray-light); text-decoration: none; padding: 8px 14px; font-size: 0.88rem; font-weight: 500; border-radius: 8px; transition: all var(--transition-fast); }}
        .nav-desktop a:hover, .nav-desktop a.active {{ color: var(--white); background: var(--glass-bg); }}
        .nav-desktop a.active {{ color: var(--blue-neon); }}
        .search-container {{ position: relative; }}
        .search-input {{ background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 25px; padding: 8px 16px 8px 38px; color: var(--white); font-size: 0.85rem; width: 200px; outline: none; transition: all var(--transition-normal); }}
        .search-input::placeholder {{ color: var(--gray-mid); }}
        .search-input:focus {{ border-color: var(--blue-neon); width: 260px; }}
        .search-icon {{ position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--gray-mid); font-size: 0.85rem; }}
        .hamburger {{ display: none; flex-direction: column; gap: 5px; cursor: pointer; padding: 5px; }}
        .hamburger span {{ width: 25px; height: 2px; background: var(--white); border-radius: 2px; transition: all var(--transition-normal); }}
        .hamburger.active span:nth-child(1){{ transform: rotate(45deg) translate(5px,5px); }}
        .hamburger.active span:nth-child(2){{ opacity: 0; }}
        .hamburger.active span:nth-child(3){{ transform: rotate(-45deg) translate(5px,-5px); }}

        /* MOBILE NAV */
        .mobile-nav {{ display: none; position: fixed; top: 0; right: -100%; width: 300px; height: 100vh; background: rgba(11,16,32,0.98); backdrop-filter: blur(20px); z-index: 999; padding: 90px 20px 20px; transition: right var(--transition-normal); overflow-y: auto; }}
        .mobile-nav.active {{ right: 0; }}
        .mobile-nav-overlay {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 998; }}
        .mobile-nav-overlay.active {{ display: block; }}
        .mobile-nav a {{ display: block; color: var(--gray-light); text-decoration: none; padding: 14px 16px; border-radius: 10px; font-size: 1rem; transition: all var(--transition-fast); margin-bottom: 4px; }}
        .mobile-nav a:hover {{ background: var(--blue-light); color: var(--blue-neon); }}

        /* HERO */
        .hero {{ margin-top: 70px; position: relative; overflow: hidden; }}
        .hero-slider {{ position: relative; width: 100%; height: 520px; overflow: hidden; }}
        .hero-slide {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; transition: opacity 1s ease-in-out; }}
        .hero-slide.active {{ opacity: 1; }}
        .hero-bg {{ width: 100%; height: 100%; object-fit: cover; }}
        .hero-overlay {{ position: absolute; inset: 0; background: linear-gradient(to top, rgba(11,16,32,0.95) 0%, rgba(11,16,32,0.6) 50%, rgba(11,16,32,0.3) 100%); }}
        .hero-content {{ position: absolute; bottom: 0; left: 0; right: 0; padding: 40px; z-index: 2; max-width: var(--container-max); margin: 0 auto; }}
        .hero-category {{ display: inline-block; background: var(--blue-neon); color: #fff; padding: 4px 14px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; }}
        .hero-title {{ font-family: 'Montserrat', sans-serif; font-size: 2.4rem; font-weight: 800; color: #fff; line-height: 1.2; margin-bottom: 16px; text-shadow: 0 2px 20px rgba(0,0,0,0.5); max-width: 700px; }}
        .hero-subtitle {{ font-size: 1rem; color: var(--gray-light); margin-bottom: 24px; max-width: 550px; }}
        .hero-btn {{ display: inline-flex; align-items: center; gap: 8px; background: var(--blue-neon); color: #fff; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 0.9rem; transition: all var(--transition-normal); }}
        .hero-btn:hover {{ background: #fff; color: var(--blue-neon); transform: translateY(-2px); box-shadow: var(--shadow-neon); }}
        .hero-nav {{ position: absolute; bottom: 20px; right: 40px; display: flex; gap: 10px; z-index: 3; }}
        .hero-dot {{ width: 10px; height: 10px; border-radius: 50%; background: rgba(255,255,255,0.4); cursor: pointer; transition: all var(--transition-fast); border: none; }}
        .hero-dot.active {{ background: var(--blue-neon); box-shadow: 0 0 10px var(--blue-neon); transform: scale(1.2); }}
        .hero-slide-counter {{ position: absolute; top: 20px; right: 40px; color: #fff; font-size: 0.8rem; font-weight: 600; z-index: 3; background: rgba(0,0,0,0.4); padding: 6px 14px; border-radius: 20px; }}

        /* SECTION */
        .section-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 30px; padding-bottom: 15px; border-bottom: 2px solid var(--glass-border); }}
        .section-title {{ font-family: 'Montserrat', sans-serif; font-size: 1.5rem; font-weight: 700; color: var(--white); display: flex; align-items: center; gap: 12px; }}
        .section-title i {{ color: var(--blue-neon); }}
        .view-more {{ color: var(--blue-neon); text-decoration: none; font-size: 0.85rem; font-weight: 600; display: flex; align-items: center; gap: 6px; transition: all var(--transition-fast); }}
        .view-more:hover {{ gap: 10px; }}
        .divider {{ height: 1px; background: var(--glass-border); margin: 40px 0; }}

        /* CARDS */
        .news-grid {{ display: grid; gap: 24px; }}
        .news-grid-4 {{ grid-template-columns: repeat(4,1fr); }}
        .news-grid-3 {{ grid-template-columns: repeat(3,1fr); }}
        .news-card {{ background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 14px; overflow: hidden; transition: all var(--transition-normal); }}
        .news-card:hover {{ transform: translateY(-6px); box-shadow: var(--shadow-hover); border-color: rgba(30,144,255,0.3); }}
        .news-card:hover .card-image img {{ transform: scale(1.05); }}
        .card-image {{ position: relative; height: 200px; overflow: hidden; }}
        .card-image img {{ width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s ease; }}
        .card-category {{ position: absolute; top: 12px; left: 12px; padding: 4px 12px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: #fff; }}
        .cat-politics {{ background: var(--cat-politics); }}
        .cat-tech {{ background: var(--cat-tech); color: #0b1020; }}
        .cat-economy {{ background: var(--cat-economy); color: #0b1020; }}
        .cat-sports {{ background: var(--cat-sports); color: #0b1020; }}
        .cat-world {{ background: var(--cat-world); }}
        .cat-entertainment {{ background: var(--cat-entertainment); }}
        .card-body {{ padding: 20px; }}
        .card-title {{ font-family: 'Montserrat', sans-serif; font-size: 1rem; font-weight: 700; color: var(--white); line-height: 1.4; margin-bottom: 10px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
        .card-summary {{ font-size: 0.85rem; color: var(--gray-mid); margin-bottom: 16px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
        .card-meta {{ display: flex; align-items: center; justify-content: space-between; padding-top: 12px; border-top: 1px solid var(--glass-border); }}
        .card-author {{ display: flex; align-items: center; gap: 8px; }}
        .avatar {{ width: 28px; height: 28px; border-radius: 50%; background: var(--blue-light); display: flex; align-items: center; justify-content: center; font-size: 0.7rem; color: var(--blue-neon); font-weight: 700; }}
        .card-author span {{ font-size: 0.8rem; color: var(--gray-mid); }}
        .card-date {{ font-size: 0.75rem; color: var(--gray-mid); display: flex; align-items: center; gap: 4px; }}
        .card-read-more {{ display: inline-flex; align-items: center; gap: 6px; color: var(--blue-neon); font-size: 0.82rem; font-weight: 600; margin-top: 12px; }}

        /* MAIN LAYOUT */
        .main-layout {{ display: grid; grid-template-columns: 1fr 340px; gap: 30px; padding: 40px 0; }}

        /* SIDEBAR */
        .sidebar {{ display: flex; flex-direction: column; gap: 24px; }}
        .sidebar-widget {{ background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 14px; padding: 24px; }}
        .sidebar-widget h3 {{ font-family: 'Montserrat', sans-serif; font-size: 1rem; font-weight: 700; color: var(--white); margin-bottom: 16px; display: flex; align-items: center; gap: 8px; padding-bottom: 12px; border-bottom: 1px solid var(--glass-border); }}
        .sidebar-widget h3 i {{ color: var(--blue-neon); }}
        .most-read-item {{ display: flex; gap: 12px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); transition: all var(--transition-fast); }}
        .most-read-item:last-child {{ border-bottom: none; }}
        .most-read-item:hover {{ padding-left: 6px; }}
        .mr-number {{ width: 28px; height: 28px; border-radius: 6px; background: var(--blue-light); color: var(--blue-neon); display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.8rem; flex-shrink: 0; }}
        .mr-number.top-1 {{ background: linear-gradient(135deg,#ffd700,#ff8c00); color: #0b1020; }}
        .mr-number.top-2 {{ background: linear-gradient(135deg,#c0c0c0,#a0a0a0); color: #0b1020; }}
        .mr-number.top-3 {{ background: linear-gradient(135deg,#cd7f32,#a0522d); color: #fff; }}
        .mr-content h4 {{ font-size: 0.82rem; color: var(--white); font-weight: 500; line-height: 1.4; margin-bottom: 4px; }}
        .mr-content span {{ font-size: 0.72rem; color: var(--gray-mid); }}
        .trending-tags {{ display: flex; flex-wrap: wrap; gap: 8px; }}
        .trending-tag {{ background: var(--glass-bg); border: 1px solid var(--glass-border); padding: 6px 14px; border-radius: 20px; font-size: 0.78rem; color: var(--gray-light); cursor: pointer; transition: all var(--transition-fast); text-decoration: none; }}
        .trending-tag:hover {{ background: var(--blue-light); color: var(--blue-neon); border-color: var(--blue-neon); }}
        .newsletter-sidebar {{ background: linear-gradient(135deg,rgba(30,144,255,0.1),rgba(10,111,212,0.1)); border: 1px solid rgba(30,144,255,0.2) !important; }}
        .newsletter-sidebar p {{ font-size: 0.85rem; color: var(--gray-light); margin-bottom: 14px; }}
        .email-input {{ width: 100%; padding: 10px 14px; background: rgba(255,255,255,0.05); border: 1px solid var(--glass-border); border-radius: 8px; color: var(--white); font-size: 0.85rem; margin-bottom: 10px; outline: none; transition: border-color var(--transition-fast); }}
        .email-input:focus {{ border-color: var(--blue-neon); }}
        .email-input::placeholder {{ color: var(--gray-mid); }}
        .sidebar-submit {{ width: 100%; padding: 10px; background: var(--blue-neon); color: #fff; border: none; border-radius: 8px; font-weight: 600; font-size: 0.85rem; cursor: pointer; transition: all var(--transition-fast); font-family: 'Montserrat', sans-serif; }}
        .sidebar-submit:hover {{ background: #fff; color: var(--blue-neon); }}

        /* CATEGORY SECTION */
        .category-section {{ padding: 50px 0; }}

        /* NEWSLETTER SECTION */
        .newsletter-section {{ padding: 60px 0; background: linear-gradient(135deg,#0a1628,#111d35,#0a1628); }}
        .newsletter-inner {{ text-align: center; max-width: 600px; margin: 0 auto; }}
        .newsletter-inner h2 {{ font-family: 'Montserrat', sans-serif; font-size: 2rem; font-weight: 800; color: #fff; margin-bottom: 12px; }}
        .newsletter-inner h2 span {{ color: var(--blue-neon); }}
        .newsletter-inner p {{ color: var(--gray-mid); margin-bottom: 28px; }}
        .newsletter-form {{ display: flex; gap: 12px; max-width: 500px; margin: 0 auto; }}
        .newsletter-form input {{ flex: 1; padding: 14px 20px; border-radius: 10px; border: 1px solid var(--glass-border); background: rgba(255,255,255,0.05); color: #fff; font-size: 0.9rem; outline: none; }}
        .newsletter-form input:focus {{ border-color: var(--blue-neon); }}
        .newsletter-form input::placeholder {{ color: var(--gray-mid); }}
        .newsletter-form button {{ padding: 14px 28px; background: var(--blue-neon); color: #fff; border: none; border-radius: 10px; font-weight: 700; cursor: pointer; transition: all var(--transition-normal); font-family: 'Montserrat', sans-serif; white-space: nowrap; }}
        .newsletter-form button:hover {{ background: #fff; color: var(--blue-neon); }}

        /* FOOTER */
        .footer {{ background: var(--bg-secondary); border-top: 1px solid var(--glass-border); padding: 50px 0 0; }}
        .footer-grid {{ display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 40px; padding-bottom: 40px; border-bottom: 1px solid var(--glass-border); }}
        .footer-about p {{ color: var(--gray-mid); font-size: 0.88rem; margin: 16px 0 20px; line-height: 1.7; }}
        .footer-social {{ display: flex; gap: 12px; }}
        .footer-social a {{ width: 40px; height: 40px; border-radius: 10px; background: var(--glass-bg); border: 1px solid var(--glass-border); display: flex; align-items: center; justify-content: center; color: var(--gray-light); text-decoration: none; transition: all var(--transition-fast); }}
        .footer-social a:hover {{ background: var(--blue-neon); color: #fff; border-color: var(--blue-neon); transform: translateY(-3px); }}
        .footer-col h4 {{ font-family: 'Montserrat', sans-serif; font-size: 0.9rem; font-weight: 700; color: var(--white); margin-bottom: 18px; position: relative; padding-bottom: 10px; }}
        .footer-col h4::after {{ content: ''; position: absolute; bottom: 0; left: 0; width: 30px; height: 2px; background: var(--blue-neon); border-radius: 2px; }}
        .footer-col ul {{ list-style: none; }}
        .footer-col ul li {{ margin-bottom: 10px; }}
        .footer-col ul li a {{ color: var(--gray-mid); text-decoration: none; font-size: 0.85rem; transition: all var(--transition-fast); }}
        .footer-col ul li a:hover {{ color: var(--blue-neon); padding-left: 6px; }}
        .footer-bottom {{ padding: 20px 0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }}
        .footer-bottom p {{ font-size: 0.82rem; color: var(--gray-mid); }}
        .footer-bottom a {{ color: var(--blue-neon); text-decoration: none; }}
        .footer-bottom-links {{ display: flex; gap: 20px; }}
        .footer-bottom-links a {{ font-size: 0.82rem; color: var(--gray-mid); text-decoration: none; transition: color var(--transition-fast); }}
        .footer-bottom-links a:hover {{ color: var(--blue-neon); }}

        /* BACK TO TOP */
        .back-to-top {{ position: fixed; bottom: 30px; right: 30px; width: 48px; height: 48px; background: var(--blue-neon); color: #fff; border: none; border-radius: 12px; font-size: 1.1rem; cursor: pointer; z-index: 900; opacity: 0; visibility: hidden; transform: translateY(20px); transition: all var(--transition-normal); box-shadow: var(--shadow-neon); display: flex; align-items: center; justify-content: center; }}
        .back-to-top.visible {{ opacity: 1; visibility: visible; transform: translateY(0); }}
        .back-to-top:hover {{ background: #fff; color: var(--blue-neon); transform: translateY(-3px); }}

        /* RESPONSIVE */
        @media (max-width: 1024px) {{
            .main-layout {{ grid-template-columns: 1fr; }}
            .news-grid-4 {{ grid-template-columns: repeat(2,1fr); }}
            .footer-grid {{ grid-template-columns: 1fr 1fr; }}
        }}
        @media (max-width: 768px) {{
            .hamburger {{ display: flex; }}
            .nav-desktop, .search-container {{ display: none; }}
            .hero-slider {{ height: 380px; }}
            .hero-title {{ font-size: 1.5rem; }}
            .news-grid-4, .news-grid-3 {{ grid-template-columns: 1fr; }}
            .footer-grid {{ grid-template-columns: 1fr; gap: 30px; }}
            .footer-bottom {{ flex-direction: column; text-align: center; }}
            .newsletter-form {{ flex-direction: column; }}
            .top-bar {{ display: none; }}
        }}
    </style>
</head>
<body>

    <!-- TOP BAR -->
    <div class="top-bar">
        <div class="container">
            <div class="top-bar-left">
                <a href="#"><i class="fas fa-map-marker-alt"></i> Brasil</a>
                <span class="update-badge"><i class="fas fa-sync-alt"></i> Atualizado em {data_atualizacao}</span>
            </div>
            <div class="datetime-display">
                <i class="far fa-clock"></i>
                <span id="clock"></span>
            </div>
            <button class="dark-mode-toggle" id="darkModeToggle">
                <i class="fas fa-moon"></i>
                <span>Modo Claro</span>
            </button>
        </div>
    </div>

    <!-- BREAKING NEWS TICKER -->
    <div class="breaking-news-bar">
        <div class="container" style="display:flex;align-items:center;">
            <div class="breaking-label"><i class="fas fa-bell"></i> AO VIVO</div>
            <div class="ticker-track">{ticker_html}</div>
        </div>
    </div>

    <!-- HEADER -->
    <header class="header" id="header">
        <div class="container">
            <a href="#" class="logo">
                <div class="logo-icon"><i class="fas fa-newspaper"></i></div>
                <div>
                    <div class="logo-text">Voz <span>Brasil</span></div>
                    <div class="logo-subtitle">Portal de Notícias</div>
                </div>
            </a>
            <nav class="nav-desktop">
                <a href="#" class="active">Home</a>
                <a href="#breaking">Última Hora</a>
                <a href="#politics">Política</a>
                <a href="#technology">Tecnologia</a>
                <a href="#economy">Economia</a>
                <a href="#sports">Esportes</a>
            </nav>
            <div class="search-container">
                <i class="fas fa-search search-icon"></i>
                <input type="text" class="search-input" placeholder="Buscar notícias...">
            </div>
            <div class="hamburger" id="hamburger">
                <span></span><span></span><span></span>
            </div>
        </div>
    </header>

    <!-- MOBILE NAV -->
    <div class="mobile-nav-overlay" id="mobileOverlay"></div>
    <nav class="mobile-nav" id="mobileNav">
        <a href="#" class="active">Home</a>
        <a href="#breaking">Última Hora</a>
        <a href="#politics">Política</a>
        <a href="#technology">Tecnologia</a>
        <a href="#economy">Economia</a>
        <a href="#sports">Esportes</a>
    </nav>

    <!-- HERO SLIDER -->
    <section class="hero" id="hero">
        <div class="hero-slider" id="heroSlider">
            {hero_slides}
            <div class="hero-nav" id="heroNav">{hero_dots}</div>
        </div>
        <div class="hero-slide-counter">
            <span id="currentSlide">1</span> / <span>{min(len(destaques), 4)}</span>
        </div>
    </section>

    <!-- MAIN CONTENT -->
    <main>
        <div class="container">
            <div class="main-layout">
                <div class="main-content">

                    <!-- ÚLTIMAS NOTÍCIAS -->
                    <section id="breaking">
                        <div class="section-header">
                            <h2 class="section-title"><i class="fas fa-bolt"></i> Últimas Notícias</h2>
                        </div>
                        <div class="news-grid news-grid-4">
                            {top_news_html}
                        </div>
                    </section>

                    <div class="divider"></div>

                    <!-- MAIS NOTÍCIAS -->
                    <section>
                        <div class="section-header">
                            <h2 class="section-title"><i class="fas fa-newspaper"></i> Mais Notícias</h2>
                        </div>
                        <div class="news-grid news-grid-3">
                            {more_news_html}
                        </div>
                    </section>
                </div>

                <!-- SIDEBAR -->
                <aside class="sidebar">
                    <div class="sidebar-widget">
                        <h3><i class="fas fa-fire"></i> Mais Lidas</h3>
                        {mais_lidas}
                    </div>
                    <div class="sidebar-widget">
                        <h3><i class="fas fa-chart-line"></i> Assuntos em Alta</h3>
                        <div class="trending-tags">
                            <a href="#" class="trending-tag">#Política</a>
                            <a href="#" class="trending-tag">#Economia</a>
                            <a href="#" class="trending-tag">#Tecnologia</a>
                            <a href="#" class="trending-tag">#Esportes</a>
                            <a href="#" class="trending-tag">#Brasil</a>
                            <a href="#" class="trending-tag">#Mundo</a>
                        </div>
                    </div>
                    <div class="sidebar-widget newsletter-sidebar">
                        <h3 style="border:none;padding-bottom:0;"><i class="fas fa-envelope-open-text"></i> Newsletter</h3>
                        <p>Receba as principais notícias no seu e-mail.</p>
                        <input type="email" class="email-input" placeholder="Seu melhor e-mail...">
                        <button class="sidebar-submit"><i class="fas fa-paper-plane"></i> Inscrever-se</button>
                    </div>
                </aside>
            </div>
        </div>

        <!-- POLÍTICA -->
        <section id="politics" class="category-section">
            <div class="container">
                <div class="section-header">
                    <h2 class="section-title"><i class="fas fa-landmark"></i> Política</h2>
                    <span style="font-size:0.78rem;color:var(--gray-mid);">Fonte: Revista Oeste</span>
                </div>
                <div class="news-grid news-grid-4">{politics_html}</div>
            </div>
        </section>

        <!-- TECNOLOGIA -->
        <section id="technology" class="category-section">
            <div class="container">
                <div class="section-header">
                    <h2 class="section-title"><i class="fas fa-microchip"></i> Tecnologia</h2>
                    <span style="font-size:0.78rem;color:var(--gray-mid);">Fonte: Adrenaline</span>
                </div>
                <div class="news-grid news-grid-4">{tech_html}</div>
            </div>
        </section>

        <!-- ECONOMIA -->
        <section id="economy" class="category-section">
            <div class="container">
                <div class="section-header">
                    <h2 class="section-title"><i class="fas fa-chart-bar"></i> Economia</h2>
                    <span style="font-size:0.78rem;color:var(--gray-mid);">Fonte: Exame</span>
                </div>
                <div class="news-grid news-grid-4">{economy_html}</div>
            </div>
        </section>

        <!-- ESPORTES -->
        <section id="sports" class="category-section">
            <div class="container">
                <div class="section-header">
                    <h2 class="section-title"><i class="fas fa-trophy"></i> Esportes</h2>
                    <span style="font-size:0.78rem;color:var(--gray-mid);">Fonte: Lance</span>
                </div>
                <div class="news-grid news-grid-4">{sports_html}</div>
            </div>
        </section>

        <!-- NEWSLETTER -->
        <section class="newsletter-section">
            <div class="container">
                <div class="newsletter-inner">
                    <h2>Fique por dentro de tudo com a <span>Voz Brasil</span></h2>
                    <p>Receba diariamente as principais notícias do Brasil e do mundo. 100% gratuito.</p>
                    <div class="newsletter-form">
                        <input type="email" placeholder="Digite seu melhor e-mail...">
                        <button><i class="fas fa-paper-plane"></i> Receber Notícias</button>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <!-- FOOTER -->
    <footer class="footer">
        <div class="container">
            <div class="footer-grid">
                <div class="footer-about">
                    <a href="#" class="logo">
                        <div class="logo-icon"><i class="fas fa-newspaper"></i></div>
                        <div>
                            <div class="logo-text">Voz <span>Brasil</span></div>
                            <div class="logo-subtitle">Portal de Notícias</div>
                        </div>
                    </a>
                    <p>O Voz Brasil traz informações precisas e cobertura completa dos acontecimentos nacionais e internacionais.</p>
                    <div class="footer-social">
                        <a href="https://facebook.com" target="_blank"><i class="fab fa-facebook-f"></i></a>
                        <a href="https://x.com" target="_blank"><i class="fab fa-x-twitter"></i></a>
                        <a href="https://instagram.com" target="_blank"><i class="fab fa-instagram"></i></a>
                        <a href="https://youtube.com" target="_blank"><i class="fab fa-youtube"></i></a>
                    </div>
                </div>
                <div class="footer-col">
                    <h4>Navegação</h4>
                    <ul>
                        <li><a href="#">Home</a></li>
                        <li><a href="#breaking">Última Hora</a></li>
                        <li><a href="#politics">Política</a></li>
                        <li><a href="#technology">Tecnologia</a></li>
                        <li><a href="#economy">Economia</a></li>
                        <li><a href="#sports">Esportes</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h4>Fontes</h4>
                    <ul>
                        <li><a href="https://www.cnnbrasil.com.br" target="_blank">CNN Brasil</a></li>
                        <li><a href="https://exame.com" target="_blank">Exame</a></li>
                        <li><a href="https://www.lance.com.br" target="_blank">Lance</a></li>
                        <li><a href="https://adrenaline.com" target="_blank">Adrenaline</a></li>
                        <li><a href="https://revistaoeste.com" target="_blank">Revista Oeste</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h4>Legal</h4>
                    <ul>
                        <li><a href="#">Política de Privacidade</a></li>
                        <li><a href="#">Termos de Uso</a></li>
                        <li><a href="#">Anuncie</a></li>
                        <li><a href="#">Contato</a></li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; {agora.year} <a href="#">Voz Brasil</a>. Notícias agregadas de fontes públicas.</p>
                <div class="footer-bottom-links">
                    <a href="#">Privacidade</a>
                    <a href="#">Termos</a>
                </div>
            </div>
        </div>
    </footer>

    <button class="back-to-top" id="backToTop"><i class="fas fa-chevron-up"></i></button>

    <script>
        // RELÓGIO
        function updateClock() {{
            const now = new Date();
            document.getElementById('clock').textContent = now.toLocaleDateString('pt-BR', {{weekday:'short',year:'numeric',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}});
        }}
        setInterval(updateClock, 1000); updateClock();

        // DARK MODE
        const toggle = document.getElementById('darkModeToggle');
        toggle.addEventListener('click', () => {{
            document.body.classList.toggle('light-mode');
            const icon = toggle.querySelector('i'), text = toggle.querySelector('span');
            if (document.body.classList.contains('light-mode')) {{ icon.className='fas fa-sun'; text.textContent='Modo Escuro'; localStorage.setItem('vb-theme','light'); }}
            else {{ icon.className='fas fa-moon'; text.textContent='Modo Claro'; localStorage.setItem('vb-theme','dark'); }}
        }});
        if (localStorage.getItem('vb-theme')==='light') {{ document.body.classList.add('light-mode'); toggle.querySelector('i').className='fas fa-sun'; toggle.querySelector('span').textContent='Modo Escuro'; }}

        // HEADER SCROLL
        const header = document.getElementById('header');
        let lastScroll = 0;
        window.addEventListener('scroll', () => {{
            const s = window.pageYOffset;
            header.style.transform = (s > lastScroll && s > 100) ? 'translateY(-100%)' : 'translateY(0)';
            lastScroll = s;
            document.getElementById('backToTop').classList.toggle('visible', s > 400);
        }}, {{passive:true}});
        document.getElementById('backToTop').addEventListener('click', () => window.scrollTo({{top:0,behavior:'smooth'}}));

        // MOBILE NAV
        const hamburger = document.getElementById('hamburger'), mobileNav = document.getElementById('mobileNav'), overlay = document.getElementById('mobileOverlay');
        hamburger.addEventListener('click', () => {{ hamburger.classList.toggle('active'); mobileNav.classList.toggle('active'); overlay.classList.toggle('active'); }});
        overlay.addEventListener('click', () => {{ hamburger.classList.remove('active'); mobileNav.classList.remove('active'); overlay.classList.remove('active'); }});

        // HERO SLIDER
        let currentSlide = 0;
        const totalSlides = document.querySelectorAll('.hero-slide').length;
        function showSlide(index) {{
            document.querySelectorAll('.hero-slide').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.hero-dot').forEach(d => d.classList.remove('active'));
            if (document.querySelectorAll('.hero-slide')[index]) {{
                document.querySelectorAll('.hero-slide')[index].classList.add('active');
                document.querySelectorAll('.hero-dot')[index].classList.add('active');
                document.getElementById('currentSlide').textContent = index + 1;
                currentSlide = index;
            }}
        }}
        document.querySelectorAll('.hero-dot').forEach(dot => {{
            dot.addEventListener('click', () => {{ showSlide(parseInt(dot.getAttribute('data-slide'))); resetSlider(); }});
        }});
        let sliderInterval = setInterval(() => showSlide((currentSlide + 1) % totalSlides), 6000);
        function resetSlider() {{ clearInterval(sliderInterval); sliderInterval = setInterval(() => showSlide((currentSlide + 1) % totalSlides), 6000); }}

        // PARALLAX HERO
        window.addEventListener('scroll', () => {{
            const hero = document.querySelector('.hero-slider');
            if (hero && window.pageYOffset < hero.offsetHeight) hero.style.transform = `translateY(${{window.pageYOffset * 0.3}}px)`;
        }}, {{passive:true}});

        // FADE IN CARDS
        const obs = new IntersectionObserver(entries => entries.forEach(e => {{ if (e.isIntersecting) {{ e.target.style.opacity='1'; e.target.style.transform='translateY(0)'; obs.unobserve(e.target); }} }}), {{threshold:0.1}});
        document.querySelectorAll('.news-card').forEach((card, i) => {{
            card.style.opacity='0'; card.style.transform='translateY(30px)';
            card.style.transition=`opacity 0.5s ease ${{(i%4)*0.1}}s, transform 0.5s ease ${{(i%4)*0.1}}s`;
            obs.observe(card);
        }});
    </script>
</body>
</html>"""

# ============================================================
# MAIN
# ============================================================
def main():
    print("\n========================================")
    print("  VOZ BRASIL - Atualização de Notícias  ")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("========================================\n")

    todas_noticias = {}
    for chave, config in RSS_SOURCES.items():
        noticias = buscar_noticias(chave, config, limite=6)
        todas_noticias[chave] = noticias

    total = sum(len(v) for v in todas_noticias.values())
    print(f"\n✓ Total: {total} notícias coletadas\n")

    print("Gerando index.html...")
    html_content = gerar_html(todas_noticias)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✓ index.html gerado com sucesso! ({len(html_content):,} caracteres)")
    print("\n========================================\n")

if __name__ == "__main__":
    main()
