"""
Clasificador de intención por reglas + opcionalmente Ollama (IA local)
"""
import re

# Palabras clave por nivel de intencion
ALTA_INTENCION = [
    "necesito contador urgente", "busco contador", "necesito un contador",
    "alguien me recomiende contador", "problema afip urgente", "me bloquearon afip",
    "me cayó una multa", "deuda afip", "necesito asesor impositivo",
    "me dieron de baja el monotributo", "no puedo pagar afip",
    "necesito abogado urgente", "busco abogado", "necesito un abogado",
    "me iniciaron juicio", "me demandaron", "necesito defensa"
]

MEDIA_INTENCION = [
    "contador", "monotributo", "afip", "factura", "ganancias", "iva",
    "responsable inscripto", "autónomo", "declaracion jurada",
    "abogado", "juicio", "demanda", "contrato", "herencia", "divorcio",
    "asesor", "consulta impositiva"
]

BAJA_INTENCION = [
    "impuestos", "facturar", "cobrar", "deuda", "legal", "asesoramiento",
    "cómo funciona", "qué pasa si", "me conviene"
]

def classify_intent(texto: str) -> str:
    """
    Clasifica el texto en: alta / media / baja / sin_intencion
    Primero reglas, luego opcionalmente Ollama.
    """
    texto_lower = texto.lower()

    # Alta intención: frases exactas de búsqueda activa
    for phrase in ALTA_INTENCION:
        if phrase in texto_lower:
            return "alta"

    # Contar señales
    media_count = sum(1 for kw in MEDIA_INTENCION if kw in texto_lower)
    baja_count  = sum(1 for kw in BAJA_INTENCION  if kw in texto_lower)

    # Detectar patrones de intención activa
    patrones_alta = [
        r"necesito\s+(un\s+)?(contador|abogado|asesor)",
        r"busco\s+(un\s+)?(contador|abogado|asesor)",
        r"alguien\s+(me\s+)?recomiende",
        r"(no\s+)?puedo\s+(pagar|facturar|declarar)",
        r"me\s+(cayó|bloquearon|dieron de baja|demandaron|iniciaron)",
        r"(tengo|hay)\s+.{0,20}(problema|deuda|multa|lío).{0,20}(afip|impuesto|fisco)",
    ]
    for patron in patrones_alta:
        if re.search(patron, texto_lower):
            return "alta"

    if media_count >= 2:
        return "media"
    if media_count == 1 or baja_count >= 2:
        return "baja"

    return "sin_intencion"

# OPCION: Usar Ollama para clasificacion mas precisa
def classify_with_ollama(texto: str) -> str:
    """
    Requiere Ollama corriendo localmente: ollama run llama3
    Solo usar si reglas no alcanzan.
    """
    try:
        import requests
        prompt = f"""Clasificá el siguiente texto segun si la persona NECESITA contratar un contador o abogado AHORA.
Responde SOLO con una de estas palabras: alta / media / baja / sin_intencion

Texto: "{texto}"
Respuesta:"""
        r = requests.post("http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": False}, timeout=15)
        resp = r.json().get("response","").strip().lower()
        for nivel in ["alta", "media", "baja", "sin_intencion"]:
            if nivel in resp:
                return nivel
    except Exception as e:
        print(f"[Ollama] No disponible: {e}")
    return classify_intent(texto)  # fallback a reglas
