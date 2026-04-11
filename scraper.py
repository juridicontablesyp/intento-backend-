"""
scraper.py - Scraping LEGAL de múltiples fuentes públicas argentinas
Fuentes: Reddit API + Foros + TodoExpertos + Nitter (Twitter público)
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
import random
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

DELAY_MIN = 1.5
DELAY_MAX = 3.5

KEYWORDS = {
    "contador": [
        "necesito contador", "busco contador", "problema monotributo",
        "ayuda AFIP", "multa AFIP", "carta AFIP", "me llegó AFIP",
        "no entiendo monotributo", "cómo facturo", "inscribirme AFIP",
        "cambio categoría monotributo", "deuda AFIP", "necesito contadora",
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

SUBREDDITS = ["argentina", "DerechoArg", "trabajo_ar", "buenosaires", "merval"]

async def scrape_reddit(keywords: list, client: httpx.AsyncClient) -> list:
    resultados = []
    for kw in keywords[:4]:
        for sub in SUBREDDITS[:3]:
            try:
                await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
                url = f"https://www.reddit.com/r/{sub}/search.json?q={kw}&sort=new&limit=10&restrict_sr=1"
                resp = await client.get(url, headers={**HEADERS, "User-Agent": "IntentoBot:1.0"})
                if resp.status_code != 200:
                    continue
                posts = resp.json().get("data", {}).get("children", [])
                for post in posts:
                    p = post.get("data", {})
                    titulo = p.get("title", "")
                    cuerpo = p.get("selftext", "")[:400]
                    texto = f"{titulo}. {cuerpo}".strip(". ")
                    if len(texto) < 15:
                        continue
                    resultados.append({
                        "texto": texto,
                        "link": f"https://reddit.com{p.get('permalink', '')}",
                        "fuente": f"Reddit/r/{sub}",
                        "autor": p.get("author", ""),
                        "fecha_original": datetime.fromtimestamp(p.get("created_utc", 0)).isoformat() if p.get("created_utc") else "",
                    })
            except Exception as e:
                print(f"[Reddit] Error {kw}/{sub}: {e}")
    return resultados

NITTER_INSTANCES = ["https://nitter.net", "https://nitter.privacydev.net"]

async def scrape_twitter_publico(keywords: list, client: httpx.AsyncClient) -> list:
    resultados = []
    for kw in keywords[:3]:
        for instance in NITTER_INSTANCES[:1]:
            try:
                await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
                url = f"{instance}/search?q={kw.replace(' ', '+')}&f=tweets"
                resp = await client.get(url, headers=HEADERS, timeout=10.0)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                tweets = soup.select(".tweet-content")[:10]
                usernames = soup.select(".username")
                for i, tweet in enumerate(tweets):
                    texto = tweet.get_text(strip=True)
                    if len(texto) < 20:
                        continue
                    username = usernames[i].get_text(strip=True) if i < len(usernames) else ""
                    link = f"https://twitter.com/{username.strip('@')}" if username else instance
                    resultados.append({
                        "texto": texto,
                        "link": link,
                        "fuente": "Twitter/X",
                        "autor": username,
                        "fecha_original": "",
                    })
            except Exception as e:
                print(f"[Twitter] Error: {e}")
    return resultados

async def scrape_forocontable(client: httpx.AsyncClient) -> list:
    resultados = []
    try:
        await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
        resp = await client.get("https://www.forocontable.com.ar/viewforum.php?f=2", headers=HEADERS, timeout=10.0)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        for topic in soup.select(".topictitle")[:15]:
            titulo = topic.get_text(strip=True)
            href = topic.get("href", "")
            kws = ["necesito", "ayuda", "problema", "consulta", "urgente", "afip", "monotributo", "busco"]
            if any(k in titulo.lower() for k in kws):
                resultados.append({
                    "texto": titulo,
                    "link": f"https://www.forocontable.com.ar/{href}",
                    "fuente": "ForoContable",
                    "autor": "",
                    "fecha_original": "",
                })
    except Exception as e:
        print(f"[ForoContable] Error: {e}")
    return resultados

async def scrape_todoexpertos(keywords: list, client: httpx.AsyncClient) -> list:
    resultados = []
    for kw in keywords[:2]:
        try:
            await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            url = f"https://www.todoexpertos.com/buscar?q={kw.replace(' ', '+')}"
            resp = await client.get(url, headers=HEADERS, timeout=10.0)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select(".question-title, h2 a, .title a")[:8]:
                texto = item.get_text(strip=True)
                href = item.get("href", "")
                if len(texto) > 20:
                    resultados.append({
                        "texto": texto,
                        "link": href if href.startswith("http") else f"https://www.todoexpertos.com{href}",
                        "fuente": "TodoExpertos",
                        "autor": "",
                        "fecha_original": "",
                    })
        except Exception as e:
            print(f"[TodoExpertos] Error: {e}")
    return resultados

def calcular_score(texto: str) -> int:
    texto_lower = texto.lower()
    score = 0
    alta = ["urgente", "ya mismo", "hoy", "lo antes posible", "necesito ya",
            "cuanto antes", "para mañana", "me llegó carta", "me intimaron",
            "embargo", "multa", "ejecución"]
    score += min(sum(15 for k in alta if k in texto_lower), 60)
    media = ["necesito", "busco", "me recomiendan", "cuánto cobra", "precio",
             "honorarios", "contratar", "alguien que"]
    score += min(sum(10 for k in media if k in texto_lower), 45)
    problema = ["problema", "error", "no entiendo", "no sé", "ayuda",
                "afip", "monotributo", "factura", "deuda"]
    score += min(sum(5 for k in problema if k in texto_lower), 30)
    return min(score, 100)

def enrich_contact(resultado: dict) -> dict:
    link = resultado.get("link", "")
    autor = resultado.get("autor", "")
    contacto = {}
    if "reddit.com" in link and autor:
        contacto["reddit_user"] = autor
        contacto["reddit_perfil"] = f"https://reddit.com/u/{autor}"
        contacto["como_contactar"] = f"https://reddit.com/message/compose/?to={autor}"
    elif "twitter.com" in link and autor:
        contacto["twitter_user"] = autor
        contacto["como_contactar"] = link
    elif link:
        contacto["como_contactar"] = link
    return {**resultado, "contacto": contacto}

async def scrape_todas_fuentes(keywords_texto: str, servicio: str = "contador", max_results: int = 40) -> list:
    kws_servicio = KEYWORDS.get(servicio, KEYWORDS["contador"])
    kws_custom = [keywords_texto] if keywords_texto else []
    todas_kws = list(set(kws_custom + kws_servicio[:5]))

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        tareas = await asyncio.gather(
            scrape_reddit(todas_kws, client),
            scrape_twitter_publico(todas_kws, client),
            scrape_forocontable(client),
            scrape_todoexpertos(todas_kws, client),
            return_exceptions=True
        )

    resultados = []
    for t in tareas:
        if isinstance(t, list):
            resultados.extend(t)

    for r in resultados:
        r["score"] = calcular_score(r.get("texto", ""))
        r = enrich_contact(r)

    seen = set()
    unique = []
    for r in resultados:
        key = r["texto"][:60].lower()
        if key not in seen:
            seen.add(key)
            unique.append(r)

    unique.sort(key=lambda x: x.get("score", 0), reverse=True)
    print(f"[SCRAPER] {len(unique)} resultados únicos")
    return unique[:max_results]
