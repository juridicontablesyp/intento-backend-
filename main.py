from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from datetime import datetime
from database import init_db, get_leads, save_lead, get_stats, marcar_contactado
from classifier import classify_intent
from message_generator import generate_message
from scraper import scrape_todas_fuentes

app = FastAPI(title="Intento API", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/api/leads")
def list_leads(intencion=None, fuente=None):
    return get_leads(intencion=intencion, fuente=fuente)

@app.get("/api/stats")
def stats():
    return get_stats()

@app.post("/api/scan")
def scan(background_tasks: BackgroundTasks, keywords: str = "necesito contador", servicio: str = "contador"):
    background_tasks.add_task(run_scan, keywords, servicio)
    return {"status": "scanning", "keywords": keywords}

def run_scan(keywords: str, servicio: str = "contador"):
    resultados = asyncio.run(scrape_todas_fuentes(keywords, servicio))
    saved = 0
    for r in resultados:
        nivel = classify_intent(r["texto"])
        lead = {
            "texto_detectado": r["texto"],
            "nivel_intencion": nivel,
            "fuente": r["fuente"],
            "link": r["link"],
            "fecha": datetime.now().isoformat(),
            "score": r.get("score", 0),
            "autor": r.get("autor", ""),
            "fecha_original": r.get("fecha_original", ""),
            "contacto": r.get("contacto", {}),
        }
        save_lead(lead)
        saved += 1
    print(f"[SCAN] {saved} leads guardados")

@app.post("/api/leads/manual")
def add_manual_lead(texto: str, fuente: str = "manual", link: str = ""):
    nivel = classify_intent(texto)
    from scraper import calcular_score
    lead = {
        "texto_detectado": texto,
        "nivel_intencion": nivel,
        "fuente": fuente,
        "link": link,
        "fecha": datetime.now().isoformat(),
        "score": calcular_score(texto),
    }
    lead_id = save_lead(lead)
    return {"id": lead_id, **lead}

@app.post("/api/leads/{lead_id}/message")
def get_message(lead_id: int):
    leads = get_leads()
    lead = next((l for l in leads if l["id"] == lead_id), None)
    if not lead:
        return {"error": "Lead no encontrado"}
    msg = generate_message(lead["texto_detectado"], lead.get("nivel_intencion", "media"))
    return {"mensaje": msg}

@app.post("/api/leads/{lead_id}/contactado")
def marcar(lead_id: int):
    marcar_contactado(lead_id)
    return {"ok": True}

@app.get("/")
def root():
    return {"status": "Intento API v2.0 corriendo"}

if __name__ == "__main__":
    init_db()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
