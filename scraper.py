"""
scraper.py - Scraping LEGAL de múltiples fuentes públicas argentinas
Fuentes: Reddit API + Foros + Grupos públicos + Búsquedas web
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
import random
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "es-AR,es;q=0.9",
}

DELAY_MIN = 1.5
DELAY_MAX = 3.5

# ─── KEYWORDS POR SERVICIO ────────────────────────────────────────────────────

KEYWORDS = {
    "contador": [
        "necesito contador", "busco contador", "problema monotributo",
        "ayuda AFIP", "multa AFIP", "carta AFIP", "me llegó AFIP",
        "no entiendo monotributo", "cómo facturo", "inscribirme AFIP",
        "cambio categoría monotributo", "deuda AFIP",
    ],
    "abogado": [
        "necesito abogado", "busco abogado", "consulta legal",
        "carta documento", "me demandan", "juicio laboral",
        "despido injustificado", "problema con mi empleador",
    ],
    "medico": [
        "necesito turno médico", "busco médico", "sin obra social",
        "dónde atenderse", "médico particular",
    ],
}

# ─── REDDIT API PÚBLICA ───────────────────────────────────────────────────────

REDDIT_SUBREDDITS = [
    "argentina", "DerechoArg", "ContadoresArg",
    "trabajo_ar", "merval", "buenosaires"
]

async def scrape_reddit(keywords: list, client: httpx.AsyncClient) -> list:
    resultados = []
    for kw in keywords[:3]:  # máximo 3 keywords para no sobrecargar
        for sub in REDDIT_SUBREDDITS[:3]:
            try:
                await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
                url = f"https://www.reddit.com/r/{sub}/search.json?q={kw}&sort=new&limit=10&restrict_sr=1"
                resp = await client.get(url, headers={
                    **HEADERS,
                    "User-Agent": "IntentoBot:1.0 (lead detection)"
                })
                if resp.status_code != 200:
                    continue
                data = resp.json()
                posts = data.get("data", {}).get("children", [])
                for post in posts:
                    p = post.get("data", {})
                    titulo = p.get("title", "")
                    cuerpo = p.get("selftext", "")[:300]
                    texto = f"{titulo} {cuerpo}".strip()
                    if len(texto) < 15:
                        continue
                    resultados.append({
                        "texto": texto,
                        "link": f"https://reddit.com{p.get('permalink', '')}",
                        "fuente": f"Reddit/r/{sub}",
                    })
            except Exception as e:
                print(f"[Reddit] Error: {e}")
    return resultados

# ─── FOROCONTABLE ─────────────────────────────────────────────────────────────

async def scrape_forocontable(client: httpx.AsyncClient) -> list:
    resultados = []
    try:
        await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
        url = "https://www.forocontable.com.ar/viewforum.php?f=2"
        resp = await client.get(url, headers=HEADERS, timeout=10.0)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        for topic in soup.select(".topictitle")[:15]:
            titulo = topic.get_text(strip=True)
            link = topic.get("href", "")
            if any(kw in titulo.lower() for kw in ["necesito", "ayuda", "problema", "consulta", "urgente", "afip", "monotributo"]):
                resultados.append({
                    "texto": titulo,
                    "link": f"https://www.forocontable.com.ar/{link}",
                    "fuente": "ForoContable",
                })
    except Exception as e:
        print(f"[ForoContable] Error: {e}")
    return resultados

# ─── MERCADOLIBRE FOROS (PÚBLICO) ─────────────────────────────────────────────

async def scrape_ml_foros(keywords: list, client: httpx.AsyncClient) -> list:
    """MercadoLibre tiene foros públicos con preguntas de usuarios."""
    resultados = []
    for kw in keywords[:2]:
        try:
            await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            url = f"https://vendedores.mercadolibre.com.ar/nota/buscar?q={kw.replace(' ', '+')}"
            resp = await client.get(url, headers=HEADERS, timeout=10.0)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select("h2, h3, .post-title")[:10]:
                texto = item.get_text(strip=True)
                if len(texto) > 20:
                    resultados.append({
                        "texto": texto,
                        "link": url,
                        "fuente": "MercadoLibre Foros",
                    })
        except Exception as e:
            print(f"[ML Foros] Error: {e}")
    return resultados

# ─── YAHOO RESPUESTAS ALTERNATIVAS / PREGUNTAS PÚBLICAS ──────────────────────

async def scrape_quora_publico(keywords: list, client: httpx.AsyncClient) -> list:
    """Busca en sitios de preguntas y respuestas públicos."""
    resultados = []
    for kw in keywords[:2]:
        try:
            await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            # Todoexpertos.com - foro público en español
            url = f"https://www.todoexpertos.com/buscar?q={kw.replace(' ', '+')}"
            resp = await client.get(url, headers=HEADERS, timeout=10.0)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select(".question-title, .title, h2 a")[:8]:
                texto = item.get_text(strip=True)
                link = item.get("href", url)
                if len(texto) > 20:
                    resultados.append({
                        "texto": texto,
                        "link": link if link.startswith("http") else f"https://www.todoexpertos.com{link}",
                        "fuente": "TodoExpertos",
                    })
        except Exception as e:
            print(f"[TodoExpertos] Error: {e}")
    return resultados

# ─── ORQUESTADOR PRINCIPAL ────────────────────────────────────────────────────

async def scrape_todas_fuentes(keywords_texto: str, servicio: str = "contador", max_results: int = 30) -> list:
    """
    Busca en todas las fuentes públicas disponibles.
    keywords_texto: texto libre como "necesito contador urgente"
    """
    # Combinar keywords del servicio con el texto ingresado
    kws_servicio = KEYWORDS.get(servicio, KEYWORDS["contador"])
    kws_custom = [keywords_texto] if keywords_texto else []
    todas_kws = list(set(kws_custom + kws_servicio[:5]))

    resultados = []

    async with httpx.AsyncClient(
        timeout=15.0,
        follow_redirects=True,
        headers=HEADERS
    ) as client:
        # Ejecutar todas las fuentes en paralelo
        tareas = await asyncio.gather(
            scrape_reddit(todas_kws, client),
            scrape_forocontable(client),
            scrape_ml_foros(todas_kws, client),
            scrape_quora_publico(todas_kws, client),
            return_exceptions=True
        )

        for resultado in tareas:
            if isinstance(resultado, list):
                resultados.extend(resultado)

    # Deduplicar por texto similar
    seen_texts = set()
    unique = []
    for r in resultados:
        key = r["texto"][:50].lower()
        if key not in seen_texts:
            seen_texts.add(key)
            unique.append(r)

    print(f"[SCRAPER] {len(unique)} resultados únicos de {len(resultados)} totales")
    return unique[:max_results]
