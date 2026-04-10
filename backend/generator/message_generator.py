"""
Generador de mensajes de contacto naturales y no invasivos
"""

TEMPLATES = {
    "alta": [
        "Hola! Vi que estás buscando un {servicio}. Te puedo ayudar, tengo experiencia en exactamente ese tema. Sin compromiso, si querés charlamos.",
        "Hola! Noté que necesitás ayuda con {tema}. Soy {servicio} y trabajo con ese tipo de casos. ¿Te puedo contar cómo funciona?",
        "Hola! Trabajo como {servicio} y me especializo en {tema}. ¿Querés que te cuente cómo puedo ayudarte?"
    ],
    "media": [
        "Hola! Vi que mencionaste {tema}. Si en algún momento necesitás asesoramiento, estoy disponible para una consulta sin cargo.",
        "Hola! Soy {servicio} y vi tu consulta sobre {tema}. Si necesitás orientación, con gusto te ayudo."
    ],
    "baja": [
        "Hola! Si en algún momento necesitás ayuda con {tema}, no dudes en consultarme. Trabajo como {servicio}."
    ]
}

SERVICIOS = {
    "contador": {"servicio": "contador público", "tema": "AFIP / impuestos"},
    "abogado":  {"servicio": "abogado",           "tema": "temas legales"},
    "afip":     {"servicio": "asesor impositivo",  "tema": "AFIP"},
    "monotributo": {"servicio": "contador",        "tema": "monotributo"},
}

def generate_message(texto_detectado: str, nivel_intencion: str) -> str:
    """
    Genera mensaje personalizado basado en el texto detectado y nivel de intención.
    """
    import random

    # Detectar tipo de servicio
    ctx = {"servicio": "profesional", "tema": "tu consulta"}
    texto_lower = texto_detectado.lower()
    for kw, vals in SERVICIOS.items():
        if kw in texto_lower:
            ctx = vals
            break

    templates = TEMPLATES.get(nivel_intencion, TEMPLATES["baja"])
    template = random.choice(templates)
    return template.format(**ctx)
