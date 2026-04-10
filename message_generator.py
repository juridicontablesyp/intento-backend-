"""
message_generator.py - Genera mensajes de contacto personalizados con IA
Usa Claude API (o Ollama local como fallback)
"""
import httpx
import os

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """Sos un experto en ventas consultivas para profesionales independientes argentinos.
Tu tarea es redactar mensajes de contacto para personas que están buscando un servicio profesional.

REGLAS:
- Máximo 3 oraciones
- Tono natural y humano, no robótico
- No sonar como spam ni vendedor agresivo  
- Hacer referencia sutil al problema específico que mencionó la persona
- Terminar con una pregunta abierta o una oferta de ayuda concreta
- Usar lenguaje argentino casual (podés tutear)
- NUNCA mencionar que usás IA ni que encontraste el mensaje de forma automatizada
- El mensaje debe parecer que lo escribió una persona real"""

async def generate_message(texto_lead: str, servicio: str = "contador") -> str:
    """
    Genera un mensaje de contacto personalizado para un lead.
    """
    if not ANTHROPIC_API_KEY:
        return _fallback_message(texto_lead, servicio)

    prompt = f"""La persona escribió esto en internet:
"{texto_lead}"

Están buscando o necesitan: {servicio}

Generá un mensaje corto y natural para contactarlos y ofrecerles ayuda."""

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 200,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": prompt}],
                }
            )
            data = resp.json()
            return data["content"][0]["text"].strip()
    except Exception as e:
        print(f"Error generando mensaje: {e}")
        return _fallback_message(texto_lead, servicio)

def _fallback_message(texto: str, servicio: str) -> str:
    """Mensajes de fallback por plantilla si no hay API key."""
    templates = {
        "contador": [
            "¡Hola! Vi que tenés dudas con el monotributo. Soy contador y puedo ayudarte a resolverlo rápido. ¿Cuál es tu situación puntual?",
            "Hola, pasé por acá y vi tu consulta. Te puedo dar una mano con los temas de AFIP sin vueltas. ¿Querés que hablemos?",
            "Hey, vi que estás buscando un contador. Trabajo con clientes en situaciones similares, si querés te cuento cómo te puedo ayudar.",
        ],
        "abogado": [
            "Hola, vi tu consulta legal. Soy abogado y puedo orientarte sin compromiso. ¿Qué necesitás exactamente?",
        ],
    }
    import random
    msgs = templates.get(servicio, templates["contador"])
    return random.choice(msgs)
