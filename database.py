"""
Base de datos SQLite - modelo de datos de leads
"""
import sqlite3
from typing import Optional
from datetime import datetime

DB_PATH = "../data/intento.db"

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
            nivel_intencion  TEXT NOT NULL,  -- alta / media / baja / sin_intencion
            fuente           TEXT,            -- reddit / twitter / google / manual
            link             TEXT,
            fecha            TEXT,
            contactado       INTEGER DEFAULT 0,
            mensaje_enviado  TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("[DB] Inicializada correctamente")

def save_lead(lead: dict) -> int:
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO leads (texto_detectado, nivel_intencion, fuente, link, fecha)
           VALUES (?, ?, ?, ?, ?)""",
        (lead["texto_detectado"], lead["nivel_intencion"],
         lead.get("fuente",""), lead.get("link",""),
         lead.get("fecha", datetime.now().isoformat()))
    )
    conn.commit()
    lead_id = cur.lastrowid
    conn.close()
    return lead_id

def get_leads(intencion: Optional[str] = None, fuente: Optional[str] = None, limit: int = 50):
    conn = get_conn()
    query = "SELECT * FROM leads WHERE 1=1"
    params = []
    if intencion:
        query += " AND nivel_intencion = ?"
        params.append(intencion)
    if fuente:
        query += " AND fuente = ?"
        params.append(fuente)
    query += " ORDER BY fecha DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    alta = conn.execute("SELECT COUNT(*) FROM leads WHERE nivel_intencion='alta'").fetchone()[0]
    media = conn.execute("SELECT COUNT(*) FROM leads WHERE nivel_intencion='media'").fetchone()[0]
    baja = conn.execute("SELECT COUNT(*) FROM leads WHERE nivel_intencion='baja'").fetchone()[0]
    contactados = conn.execute("SELECT COUNT(*) FROM leads WHERE contactado=1").fetchone()[0]
    conn.close()
    return {
        "total": total,
        "alta_intencion": alta,
        "media_intencion": media,
        "baja_intencion": baja,
        "contactados": contactados,
        "tasa_conversion": round(contactados / total * 100, 1) if total > 0 else 0
    }
