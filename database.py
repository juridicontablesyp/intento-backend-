"""
database.py - SQLite con score e info de contacto
"""
import sqlite3
import json
from typing import Optional
from datetime import datetime

DB_PATH = "/tmp/intento.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            texto_detectado  TEXT NOT NULL,
            nivel_intencion  TEXT NOT NULL,
            fuente           TEXT,
            link             TEXT,
            fecha            TEXT,
            score            INTEGER DEFAULT 0,
            autor            TEXT,
            fecha_original   TEXT,
            contacto         TEXT,
            contactado       INTEGER DEFAULT 0,
            mensaje_enviado  TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_lead(lead: dict) -> int:
    conn = get_conn()
    contacto = lead.get("contacto", {})
    cur = conn.execute(
        """INSERT INTO leads 
           (texto_detectado, nivel_intencion, fuente, link, fecha, score, autor, fecha_original, contacto)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            lead["texto_detectado"],
            lead["nivel_intencion"],
            lead.get("fuente", ""),
            lead.get("link", ""),
            lead.get("fecha", datetime.now().isoformat()),
            lead.get("score", 0),
            lead.get("autor", ""),
            lead.get("fecha_original", ""),
            json.dumps(contacto) if contacto else "",
        )
    )
    conn.commit()
    lead_id = cur.lastrowid
    conn.close()
    return lead_id

def get_leads(intencion=None, fuente=None, limit=100):
    conn = get_conn()
    query = "SELECT * FROM leads WHERE 1=1"
    params = []
    if intencion:
        query += " AND nivel_intencion = ?"
        params.append(intencion)
    if fuente:
        query += " AND fuente = ?"
        params.append(fuente)
    query += " ORDER BY score DESC, fecha DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get("contacto"):
            try:
                d["contacto"] = json.loads(d["contacto"])
            except:
                d["contacto"] = {}
        result.append(d)
    return result

def get_stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    alta = conn.execute("SELECT COUNT(*) FROM leads WHERE nivel_intencion='alta'").fetchone()[0]
    media = conn.execute("SELECT COUNT(*) FROM leads WHERE nivel_intencion='media'").fetchone()[0]
    baja = conn.execute("SELECT COUNT(*) FROM leads WHERE nivel_intencion='baja'").fetchone()[0]
    contactados = conn.execute("SELECT COUNT(*) FROM leads WHERE contactado=1").fetchone()[0]
    tasa = round((contactados / total * 100), 1) if total > 0 else 0
    conn.close()
    return {"total": total, "alta_intencion": alta, "media_intencion": media, "baja_intencion": baja, "contactados": contactados, "tasa_conversion": tasa}

def marcar_contactado(lead_id: int):
    conn = get_conn()
    conn.execute("UPDATE leads SET contactado=1 WHERE id=?", (lead_id,))
    conn.commit()
    conn.close()
