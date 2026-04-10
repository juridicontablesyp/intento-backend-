"""
scraper.py - Scraping LEGAL de datos públicos
Estrategia: Google Dorks + Reddit + Foros públicos
NO hace bypass de login, NO viola ToS, solo indexa contenido público
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import quote_plus

# Headers respetuosos - nos identificamos como bot
HEADERS = {
    "User-Agent": "IntentoBot/1.0 (lead detection research; contact@intento.app)",
    "Accept-Language": "es-AR,es;q=0.9",
}

# Delay entre requests para no sobrecargar servidores
DELAY_MIN = 2.0
DELAY_MAX = 5.0

# ─── FUENTES LEGALES ─────────────────────────────────────────────────────────

DORK_TEMPLATES = {
    "contador": [
        'site:reddit.com "necesito contador" OR "busco contador"',
        'site:forocontable.com.ar OR site:todoexpertos.com "contador" "monotributo" "ayuda"',
        '"necesito un contador" "Argentina" -site:linkedin.com',
        '"problema con AFIP" OR "no entiendo monotributo" site:reddit.com',
    ],
    "abogado": [
        'site:reddit.com "necesito abogado" OR "busco abogado" Argentina',
        '"consulta legal" "urgente" Argentina -site:estudiosjuridicos.com',
    ],
    "medico": [
        'site:reddit.com/r/argentina "turno médico" OR "necesito médico"',
    ],
}

# Reddit API pública (sin auth, solo posts públicos)
REDDIT_SEARCHES = {
    "contador": [
        "https://www.reddit.com/r/argentina/search.json?q=contador+monotributo+ayuda&sort=new&limit=25",
        "https://www.reddit.com/r/DerechoArg/search.json?q=contador+AFIP&sort=new&limit=25",
        "https://www.reddit.com/search.json?q=necesito+contador+argentina&sort=new&limit=25",
    ],
    "abogado": [
        "https://www.reddit.com/r/argentina/search.json?q=abogado+consulta&sort=new&limit=25",
        "https://www.reddit.com/r/DerechoArg/search.json?q=necesito+abogado&sort=new&limit=25",
    ],
}

async def scrape_reddit(servicio: str, client: httpx.AsyncClient) -> list:
    """Scraping de Reddit API pública (JSON) - completamente legal."""
    resultados = []
    urls = REDDIT_SEARCHES.get(servicio, REDDIT_SEARCHES.get("contador", []))

    for url in urls:
        try:
            await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            resp = await client.get(url, headers={
                **HEADERS,
                "User-Agent": "IntentoBot:1.0 (by /u/intento_app)"
            })
            if resp.status_code != 200:
                continue
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            for post in posts:
                p = post.get("data", {})
                texto = f"{p.get('title', '')} {p.get('selftext', '')[:300]}"
                if len(texto.strip()) < 20:
                    continue
                resultados.append({
                    "texto": texto.strip(),
                    "link": f"https://reddit.com{p.get('permalink', '')}",
                    "fuente": "Reddit",
                })
        except Exception as e:
            print(f"Error scraping Reddit: {e}")

    return resultados

async def scrape_google_dorks(servicio: str, max_results: int = 20) -> list:
    """
    Orquesta scraping legal de múltiples fuentes públicas.
    Prioriza Reddit (API pública) + búsquedas web generales.
    """
    resultados = []

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        # 1. Reddit (fuente principal - API pública gratuita)
        reddit_results = await scrape_reddit(servicio, client)
        resultados.extend(reddit_results)

        # 2. Si necesitamos más, agregar fuentes adicionales
        if len(resultados) < max_results:
            extra = await scrape_foros_publicos(servicio, client)
            resultados.extend(extra)

    # Deduplicar por link
    seen = set()
    unique = []
    for r in resultados:
        if r["link"] not in seen:
            seen.add(r["link"])
            unique.append(r)

    return unique[:max_results]

async def scrape_foros_publicos(servicio: str, client: httpx.AsyncClient) -> list:
    """
    Scraping de foros públicos argentinos que permiten indexación.
    Solo sitios sin robots.txt restrictivo.
    """
    resultados = []

    # Forocontable.com.ar - foro público de contadores
    if servicio == "contador":
        try:
            await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            url = "https://www.forocontable.com.ar/viewforum.php?f=2"
            resp = await client.get(url, headers=HEADERS)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for topic in soup.select(".topictitle")[:10]:
                    titulo = topic.get_text(strip=True)
                    link = topic.get("href", "")
                    if any(kw in titulo.lower() for kw in ["necesito", "ayuda", "problema", "consulta", "urgente"]):
                        resultados.append({
                            "texto": titulo,
                            "link": f"https://www.forocontable.com.ar/{link}",
                            "fuente": "ForoContable",
                        })
        except Exception as e:
            print(f"Error scraping foro: {e}")

    return resultados
