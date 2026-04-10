"""
Scraper usando Google Custom Search API (legal, gratuita hasta 100 queries/dia)
y Reddit JSON API (publica sin login)
"""
import requests
import time
from datetime import datetime

GOOGLE_API_KEY = "TU_API_KEY_AQUI"
GOOGLE_CX      = "TU_CX_AQUI"
REDDIT_BASE    = "https://www.reddit.com/search.json"

class GoogleScraper:
    def search(self, keywords: str) -> list:
        results = []
        results += self._search_reddit(keywords)
        results += self._search_google_cse(keywords)
        return results

    def _search_reddit(self, keywords: str) -> list:
        leads = []
        try:
            params = {"q": keywords, "sort": "new", "limit": 25, "type": "link"}
            headers = {"User-Agent": "IntentoBotMVP/1.0"}
            r = requests.get(REDDIT_BASE, params=params, headers=headers, timeout=10)
            data = r.json()
            for post in data.get("data", {}).get("children", []):
                p = post["data"]
                texto = p.get("title","") + " " + p.get("selftext","")[:300]
                leads.append({
                    "texto": texto.strip(),
                    "fuente": "reddit",
                    "link": f"https://reddit.com{p.get('permalink','')}",
                    "fecha": datetime.now().isoformat()
                })
            time.sleep(1)
        except Exception as e:
            print(f"[Reddit] Error: {e}")
        return leads

    def _search_google_cse(self, keywords: str) -> list:
        leads = []
        if GOOGLE_API_KEY == "TU_API_KEY_AQUI":
            return leads
        try:
            params = {"key": GOOGLE_API_KEY, "cx": GOOGLE_CX, "q": keywords, "num": 10}
            r = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=10)
            data = r.json()
            for item in data.get("items", []):
                leads.append({
                    "texto": item.get("title","") + ". " + item.get("snippet",""),
                    "fuente": "google",
                    "link": item.get("link",""),
                    "fecha": datetime.now().isoformat()
                })
        except Exception as e:
            print(f"[Google CSE] Error: {e}")
        return leads
