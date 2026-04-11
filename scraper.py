"""
scraper.py - Scraping LEGAL de múltiples fuentes públicas argentinas
Ambientado para: Contadores + Abogados
Fuentes: Reddit + Twitter/X + ForoContable + TodoExpertos + 
         MercadoLibre + OLX + Quora + Foros jurídicos
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
DELAY_MAX = 3.0

KEYWORDS = {
    "contador": [
        "necesito contador", "busco contador", "problema monotributo",
        "ayuda AFIP", "multa AFIP", "carta AFIP", "me llegó AFIP",
        "no entiendo monotributo", "cómo facturo", "inscribirme AFIP",
        "cambio categoría monotributo", "deuda AFIP", "necesito contadora",
        "busco estudio contable", "necesito asesor impositivo",
        "problema con ganancias", "declaración jurada AFIP",
        "factura electrónica problema", "baja monotributo",
    ],
    "abogado": [
        "necesito abogado", "busco abogado", "consulta legal urgente",
        "carta documento", "me demandan", "juicio laboral",
        "despido injustificado", "problema con mi empleador",
        "necesito abogada", "busco estudio jurídico",
        "me llegó carta documento", "me iniciaron juicio",
        "demanda laboral", "accidente de trabajo abogado",
        "divorcio abogado", "custodia hijos abogado",
        "sucesión herencia abogado", "contrato alquiler problema",
        "desalojo inquilino", "deuda banco abogado",
        "me estafaron necesito abogado", "denuncia penal",
        "querella penal", "violencia familiar abogado",
        "accidente tránsito abogado", "mala praxis médica",
    ],
    "medico": [
        "necesito turno médico", "busco médico", "sin obra social",
        "dónde atenderse", "médico particular",
    ],
}

SUBREDDITS_CONTADOR = ["argentina", "DerechoArg", "trabajo_ar", "buenosaires", "merval"]
SUBREDDITS_ABOGADO  = ["argentina", "DerechoArg", "trabajo_ar", "buenosaires", "actualidad_arg"]

# ─── REDDIT ───────────────────────────────────────────────────────────────────

async def scrape_reddit(keywords: list, servicio: str, client: httpx.AsyncClient) -> list:
    resultados = []
    subs = SUBREDDITS_ABOGADO if servicio == "abogado" else SUBREDDITS_CONTADOR
    for kw in keywords[:4]:
        for sub in subs[:3]:
            try:
                await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
                url = f"https://www.reddit.com/r/{sub}/search.json?q={kw}&sort=new&limit=10&restrict_sr=1&t=week"
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
                    autor = p.get("author", "")
                    resultados.append({
                        "texto": texto,
                        "link": f"https://reddit.com{p.get('permalink', '')}",
                        "fuente": f"Reddit/r/{sub}",
                        "autor": autor,
                        "contacto": {
                            "como_contactar": f"https://reddit.com/message/compose/?to={autor}",
                            "perfil": f"https://reddit.com/u/{autor}",
                        },
                        "fecha_original": datetime.fromtimestamp(p.get("created_utc", 0)).isoformat() if p.get("created_utc") else "",
                    })
            except Exception as e:
                print(f"[Reddit] Error {kw}/{sub}: {e}")
    return resultados

# ─── TWITTER/X VÍA NITTER ────────────────────────────────────────────────────

NITTER_INSTANCES = ["https://nitter.net", "https://nitter.privacydev.net"]

async def scrape_twitter(keywords: list, client: httpx.AsyncClient) -> list:
    resultados = []
    for kw in keywords[:3]:
        for instance in NITTER_INSTANCES[:2]:
            try:
                await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
                url = f"{instance}/search?q={kw.replace(' ', '+')}&f=tweets"
                resp = await client.get(url, headers=HEADERS, timeout=10.0)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                tweets = soup.select(".tweet-content")[:8]
                usernames = soup.select(".username")
                for i, tweet in enumerate(tweets):
                    texto = tweet.get_text(strip=True)
                    if len(texto) < 20:
                        continue
                    username = usernames[i].get_text(strip=True) if i < len(usernames) else ""
                    clean_user = username.strip("@")
                    resultados.append({
                        "texto": texto,
                        "link": f"https://twitter.com/{clean_user}" if clean_user else instance,
                        "fuente": "Twitter/X",
                        "autor": username,
                        "contacto": {
                            "como_contactar": f"https://twitter.com/{clean_user}" if clean_user else "",
                            "perfil": f"https://twitter.com/{clean_user}" if clean_user else "",
                        },
                        "fecha_original": "",
                    })
                break
            except Exception as e:
                print(f"[Twitter] Error: {e}")
    return resultados

# ─── FOROCONTABLE ─────────────────────────────────────────────────────────────

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
                link = f"https://www.forocontable.com.ar/{href}"
                resultados.append({
                    "texto": titulo,
                    "link": link,
                    "fuente": "ForoContable",
                    "autor": "",
                    "contacto": {"como_contactar": link},
                    "fecha_original": "",
                })
    except Exception as e:
        print(f"[ForoContable] Error: {e}")
    return resultados

# ─── FORO JURÍDICO / DERECHO ──────────────────────────────────────────────────

async def scrape_foro_juridico(keywords: list, client: httpx.AsyncClient) -> list:
    """Foros públicos de consultas legales en español."""
    resultados = []
    fuentes = [
        ("https://www.abogados.com.ar/foros", "Abogados.com.ar"),
        ("https://www.derechoargentino.com.ar", "DerechoArgentino"),
    ]
    for base_url, nombre in fuentes:
        try:
            await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            resp = await client.get(base_url, headers=HEADERS, timeout=10.0)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select("h2 a, h3 a, .topic-title, .thread-title")[:10]:
                texto = item.get_text(strip=True)
                href = item.get("href", "")
                kws_legal = ["necesito", "ayuda", "problema", "consulta", "urgente",
                             "abogado", "demanda", "juicio", "carta documento", "despido"]
                if len(texto) > 20 and any(k in texto.lower() for k in kws_legal):
                    link = href if href.startswith("http") else f"{base_url}/{href}"
                    resultados.append({
                        "texto": texto,
                        "link": link,
                        "fuente": nombre,
                        "autor": "",
                        "contacto": {"como_contactar": link},
                        "fecha_original": "",
                    })
        except Exception as e:
            print(f"[{nombre}] Error: {e}")
    return resultados

# ─── TODOEXPERTOS ─────────────────────────────────────────────────────────────

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
                    link = href if href.startswith("http") else f"https://www.todoexpertos.com{href}"
                    resultados.append({
                        "texto": texto,
                        "link": link,
                        "fuente": "TodoExpertos",
                        "autor": "",
                        "contacto": {"como_contactar": link},
                        "fecha_original": "",
                    })
        except Exception as e:
            print(f"[TodoExpertos] Error: {e}")
    return resultados

# ─── MERCADOLIBRE SERVICIOS ───────────────────────────────────────────────────

async def scrape_mercadolibre(keywords: list, client: httpx.AsyncClient) -> list:
    resultados = []
    for kw in keywords[:2]:
        try:
            await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            url = f"https://listado.mercadolibre.com.ar/{kw.replace(' ', '-')}"
            resp = await client.get(url, headers=HEADERS, timeout=10.0)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select(".ui-search-item__title, .main-title")[:8]:
                texto = item.get_text(strip=True)
                parent = item.find_parent("a") or item.find_parent("li")
                link = parent.get("href", url) if parent else url
                if len(texto) > 15 and any(k in texto.lower() for k in ["busco", "necesito", "quiero", "solicito"]):
                    resultados.append({
                        "texto": texto,
                        "link": link if link.startswith("http") else url,
                        "fuente": "MercadoLibre",
                        "autor": "",
                        "contacto": {"como_contactar": link if link.startswith("http") else url},
                        "fecha_original": "",
                    })
        except Exception as e:
            print(f"[MercadoLibre] Error: {e}")
    return resultados

# ─── OLX ─────────────────────────────────────────────────────────────────────

async def scrape_olx(keywords: list, client: httpx.AsyncClient) -> list:
    resultados = []
    for kw in keywords[:2]:
        try:
            await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            url = f"https://www.olx.com.ar/items/q-{kw.replace(' ', '-')}"
            resp = await client.get(url, headers=HEADERS, timeout=10.0)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select("h2, .title, [data-aut-id='itemTitle']")[:8]:
                texto = item.get_text(strip=True)
                parent_link = item.find_parent("a")
                link = parent_link.get("href", url) if parent_link else url
                if len(texto) > 15:
                    resultados.append({
                        "texto": texto,
                        "link": link if link.startswith("http") else f"https://www.olx.com.ar{link}",
                        "fuente": "OLX",
                        "autor": "",
                        "contacto": {"como_contactar": link if link.startswith("http") else f"https://www.olx.com.ar{link}"},
                        "fecha_original": "",
                    })
        except Exception as e:
            print(f"[OLX] Error: {e}")
    return resultados

# ─── QUORA EN ESPAÑOL ─────────────────────────────────────────────────────────

async def scrape_quora(keywords: list, client: httpx.AsyncClient) -> list:
    resultados = []
    for kw in keywords[:2]:
        try:
            await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            url = f"https://es.quora.com/search?q={kw.replace(' ', '+')}"
            resp = await client.get(url, headers=HEADERS, timeout=10.0)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select(".q-text, a[href*='/question/']")[:8]:
                texto = item.get_text(strip=True)
                href = item.get("href", "")
                if len(texto) > 20:
                    link = href if href.startswith("http") else f"https://es.quora.com{href}"
                    resultados.append({
                        "texto": texto,
                        "link": link,
                        "fuente": "Quora",
                        "autor": "",
                        "contacto": {"como_contactar": link},
                        "fecha_original": "",
                    })
        except Exception as e:
            print(f"[Quora] Error: {e}")
    return resultados

# ─── SCORE DE INTENCIÓN ───────────────────────────────────────────────────────

def calcular_score(texto: str) -> int:
    texto_lower = texto.lower()
    score = 0
    alta = [
        "urgente", "ya mismo", "hoy", "lo antes posible", "necesito ya",
        "cuanto antes", "para mañana", "me llegó carta", "me intimaron",
        "embargo", "multa", "ejecución", "carta documento", "me demandaron",
        "me echaron", "me despidieron", "me estafaron", "violencia",
    ]
    score += min(sum(15 for k in alta if k in texto_lower), 60)
    media = [
        "necesito", "busco", "me recomiendan", "cuánto cobra", "precio",
        "honorarios", "contratar", "alguien que", "me pueden recomendar",
        "estudio jurídico", "estudio contable",
    ]
    score += min(sum(10 for k in media if k in texto_lower), 45)
    problema = [
        "problema", "error", "no entiendo", "no sé", "ayuda",
        "afip", "monotributo", "factura", "deuda", "juicio",
        "demanda", "despido", "alquiler", "herencia",
    ]
    score += min(sum(5 for k in problema if k in texto_lower), 30)
    return min(score, 100)

# ─── ORQUESTADOR PRINCIPAL ────────────────────────────────────────────────────

async def scrape_todas_fuentes(keywords_texto: str, servicio: str = "contador", max_results: int = 50) -> list:
    kws_servicio = KEYWORDS.get(servicio, KEYWORDS["contador"])
    kws_custom = [keywords_texto] if keywords_texto else []
    todas_kws = list(set(kws_custom + kws_servicio[:6]))

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        tareas_base = [
            scrape_reddit(todas_kws, servicio, client),
            scrape_twitter(todas_kws, client),
            scrape_todoexpertos(todas_kws, client),
            scrape_mercadolibre(todas_kws, client),
            scrape_olx(todas_kws, client),
            scrape_quora(todas_kws, client),
        ]
        # Fuentes específicas por servicio
        if servicio == "contador":
            tareas_base.append(scrape_forocontable(client))
        elif servicio == "abogado":
            tareas_base.append(scrape_foro_juridico(todas_kws, client))

        tareas = await asyncio.gather(*tareas_base, return_exceptions=True)

    resultados = []
    for t in tareas:
        if isinstance(t, list):
            resultados.extend(t)

    for r in resultados:
        r["score"] = calcular_score(r.get("texto", ""))

    seen = set()
    unique = []
    for r in resultados:
        key = r["texto"][:60].lower()
        if key not in seen:
            seen.add(key)
            unique.append(r)

    unique.sort(key=lambda x: x.get("score", 0), reverse=True)
    print(f"[SCRAPER] {len(unique)} resultados únicos de {len(resultados)} totales")
    return unique[:max_results]
