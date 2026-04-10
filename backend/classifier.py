"""
classifier.py - Clasificación de intención por reglas de palabras clave
Simple, rápido, sin dependencias de IA (opcional: integrar Ollama después)
"""

# ─── REGLAS DE INTENCIÓN ─────────────────────────────────────────────────────

ALTA_INTENCION = [
    # Urgencia explícita
    "necesito urgente", "urgente", "para mañana", "lo antes posible",
    "ya mismo", "hoy mismo", "cuanto antes",
    # Búsqueda activa
    "busco contador", "necesito contador", "busco abogado", "necesito abogado",
    "quiero contratar", "me recomiendan", "alguien me puede recomendar",
    "cuánto cobra", "cuanto cobra", "precio", "honorarios", "tarifa",
    # Problema concreto grave
    "me llegó carta documento", "me intiman", "carta de afip",
    "me ejecutaron", "embargo", "deuda afip", "multa afip",
    "me dieron de baja", "me cancelaron", "monotributo vencido",
]

MEDIA_INTENCION = [
    # Consultas con intención implícita
    "cómo hago para", "como hago para", "qué necesito para", "que necesito para",
    "dónde puedo", "donde puedo", "me conviene",
    "consulta", "pregunta", "ayuda con",
    # Problemas que llevan a contratar
    "no entiendo", "no sé cómo", "no se como",
    "problema con monotributo", "problema con afip",
    "me rechazaron", "me denegaron",
    "primera vez que", "recién empiezo", "estoy empezando",
    "monotributo", "factura", "afip", "inscribirme",
]

BAJA_INTENCION = [
    # Curiosidad o información general
    "qué es", "que es", "para qué sirve", "para que sirve",
    "alguien sabe", "me pregunto", "curiosidad",
    "vi que", "leí que", "lei que",
    "hace tiempo", "en algún momento",
]

def classify_intent(texto: str) -> str:
    """
    Clasifica el nivel de intención de un texto.
    Retorna: 'alta', 'media', o 'baja'
    """
    texto_lower = texto.lower()

    # Score ponderado
    score_alta = sum(2 for kw in ALTA_INTENCION if kw in texto_lower)
    score_media = sum(1 for kw in MEDIA_INTENCION if kw in texto_lower)
    score_baja = sum(0.5 for kw in BAJA_INTENCION if kw in texto_lower)

    total = score_alta + score_media + score_baja

    if total == 0:
        return "baja"

    if score_alta >= 1:
        return "alta"
    elif score_media >= 2 or (score_media >= 1 and score_baja == 0):
        return "media"
    else:
        return "baja"

def get_intent_reason(texto: str) -> list:
    """Retorna qué palabras clave dispararon la clasificación (para debug)."""
    texto_lower = texto.lower()
    matched = []
    for kw in ALTA_INTENCION:
        if kw in texto_lower:
            matched.append(("alta", kw))
    for kw in MEDIA_INTENCION:
        if kw in texto_lower:
            matched.append(("media", kw))
    return matched
